using Microsoft.Data.Sqlite;

public class LinkRepository
{
    private readonly Database _db;
    private readonly AccessGuard _guard;

    public LinkRepository(Database db, AccessGuard guard)
    {
        _db = db;
        _guard = guard;
    }

    public List<LinkRecord> GetAll()
    {
        var result = new List<LinkRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"SELECT link_id, link_path, created_at_utc, updated_at_utc FROM ""Link"" ORDER BY link_id DESC";

        using var reader = cmd.ExecuteReader();
        while (reader.Read())
        {
            result.Add(new LinkRecord(
                reader.GetInt64(0),
                reader.GetString(1),
                reader.IsDBNull(2) ? "" : reader.GetString(2),
                reader.IsDBNull(3) ? "" : reader.GetString(3)));
        }
        return result;
    }

    // Ok, Forbidden, or Conflict when the path already exists.
    public WriteResult Add(long actorUserId, string path)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        var now = DateTime.UtcNow.ToString("o");
        cmd.CommandText = @"INSERT INTO ""Link"" (link_path, created_at_utc, updated_at_utc) VALUES ($path, $now, $now)";
        cmd.Parameters.AddWithValue("$path", path);
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

    // Ok, Forbidden, NotFound (no such link) or Conflict (another link has this path).
    public WriteResult Update(long actorUserId, long linkId, string path)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"UPDATE ""Link"" SET link_path = $path, updated_at_utc = $now WHERE link_id = $linkId";
        cmd.Parameters.AddWithValue("$path", path);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        cmd.Parameters.AddWithValue("$linkId", linkId);

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
