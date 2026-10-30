using Microsoft.Data.Sqlite;

public class PhoneRepository
{
    private readonly Database _db;
    public PhoneRepository(Database db) { _db = db; }

    public List<PhoneRecord> GetAll()
    {
        var result = new List<PhoneRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"SELECT phone_id, phone_number, created_at_utc, updated_at_utc FROM ""PhoneNumber"" ORDER BY phone_id DESC";
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            result.Add(new PhoneRecord(reader.GetInt64(0), reader.GetString(1), reader.IsDBNull(2) ? "" : reader.GetString(2), reader.IsDBNull(3) ? "" : reader.GetString(3)));
        return result;
    }

    public MutationResult TryAdd(string phoneNumber)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        var now = DateTime.UtcNow.ToString("o");
        cmd.CommandText = @"INSERT INTO ""PhoneNumber"" (phone_number, created_at_utc, updated_at_utc) VALUES ($phoneNumber, $now, $now)";
        cmd.Parameters.AddWithValue("$phoneNumber", phoneNumber);
        cmd.Parameters.AddWithValue("$now", now);
        try { return cmd.ExecuteNonQuery() == 1 ? MutationResult.Ok : MutationResult.BadRequest; }
        catch (SqliteException ex) when (ex.SqliteExtendedErrorCode == 787) { return MutationResult.BadRequest; }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19) { return MutationResult.Conflict; }
    }

    public MutationResult TryUpdate(long phoneId, string phoneNumber)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"UPDATE ""PhoneNumber"" SET phone_number = $phoneNumber, updated_at_utc = $now WHERE phone_id = $phoneId";
        cmd.Parameters.AddWithValue("$phoneNumber", phoneNumber);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        cmd.Parameters.AddWithValue("$phoneId", phoneId);
        try
        {
            if (cmd.ExecuteNonQuery() == 0)
                return MutationResult.NotFound;
            return MutationResult.Ok;
        }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19) { return MutationResult.Conflict; }
    }
}
