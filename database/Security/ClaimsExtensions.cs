using System.Security.Claims;

public static class ClaimsExtensions
{
    public static bool TryGetUserId(this ClaimsPrincipal user, out long userId)
        => long.TryParse(user.FindFirst(ClaimTypes.NameIdentifier)?.Value, out userId);

    public static string GetRole(this ClaimsPrincipal user)
        => user.FindFirst(ClaimTypes.Role)?.Value ?? "basic";
}