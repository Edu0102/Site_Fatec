using Microsoft.Data.Sqlite;

public class UserDepartmentRepository
{
    private readonly Database _db;

    public UserDepartmentRepository(Database db)
    {
        _db = db;
    }

    // Returns false when the user or the department does not exist.
    public bool Assign(long userId, long departmentId, string accessType)
    {
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
            return true;
        }
        catch (SqliteException ex) when (ex.SqliteExtendedErrorCode == 787)
        {
            return false;   // 787 = foreign key violation
        }
    }

    // YOUR TURN: write this one
    public List<DepartmentRecord> GetDepartmentsForUser(long userId)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"SELECT d.department_id, d.department_name, d.department_code, d.is_active
                FROM ""UserDepartment"" ud
                JOIN ""Department"" d ON d.department_id = ud.department_id
                WHERE ud.user_id = $userId
                AND ud.revoked_at_utc IS NULL
                ORDER BY d.department_name";
        cmd.Parameters.AddWithValue("$userId", userId);
        var departments = new List<DepartmentRecord>();
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