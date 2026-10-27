var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton(new Database("Data Source=database.db"));
builder.Services.AddSingleton<UserRepository>();

var app = builder.Build();

app.Services.GetRequiredService<Database>().Initialize();

app.MapGet("/", () => "Server is running");

app.MapGet("/users", (UserRepository users) =>
    Results.Ok(users.GetActiveUserNames()));

app.MapPost("/add-user", (NewUser user, UserRepository users) =>
{
    if (string.IsNullOrWhiteSpace(user.Name) || string.IsNullOrWhiteSpace(user.Email))
        return Results.BadRequest(new { error = "Name and email are required." });

    return users.TryAdd(user.Name.Trim(), user.Email.Trim())
        ? Results.Ok(new { message = "User added." })
        : Results.Conflict(new { error = "This email is already registered." });
});

app.Run();