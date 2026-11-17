import os
import json
import sqlite3
import bcrypt
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cloud_config = {
    'secure_connect_bundle': os.path.join(BASE_DIR, 'secure-connect-learnloop.zip')
}
token_path = os.path.join(BASE_DIR, 'onep51899@gmail.com-token.json')

session = None
db_type = "sqlite"

# Try connecting to Cassandra Astra DB with a short timeout
if os.path.exists(cloud_config['secure_connect_bundle']) and os.path.exists(token_path):
    try:
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
        from cassandra.policies import DCAwareRoundRobinPolicy

        with open(token_path) as f:
            secrets = json.load(f)

        CLIENT_ID = secrets["clientId"]
        CLIENT_SECRET = secrets["secret"]
        auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)

        cluster = Cluster(
            cloud=cloud_config,
            auth_provider=auth_provider,
            connect_timeout=3,
            load_balancing_policy=DCAwareRoundRobinPolicy()
        )
        session = cluster.connect()
        keyspace_name = 'database'
        session.execute(f"USE {keyspace_name}")
        db_type = "cassandra"
        print("Connected to Astra DB Cassandra successfully!")
    except Exception as e:
        print(f"Notice: Astra DB unavailable ({e}). Using local SQLite database fallback.")
        session = None
        db_type = "sqlite"

SQLITE_DB_PATH = os.path.join(BASE_DIR, "local_users.db")

def get_sqlite_conn():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite():
    with get_sqlite_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS register (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                password TEXT
            )
        """)
    # Add a default demo user if table is empty
    with get_sqlite_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM register")
        if cur.fetchone()["count"] == 0:
            demo_pw_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode('utf-8')
            conn.execute(
                "INSERT INTO register (id, name, email, password) VALUES (?, ?, ?, ?)",
                (1, "Demo User", "demo@example.com", demo_pw_hash)
            )

init_sqlite()

def create_tables():
    if session:
        create_register_table = """
        CREATE TABLE IF NOT EXISTS register (
            id INT PRIMARY KEY,
            name TEXT,
            email TEXT,
            password TEXT
        )
        """
        try:
            session.execute(create_register_table)
            print("Table 'register' created successfully in Astra DB!")
        except Exception as e:
            print(f"Failed to create 'register' table. Error: {e}")
    else:
        init_sqlite()
        print("Table 'register' initialized in local SQLite database!")

def register_account(fname, lname, email, password, ids):
    name = f"{fname} {lname}"
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

    if session:
        try:
            session.execute(
                "INSERT INTO register (id, name, email, password) VALUES (%s, %s, %s, %s)",
                (ids, name, email, hashed_password)
            )
            print("Account registered successfully in Astra DB!")
            return True
        except Exception as e:
            print(f"Failed to register account in Astra DB. Error: {e}")
            return False
    else:
        try:
            with get_sqlite_conn() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO register (id, name, email, password) VALUES (?, ?, ?, ?)",
                    (ids, name, email, hashed_password)
                )
            print("Account registered successfully in local SQLite!")
            return True
        except Exception as e:
            print(f"Failed to register account in SQLite. Error: {e}")
            return False

def login(email, password):
    if session:
        try:
            result = session.execute(
                "SELECT email, password FROM register WHERE email = %s ALLOW FILTERING",
                (email,)
            )
            for row in result:
                if bcrypt.checkpw(password.encode(), row.password.encode()):
                    return True
            return False
        except Exception as e:
            print(f"Astra DB login error: {e}")
            return False
    else:
        try:
            with get_sqlite_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT password FROM register WHERE email = ?", (email,))
                for row in cur.fetchall():
                    if bcrypt.checkpw(password.encode(), row["password"].encode()):
                        return True
            return False
        except Exception as e:
            print(f"SQLite login error: {e}")
            return False

def get_name(email):
    if session:
        try:
            result = session.execute("SELECT name, email FROM register WHERE email = %s ALLOW FILTERING", (email,))
            if not result:
                return None
            for row in result:
                return row.name
        except Exception:
            return None
    else:
        try:
            with get_sqlite_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM register WHERE email = ?", (email,))
                row = cur.fetchone()
                if row:
                    return row["name"]
            return None
        except Exception:
            return None

def get_id_by_email(email):
    if session:
        try:
            result = session.execute("SELECT id FROM register WHERE email = %s LIMIT 1", (email,))
            if result:
                return result[0].id
            return None
        except Exception as e:
            print(f"Failed to get id by email. Error: {e}")
            return None
    else:
        try:
            with get_sqlite_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM register WHERE email = ?", (email,))
                row = cur.fetchone()
                if row:
                    return row["id"]
            return None
        except Exception as e:
            print(f"Failed to get id by email: {e}")
            return None

if __name__ == '__main__':
    create_tables()
    print("Testing registration and login...")
    test_email = "test@example.com"
    test_pass = "mypassword"
    register_account("Test", "User", test_email, test_pass, 99)
    print("Login with correct pass:", login(test_email, test_pass))
    print("Login with wrong pass:", login(test_email, "wrong"))
    print("Get name:", get_name(test_email))
    print("Get ID:", get_id_by_email(test_email))
