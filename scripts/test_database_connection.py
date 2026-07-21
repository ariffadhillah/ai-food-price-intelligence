from app.database.db import get_connection


def main() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user,
                    version();
                """
            )

            database_name, user_name, version = cursor.fetchone()

    print(f"Database : {database_name}")
    print(f"User     : {user_name}")
    print(f"Version  : {version}")
    print()
    print("Database connection berhasil.")


if __name__ == "__main__":
    main()