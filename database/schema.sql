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
)