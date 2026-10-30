public record NewPop(string Title, string? Description, string? FilePath, string? Version, string? Status);
public record UpdatePop(string Title, string? Description, string? FilePath, string? Version, string Status);
public record PopRecord(long Id, long CreatedBy, long UpdatedBy, string Title, string? Description, string? FilePath, string? Version, string Status, string CreatedAtUtc, string UpdatedAtUtc);
