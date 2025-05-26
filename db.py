#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from aiosqlite import Connection, Error


async def run_db_query(dbc: Connection, query: str, params: dict):
    cursor = await dbc.cursor()
    try:
        await cursor.execute(query, params)
        await dbc.commit()
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'" + " " + query)
        return
    return await cursor.fetchall()


async def table_entry_exists(dbc: Connection, table: str, identifier: str, value):
    params = {'value': value}

    query = f'SELECT 1 FROM {table} WHERE {identifier} = :value'

    return await run_db_query(dbc, query, params)
