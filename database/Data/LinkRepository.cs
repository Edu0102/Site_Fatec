using Microsoft.Data.Sqlite;

public class LinkRepository
{
    private readonly Database _db;
    public LinkRepository(Database db) { _db = db; }

    public List<LinkRecord> GetAll()
    {
        var result = new List<LinkRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"SELECT link_id, link_path, created_at_utc, updated_at_utc FROM ""Link"" ORDER BY link_id DESC";
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            result.Add(new LinkRecord(reader.GetInt64(0), reader.GetString(1), reader.IsDBNull(2) ? "" : reader.GetString(2), reader.IsDBNull(3) ? "" : reader.GetString(3)));
        return result;
    }

    public MutationResult TryAdd(string path)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        var now = DateTime.UtcNow.ToString("o");
        cmd.CommandText = @"INSERT INTO ""Link"" (link_path, created_at_utc, updated_at_utc) VALUES ($path, $now, $now)";
        cmd.Parameters.AddWithValue("$path", path);
        cmd.Parameters.AddWithValue("$now", now);
        try { return cmd.ExecuteNonQuery() == 1 ? MutationResult.Ok : MutationResult.BadRequest; }
        catch (SqliteException ex) when (ex.SqliteExtendedErrorCode == 787) { return MutationResult.BadRequest; }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19) { return MutationResult.Conflict; }
    }

    public MutationResult TryUpdate(long linkId, string path)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"UPDATE ""Link"" SET link_path = $path, updated_at_utc = $now WHERE link_id = $linkId";
        cmd.Parameters.AddWithValue("$path", path);
        cmd.Parameters.AddWithValue("$now", DateTime.UtcNow.ToString("o"));
        cmd.Parameters.AddWithValue("$linkId", linkId);
        try
        {
            if (cmd.ExecuteNonQuery() == 0)
                return MutationResult.NotFound;
            return MutationResult.Ok;
        }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19) { return MutationResult.Conflict; }
    }
}
