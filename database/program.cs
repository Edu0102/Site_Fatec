using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton(new Database("Data Source=database.db;Foreign Keys=True"));
builder.Services.AddSingleton<UserRepository>();
builder.Services.AddSingleton<DepartmentRepository>();
builder.Services.AddSingleton<UserDepartmentRepository>();
builder.Services.AddSingleton<PopRepository>();
builder.Services.AddSingleton<LinkRepository>();
builder.Services.AddSingleton<PhoneRepository>();
builder.Services.AddSingleton<PopLinkRepository>();
builder.Services.AddSingleton<PopPhoneRepository>();
builder.Services.AddSingleton<PopDepartmentRepository>();

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

app.MapGet("/pops", (ClaimsPrincipal user, PopRepository pops) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    var role = user.FindFirst(ClaimTypes.Role)?.Value ?? "basic";
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    return Results.Ok(pops.GetAllForUser(userId, role));
}).RequireAuthorization();

app.MapGet("/pops/{popId:long}", (long popId, ClaimsPrincipal user, PopRepository pops) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    var role = user.FindFirst(ClaimTypes.Role)?.Value ?? "basic";
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    var pop = pops.GetByIdForUser(popId, userId, role);
    return pop is null
        ? Results.NotFound(new { error = "POP not found or not available." })
        : Results.Ok(pop);
}).RequireAuthorization();

app.MapPost("/pops", (NewPop req, ClaimsPrincipal user, PopRepository pops) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    if (string.IsNullOrWhiteSpace(req.Title))
        return Results.BadRequest(new { error = "Title is required." });
    var status = string.IsNullOrWhiteSpace(req.Status) ? "draft" : req.Status.Trim().ToLowerInvariant();
    if (status != "draft" && status != "published" && status != "archived")
        return Results.BadRequest(new { error = "Status must be draft, published or archived." });
    return pops.TryAdd(req.Title.Trim(), req.Description?.Trim(), req.FilePath?.Trim(), req.Version?.Trim(), status, userId)
        ? Results.Ok(new { message = "POP created." })
        : Results.BadRequest(new { error = "The creator does not exist." });
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPut("/pops/{popId:long}", (long popId, UpdatePop req, ClaimsPrincipal user, PopRepository pops) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    if (string.IsNullOrWhiteSpace(req.Title))
        return Results.BadRequest(new { error = "Title is required." });
    var status = req.Status?.Trim().ToLowerInvariant() ?? "";
    if (status != "draft" && status != "published" && status != "archived")
        return Results.BadRequest(new { error = "Status must be draft, published or archived." });
    return pops.TryUpdate(popId, req.Title.Trim(), req.Description?.Trim(), req.FilePath?.Trim(), req.Version?.Trim(), status, userId)
        ? Results.Ok(new { message = "POP updated." })
        : Results.NotFound(new { error = "POP not found." });
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPost("/pops/{popId:long}/archive", (long popId, ClaimsPrincipal user, PopRepository pops) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    return pops.TryArchive(popId, userId)
        ? Results.Ok(new { message = "POP archived." })
        : Results.NotFound(new { error = "POP not found." });
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapGet("/links", (LinkRepository links) => Results.Ok(links.GetAll()))
    .RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPost("/links", (NewLink req, LinkRepository links) =>
{
    if (string.IsNullOrWhiteSpace(req.Path))
        return Results.BadRequest(new { error = "Path is required." });
    return links.TryAdd(req.Path.Trim())
        ? Results.Ok(new { message = "Link created." })
        : Results.Conflict(new { error = "This link path already exists." });
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPut("/links/{linkId:long}", (long linkId, UpdateLink req, LinkRepository links) =>
{
    if (string.IsNullOrWhiteSpace(req.Path))
        return Results.BadRequest(new { error = "Path is required." });
    return links.TryUpdate(linkId, req.Path.Trim())
        ? Results.Ok(new { message = "Link updated." })
        : Results.NotFound(new { error = "Link not found or duplicate path." });
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapGet("/phones", (PhoneRepository phones) => Results.Ok(phones.GetAll()))
    .RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPost("/phones", (NewPhone req, PhoneRepository phones) =>
{
    if (string.IsNullOrWhiteSpace(req.PhoneNumber))
        return Results.BadRequest(new { error = "Phone number is required." });
    return phones.TryAdd(req.PhoneNumber.Trim())
        ? Results.Ok(new { message = "Phone number created." })
        : Results.Conflict(new { error = "This phone number already exists." });
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPut("/phones/{phoneId:long}", (long phoneId, UpdatePhone req, PhoneRepository phones) =>
{
    if (string.IsNullOrWhiteSpace(req.PhoneNumber))
        return Results.BadRequest(new { error = "Phone number is required." });
    return phones.TryUpdate(phoneId, req.PhoneNumber.Trim())
        ? Results.Ok(new { message = "Phone number updated." })
        : Results.NotFound(new { error = "Phone number not found or duplicate number." });
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapGet("/pops/{popId:long}/links", (long popId, ClaimsPrincipal user, PopRepository pops, PopLinkRepository popLinks) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    var role = user.FindFirst(ClaimTypes.Role)?.Value ?? "basic";
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    return pops.GetByIdForUser(popId, userId, role) is null
        ? Results.NotFound(new { error = "POP not found or not available." })
        : Results.Ok(popLinks.GetLinksForPop(popId));
}).RequireAuthorization();

app.MapPost("/pop-links", (AssignPopLink req, PopLinkRepository popLinks) =>
    popLinks.TryAssign(req.PopId, req.LinkId)
        ? Results.Ok(new { message = "Link assigned to POP." })
        : Results.BadRequest(new { error = "POP or link does not exist, or already assigned." }))
    .RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapGet("/pops/{popId:long}/phones", (long popId, ClaimsPrincipal user, PopRepository pops, PopPhoneRepository popPhones) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    var role = user.FindFirst(ClaimTypes.Role)?.Value ?? "basic";
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    return pops.GetByIdForUser(popId, userId, role) is null
        ? Results.NotFound(new { error = "POP not found or not available." })
        : Results.Ok(popPhones.GetPhonesForPop(popId));
}).RequireAuthorization();

app.MapPost("/pop-phones", (AssignPopPhone req, PopPhoneRepository popPhones) =>
    popPhones.TryAssign(req.PopId, req.PhoneId)
        ? Results.Ok(new { message = "Phone number assigned to POP." })
        : Results.BadRequest(new { error = "POP or phone number does not exist, or already assigned." }))
    .RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapGet("/pops/{popId:long}/departments", (long popId, ClaimsPrincipal user, PopRepository pops, PopDepartmentRepository popDepartments) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    var role = user.FindFirst(ClaimTypes.Role)?.Value ?? "basic";
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    return pops.GetByIdForUser(popId, userId, role) is null
        ? Results.NotFound(new { error = "POP not found or not available." })
        : Results.Ok(popDepartments.GetDepartmentsForPop(popId));
}).RequireAuthorization();

app.MapPost("/pop-departments", (AssignPopDepartment req, PopDepartmentRepository popDepartments) =>
{
    var accessType = string.IsNullOrWhiteSpace(req.AccessType) ? "read" : req.AccessType.Trim();
    return popDepartments.TryAssign(req.PopId, req.DepartmentId, accessType)
        ? Results.Ok(new { message = "Department assigned to POP." })
        : Results.BadRequest(new { error = "POP or department does not exist, or already assigned." });
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.Run();