import os

import pandas as pd
from databricks.sdk import WorkspaceClient
from sqlalchemy import create_engine, event, text

workspace_client = WorkspaceClient()
user = workspace_client.current_user.me().user_name

postgres_username = user
postgres_host = os.getenv("PGHOST")
postgres_port = os.getenv("PGPORT")
postgres_database = os.getenv("PGDATABASE")

print("postgres_username", postgres_username)
print("postgres_host", postgres_host)
print("postgres_port", postgres_port)
print("postgres_database", postgres_database)

postgres_pool = create_engine(f"postgresql+psycopg://{postgres_username}:@{postgres_host}:{postgres_port}/{postgres_database}")

@event.listens_for(postgres_pool, "do_connect")
def provide_token(dialect, conn_rec, cargs, cparams):
    """Provide the App's OAuth token. Caching is managed by WorkspaceClient"""
    cparams["password"] = workspace_client.config.oauth_token().access_token

def get_holiday_requests():
    """
    Fetch all holiday requests from the database.

    Returns:
        pd.DataFrame: DataFrame containing holiday requests.
    """
    df = pd.read_sql_query("SELECT * FROM holidays.holiday_requests;", postgres_pool)
    return df

def update_request_status(request_id, status, comment):
    """Update the status and manager note for a specific holiday request."""
    with postgres_pool.begin() as conn:
        conn.execute(
            text("""
                 UPDATE holidays.holiday_requests
                 SET status = :status, manager_note = :comment
                 WHERE request_id = :request_id
                 """
                 ),
            {"status": status, "comment": comment or "", "request_id": request_id}
        )

def initialize_schema():
    with postgres_pool.begin() as conn:
        # create schema:
        conn.execute(
            text("""CREATE SCHEMA IF NOT EXISTS holidays""")
        )
        print("schema created (or already exists)")
        # grant privileges
        conn.execute(
            text("""GRANT USAGE ON SCHEMA holidays TO PUBLIC""")
        )
        conn.execute(
            text("""GRANT SELECT ON ALL TABLES IN SCHEMA holidays TO PUBLIC""")
        )
        print("Read permissions granted to all users")

        # Create the table within the schema:
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS holidays.holiday_requests (
                  request_id SERIAL PRIMARY KEY,
                  employee_name VARCHAR(255) NOT NULL,
                  start_date DATE NOT NULL,
                  end_date DATE NOT NULL,
                  status VARCHAR(50) NOT NULL,
                  manager_note TEXT
                )
            """)
        )
        print("table created (or already exists)")
        # Insert demo values:
        conn.execute(
            text("""
                INSERT INTO holidays.holiday_requests (employee_name, start_date, end_date, status, manager_note)
                VALUES
                    ('Joe', '2025-08-01', '2025-08-20', 'Pending', ''),
                    ('Suzy', '2025-07-22', '2025-07-25', 'Pending', ''),
                    ('Charlie', '2025-08-01', '2025-08-05', 'Pending', '')
            """)
        )
        print("demo data is inserted")

initialize_schema()
