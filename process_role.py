#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

from aiosqlite import Connection
import discord

from queries import fetch_eligible_role, fetch_veteran_roles, fetch_unique_years_played, get_linked_poe_username
from utils import purge_prior_roles


async def process_role(dbc: Connection, user: discord.User) -> str:

    # Check if there is a PoE account linked to the Discord user
    query_result = await get_linked_poe_username(dbc, user)
    if query_result is None or query_result["value"] is None:
        return query_result["query_error"]
    else:
        poe_acc_name = query_result["value"]

    # Fetch the distinct amount of start_at years the given user has on record
    query_result = await fetch_unique_years_played(dbc, poe_acc_name)
    if query_result is None or query_result["value"] is None:
        return query_result["query_error"]
    else:
        unique_years_played = query_result["value"]

    return await update_veteran_role(dbc, user, unique_years_played)


async def update_veteran_role(dbc: Connection, user: discord.User, unique_years_played: int) -> str:
    # Fetch the veteran role IDs from the database
    query_result = await fetch_veteran_roles(dbc)
    if query_result is None or query_result["value"] is None:
        return query_result["query_error"]
    else:
        vet_roles = query_result["value"]

    vet_roles = [row[0] for row in vet_roles] # Fetch roles and construct a list of ids
    user_vet_roles = [role.id for role in user.roles if role.id in vet_roles] # the vet roles the user currently has

    query_result = await fetch_eligible_role(dbc, unique_years_played) # [0][1] is role id in db
    if query_result is None or query_result["value"] is None:
        return query_result["query_error"]
    else:
        eligible_role = query_result["value"]

    if eligible_role in user_vet_roles:
        return 'Skipped role processing: User already has the maximum eligible role.'

    await purge_prior_roles(user, user_vet_roles)
    await user.add_roles(user.guild.get_role(eligible_role))
    response_message = (f'For playing Conflux during {unique_years_played} years, '
                                f'<@{str(user.id)}> has been awarded the following: ')
    response_message += f'<@&{eligible_role}>'
    return response_message
