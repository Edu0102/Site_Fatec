using Microsoft.Data.Sqlite;

public class PopLinkRepository
{
    private readonly Database _db;
    private readonly AccessGuard _guard;

    public PopLinkRepository(Database db, AccessGuard guard)
    {
        _db = db;
        _guard = guard;
    }

    // Ok, Forbidden, NotFound (POP or link does not exist) or Conflict (already assigned).
    public WriteResult Assign(long actorUserId, long popId, long linkId)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO ""PopLink"" (pop_id, link_id) VALUES ($popId, $linkId)";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$linkId", linkId);

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

    // Ok, Forbidden, or NotFound when the link was not assigned to this POP.
    public WriteResult Remove(long actorUserId, long popId, long linkId)
    {
        if (!_guard.IsActiveAdmin(actorUserId))
            return WriteResult.Forbidden;

        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"DELETE FROM ""PopLink"" WHERE pop_id = $popId AND link_id = $linkId";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$linkId", linkId);

        return cmd.ExecuteNonQuery() == 1 ? WriteResult.Ok : WriteResult.NotFound;
    }

    public List<LinkRecord> GetLinksForPop(long popId)
    {
        var result = new List<LinkRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            SELECT l.link_id, l.link_path, l.created_at_utc, l.updated_at_utc
            FROM ""PopLink"" pl
            JOIN ""Link"" l ON l.link_id = pl.link_id
            WHERE pl.pop_id = $popId
            ORDER BY l.link_id";
        cmd.Parameters.AddWithValue("$popId", popId);

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
}
