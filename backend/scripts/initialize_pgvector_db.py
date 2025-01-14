import os
import subprocess
import time

def initialize_pgvector():
    # Define paths
    data_dir = r"C:\Users\mkahs\GIT_REPO\Izzy_SlackBot\data_ingestion\data\vds_pgvector"
    logfile = os.path.join(data_dir, "logfile")
    postgresql_conf = os.path.join(data_dir, "postgresql.conf")
    port = "5434"

    # Step 1: Remove existing directory if it exists
    if os.path.exists(data_dir):
        print("Removing existing data directory...")
        subprocess.run(["rmdir", "/S", "/Q", data_dir], shell=True, check=True)
        print("Data directory removed.")

    # Step 2: Initialize PostgreSQL data directory
    print("Initializing PostgreSQL data directory...")
    subprocess.run([
    r"C:\Program Files\PostgreSQL\14\bin\initdb",  # Replace <version> with your PostgreSQL version
    "-D", data_dir,
    "-U", "postgres",
    "-A", "trust"
    ], check=True)


    # Step 3: Update postgresql.conf for listen_addresses and port
    print("Modifying postgresql.conf...")
    if os.path.exists(postgresql_conf):
        with open(postgresql_conf, "r") as f:
            config_lines = f.readlines()

        updated_lines = []
        for line in config_lines:
            if line.strip().startswith("#listen_addresses"):
                updated_lines.append(f"listen_addresses = '127.0.0.1'\n")
            elif line.strip().startswith("#port"):
                updated_lines.append(f"port = {port}\n")
            else:
                updated_lines.append(line)

        with open(postgresql_conf, "w") as f:
            f.writelines(updated_lines)

        print(f"Updated {postgresql_conf} for listen_addresses and port.")

    # Step 4: Start PostgreSQL server
    print("Starting PostgreSQL server...")
    subprocess.run([
        r"C:\Program Files\PostgreSQL\14\bin\pg_ctl", "-D", data_dir, "-l", logfile, "start"
    ], check=True)
    time.sleep(5)  # Give time for the server to start
    print("PostgreSQL server started.")

    # Step 5: Enable PGVector extension
    print("Connecting to PostgreSQL to enable PGVector extension...")
    import psycopg2
    try:
        conn = psycopg2.connect(
            dbname="postgres", user="postgres", host="127.0.0.1", port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Create database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'cerebro_pgvectordb';")
        if cursor.fetchone() is None:
            print("Creating database cerebro_pgvectordb...")
            cursor.execute("CREATE DATABASE cerebro_pgvectordb;")

        # Enable PGVector extension
        conn.close()
        conn = psycopg2.connect(
            dbname="cerebro_pgvectordb", user="postgres", host="127.0.0.1", port=port
        )
        cursor = conn.cursor()
        print("Enabling PGVector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        print("PGVector extension enabled.")

    except Exception as e:
        print(f"Error enabling PGVector extension: {e}")
    finally:
        if conn:
            conn.close()

    print("PostgreSQL setup complete.")

if __name__ == "__main__":
    initialize_pgvector()
