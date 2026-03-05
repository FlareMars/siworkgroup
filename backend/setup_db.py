#!/usr/bin/env python3
"""
Complete database setup script.
Run: python setup_db.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

RESULT_FILE = os.path.join(os.path.dirname(__file__), "setup_db_result.txt")
lines = []


def log(msg):
    print(msg)
    lines.append(msg)


def write_result():
    with open(RESULT_FILE, "w") as f:
        f.write("\n".join(lines))


try:
    # 1. Check psycopg2 connection
    import psycopg2

    log("Checking PostgreSQL connection...")
    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="siworkgroup", user="siuser", password="sipass"
    )
    conn.autocommit = True
    cur = conn.cursor()

    # 2. Get existing tables
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name"
    )
    existing = [r[0] for r in cur.fetchall()]
    log(f"Existing tables: {existing}")

    # 3. Create all tables via DDL if they don't exist
    TABLES_SQL = """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) NOT NULL UNIQUE,
        username VARCHAR(50) NOT NULL UNIQUE,
        display_name VARCHAR(100) NOT NULL,
        hashed_password TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT true,
        is_superadmin BOOLEAN NOT NULL DEFAULT false,
        avatar_url VARCHAR(512),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_login_at TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);

    CREATE TABLE IF NOT EXISTS claws (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL,
        description TEXT,
        slug VARCHAR(120) NOT NULL UNIQUE,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        container_id VARCHAR(64),
        container_name VARCHAR(100),
        model VARCHAR(100) NOT NULL DEFAULT 'gpt-4o',
        system_prompt TEXT,
        sandbox_config JSONB NOT NULL DEFAULT '{}',
        enabled_tools JSONB NOT NULL DEFAULT '[]',
        work_dir VARCHAR(512) NOT NULL DEFAULT '/workspace',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_active_at TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS ix_claws_name ON claws(name);
    CREATE INDEX IF NOT EXISTS ix_claws_slug ON claws(slug);
    CREATE INDEX IF NOT EXISTS ix_claws_status ON claws(status);
    CREATE INDEX IF NOT EXISTS ix_claws_owner_id ON claws(owner_id);

    CREATE TABLE IF NOT EXISTS claw_permissions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claw_id UUID NOT NULL REFERENCES claws(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role VARCHAR(20) NOT NULL DEFAULT 'viewer',
        granted_by UUID,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE(claw_id, user_id)
    );
    CREATE INDEX IF NOT EXISTS ix_claw_permissions_claw_id ON claw_permissions(claw_id);
    CREATE INDEX IF NOT EXISTS ix_claw_permissions_user_id ON claw_permissions(user_id);

    CREATE TABLE IF NOT EXISTS claw_policies (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claw_id UUID NOT NULL UNIQUE REFERENCES claws(id) ON DELETE CASCADE,
        network_policy JSONB NOT NULL DEFAULT '{}',
        fs_policy JSONB NOT NULL DEFAULT '{}',
        command_blacklist JSONB NOT NULL DEFAULT '[]',
        api_keys JSONB NOT NULL DEFAULT '[]',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_claw_policies_claw_id ON claw_policies(claw_id);

    CREATE TABLE IF NOT EXISTS chat_sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claw_id UUID NOT NULL REFERENCES claws(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL DEFAULT 'New Session',
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_chat_sessions_claw_id ON chat_sessions(claw_id);
    CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions(user_id);

    CREATE TABLE IF NOT EXISTS chat_messages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        role VARCHAR(20) NOT NULL,
        content TEXT NOT NULL,
        tool_calls JSONB,
        tool_call_id VARCHAR(100),
        tool_name VARCHAR(100),
        input_tokens INTEGER,
        output_tokens INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages(session_id);
    CREATE INDEX IF NOT EXISTS ix_chat_messages_created_at ON chat_messages(created_at);

    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claw_id UUID REFERENCES claws(id) ON DELETE SET NULL,
        actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
        action VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        context JSONB NOT NULL DEFAULT '{}',
        ip_address VARCHAR(45),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_audit_logs_claw_id ON audit_logs(claw_id);
    CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_id ON audit_logs(actor_id);
    CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
    CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at);

    CREATE TABLE IF NOT EXISTS alembic_version (
        version_num VARCHAR(32) NOT NULL PRIMARY KEY
    );
    INSERT INTO alembic_version(version_num) VALUES ('001')
        ON CONFLICT DO NOTHING;
    """

    log("Creating tables...")
    for stmt in TABLES_SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt + ";")

    log("Tables created/verified successfully!")

    # 4. Verify
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name"
    )
    all_tables = [r[0] for r in cur.fetchall()]
    log(f"Final tables: {all_tables}")

    cur.close()
    conn.close()
    log("=== DATABASE SETUP COMPLETE ===")

except Exception as e:
    import traceback
    log(f"ERROR: {e}")
    log(traceback.format_exc())

write_result()