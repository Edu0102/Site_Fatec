using Microsoft.Data.Sqlite;

public class UserDepartmentRepository
{
    private readonly Database _db;
    private readonly AccessGuard _guard;

    public UserDepartmentRepository(Database db, AccessGuard guard)
    {
        _db = db;
        _guard = guard;
    }

    public WriteResult Assign(long actorUserId, long userId, long departmentId, string accessType)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            INSERT INTO ""UserDepartment""
                (user_id, department_id, access_type, valid_from_utc)
            VALUES
                ($userId, $departmentId, $accessType, $now)";

        cmd.Parameters.AddWithValue("$userId", userId);
        cmd.Parameters.AddWithValue("$departmentId", departmentId);
        cmd.Parameters.AddWithValue("$accessType", accessType);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));

        try
        {
            cmd.ExecuteNonQuery();
            return WriteResult.Ok;
        }
        catch (SqliteException ex) when (ex.IsForeignKey())
        {
            return WriteResult.NotFound;
        }
        catch (SqliteException ex) when (ex.IsUnique())
        {
            return WriteResult.Conflict;
        }
    }
    
    public List<DepartmentRecord> GetDepartmentsForUser(long userId)
{
    var departments = new List<DepartmentRecord>();
    using var conn = _db.OpenConnection();
    using var cmd = conn.CreateCommand();
    cmd.CommandText = @"
        SELECT d.department_id, d.department_name, d.department_code, d.is_active
        FROM ""UserDepartment"" ud
        JOIN ""Department"" d ON d.department_id = ud.department_id
        WHERE ud.user_id = $userId
          AND ud.revoked_at_utc IS NULL
          AND (ud.valid_from_utc IS NULL OR ud.valid_from_utc <= $now)
          AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > $now)
        ORDER BY d.department_name";
    cmd.Parameters.AddWithValue("$userId", userId);
    cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));

    using var reader = cmd.ExecuteReader();
    while (reader.Read())
    {
        departments.Add(new DepartmentRecord(
            reader.GetInt64(0),
            reader.IsDBNull(1) ? "" : reader.GetString(1),
            reader.IsDBNull(2) ? "" : reader.GetString(2),
            !reader.IsDBNull(3) && reader.GetInt64(3) == 1));
    }
    return departments;
}
}