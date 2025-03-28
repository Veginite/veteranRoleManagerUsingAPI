from aiosqlite import Connection, Error


async def run_db_query(dbc: Connection, query: str) -> bool:
    cursor = await dbc.cursor()
    try:
        await cursor.execute(query)
        await dbc.commit()
        print(f"Query: '{query}' executed successfully.")
    except Error as error:
        print(f"Error: '{error}'")
        return False
    return True
