<div style="text-align: center">

# Path of Exile Private League Bot Template

</div>

## What this is:

<p>This is a bot designed to fetch data from GGG's API, parse it and store it into a database. What scope you're interested in and what data to process & use is up to you. This template focuses on fetching private league data and verifying PoE account ownership through Discord bot commands.</p>

<p></p>


## How to use:

1. Visit https://www.pathofexile.com/developer/docs/index and follow the steps to register an application. This can take anywhere from days to weeks depending on GGG's workload. By default this template uses <b>account:profile</b> and <b>service:leagues:ladder</b>
2. Download this repo and install the dependencies in libstoinstall.txt
3. Visit https://discord.com/developers/applications/ and create & configure your application.
4. Invite the bot to the relevant server by going into the OAuth2 section on the developer page. Only the servers you have permissions for will show up in the list. The scopes the bot designed here uses are:
- Scopes: applications.commands, bot
- Bot: Send Messages, Read Message History, Manage Roles, Use Slash Commands
5. Insert the relevant data into the .env file
6. Run main.py
7. Execute the database queries found in db-queries.txt in order to setup the database

<p>The bot is now ready for use! Don't forget to restrict command usage in the server settings where necessary.</p>

<p>If you wish to add more commands, simply make a new @bot.tree.command section in main.py and write your own code.</p>

## License and distribution

Forking and derived work may be published and distributed as long as there's clear credit to me, where due.

## Credits & Special Thanks:

- <b>Yeknom</b> for assisting with hosting, troubleshooting and hotfixes
- <b>PeskyTheBear</b> for helping me understand request modules and a bit of SQL
- <b>Lily</b> for sacrificing your IP address during the launch of the original project which scraped html