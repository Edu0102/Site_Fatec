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
            IsAdmin = true
        });
        await db.SaveChangesAsync();
    }
}

app.UseAuthentication();

app.MapPost("/api/auth/login", async (LoginRequest request, HttpContext context, PortalDbContext db) =>
{
    var email = request.Email?.Trim().ToLowerInvariant();
    if (string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(request.Password))
        return Results.BadRequest(new { message = "E-mail e senha são obrigatórios." });

    var user = await db.Users.SingleOrDefaultAsync(item => item.UserEmail == email);
    if (user is null || !Passwords.Verify(request.Password, user.UserPasswordHash))
        return Results.Unauthorized();

    var claims = new[]
    {
        new Claim(ClaimTypes.NameIdentifier, user.UserId.ToString()),
        new Claim(ClaimTypes.Name, user.UserName),
        new Claim(ClaimTypes.Email, user.UserEmail),
        new Claim(ClaimTypes.Role, user.IsAdmin ? "Administrator" : "Basic")
    };
    await context.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme,
        new ClaimsPrincipal(new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme)),
        new AuthenticationProperties { IsPersistent = request.Remember, ExpiresUtc = DateTimeOffset.UtcNow.AddHours(8) });
    return Results.Ok(new { name = user.UserName, email = user.UserEmail, isAdmin = user.IsAdmin });
});

app.MapPost("/api/auth/logout", async (HttpContext context) =>
{
    await context.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
    return Results.NoContent();
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

sealed class PortalUser
{
    public int UserId { get; set; }
    public required string UserName { get; set; }
    public required string UserEmail { get; set; }
    public required string UserPasswordHash { get; set; }
    public bool IsAdmin { get; set; }
}

sealed class PortalDbContext(DbContextOptions<PortalDbContext> options) : DbContext(options)
{
    public DbSet<PortalUser> Users => Set<PortalUser>();
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<PortalUser>(entity =>
        {
            entity.ToTable("Users");
            entity.HasKey(user => user.UserId);

            entity.Property(user => user.UserId)
                .HasColumnName("user_id")
                .ValueGeneratedOnAdd();
            entity.Property(user => user.UserName)
                .HasColumnName("user_name")
                .HasMaxLength(120)
                .IsRequired();
            entity.Property(user => user.UserEmail)
                .HasColumnName("user_email")
                .HasMaxLength(256)
                .IsRequired();
            entity.Property(user => user.UserPasswordHash)
                .HasColumnName("user_password_hash")
                .HasMaxLength(512)
                .IsRequired();
            entity.Property(user => user.IsAdmin)
                .HasColumnName("user_level")
                .IsRequired();

            entity.HasIndex(user => user.UserEmail)
                .IsUnique()
                .HasDatabaseName("IX_Users_user_email");
        });
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
