// The possible outcomes of a write (insert / update / delete) on the database.
public enum WriteResult
{
    Ok,
    NotFound,   // the row (or a row it points to) does not exist
    Conflict    // the write would create a duplicate
}