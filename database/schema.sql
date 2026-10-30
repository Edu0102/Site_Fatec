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
CREATE TABLE IF NOT EXISTS "Pop" (
    "pop_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "created_by" INTEGER NOT NULL,
    "updated_by" INTEGER NOT NULL,
    "pop_title" TEXT NOT NULL,
    "pop_description" TEXT,
    "pop_file_path" TEXT,
    "pop_version" TEXT,
    "pop_status" TEXT NOT NULL DEFAULT 'draft' CHECK ("pop_status" IN ('draft','published','archived')),
    "created_at_utc" TEXT,
    "updated_at_utc" TEXT,
    FOREIGN KEY ("created_by") REFERENCES "User"("user_id"),
    FOREIGN KEY ("updated_by") REFERENCES "User"("user_id")
);
CREATE TABLE IF NOT EXISTS "Link" (
    "link_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "link_path" TEXT NOT NULL UNIQUE,
    "created_at_utc" TEXT,
    "updated_at_utc" TEXT
);
CREATE TABLE IF NOT EXISTS "PhoneNumber" (
    "phone_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "phone_number" TEXT NOT NULL UNIQUE,
    "created_at_utc" TEXT,
    "updated_at_utc" TEXT
);
CREATE TABLE IF NOT EXISTS "PopLink" (
    "pop_link_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "pop_id" INTEGER NOT NULL,
    "link_id" INTEGER NOT NULL,
    UNIQUE ("pop_id", "link_id"),
    FOREIGN KEY ("pop_id") REFERENCES "Pop"("pop_id"),
    FOREIGN KEY ("link_id") REFERENCES "Link"("link_id")
);
CREATE TABLE IF NOT EXISTS "PopPhone" (
    "pop_phone_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "pop_id" INTEGER NOT NULL,
    "phone_id" INTEGER NOT NULL,
    UNIQUE ("pop_id", "phone_id"),
    FOREIGN KEY ("pop_id") REFERENCES "Pop"("pop_id"),
    FOREIGN KEY ("phone_id") REFERENCES "PhoneNumber"("phone_id")
);
CREATE TABLE IF NOT EXISTS "PopDepartment" (
    "pop_department_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "pop_id" INTEGER NOT NULL,
    "department_id" INTEGER NOT NULL,
    "access_type" TEXT NOT NULL DEFAULT 'read',
    UNIQUE ("pop_id", "department_id"),
    FOREIGN KEY ("pop_id") REFERENCES "Pop"("pop_id"),
    FOREIGN KEY ("department_id") REFERENCES "Department"("department_id")
);