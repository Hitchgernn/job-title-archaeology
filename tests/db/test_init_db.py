from unittest.mock import MagicMock, patch

import init_db


def test_main_runs_migrations_and_closes_connection() -> None:
    connection = MagicMock()

    with patch("init_db.open_connection", return_value=connection) as open_connection, patch("init_db.run_migrations") as run_migrations:
        init_db.main()

    open_connection.assert_called_once_with()
    run_migrations.assert_called_once_with(connection)
    connection.close.assert_called_once_with()
