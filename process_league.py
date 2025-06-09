#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

from aiosqlite import Connection
import aiohttp
import json

from db import run_db_query, run_many_db_queries
from utils import get_host_mention, query_was_unsuccessful


async def process_league(league_name: str, dbc: Connection, session) -> str:
    account_entries: list = []
    character_entries: list = []

    # FOR TESTING WITH LOCALLY SOURCED JSON DATA
    # with open('league_example.json', encoding='utf-8') as f:
        # league_data = json.load(f)

    # The Initial API request gives us information about how many ladder character entries the league has.
    # This allows us to precisely calculate the rest of the necessary API requests.
    # Grinding Gear Games has a hard limit of 500 entries per API request.
    league_data = await fetch_league_data(session, league_name, 500, 0)

    if league_data is None:
        return "Unable to fetch league data. Check console for HTTP status code. " + get_host_mention()

    # If the league is brand new, add it to the database
    query_error = await insert_league_entry(dbc, league_data["league"])
    if query_was_unsuccessful(query_error):
        return query_error

    process_ladder_entries(league_data["ladder"]["entries"],
                           account_entries,
                           character_entries,
                           league_data["league"]["name"])

    total_entries = int(league_data["ladder"]["total"])
    remaining_entries = total_entries - len(league_data["ladder"]["entries"])
    print("Remaining entries: " + str(remaining_entries))

    # Based on the number of ladder character entries left after the initial API request, fetch and process the rest
    while remaining_entries > 0:
        time.sleep(0.05) # There is no guideline for rate-limiting, so I'll just go with 50 ms to be safe
        offset = total_entries - remaining_entries

        league_data = await fetch_league_data(session, league_name, min(remaining_entries, 500), offset)
        if league_data is None:
            return "Unable to fetch league data. Check console for HTTP status code. " + get_host_mention()

        process_ladder_entries(league_data["ladder"]["entries"],
                               account_entries,
                               character_entries,
                               league_data["league"]["name"])

        remaining_entries -= len(league_data["ladder"]["entries"])

    # Insert the full list of PoE accounts for the given league
    query_error = await insert_account_entries(dbc, account_entries)
    if query_was_unsuccessful(query_error):
        return query_error

    # Insert the full list of PoE characters for the given league
    query_error = await insert_character_entries(dbc, character_entries)
    if query_was_unsuccessful(query_error):
        return query_error

    return f"Successfully processed {league_name} with {total_entries} total entries."


async def fetch_league_data(session: aiohttp.ClientSession, league_name: str, limit: int, offset: int) -> dict | None:
    url = f'https://api.pathofexile.com/league/{league_name}/ladder?limit={limit}&offset={offset}'

    async with session.get(url) as response:
        league_data = json.loads(await response.text())
        if response.status == 200:
            fetched_entries = len(league_data["ladder"]["entries"])
            total_entries = league_data["ladder"]["total"]
            print(f'{league_name}: Fetched entries: {offset+1}-{offset+min(limit, fetched_entries)}/{total_entries}.')
            return league_data
        else:
            print(str(response.status))
            return None


def process_ladder_entries(ladder_entries, account_entries, character_entries, league_name) -> None:
    for entry in ladder_entries:
        character = entry["character"]

        # New accounts need to be added before the characters because the foreign key is not allowed to be null
        account_entries.append({'username': entry["account"]["name"]})

        character_entries.append({
            'id': character["id"],
            'name': character["name"],
            'rank': int(entry["rank"]),
            'class': character["class"],
            'level': int(character["level"]),
            'experience': int(character["experience"]),
            'delve_depth': int(character["depth"]['default']) if 'depth' in character else None,
            'owner': entry["account"]["name"],
            'league_name': league_name})


async def illegitimize_league(dbc: Connection, league_name: str) -> str:
    query_error = await update_league_no_roles(dbc, league_name)
    if query_was_unsuccessful(query_error):
        return query_error

    return f"{league_name} is now ineligible for vet roles."


# ------------------------------------ SQL QUERIES ------------------------------------


async def insert_account_entries(dbc: Connection, account_entries: list) -> str:
    query = f'INSERT INTO poe_account (username) VALUES (:username) ON CONFLICT(username) DO NOTHING;'

    insertion = await run_many_db_queries(dbc, query, account_entries)

    query_error = ""
    if insertion is None:
        query_error = get_generic_query_error_msg() + insert_account_entries.__name__

    return query_error


async def insert_character_entries(dbc:Connection, character_entries: list) -> str:
    subquery_owner = f'SELECT id FROM poe_account WHERE username = :owner'  # FK surrogate key
    subquery_league = f'SELECT id FROM league WHERE name = :league_name'  # FK surrogate key

    query = (f'INSERT INTO character (id, name, rank, class, level, experience, delve_depth, owner, league) '
             f'VALUES(:id, :name, :rank, :class, :level, :experience, :delve_depth, '
             f'({subquery_owner}), ({subquery_league}))'
             f'ON CONFLICT(id) DO '
             f'UPDATE SET '
             f'name=:name, rank=:rank, class=:class, level=:level, experience=:experience, delve_depth=:delve_depth, '
             f'WHERE id=:id;')

    upsert = await run_many_db_queries(dbc, query, character_entries)

    query_error = ""
    if upsert is None:
        query_error = get_generic_query_error_msg() + insert_character_entries.__name__

    return query_error


async def insert_league_entry(dbc, league_data) -> str:
    league_entry = {
        'league_name': league_data["name"],
        'start_at': league_data["startAt"],
        'end_at': league_data["endAt"]}

    query = (f'INSERT INTO league (name, start_at, end_at) '
             f'VALUES (:league_name, :start_at, :end_at) '
             f'ON CONFLICT(name) DO UPDATE SET start_at=:start_at, end_at=:end_at;')

    insertion = await run_db_query(dbc, query, league_entry)

    query_error = ""
    if insertion is None:
        query_error = get_generic_query_error_msg() + insert_league_entry.__name__

    return query_error


async def update_league_no_roles(dbc: Connection, league_name: str) -> str:
    query = "UPDATE league SET awards_veteran_roles = FALSE WHERE name = :league_name;"
    update = await run_db_query(dbc, query, {'league_name': league_name})

    query_error = ""
    if update is None:
        query_error = get_generic_query_error_msg() + update_league_no_roles.__name__

    return query_error