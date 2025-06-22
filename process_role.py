#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

from aiosqlite import Connection
import discord
import datetime

from queries import fetch_eligible_role, fetch_veteran_roles, fetch_unique_years_played, get_linked_poe_username
from queries import update_discord_account_vet_role
from utils import purge_roles, query_was_unsuccessful


async def process_role(dbc: Connection, user: discord.User) -> str:

    # Attempt to get the PoE account name linked to the Discord user
    query_result = await get_linked_poe_username(dbc, user)
    if query_result is None or not query_result["value"]:
        return query_result["query_error"]
    else:
        poe_acc_name = query_result["value"]

    # Fetch the distinct start_at years the given user has on record
    query_result = await fetch_unique_years_played(dbc, poe_acc_name)
    if query_result is None or not query_result["value"]:
        return query_result["query_error"]
    else:
        unique_years_played = query_result["value"]

    unique_years_played = [int(row[0]) for row in unique_years_played]

    return await update_veteran_role(dbc, user, unique_years_played)


async def update_veteran_role(dbc: Connection, user: discord.User, unique_years_played: list) -> str:
    # Fetch the veteran role IDs from the database and generate a list of the ones the invoked user already has
    query_result = await fetch_veteran_roles(dbc)
    if query_result is None or not query_result["value"]:
        return query_result["query_error"]
    else:
        vet_roles = query_result["value"]

    vet_roles = [{"id": row[0], "req_years": row[1]} for row in vet_roles] # Create a list of role id & req years
    vet_role_ids = [d["id"] for d in vet_roles]
    user_vet_role_ids = [role.id for role in user.roles if role.id in vet_role_ids] # the vet role ids of invoked user

    # Update the invoked user's veteran role
    unique_amount_of_years_played = len(unique_years_played)
    matched_role_required_year: int = min(len(vet_roles), unique_amount_of_years_played)
    eligible_role: dict = next(role for role in vet_roles if role["req_years"] is matched_role_required_year)
    if matched_role_required_year == len(vet_roles):
        return f'The only thing beyond <@&{eligible_role["id"]}> is NON-EXISTENCE'
    elif eligible_role["id"] in user_vet_role_ids:
        current_year = datetime.datetime.now().year
        next_eligible_role: dict = next(role for role in vet_roles if role["req_years"] is matched_role_required_year+1)
        next_eligible_year = current_year if not current_year in unique_years_played else current_year + 1

        return (f'You will be eligible for <@&{next_eligible_role["id"]}> swag once you have '
                f'made a character in any {next_eligible_year} ladder!')

    await purge_roles(user, user_vet_role_ids)
    await user.add_roles(user.guild.get_role(eligible_role["id"]))
    response_message = (f'For playing Conflux during {len(unique_years_played)} years, '
                                f'<@{str(user.id)}> is now part of team: ')
    response_message += f'<@&{eligible_role["id"]}>'

    # Update the Discord account's vet role
    query_error = await update_discord_account_vet_role(dbc, user, eligible_role["id"])
    if query_was_unsuccessful(query_error):
        return query_error

    return response_message
