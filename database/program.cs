using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton(new Database("Data Source=database.db"));
builder.Services.AddSingleton<UserRepository>();

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

app.Run();