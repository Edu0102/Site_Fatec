using Microsoft.Data.Sqlite;

public class PopPhoneRepository
{
    private readonly Database _db;
    public PopPhoneRepository(Database db) { _db = db; }

    public MutationResult TryAssign(long popId, long phoneId)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO ""PopPhone"" (pop_id, phone_id) VALUES ($popId, $phoneId)";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$phoneId", phoneId);
        try { return cmd.ExecuteNonQuery() == 1 ? MutationResult.Ok : MutationResult.BadRequest; }
        catch (SqliteException ex) when (ex.SqliteExtendedErrorCode == 787) { return MutationResult.BadRequest; }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19) { return MutationResult.Conflict; }
    }

    public List<PhoneRecord> GetPhonesForPop(long popId)
    {
        var result = new List<PhoneRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"SELECT p.phone_id, p.phone_number, p.created_at_utc, p.updated_at_utc
            FROM ""PopPhone"" pp JOIN ""PhoneNumber"" p ON p.phone_id = pp.phone_id
            WHERE pp.pop_id = $popId ORDER BY p.phone_id";
        cmd.Parameters.AddWithValue("$popId", popId);
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            result.Add(new PhoneRecord(reader.GetInt64(0), reader.GetString(1), reader.IsDBNull(2) ? "" : reader.GetString(2), reader.IsDBNull(3) ? "" : reader.GetString(3)));
        return result;
    }
}
