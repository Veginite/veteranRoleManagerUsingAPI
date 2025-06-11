#########################################
# Author: Veginite
# Module status: FINISHED - Expandable
#########################################

from aiosqlite import Connection

from db import run_db_query
from queries import fetch_characters_from_username


async def get_character_tables_from_username(dbc: Connection, poe_acc_name: str) -> list | str:
    query_result = await fetch_characters_from_username(dbc, poe_acc_name)
    if query_result is None or not query_result["value"]:
        return query_result["query_error"]
    else:
        character_list = query_result["value"]

    tables = []
    table = []
    for row in character_list:
        table.append(list(row))
        if len(table) == 10:
            tables.append(table)
            table = []
    if len(table) > 0:
        tables.append(table)

    return tables
