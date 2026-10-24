using Microsoft.Data.Sqlite;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var connString = "Data Source=database.db";

app.MapGet("/", () => "Server is running");

app.MapGet("/db-test", () =>
{
    using var conn = new SqliteConnection(connString);
    conn.Open();

    using var cmd = conn.CreateCommand();
    cmd.CommandText = "SELECT COUNT(*) FROM \"User\"";
    var count = (long)cmd.ExecuteScalar()!;

    return Results.Ok(new { users = count });
});
app.MapGet("/db-names", () =>//teste numero 2 pegar nome de usuario se for adm
{
    using var conn = new SqliteConnection(connString);
    conn.Open();

    using var cmd = conn.CreateCommand();
    cmd.CommandText = "SELECT user_name FROM \"User\" WHERE is_active = 1";//SELECT name FROM sqlite_master WHERE type = 'table'
    
    using var reader = cmd.ExecuteReader()!;

    var names = new List<string>();
    while (reader.Read())
    {
        names.Add(reader.GetString(0));
    }

    return Results.Ok(names);
});
app.MapGet("/db-adduser", (string name, string email) =>
{
    using var conn = new SqliteConnection(connString);
    conn.Open();

    using var cmd = conn.CreateCommand();
    cmd.CommandText = @"
        INSERT INTO ""USER""
            (user_name, user_email, user_password_hash, user_role, is_active, created_at_utc, updated_at_utc)
        VALUES
            ($name, $email, 'temp-hash', 'basic', 1, $now, $now)";

    cmd.Parameters.AddWithValue("$name", name);
    cmd.Parameters.AddWithValue("$email", email);
    cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));

    var rows = cmd.ExecuteNonQuery();

    return Results.Ok(new{ rowsAdded = rows});   
    

});

app.Run();