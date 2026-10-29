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
}

/*public bool TryAdd(string name, string code) {}  // false when the code already exists
}*/