#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from aiosqlite import Connection, Error


async def run_db_query(dbc: Connection, query: str, params):
    cursor = await dbc.cursor()
    try:
        await cursor.execute(query, params)
        await dbc.commit()
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'" + " " + query)
        return
    return await cursor.fetchall()
