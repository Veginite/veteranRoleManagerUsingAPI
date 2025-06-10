#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

# Programmer note: both run_db_query and run_many_db_queries always returns a list (empty or with tuples)
# or None if the query failed to execute.

from aiosqlite import Connection, Error

from utils import get_host_mention


async def run_db_query(dbc: Connection, query: str, param: dict):
    cursor = await dbc.cursor()
    try:
        await cursor.execute(query, param)
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'" + " " + query)
        await cursor.close()
        return None
    rows = await cursor.fetchall()
    await dbc.commit()
    await cursor.close()
    return rows


async def run_many_db_queries(dbc: Connection, query: str, params: list):
    cursor = await dbc.cursor()
    try:
        await cursor.executemany(query, params)
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'" + " " + query)
        await cursor.close()
        return None
    rows = await cursor.fetchall()
    await dbc.commit()
    await cursor.close()
    return rows


def get_generic_query_error_msg() -> str:
    return "Process aborted: Query failed. " + get_host_mention()
