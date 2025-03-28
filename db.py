import mysql.connector
from mysql.connector import Error


def run_db_query(connection: mysql.connector, query: str):
    cursor = connection.cursor(prepare=True)
    try:
        cursor.execute(query)
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'")