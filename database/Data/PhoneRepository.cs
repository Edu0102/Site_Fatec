using Microsoft.Data.Sqlite;

public class PhoneRepository
{
    private readonly Database _db;
    private readonly AccessGuard _guard;

    public PhoneRepository(Database db, AccessGuard guard)
    {
        _db = db;
        _guard = guard;
    }

    public List<PhoneRecord> GetAll()
    {
        var result = new List<PhoneRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"SELECT phone_id, phone_number, created_at_utc, updated_at_utc FROM ""PhoneNumber"" ORDER BY phone_id DESC";

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

    // Ok, Forbidden, or Conflict when the number already exists.
    public WriteResult Add(long actorUserId, string phoneNumber)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        var now = DateTime.UtcNow.ToString("o");
        cmd.CommandText = @"INSERT INTO ""PhoneNumber"" (phone_number, created_at_utc, updated_at_utc) VALUES ($phoneNumber, $now, $now)";
        cmd.Parameters.AddWithValue("$phoneNumber", phoneNumber);
        cmd.Parameters.AddWithValue("$now", now);

        try
        {
            cmd.ExecuteNonQuery();
            return WriteResult.Ok;
        }
        catch (SqliteException ex) when (ex.IsUnique())
        {
            return WriteResult.Conflict;
        }
    }

    // Ok, Forbidden, NotFound (no such phone) or Conflict (another row has this number).
    public WriteResult Update(long actorUserId, long phoneId, string phoneNumber)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"UPDATE ""PhoneNumber"" SET phone_number = $phoneNumber, updated_at_utc = $now WHERE phone_id = $phoneId";
        cmd.Parameters.AddWithValue("$phoneNumber", phoneNumber);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        cmd.Parameters.AddWithValue("$phoneId", phoneId);

        try
        {
            var rows = cmd.ExecuteNonQuery();
            return rows == 1 ? WriteResult.Ok : WriteResult.NotFound;
        }
        catch (SqliteException ex) when (ex.IsUnique())
        {
            return WriteResult.Conflict;
        }
    }
}
