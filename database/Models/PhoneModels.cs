public record NewPhone(string PhoneNumber);
public record UpdatePhone(string PhoneNumber);
public record PhoneRecord(long Id, string PhoneNumber, string CreatedAtUtc, string UpdatedAtUtc);