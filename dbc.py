import mysql.connector
from mysql.connector import Error


def create_server_connection(host_name, user_name, user_password) -> mysql.connector.connect:
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            password=user_password
        )
        print("Database connection successful!")
    except Error as error:
        print(f"Error: '{error}'")

    return connection