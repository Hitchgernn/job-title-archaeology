from backend.db.connection import open_connection
from backend.db.migrate import run_migrations


def main() -> None:
    connection = open_connection()
    try:
        run_migrations(connection)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
