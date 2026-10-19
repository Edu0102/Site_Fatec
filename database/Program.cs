using System.Security.Claims;
using System.Security.Cryptography;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.FileProviders;

var builder = WebApplication.CreateBuilder(args);

builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Services.AddDataProtection()
    .PersistKeysToFileSystem(new DirectoryInfo(Path.Combine(builder.Environment.ContentRootPath, "keys")));

builder.Services.AddDbContext<PortalDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("PortalDatabase") ?? "Data Source=portal.db"));
builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.LoginPath = "/login.html";
        options.Cookie.Name = "FatecPortal.Auth";
        options.Cookie.HttpOnly = true;
        options.Cookie.SameSite = SameSiteMode.Lax;
        options.ExpireTimeSpan = TimeSpan.FromHours(8);
        options.SlidingExpiration = true;
    });

var app = builder.Build();

await using (var scope = app.Services.CreateAsyncScope())
{
    var db = scope.ServiceProvider.GetRequiredService<PortalDbContext>();
    await db.Database.MigrateAsync();
    if (!await db.Users.AnyAsync())
    {
        db.Users.Add(new PortalUser
        {
            UserEmail = "admin@teste.com",
            UserName = "Administrador",
            UserPasswordHash = Passwords.Hash("Senha123"),
            UserRole = "admin",
            IsActive = true,
            CreatedAtUtc = DateTime.UtcNow,
            UpdatedAtUtc = DateTime.UtcNow
        });
    }
    if (!await db.Users.AnyAsync(user => user.UserEmail == "usuario@teste.com"))
    {
        db.Users.Add(new PortalUser
        {
            UserEmail = "usuario@teste.com",
            UserName = "Usuário de teste",
            UserPasswordHash = Passwords.Hash("Senha123"),
            UserRole = "basic",
            IsActive = true,
            CreatedAtUtc = DateTime.UtcNow,
            UpdatedAtUtc = DateTime.UtcNow
        });
    }
    await db.SaveChangesAsync();
}

app.UseAuthentication();

app.MapPost("/api/auth/login", async (LoginRequest request, HttpContext context, PortalDbContext db) =>
{
    var email = request.Email?.Trim().ToLowerInvariant();
    if (string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(request.Password))
        return Results.BadRequest(new { message = "E-mail e senha são obrigatórios." });

    var user = await db.Users.SingleOrDefaultAsync(item => item.UserEmail == email);
    if (user is null || !user.IsActive || !Passwords.Verify(request.Password, user.UserPasswordHash))
        return Results.Unauthorized();

    var claims = new[]
    {
        new Claim(ClaimTypes.NameIdentifier, user.UserId.ToString()),
        new Claim(ClaimTypes.Name, user.UserName),
        new Claim(ClaimTypes.Email, user.UserEmail),
        new Claim(ClaimTypes.Role, user.UserRole == "admin" ? "Administrator" : "Basic")
    };
    await context.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme,
        new ClaimsPrincipal(new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme)),
        new AuthenticationProperties { IsPersistent = request.Remember, ExpiresUtc = DateTimeOffset.UtcNow.AddHours(8) });
    return Results.Ok(new { name = user.UserName, email = user.UserEmail, isAdmin = user.UserRole == "admin" });
});

app.MapPost("/api/auth/logout", async (HttpContext context) =>
{
    await context.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
    return Results.NoContent();
});

app.MapPost("/api/users", async (RegisterUserRequest request, HttpContext context, PortalDbContext db) =>
{
    if (context.User.Identity?.IsAuthenticated != true || !context.User.IsInRole("Administrator"))
        return Results.Forbid();

    var name = request.Name?.Trim();
    var email = request.Email?.Trim().ToLowerInvariant();
    if (string.IsNullOrWhiteSpace(name) || string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(request.Password))
        return Results.BadRequest(new { message = "Nome, e-mail e senha são obrigatórios." });
    if (request.Password.Length < 6)
        return Results.BadRequest(new { message = "A senha deve ter ao menos 6 caracteres." });
    if (!System.Net.Mail.MailAddress.TryCreate(email, out _))
        return Results.BadRequest(new { message = "Informe um e-mail válido." });
    if (await db.Users.AnyAsync(user => user.UserEmail == email))
        return Results.Conflict(new { message = "Já existe um usuário com este e-mail." });

    var user = new PortalUser
    {
        UserName = name,
        UserEmail = email,
        UserPasswordHash = Passwords.Hash(request.Password),
        UserRole = "basic",
        IsActive = true,
        CreatedAtUtc = DateTime.UtcNow,
        UpdatedAtUtc = DateTime.UtcNow
    };
    db.Users.Add(user);
    await db.SaveChangesAsync();
    return Results.Created($"/api/users/{user.UserId}", new { name = user.UserName, email = user.UserEmail });
});

app.MapGet("/api/auth/me", (HttpContext context) =>
{
    if (context.User.Identity?.IsAuthenticated != true) return Results.Unauthorized();
    return Results.Ok(new
    {
        name = context.User.Identity.Name,
        email = context.User.FindFirstValue(ClaimTypes.Email),
        isAdmin = context.User.IsInRole("Administrator")
    });
});

var portalRoot = Path.GetFullPath(Path.Combine(app.Environment.ContentRootPath, "..", "wwwroot"));
var portalFiles = new PhysicalFileProvider(portalRoot);

app.Use(async (context, next) =>
{
    var path = context.Request.Path;
    var isPublic = path.StartsWithSegments("/login.html") ||
                   path.StartsWithSegments("/api/auth/login") ||
                   path.StartsWithSegments("/css") ||
                   path.StartsWithSegments("/js") ||
                   path.StartsWithSegments("/assets") ||
                   path == "/favicon.ico";
    if (path.StartsWithSegments("/html/cadastro.html") &&
        (context.User.Identity?.IsAuthenticated != true || !context.User.IsInRole("Administrator")))
    {
        if (context.User.Identity?.IsAuthenticated == true)
        {
            context.Response.StatusCode = StatusCodes.Status403Forbidden;
        }
        else
        {
            context.Response.Redirect("/login.html");
        }
        return;
    }
    if (!isPublic && context.User.Identity?.IsAuthenticated != true)
    {
        if (path.StartsWithSegments("/api"))
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            return;
        }
        context.Response.Redirect("/login.html");
        return;
    }
    await next();
});

app.UseDefaultFiles(new DefaultFilesOptions { FileProvider = portalFiles });
app.UseStaticFiles(new StaticFileOptions { FileProvider = portalFiles });
app.Run();

record LoginRequest(string? Email, string? Password, bool Remember);
record RegisterUserRequest(string? Name, string? Email, string? Password);

sealed class PortalDbContext(DbContextOptions<PortalDbContext> options) : DbContext(options)
{
    public DbSet<PortalUser> Users => Set<PortalUser>();
    public DbSet<Department> Departments => Set<Department>();
    public DbSet<Pop> Pops => Set<Pop>();
    public DbSet<UserDepartment> UserDepartments => Set<UserDepartment>();
    public DbSet<PortalLink> Links => Set<PortalLink>();
    public DbSet<Feedback> Feedbacks => Set<Feedback>();
    public DbSet<Checklist> Checklists => Set<Checklist>();
    public DbSet<StandardCheck> StandardChecks => Set<StandardCheck>();
    public DbSet<ChecklistItemResult> ChecklistItemResults => Set<ChecklistItemResult>();
    public DbSet<PopLink> PopLinks => Set<PopLink>();
    public DbSet<PopDepartment> PopDepartments => Set<PopDepartment>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ConfigurePortalSchema();
    }
}

static class Passwords
{
    private const int Iterations = 210_000;
    public static string Hash(string password)
    {
        var salt = RandomNumberGenerator.GetBytes(16);
        var hash = Rfc2898DeriveBytes.Pbkdf2(password, salt, Iterations, HashAlgorithmName.SHA512, 32);
        return $"{Iterations}.{Convert.ToBase64String(salt)}.{Convert.ToBase64String(hash)}";
    }
    public static bool Verify(string password, string storedValue)
    {
        var parts = storedValue.Split('.');
        if (parts.Length != 3 || !int.TryParse(parts[0], out var iterations)) return false;
        try
        {
            var salt = Convert.FromBase64String(parts[1]);
            var expected = Convert.FromBase64String(parts[2]);
            var actual = Rfc2898DeriveBytes.Pbkdf2(password, salt, iterations, HashAlgorithmName.SHA512, expected.Length);
            return CryptographicOperations.FixedTimeEquals(actual, expected);
        }
        catch (FormatException) { return false; }
    }
}
