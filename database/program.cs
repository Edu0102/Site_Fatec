using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton(new Database("Data Source=database.db;Foreign Keys=True"));
builder.Services.AddSingleton<UserRepository>();
builder.Services.AddSingleton<DepartmentRepository>();
builder.Services.AddSingleton<UserDepartmentRepository>();

builder.Services.AddAuthentication("Cookies")
    .AddCookie("Cookies", options =>
    {
        options.Cookie.Name = "site_auth";
        options.Cookie.HttpOnly = true;
        options.ExpireTimeSpan = TimeSpan.FromHours(8);
        options.SlidingExpiration = true;

        // Answer with status codes instead of redirecting to a login page
        options.Events.OnRedirectToLogin = ctx =>
        {
            ctx.Response.StatusCode = 401;
            return Task.CompletedTask;
        };
        options.Events.OnRedirectToAccessDenied = ctx =>
        {
            ctx.Response.StatusCode = 403;
            return Task.CompletedTask;
        };
    });
builder.Services.AddAuthorization();

var app = builder.Build();

app.Services.GetRequiredService<Database>().Initialize();

app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/", () => "Server is running");

app.MapPost("/register", (NewUser user, UserRepository users) =>
{
    if (string.IsNullOrWhiteSpace(user.Name) ||
        string.IsNullOrWhiteSpace(user.Email) ||
        string.IsNullOrWhiteSpace(user.Password))
        return Results.BadRequest(new { error = "Name, email and password are required." });

    if (user.Password.Length < 8)
        return Results.BadRequest(new { error = "Password must have at least 8 characters." });

    var email = user.Email.Trim().ToLowerInvariant();
    var hash = PasswordHasher.Hash(user.Password);

    return users.TryAdd(user.Name.Trim(), email, hash)
        ? Results.Ok(new { message = "User registered." })
        : Results.Conflict(new { error = "This email is already registered." });
});

app.MapPost("/login", async (LoginRequest login, UserRepository users, HttpContext http) =>
{
    var email = (login.Email ?? "").Trim().ToLowerInvariant();
    var user = users.GetByEmail(email);

    // Same answer for every failure, so nobody can tell which part was wrong
    if (user is null || !user.IsActive || !PasswordHasher.Verify(login.Password ?? "", user.PasswordHash))
        return Results.Unauthorized();

    var claims = new List<Claim>
    {
        new(ClaimTypes.NameIdentifier, user.Id.ToString()),
        new(ClaimTypes.Name, user.Name),
        new(ClaimTypes.Email, user.Email),
        new(ClaimTypes.Role, user.Role)
    };
    var identity = new ClaimsIdentity(claims, "Cookies");
    await http.SignInAsync("Cookies", new ClaimsPrincipal(identity));

    return Results.Ok(new { message = "Logged in." });
});

app.MapPost("/logout", async (HttpContext http) =>
{
    await http.SignOutAsync("Cookies");
    return Results.Ok(new { message = "Logged out." });
});

app.MapGet("/me", (ClaimsPrincipal user) => Results.Ok(new
{
    name = user.Identity?.Name,
    email = user.FindFirst(ClaimTypes.Email)?.Value,
    role = user.FindFirst(ClaimTypes.Role)?.Value
})).RequireAuthorization();

app.MapGet("/users", (UserRepository users) =>
    Results.Ok(users.GetActiveUserNames()))
    .RequireAuthorization();

app.MapGet("/admin-only", () => Results.Ok(new { secret = "admins only" }))
    .RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapGet("/departments", (DepartmentRepository departments) =>
    Results.Ok(departments.GetAll()))
    .RequireAuthorization();

app.MapPost("/departments", (NewDepartment dept, DepartmentRepository departments) =>
{
    if (string.IsNullOrWhiteSpace(dept.Name) || string.IsNullOrWhiteSpace(dept.Code))
        return Results.BadRequest(new { error = "Name and code are required." });

    var code = dept.Code.Trim().ToUpperInvariant();

    return departments.TryAdd(dept.Name.Trim(), code)
        ? Results.Ok(new { message = "Department created." })
        : Results.Conflict(new { error = "This department code already exists." });
})
.RequireAuthorization(policy => policy.RequireRole("admin"));
app.MapPost("/user-departments", (AssignDepartment req, UserDepartmentRepository repo) =>
{
    var access = string.IsNullOrWhiteSpace(req.AccessType) ? "member" : req.AccessType.Trim();

    return repo.Assign(req.UserId, req.DepartmentId, access)
        ? Results.Ok(new { message = "User assigned to department." })
        : Results.BadRequest(new { error = "User or department does not exist." });
})
.RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapGet("/me/departments", (ClaimsPrincipal user, UserDepartmentRepository repo) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();

    return Results.Ok(repo.GetDepartmentsForUser(userId));
})
.RequireAuthorization();
app.Run();