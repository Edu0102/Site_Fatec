CREATE TABLE IF NOT EXISTS "User" (
	"user_id"	INTEGER NOT NULL UNIQUE,
	"user_name"	TEXT,
	"user_email"	TEXT UNIQUE,
	"user_password_hash"	TEXT,
	"user_role"	TEXT,
	"is_active"	INTEGER,
	"created_at_utc"	TEXT,
	"updated_at_utc"	TEXT,
	"user_session_version"	INTEGER NOT NULL DEFAULT 0,
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
CREATE TABLE IF NOT EXISTS "StandardCheck" (
    "standard_check_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "pop_id" INTEGER NOT NULL,
    "check_text" TEXT NOT NULL,
    "check_order" INTEGER NOT NULL,
    FOREIGN KEY ("pop_id") REFERENCES "Pop"("pop_id")
);
CREATE TABLE IF NOT EXISTS "Checklist" (
    "checklist_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "pop_id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "checklist_description" TEXT,
    "created_at_utc" TEXT,
    "completed_at_utc" TEXT,
    FOREIGN KEY ("pop_id") REFERENCES "Pop"("pop_id"),
    FOREIGN KEY ("user_id") REFERENCES "User"("user_id")
);
CREATE TABLE IF NOT EXISTS "ChecklistItemResult" (
    "checklist_item_result_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "checklist_id" INTEGER NOT NULL,
    "standard_check_id" INTEGER NOT NULL,
    "is_checked" INTEGER NOT NULL DEFAULT 0,
    UNIQUE ("checklist_id", "standard_check_id"),
    FOREIGN KEY ("checklist_id") REFERENCES "Checklist"("checklist_id"),
    FOREIGN KEY ("standard_check_id") REFERENCES "StandardCheck"("standard_check_id")
);
CREATE TABLE IF NOT EXISTS "Feedback" (
    "feedback_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "user_id" INTEGER NOT NULL,
    "pop_id" INTEGER,
    "answered_by" INTEGER,
    "feedback_description" TEXT NOT NULL,
    "feedback_status" TEXT NOT NULL DEFAULT 'open' CHECK ("feedback_status" IN ('open','answered','closed')),
    "feedback_answer" TEXT,
    "created_at_utc" TEXT,
    "answered_at_utc" TEXT,
    FOREIGN KEY ("user_id") REFERENCES "User"("user_id"),
    FOREIGN KEY ("pop_id") REFERENCES "Pop"("pop_id"),
    FOREIGN KEY ("answered_by") REFERENCES "User"("user_id")
);
CREATE TABLE IF NOT EXISTS "UserPhoto" (
    "user_id" INTEGER PRIMARY KEY,
    "photo_data" BLOB NOT NULL,
    "photo_content_type" TEXT NOT NULL CHECK ("photo_content_type" IN ('image/jpeg','image/png','image/webp')),
    "updated_at_utc" TEXT,
    FOREIGN KEY ("user_id") REFERENCES "User"("user_id")
);
