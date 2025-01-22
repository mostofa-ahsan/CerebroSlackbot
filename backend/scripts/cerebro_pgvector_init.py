import os
import subprocess
import psycopg2

# Database connection parameters
DB_USER = "ahsamo6"
DB_PASSWORD = "1056092"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_HOST = "localhost"
DUMP_PATH = "../../data_ingestion/data/vds_pgvector"

# SQL Commands
SQL_COMMANDS = [
    "CREATE EXTENSION IF NOT EXISTS vector;",
    "CREATE TABLE IF NOT EXISTS items (
        id SERIAL PRIMARY KEY,
        name TEXT,
        description TEXT,
        embedding VECTOR(1536)
    );"
]

def execute_sql_commands():
    """Execute SQL commands to initialize the database."""
    try:
        # Connect to the database
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        cursor = connection.cursor()

        # Execute each SQL command
        for command in SQL_COMMANDS:
            cursor.execute(command)
            print(f"Executed: {command}")

        # Commit changes and close the connection
        connection.commit()
        cursor.close()
        connection.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error during database initialization: {e}")

def create_db_dump():
    """Create a local database dump."""
    try:
        # Ensure the dump directory exists
        os.makedirs(DUMP_PATH, exist_ok=True)

        # Path for the dump file
        dump_file_path = os.path.join(DUMP_PATH, "vds_pgvector_dump.sql")

        # Run the pg_dump command
        subprocess.run(
            [
                "pg_dump",
                "--host", DB_HOST,
                "--port", DB_PORT,
                "--username", DB_USER,
                "--dbname", DB_NAME,
                "--file", dump_file_path
            ],
            check=True
        )

        print(f"Database dump created at: {dump_file_path}")
    except Exception as e:
        print(f"Error during database dump creation: {e}")

def main():
    # Initialize the database with the required table and extension
    execute_sql_commands()

    # Create a local database dump
    create_db_dump()

if __name__ == "__main__":
    main()
