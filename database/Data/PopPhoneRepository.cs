using Microsoft.Data.Sqlite;

public class PopPhoneRepository
{
    private readonly Database _db;
    private readonly AccessGuard _guard;

    public PopPhoneRepository(Database db, AccessGuard guard)
    {
        _db = db;
        _guard = guard;
    }

    // Ok, Forbidden, NotFound (POP or phone does not exist) or Conflict (already assigned).
    public WriteResult Assign(long actorUserId, long popId, long phoneId)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO ""PopPhone"" (pop_id, phone_id) VALUES ($popId, $phoneId)";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$phoneId", phoneId);

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

    // Ok, Forbidden, or NotFound when the phone was not assigned to this POP.
    public WriteResult Remove(long actorUserId, long popId, long phoneId)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"DELETE FROM ""PopPhone"" WHERE pop_id = $popId AND phone_id = $phoneId";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$phoneId", phoneId);

        return cmd.ExecuteNonQuery() == 1 ? WriteResult.Ok : WriteResult.NotFound;
    }

    public List<PhoneRecord> GetPhonesForPop(long popId)
    {
        var result = new List<PhoneRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            SELECT p.phone_id, p.phone_number, p.created_at_utc, p.updated_at_utc
            FROM ""PopPhone"" pp
            JOIN ""PhoneNumber"" p ON p.phone_id = pp.phone_id
            WHERE pp.pop_id = $popId
            ORDER BY p.phone_id";
        cmd.Parameters.AddWithValue("$popId", popId);

        using var reader = cmd.ExecuteReader();
        while (reader.Read())
        {
            result.Add(new PhoneRecord(
                reader.GetInt64(0),
                reader.GetString(1),
                reader.IsDBNull(2) ? "" : reader.GetString(2),
                reader.IsDBNull(3) ? "" : reader.GetString(3)));
        }
        return result;
    }
}
