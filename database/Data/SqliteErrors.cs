using Microsoft.Data.Sqlite;

// Gives readable names to raw SQLite error numbers.
public static class SqliteErrors
{
    public static bool IsUnique(this SqliteException ex) => ex.SqliteExtendedErrorCode == 2067;

    public static bool IsForeignKey(this SqliteException ex) => ex.SqliteExtendedErrorCode == 787;
}