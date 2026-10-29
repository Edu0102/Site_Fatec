using Microsoft.Data.Sqlite;

public class DepartmentRepository
{
    private readonly Database _db;

    public DepartmentRepository(Database db)
    {
        _db = db;
    }
public List<DepartmentRecord> GetAll()
{
    var result = new List<DepartmentRecord>();
    using var conn = _db.OpenConnection();
    using var cmd = conn.CreateCommand();
    cmd.CommandText = @"SELECT department_id	, department_name, department_code, is_active  FROM ""Department""";

    using var reader = cmd.ExecuteReader();
    while (reader.Read())
    {
        result.Add(new DepartmentRecord(
            reader.GetInt64(0),
            reader.IsDBNull(1) ? "" : reader.GetString(1),
            reader.IsDBNull(2) ? "" : reader.GetString(2),
            !reader.IsDBNull(3) && reader.GetInt64(3) == 1)
        );
    }
    return result;
    }


/*public bool TryAdd(string name, string code) {}  // false when the code already exists
}*/
    public bool TryAdd(string name, string code)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            INSERT INTO ""Department""
                (department_name, department_code, is_active, created_at_utc, updated_at_utc)
            VALUES
                ($name, $code, 1, $now, $now)";

        cmd.Parameters.AddWithValue("$name", name);
        cmd.Parameters.AddWithValue("$code", code);
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