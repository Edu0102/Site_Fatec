using Microsoft.Data.Sqlite;

public class PopLinkRepository
{
    private readonly Database _db;
    public PopLinkRepository(Database db) { _db = db; }

    public bool TryAssign(long popId, long linkId)
    {
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"INSERT INTO ""PopLink"" (pop_id, link_id) VALUES ($popId, $linkId)";
        cmd.Parameters.AddWithValue("$popId", popId);
        cmd.Parameters.AddWithValue("$linkId", linkId);
        try { return cmd.ExecuteNonQuery() == 1; }
        catch (SqliteException ex) when (ex.SqliteErrorCode == 19 || ex.SqliteExtendedErrorCode == 787) { return false; }
    }

    public List<LinkRecord> GetLinksForPop(long popId)
    {
        var result = new List<LinkRecord>();
        using var conn = _db.OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"SELECT l.link_id, l.link_path, l.created_at_utc, l.updated_at_utc
            FROM ""PopLink"" pl JOIN ""Link"" l ON l.link_id = pl.link_id
            WHERE pl.pop_id = $popId ORDER BY l.link_id";
        cmd.Parameters.AddWithValue("$popId", popId);
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            result.Add(new LinkRecord(reader.GetInt64(0), reader.GetString(1), reader.IsDBNull(2) ? "" : reader.GetString(2), reader.IsDBNull(3) ? "" : reader.GetString(3)));
        return result;
    }
}
