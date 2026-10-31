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
builder.Services.AddSingleton<AccessGuard>();

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

app.MapPost("/departments", (NewDepartment dept, ClaimsPrincipal user, DepartmentRepository departments) =>
{
    if (string.IsNullOrWhiteSpace(dept.Name) || string.IsNullOrWhiteSpace(dept.Code))
        return Results.BadRequest(new { error = "Name and code are required." });

    var code = dept.Code.Trim().ToUpperInvariant();

    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    return departments.TryAdd(userId, dept.Name.Trim(), code)
        .ToHttp("Department created.", "Department not found.", "This department code already exists.");
})
.RequireAuthorization();
app.MapPost("/user-departments", (AssignDepartment req, ClaimsPrincipal user, UserDepartmentRepository repo) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    var access = string.IsNullOrWhiteSpace(req.AccessType) ? "member" : req.AccessType.Trim();

    return repo.Assign(userId, req.UserId, req.DepartmentId, access)
        .ToHttp("User assigned to department.", "User or department not found.", "This user is already assigned to the department.");
})
.RequireAuthorization();

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
    return pops.TryAdd(userId, req.Title.Trim(), req.Description?.Trim(), req.FilePath?.Trim(), req.Version?.Trim(), status)
        .ToHttp("POP created.", "The creator does not exist.", "A duplicate POP write was rejected.");
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
    return pops.TryUpdate(userId, popId, req.Title.Trim(), req.Description?.Trim(), req.FilePath?.Trim(), req.Version?.Trim(), status)
        .ToHttp("POP updated.", "POP not found.", "A duplicate POP write was rejected.");
}).RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPost("/pops/{popId:long}/archive", (long popId, ClaimsPrincipal user, PopRepository pops) =>
{
    var idText = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    if (!long.TryParse(idText, out var userId))
        return Results.Unauthorized();
    return pops.TryArchive(userId, popId)
        .ToHttp("POP archived.", "POP not found.");
}).RequireAuthorization(policy => policy.RequireRole("admin"));

// ------------------------------------------------------------------
// Everything below uses WriteResult and lets the repositories decide
// who is allowed to write (AccessGuard). Endpoints only need a login.
// The HTTP developer will replace these routes with their own.
// ------------------------------------------------------------------

app.MapGet("/links", (LinkRepository links) => Results.Ok(links.GetAll()))
    .RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPost("/links", (NewLink req, ClaimsPrincipal user, LinkRepository links) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    if (string.IsNullOrWhiteSpace(req.Path))
        return Results.BadRequest(new { error = "Path is required." });

    return links.Add(userId, req.Path.Trim())
        .ToHttp("Link created.", "Link not found.", "This link path already exists.");
}).RequireAuthorization();

app.MapPut("/links/{linkId:long}", (long linkId, UpdateLink req, ClaimsPrincipal user, LinkRepository links) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    if (string.IsNullOrWhiteSpace(req.Path))
        return Results.BadRequest(new { error = "Path is required." });

    return links.Update(userId, linkId, req.Path.Trim())
        .ToHttp("Link updated.", "Link not found.", "Another link already has this path.");
}).RequireAuthorization();

app.MapGet("/phones", (PhoneRepository phones) => Results.Ok(phones.GetAll()))
    .RequireAuthorization(policy => policy.RequireRole("admin"));

app.MapPost("/phones", (NewPhone req, ClaimsPrincipal user, PhoneRepository phones) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    if (string.IsNullOrWhiteSpace(req.PhoneNumber))
        return Results.BadRequest(new { error = "Phone number is required." });

    return phones.Add(userId, req.PhoneNumber.Trim())
        .ToHttp("Phone number created.", "Phone number not found.", "This phone number already exists.");
}).RequireAuthorization();

app.MapPut("/phones/{phoneId:long}", (long phoneId, UpdatePhone req, ClaimsPrincipal user, PhoneRepository phones) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    if (string.IsNullOrWhiteSpace(req.PhoneNumber))
        return Results.BadRequest(new { error = "Phone number is required." });

    return phones.Update(userId, phoneId, req.PhoneNumber.Trim())
        .ToHttp("Phone number updated.", "Phone number not found.", "This phone number already exists.");
}).RequireAuthorization();

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

app.MapPost("/pop-links", (AssignPopLink req, ClaimsPrincipal user, PopLinkRepository popLinks) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    return popLinks.Assign(userId, req.PopId, req.LinkId)
        .ToHttp("Link assigned to POP.", "POP or link not found.", "This link is already assigned to the POP.");
}).RequireAuthorization();

app.MapDelete("/pops/{popId:long}/links/{linkId:long}", (long popId, long linkId, ClaimsPrincipal user, PopLinkRepository popLinks) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    return popLinks.Remove(userId, popId, linkId)
        .ToHttp("Link removed from POP.", "This link is not assigned to this POP.");
}).RequireAuthorization();

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

app.MapPost("/pop-phones", (AssignPopPhone req, ClaimsPrincipal user, PopPhoneRepository popPhones) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    return popPhones.Assign(userId, req.PopId, req.PhoneId)
        .ToHttp("Phone number assigned to POP.", "POP or phone number not found.", "This phone number is already assigned to the POP.");
}).RequireAuthorization();

app.MapDelete("/pops/{popId:long}/phones/{phoneId:long}", (long popId, long phoneId, ClaimsPrincipal user, PopPhoneRepository popPhones) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    return popPhones.Remove(userId, popId, phoneId)
        .ToHttp("Phone number removed from POP.", "This phone number is not assigned to this POP.");
}).RequireAuthorization();

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

app.MapPost("/pop-departments", (AssignPopDepartment req, ClaimsPrincipal user, PopDepartmentRepository popDepartments) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    var accessType = string.IsNullOrWhiteSpace(req.AccessType) ? "read" : req.AccessType.Trim();

    return popDepartments.Assign(userId, req.PopId, req.DepartmentId, accessType)
        .ToHttp("Department assigned to POP.", "POP or department not found.", "This department is already assigned to the POP.");
}).RequireAuthorization();

app.MapDelete("/pops/{popId:long}/departments/{departmentId:long}", (long popId, long departmentId, ClaimsPrincipal user, PopDepartmentRepository popDepartments) =>
{
    if (!user.TryGetUserId(out var userId))
        return Results.Unauthorized();

    return popDepartments.Remove(userId, popId, departmentId)
        .ToHttp("Department removed from POP.", "This department is not assigned to this POP.");
}).RequireAuthorization();

app.Run();
