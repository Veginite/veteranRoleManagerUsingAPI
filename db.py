#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from aiosqlite import Connection, Error


async def run_db_query(dbc: Connection, query: str, params):
    cursor = await dbc.cursor()
    try:
        # If there's only one entry, use 'execute'
        if type(params) is dict:
            await cursor.execute(query, params)
        # If there are multiple entries, use 'executemany'
        elif type(params) is list:
            await cursor.executemany(query, params)

        await dbc.commit()
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'" + " " + query)
        await cursor.close()
        return None
    data = await cursor.fetchall()
    await cursor.close()
    return data
