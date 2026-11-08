"""Development data and first-admin setup.

python seed.py                     -> test logins (NEVER on the real server)
python seed.py --admin EMAIL NAME  -> asks for a password and creates a real admin
"""
import getpass
import sys

from app import create_app
from db import get_db
from repositories import users, utc_now
from security import hash_password

TEST_PASSWORD = "mypassword123"


def create_admin(app, email, name, password):
    """Create an active admin; False if the email is already registered."""
    with app.app_context():
        email = email.strip().lower()
        if not users.add(name.strip(), email, hash_password(password)):
            return False
        db = get_db()
        db.execute('UPDATE "User" SET user_role = \'admin\' WHERE user_email = ?', (email,))
        db.commit()
        return True


def seed_test_data(app):
    """Test accounts, one department and one published POP the basic user can see. Safe to run twice."""
    create_admin(app, "admin@test.com", "Admin Test", TEST_PASSWORD)
    with app.app_context():
        db = get_db()
        users.add("Basic Test", "basic@test.com", hash_password(TEST_PASSWORD))
        if users.add("Inactive Test", "inactive@test.com", hash_password(TEST_PASSWORD)):
            db.execute('UPDATE "User" SET is_active = 0 WHERE user_email = ?', ("inactive@test.com",))
        if db.execute('SELECT 1 FROM "Department" WHERE department_code = ?', ("TEST",)).fetchone():
            db.commit()
            return
        now = utc_now()
        admin_id = users.get_by_email("admin@test.com")["user_id"]
        basic_id = users.get_by_email("basic@test.com")["user_id"]
        dept = db.execute('INSERT INTO "Department" (department_name, department_code, is_active, created_at_utc, updated_at_utc) '
                          'VALUES (?, ?, 1, ?, ?)', ("Test Department", "TEST", now, now)).lastrowid
        pop = db.execute('INSERT INTO "Pop" (created_by, updated_by, pop_title, pop_description, pop_status, created_at_utc, updated_at_utc) '
                         'VALUES (?, ?, ?, ?, \'published\', ?, ?)',
                         (admin_id, admin_id, "Test POP", "Seeded POP shared with Test Department", now, now)).lastrowid
        db.execute('INSERT INTO "PopDepartment" (pop_id, department_id) VALUES (?, ?)', (pop, dept))
        db.execute('INSERT INTO "UserDepartment" (user_id, department_id, access_type, valid_from_utc) VALUES (?, ?, \'member\', ?)',
                   (basic_id, dept, now))
        db.commit()


if __name__ == "__main__":
    application = create_app()
    if sys.argv[1:2] == ["--admin"] and len(sys.argv) == 4:
        password = getpass.getpass("Password (min 8 characters): ")
        if len(password) < 8:
            sys.exit("Password must have at least 8 characters.")
        print("Admin created." if create_admin(application, sys.argv[2], sys.argv[3], password) else "That email is already registered.")
    elif len(sys.argv) == 1:
        seed_test_data(application)
        print(f"Test logins ready (password {TEST_PASSWORD}): admin@test.com, basic@test.com, inactive@test.com")
    else:
        sys.exit(__doc__)
