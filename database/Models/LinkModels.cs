public record NewLink(string Path);
public record UpdateLink(string Path);
public record LinkRecord(long Id, string Path, string CreatedAtUtc, string UpdatedAtUtc);

public enum MutationResult
{
    Ok,
    NotFound,
    Conflict,
    BadRequest
}