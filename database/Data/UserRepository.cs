//all SQL about users (a “repository” is a class that holds the queries for one table)
using Microsoft.Data.Sqlite;

public class UserRepository
{
    private readonly Database _db;

    public UserRepository(Database db)
    {
        _db = db;
    }

    public List<string> GetActiveUserNames()
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT user_name FROM \"User\" WHERE is_active = 1";

        using var reader = cmd.ExecuteReader();
        var names = new List<string>();
        while (reader.Read())
        {
            if (!reader.IsDBNull(0))
                names.Add(reader.GetString(0));
        }
        return names;
    }

    // Returns false when the email is already registered.
    public bool TryAdd(string name, string email)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            INSERT INTO ""User""
                (user_name, user_email, user_password_hash, user_role, is_active, created_at_utc, updated_at_utc)
            VALUES
                ($name, $email, 'temp-hash', 'user', 1, $now, $now)";

        cmd.Parameters.AddWithValue("$name", name);
        cmd.Parameters.AddWithValue("$email", email);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));

        try
        {
            cmd.ExecuteNonQuery();
            return true;
        }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19)
        {
            return false;
        }
    }
}