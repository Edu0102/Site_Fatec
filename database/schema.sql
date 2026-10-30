CREATE TABLE IF NOT EXISTS "User" (
	"user_id"	INTEGER NOT NULL UNIQUE,
	"user_name"	TEXT,
	"user_email"	TEXT UNIQUE,
	"user_password_hash"	TEXT,
	"user_role"	TEXT,
	"is_active"	INTEGER,
	"created_at_utc"	TEXT,
	"updated_at_utc"	TEXT,
	PRIMARY KEY("user_id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Department"(
	"department_id"	INTEGER NOT NULL,
	"department_name"	TEXT NOT NULL,
	"department_code"	TEXT UNIQUE,
	"is_active"	INTEGER,
	"created_at_utc"	TEXT,
	"updated_at_utc"	TEXT,
	PRIMARY KEY("department_id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "UserDepartment" (
    "user_department_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "user_id"            INTEGER NOT NULL,
    "department_id"      INTEGER NOT NULL,
    "access_type"        TEXT,
    "valid_from_utc"     TEXT,
    "expires_at_utc"     TEXT,
    "revoked_at_utc"     TEXT,
    FOREIGN KEY ("user_id") REFERENCES "User"("user_id"),
    FOREIGN KEY ("department_id") REFERENCES "Department"("department_id")
);