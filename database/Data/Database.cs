//knows the connection string, opens connections, runs schema.sql
using Microsoft.Data.Sqlite;

public class Database
{
    private readonly string _connectionString;

    public Database(string connectionString)
    {
        _connectionString = connectionString;
    }

    public SqliteConnection OpenConnection()
    {
        var conn = new SqliteConnection(_connectionString);
        conn.Open();
        return conn;
    }

    public void Initialize()
    {
        var schemaPath = Path.Combine(AppContext.BaseDirectory, "schema.sql");
        var schema = File.ReadAllText(schemaPath);

        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = schema;
        cmd.ExecuteNonQuery();
    }
}