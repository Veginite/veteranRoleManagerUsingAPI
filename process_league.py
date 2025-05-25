#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from aiosqlite import Connection
import aiohttp
import json

from db import run_db_query, table_entry_exists


async def process_league(league_name: str, dbc: Connection, session) -> bool:
    # Initial API request, gives us information about how many ladder character entries the league has and allows us to
    # precisely calculate the rest of the necessary API requests. GGG has a hard limit of 500 entries per API request.
    league_data = await fetch_league_data(session, league_name, 500, 0)

    # If the league is brand new, add it to the database
    await process_league_entry(dbc, league_data["league"])

    await process_ladder_entries(dbc, league_data["ladder"]["entries"], league_data["league"]["name"])
    total_entries = int(league_data["ladder"]["total"])
    remaining_entries = total_entries - len(league_data["ladder"]["entries"])

    # Based on the number of ladder character entries left after the initial API request, fetch and process the rest
    while remaining_entries > 0:
        offset = total_entries - remaining_entries
        league_data = await fetch_league_data(session, league_name, min(remaining_entries, 500), offset)
        await process_ladder_entries(dbc, league_data["ladder"]["entries"], league_data["league"]["name"])
        remaining_entries -= len(league_data["ladder"]["entries"])

    return True


async def fetch_league_data(session: aiohttp.ClientSession, league_name: str, limit: int, offset: int):
    url = f'https://api.pathofexile.com/league/{league_name}/ladder?limit={limit}&offset={offset}'

    async with session.get(url) as response:
        return json.loads(await response.text()) if response.status == 200 else None


async def process_ladder_entries(dbc, ladder_entries, league_name):
    for entry in ladder_entries:
        character = entry["character"]

        # New accounts need to be added before the characters because the foreign key is not allowed to be null
        if not await table_entry_exists(dbc, "account", "username", entry["account"]["name"]):
            await run_db_query(dbc, f'INSERT INTO account (username) VALUES ("{entry["account"]["name"]}")')

        # Update the character data if it does not already exist or insert a new entry if it's a new character
        if await table_entry_exists(dbc, "character", "id", character["id"]):
            await run_db_query(dbc, f'UPDATE character '
                                    f'SET '
                                    f'name="{character["name"]}", '
                                    f'rank={entry["rank"]}, '
                                    f'class="{character["class"]}", '
                                    f'level={character["level"]}, '
                                    f'experience={character["experience"]} '
                                    f'WHERE '
                                    f'id="{character["id"]}"')
        else:
            await run_db_query(dbc, f'INSERT INTO character '
                                    f'(id, name, rank, class, level, experience, owner, league) '
                                    f'VALUES('
                                    f'"{character["id"]}", '
                                    f'"{character["name"]}", '
                                    f'{entry["rank"]}, '
                                    f'"{character["class"]}", '
                                    f'{character["level"]}, '
                                    f'{character["experience"]}, '
                                    f'(SELECT id FROM account WHERE username = "{entry["account"]["name"]}"), '  # FK
                                    f'(SELECT id FROM league WHERE name = "{league_name}")')  # FK


async def process_league_entry(dbc, league_data):
    if not await table_entry_exists(dbc, "league", "name", league_data["name"]):
        await run_db_query(dbc, f'INSERT INTO league '
                                f'(name, start_date, end_date) '
                                f'VALUES ('
                                f'"{league_data["name"]}", '
                                f'"{league_data["startAt"]}", '
                                f'"{league_data["endAt"]}")')
