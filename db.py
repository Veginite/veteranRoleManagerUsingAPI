#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from aiosqlite import Connection, Error


async def run_db_query(dbc: Connection, query: str, param: dict):
    cursor = await dbc.cursor()
    try:
        await cursor.execute(query, param)
        await dbc.commit()
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'" + " " + query)
        await cursor.close()
        return None
    rows = await cursor.fetchall()
    await cursor.close()
    return rows

async def run_many_db_queries(dbc: Connection, query: str, params: list):
    cursor = await dbc.cursor()
    try:
        await cursor.executemany(query, params)
        await dbc.commit()
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'" + " " + query)
        await cursor.close()
        return None
    rows = await cursor.fetchall()
    await cursor.close()
    return rows