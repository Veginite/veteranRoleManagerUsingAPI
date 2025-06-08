#########################################
# Author: Veginite
# Module status: SEMI-FINISHED
# To do: Implement linking module and require a Discord-to-PoE link to claim roles.
#########################################

from aiosqlite import Connection
import discord

from db import run_db_query, run_many_db_queries, get_generic_query_error_msg


async def process_role(dbc : Connection, user: discord.User, poe_acc_name: str) -> str:
    unique_years_played = await fetch_unique_years_played(dbc, poe_acc_name)

    if unique_years_played is None: # Query error
        return get_generic_query_error_msg()
    elif not unique_years_played: # Empty list
        return (f'Process aborted: Query returned no Conflux records for PoE account {poe_acc_name}.'
                f'If you are new to Conflux and have recently joined your first league, please await a database update.')
    return await update_veteran_role(dbc, user, unique_years_played[0][0])


async def fetch_unique_years_played(dbc: Connection, poe_acc_name: str):
    username = {'username': poe_acc_name}
    query = (f"SELECT COUNT(DISTINCT strftime('%Y', l.start_at)) FROM character "
             f"INNER JOIN poe_account a ON a.id = character.owner "
             f"INNER JOIN league l ON l.id = character.league "
             f"WHERE a.username = :username AND l.awards_veteran_roles = TRUE;")

    return await run_db_query(dbc, query, username)


async def update_veteran_role(dbc: Connection, user: discord.User, unique_years_played: int) -> str:
    vet_roles = await fetch_veteran_roles(dbc)

    if vet_roles is None: # Query error
        return get_generic_query_error_msg()
    elif not vet_roles: # Empty list
        return 'Process aborted: Query returned no veteran roles. Ping Vegi.'

    vet_roles = [row[0] for row in vet_roles] # Fetch roles and construct a list of ids
    user_vet_roles = [role.id for role in user.roles if role.id in vet_roles] # the vet roles the user currently has
    eligible_role = await fetch_eligible_role(dbc, unique_years_played) # [0][1] is role id in db

    if eligible_role is None: # Query error
        return get_generic_query_error_msg()
    elif not eligible_role:  # Empty list
        return 'Process aborted: Query returned no eligible roles. Ping Vegi.'

    eligible_role = eligible_role[0][1]  # id of the Tuple

    if eligible_role in user_vet_roles:
        return 'Skipped role processing: User already has the maximum eligible role.'

    await purge_prior_roles(user, user_vet_roles)
    await user.add_roles(user.guild.get_role(eligible_role))
    response_message = (f'For playing Conflux during {unique_years_played} years, '
                                f'<@{str(user.id)}> has been awarded the following: ')
    response_message += f'<@&{eligible_role}>'
    return response_message


async def fetch_veteran_roles(dbc: Connection):
    query = f"SELECT discord_role_id FROM veteran_role;"
    return await run_db_query(dbc, query, {})


async def fetch_eligible_role(dbc: Connection, unique_years_played: int):
    query = "SELECT name, discord_role_id FROM veteran_role WHERE required_years = :unique_years_played;"
    return await run_db_query(dbc, query, {'unique_years_played': unique_years_played})


async def purge_prior_roles(user: discord.User, user_veteran_roles: list):
    for role in user_veteran_roles:
        await user.remove_roles(user.guild.get_role(role))
