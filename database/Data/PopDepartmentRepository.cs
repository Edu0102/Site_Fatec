using Microsoft.Data.Sqlite;

public class PopDepartmentRepository
{
    private readonly Database _db;
    public PopDepartmentRepository(Database db) { _db = db; }

    public bool TryAssign(long popId, long departmentId, string accessType)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO ""PopDepartment"" (pop_id, department_id, access_type)
            VALUES ($popId, $departmentId, $accessType)";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$departmentId", departmentId);
        cmd.Parameters.AddWithValue("$accessType", accessType);
        try { return cmd.ExecuteNonQuery() == 1; }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19 || ex.SqliteExtendedErrorCode == 787) { return false; }
    }

    public List<DepartmentRecord> GetDepartmentsForPop(long popId)
    {
        var result = new List<DepartmentRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"SELECT d.department_id, d.department_name, d.department_code, d.is_active
            FROM ""PopDepartment"" pd JOIN ""Department"" d ON d.department_id = pd.department_id
            WHERE pd.pop_id = $popId ORDER BY d.department_name";
        cmd.Parameters.AddWithValue("$popId", popId);
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            result.Add(new DepartmentRecord(reader.GetInt64(0), reader.IsDBNull(1) ? "" : reader.GetString(1), reader.IsDBNull(2) ? "" : reader.GetString(2), !reader.IsDBNull(3) && reader.GetInt64(3) == 1));
        return result;
    }
}
