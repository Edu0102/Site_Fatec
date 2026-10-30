using Microsoft.Data.Sqlite;

public class PopRepository
{
    private readonly Database _db;

    public PopRepository(Database db)
    {
        _db = db;
    }

    private static PopRecord ReadPop(SqliteDataReader reader)
    {
        return new PopRecord(
            reader.GetInt64(0),
            reader.GetInt64(1),
            reader.GetInt64(2),
            reader.GetString(3),
            reader.IsDBNull(4) ? null : reader.GetString(4),
            reader.IsDBNull(5) ? null : reader.GetString(5),
            reader.IsDBNull(6) ? null : reader.GetString(6),
            reader.GetString(7),
            reader.IsDBNull(8) ? "" : reader.GetString(8),
            reader.IsDBNull(9) ? "" : reader.GetString(9));
    }

    public List<PopRecord> GetAllForUser(long userId, string role)
    {
        var result = new List<PopRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();

        if (role == "admin")
        {
            cmd.CommandText = @"SELECT pop_id, created_by, updated_by, pop_title, pop_description, pop_file_path, pop_version, pop_status, created_at_utc, updated_at_utc
                FROM ""Pop"" ORDER BY pop_id DESC";
        }
        else
        {
            cmd.CommandText = @"SELECT p.pop_id, p.created_by, p.updated_by, p.pop_title, p.pop_description, p.pop_file_path, p.pop_version, p.pop_status, p.created_at_utc, p.updated_at_utc
                FROM ""Pop"" p
                WHERE p.pop_status = 'published'
                AND EXISTS (
                    SELECT 1 FROM ""PopDepartment"" pd
                    JOIN ""UserDepartment"" ud ON ud.department_id = pd.department_id
                    WHERE pd.pop_id = p.pop_id
                    AND ud.user_id = $userId
                    AND ud.revoked_at_utc IS NULL
                    AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > $now)
                )
                ORDER BY p.pop_id DESC";
            cmd.Parameters.AddWithValue("$userId", userId);
            cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        }

        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            result.Add(ReadPop(reader));
        return result;
    }

    public PopRecord? GetByIdForUser(long popId, long userId, string role)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        if (role == "admin")
        {
            cmd.CommandText = @"SELECT pop_id, created_by, updated_by, pop_title, pop_description, pop_file_path, pop_version, pop_status, created_at_utc, updated_at_utc
                FROM ""Pop"" WHERE pop_id = $popId";
        }
        else
        {
            cmd.CommandText = @"SELECT p.pop_id, p.created_by, p.updated_by, p.pop_title, p.pop_description, p.pop_file_path, p.pop_version, p.pop_status, p.created_at_utc, p.updated_at_utc
                FROM ""Pop"" p
                WHERE p.pop_id = $popId AND p.pop_status = 'published'
                AND EXISTS (
                    SELECT 1 FROM ""PopDepartment"" pd
                    JOIN ""UserDepartment"" ud ON ud.department_id = pd.department_id
                    WHERE pd.pop_id = p.pop_id
                    AND ud.user_id = $userId
                    AND ud.revoked_at_utc IS NULL
                    AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > $now)
                )";
            cmd.Parameters.AddWithValue("$userId", userId);
            cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        }
        cmd.Parameters.AddWithValue("$popId", popId);
        using var reader = cmd.ExecuteReader();
        return reader.Read() ? ReadPop(reader) : null;
    }

    public bool TryAdd(string title, string? description, string? filePath, string? version, string status, long userId)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        var now = DateTime.UtcNow.ToString("o");
        cmd.CommandText = @"INSERT INTO ""Pop""
            (created_by, updated_by, pop_title, pop_description, pop_file_path, pop_version, pop_status, created_at_utc, updated_at_utc)
            VALUES ($userId, $userId, $title, $description, $filePath, $version, $status, $now, $now)";
        cmd.Parameters.AddWithValue("$userId", userId);
        cmd.Parameters.AddWithValue("$title", title);
        cmd.Parameters.AddWithValue("$description", description ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("$filePath", filePath ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("$version", version ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("$status", status);
        cmd.Parameters.AddWithValue("$now", now);

        try { return cmd.ExecuteNonQuery() == 1; }
        catch (SqliteException ex) when (ex.SqliteExtendedErrorCode == 787) { return false; }
    }

    public bool TryUpdate(long popId, string title, string? description, string? filePath, string? version, string status, long userId)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"UPDATE ""Pop""
            SET updated_by = $userId, pop_title = $title, pop_description = $description,
                pop_file_path = $filePath, pop_version = $version, pop_status = $status, updated_at_utc = $now
            WHERE pop_id = $popId";
        cmd.Parameters.AddWithValue("$userId", userId);
        cmd.Parameters.AddWithValue("$title", title);
        cmd.Parameters.AddWithValue("$description", description ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("$filePath", filePath ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("$version", version ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("$status", status);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        cmd.Parameters.AddWithValue("$popId", popId);

        try { return cmd.ExecuteNonQuery() == 1; }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19) { return false; }
    }

    public bool TryArchive(long popId, long userId)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"UPDATE ""Pop"" SET updated_by = $userId, pop_status = 'archived', updated_at_utc = $now
            WHERE pop_id = $popId";
        cmd.Parameters.AddWithValue("$userId", userId);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        cmd.Parameters.AddWithValue("$popId", popId);
        return cmd.ExecuteNonQuery() == 1;
    }
}
