import pyttsx3
import sqlite3
import tkinter.messagebox as mbox
import os

# Constants for DB location
DB_DIR = "app/database"
DB_FILE = os.path.join(DB_DIR, "app.db")

# Ensure the database folder exists
os.makedirs(DB_DIR, exist_ok=True)


def say(text):
    """Text-to-speech function."""
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error] {e}")


def db_connect():
    """Connect to SQLite with WAL and threading support."""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")  # Better concurrency
        return conn
    except sqlite3.Error as err:
        show_error("Database Error", str(err))
        return None


def init_db():
    """Initialize the users and responses tables."""
    conn = db_connect()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Create users table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                gmail TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
        """
        )

        # Create responses table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_gmail TEXT NOT NULL,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        # Add session_id column to responses table if it doesn't exist (for backward compatibility)
        cursor.execute("PRAGMA table_info(responses)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'session_id' not in columns:
            cursor.execute("ALTER TABLE responses ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default'")

        conn.commit()
    except sqlite3.Error as err:
        show_error("DB Init Error", str(err))
    finally:
        conn.close()


def show_error(title, message):
    """Show error popup."""
    try:
        mbox.showerror(title, message)
    except Exception:
        print(f"[ERROR] {title}: {message}")


def show_info(title, message):
    """Show info popup."""
    try:
        mbox.showinfo(title, message)
    except Exception:
        print(f"[INFO] {title}: {message}")
