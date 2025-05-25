#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from aiosqlite import Connection, Error


async def run_db_query(dbc: Connection, query: str):
    cursor = await dbc.cursor()
    try:
        await cursor.execute(query)
        await dbc.commit()
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'")
        return
    return await cursor.fetchall()


async def table_entry_exists(dbc: Connection, table: str, identifier: str, value):
    return await run_db_query(dbc, f'SELECT 1 FROM {table} WHERE {identifier} = "{value}"')
