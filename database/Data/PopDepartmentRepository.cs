using Microsoft.Data.Sqlite;

public class PopDepartmentRepository
{
    private readonly Database _db;
    private readonly AccessGuard _guard;

    public PopDepartmentRepository(Database db, AccessGuard guard)
    {
        _db = db;
        _guard = guard;
    }

    // Ok, Forbidden, NotFound (POP or department does not exist) or Conflict (already assigned).
    public WriteResult Assign(long actorUserId, long popId, long departmentId, string accessType)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            INSERT INTO ""PopDepartment"" (pop_id, department_id, access_type)
            VALUES ($popId, $departmentId, $accessType)";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$departmentId", departmentId);
        cmd.Parameters.AddWithValue("$accessType", accessType);

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

    // Ok, Forbidden, or NotFound when the department was not assigned to this POP.
    public WriteResult Remove(long actorUserId, long popId, long departmentId)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"DELETE FROM ""PopDepartment"" WHERE pop_id = $popId AND department_id = $departmentId";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$departmentId", departmentId);

        return cmd.ExecuteNonQuery() == 1 ? WriteResult.Ok : WriteResult.NotFound;
    }

    public List<DepartmentRecord> GetDepartmentsForPop(long popId)
    {
        var result = new List<DepartmentRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            SELECT d.department_id, d.department_name, d.department_code, d.is_active
            FROM ""PopDepartment"" pd
            JOIN ""Department"" d ON d.department_id = pd.department_id
            WHERE pd.pop_id = $popId
            ORDER BY d.department_name";
        cmd.Parameters.AddWithValue("$popId", popId);

        using var reader = cmd.ExecuteReader();
        while (reader.Read())
        {
            result.Add(new DepartmentRecord(
                reader.GetInt64(0),
                reader.IsDBNull(1) ? "" : reader.GetString(1),
                reader.IsDBNull(2) ? "" : reader.GetString(2),
                !reader.IsDBNull(3) && reader.GetInt64(3) == 1));
        }
        return result;
    }
}
