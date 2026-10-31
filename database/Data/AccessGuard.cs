// Answers "may this user do admin things?" by asking the database,
// so a stale cookie or a role passed by the caller can never grant access.
public class AccessGuard
{
    private readonly Database _db;

    public AccessGuard(Database db)
    {
        _db = db;
    }

    public bool IsActiveAdmin(long userId)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            SELECT COUNT(*) FROM ""User""
            WHERE user_id = $userId AND user_role = 'admin' AND is_active = 1";
        cmd.Parameters.AddWithValue("$userId", userId);

        return (long)cmd.ExecuteScalar()! > 0;
    }
}
