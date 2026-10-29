//all SQL about users (a “repository” is a class that holds the queries for one table)
using Microsoft.Data.Sqlite;

public class UserRepository
{
    private readonly Database _db;

    public UserRepository(Database db)
    {
        _db = db;
    }
    public bool UserExists(string email)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT COUNT(*) FROM \"User\" WHERE user_email = $email";
        cmd.Parameters.AddWithValue("$email", email);

        var hasEqualEmail= Convert.ToBoolean(cmd.ExecuteScalar());
        return hasEqualEmail;
    }

      public string? GetPasswordHashByEmail(string email)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT user_password_hash FROM \"User\" WHERE user_email = $email";
        cmd.Parameters.AddWithValue("$email", email);

        var passHash = (cmd.ExecuteScalar() as string);
        return passHash;
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
    public UserRecord? GetByEmail(string email)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            SELECT user_id, user_name, user_email, user_password_hash, user_role, is_active
            FROM ""User""
            WHERE user_email = $email";
        cmd.Parameters.AddWithValue("$email", email);

        using var reader = cmd.ExecuteReader();
        if (!reader.Read())
            return null;

        return new UserRecord(
            reader.GetInt64(0),
            reader.IsDBNull(1) ? "" : reader.GetString(1),
            reader.IsDBNull(2) ? "" : reader.GetString(2),
            reader.IsDBNull(3) ? "" : reader.GetString(3),
            reader.IsDBNull(4) ? "user" : reader.GetString(4),
            !reader.IsDBNull(5) && reader.GetInt64(5) == 1);
    }

    // Returns false when the email is already registered.
    public bool TryAdd(string name, string email, string passwordHash)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            INSERT INTO ""User""
                (user_name, user_email, user_password_hash, user_role, is_active, created_at_utc, updated_at_utc)
            VALUES
                ($name, $email, $hash, 'user', 1, $now, $now)";

        cmd.Parameters.AddWithValue("$name", name);
        cmd.Parameters.AddWithValue("$email", email);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        cmd.Parameters.AddWithValue("$hash", passwordHash);

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