#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from aiosqlite import Connection
import aiohttp
import json

from db import run_db_query, table_entry_exists


async def process_league(league_name: str, dbc: Connection, session) -> bool:
    # Initial API request, gives us information about how many ladder character entries the league has.
    # This allows us to precisely calculate the rest of the necessary API requests.
    # Grinding Gear Games has a hard limit of 500 entries per API request.

    # league_data = await fetch_league_data(session, league_name, 500, 0)
    with open('league_example.json') as f:
        league_data = json.load(f)

    # If the league is brand new, add it to the database
    await process_league_entry(dbc, league_data["league"])

    await process_ladder_entries(dbc, league_data["ladder"]["entries"], league_data["league"]["name"])
    total_entries = int(league_data["ladder"]["total"])
    remaining_entries = total_entries - len(league_data["ladder"]["entries"])
    print("Remaining entries: " + str(remaining_entries))

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
            params = {'username': entry["account"]["name"]}

            query = f'INSERT INTO account (username) VALUES (:username);'

            await run_db_query(dbc, query, params)

        # Update the character data if it does not already exist or insert a new entry if it's a new character
        if await table_entry_exists(dbc, "character", "id", character["id"]):
            params = {'name': character["name"],
                      'rank': entry["rank"],
                      'class': character["class"],
                      'level': character["level"],
                      'experience': character["experience"],
                      'id': character["id"]}

            query = f'UPDATE character SET name=:name, rank=:rank, class=:class, level=:level, experience=:experience WHERE id=:id;'

            await run_db_query(dbc, query, params)

        else:
            params = {'id': character["id"],
                      'name': character["name"],
                      'rank': entry["rank"],
                      'class': character["class"],
                      'level': character["level"],
                      'experience': character["experience"],
                      'owner': entry["account"]["name"],
                      'league_name': league_name}

            subquery_owner = f'SELECT id FROM account WHERE username = :owner'  # FK surrogate key
            subquery_league = f'SELECT id FROM league WHERE name = :league_name'  # FK surrogate key

            query = (f'INSERT INTO character (id, name, rank, class, level, experience, owner, league) '
                     f'VALUES(:id, :name, :rank, :class, :level, :experience, ({subquery_owner}), ({subquery_league}))')

            await run_db_query(dbc, query, params)


async def process_league_entry(dbc, league_data):
    if not await table_entry_exists(dbc, "league", "name", league_data["name"]):
        params = {'league_name': league_data["name"],
                  'start_date': league_data["startAt"],
                  'end_date': league_data["endAt"]}

        query = f'INSERT INTO league (name, start_date, end_date) VALUES (:league_name, :start_date, :end_date)'

        await run_db_query(dbc, query, params)
