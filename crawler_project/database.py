import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME
    )

def setup_database():
    """Create all tables if not exists"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS websites (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(100),
            base_url    VARCHAR(255) UNIQUE,
            category    VARCHAR(100),
            created_at  DATETIME DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            website_id    INT,
            website_name  VARCHAR(100),
            title         VARCHAR(500),
            field1_name   VARCHAR(100),
            field1_value  TEXT,
            field2_name   VARCHAR(100),
            field2_value  TEXT,
            field3_name   VARCHAR(100),
            field3_value  TEXT,
            url           VARCHAR(500) UNIQUE,
            crawled_at    DATETIME DEFAULT NOW(),
            FOREIGN KEY (website_id) REFERENCES websites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            website_id    INT,
            website_name  VARCHAR(100),
            started_at    DATETIME,
            finished_at   DATETIME,
            items_saved   INT DEFAULT 0,
            status        VARCHAR(50),
            FOREIGN KEY (website_id) REFERENCES websites(id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database setup complete!")

def register_website(name, base_url, category):
    """Add website to websites table, return website_id"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT IGNORE INTO websites (name, base_url, category)
            VALUES (%s, %s, %s)
        """, (name, base_url, category))
        conn.commit()
        cursor.execute("SELECT id FROM websites WHERE base_url = %s", (base_url,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error registering website: {e}")
        return None

def save_item(website_id, website_name, title, fields, url):
    """
    Save crawled item to items table
    fields: dict of max 3 key-value pairs
    Example: {"price": "100.000d", "author": "Nguyen Van A"}
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        field_keys   = list(fields.keys())
        field_values = list(fields.values())

        f1_name  = field_keys[0]   if len(field_keys)   > 0 else None
        f1_value = field_values[0] if len(field_values) > 0 else None
        f2_name  = field_keys[1]   if len(field_keys)   > 1 else None
        f2_value = field_values[1] if len(field_values) > 1 else None
        f3_name  = field_keys[2]   if len(field_keys)   > 2 else None
        f3_value = field_values[2] if len(field_values) > 2 else None

        cursor.execute("""
            INSERT IGNORE INTO items
            (website_id, website_name, title,
             field1_name, field1_value,
             field2_name, field2_value,
             field3_name, field3_value, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (website_id, website_name, title,
              f1_name, f1_value,
              f2_name, f2_value,
              f3_name, f3_value, url))

        conn.commit()
        saved = cursor.rowcount
        cursor.close()
        conn.close()
        return saved
    except Exception as e:
        print(f"Error saving item: {e}")
        return 0

def log_crawl(website_id, website_name, started_at, finished_at, items_saved, status):
    """Save crawl session log"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crawl_logs
            (website_id, website_name, started_at, finished_at, items_saved, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (website_id, website_name, started_at, finished_at, items_saved, status))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving log: {e}")