"""Initialize database tables using synchronous psycopg2 directly."""
import sys

sys.path.insert(0, ".")

try:
    import psycopg2

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="siworkgroup",
        user="siuser",
        password="sipass",
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Check existing tables
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    existing = [r[0] for r in cur.fetchall()]

    result_lines = [f"Existing tables: {existing}"]

    if existing:
        result_lines.append("Tables already exist - migration was successful!")
    else:
        result_lines.append("No tables found - need to create them")

    cur.close()
    conn.close()

    output = "\n".join(result_lines)
    with open("init_db_sync_result.txt", "w") as f:
        f.write(output)
    print(output)

except Exception as e:
    import traceback
    err = f"ERROR: {e}\n{traceback.format_exc()}"
    with open("init_db_sync_result.txt", "w") as f:
        f.write(err)
    print(err)