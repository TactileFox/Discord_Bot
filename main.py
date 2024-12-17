import os 
import asyncio
import psycopg2 as psy
import api_requests as api
import psql_connection as psql
from datetime import datetime as dt, timedelta
from typing import Final, Optional
from dotenv import load_dotenv
from discord import Intents, Client, Message, Reaction, User, Embed, Colour, WebhookMessage
from discord.ext import commands



# Load token
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Setup myself
intents: Intents = Intents.default()
intents.message_content = True 
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

 
# Helper methods
async def send_message(message: Message, user_message: str) -> None:

    if not user_message: # If user_message NULL
        print('Message empty; intents not enabled')
        return
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]
    elif user_message[0] == '!':
        user_message = user_message[1:]

    try: 
        response: str = get_response(user_message)
        if response == '' or not response: # don't send if empty or null
            return
        else: 
            await message.author.send(response) if is_private else await message.channel.send(response) # If private, dm to author else send to channel
    except Exception as e: 
        print(e) 
    
# Events:
# start bot
@bot.event 
async def on_ready() -> None: 
    await bot.tree.sync()
    print(f'{bot.user} is now running!') 

# incoming messages
@bot.event 
async def on_message(message: Message) -> bool:

    # Make sure message author is not the bot
    if message.author == bot.user: 
        return False
    
    await psql.create_message_log(message)

    username: str = str(message.author.name) 
    user_message: str = message.content
    channel: str = str(message.channel.name)

    print(f'[{channel}] {username}: "{user_message}"')
    return True

# Messages must be in the internal cache to trigger this
@bot.event
async def on_message_edit(before: Message, after: Message) -> None:
    if before.author == bot.user: 
        return 
    await psql.log_message_edit(before, after)

# Message must be in the internal cache to trigger this
@bot.event
async def on_message_delete(message: Message) -> None:
    if message.author == bot.user: 
        return 
    await psql.log_message_deletion(message)

# Messages must be in the internal cache to trigger this
@bot.event
async def on_bulk_message_delete(messages: list[Message]) -> None:
    for message in messages:
        if message.author == bot.user: 
            continue 
        await psql.log_message_deletion(message)

# Messages but be in the internal cache to trigger this
@bot.event
async def on_reaction_add(reaction: Reaction, user: User) -> None:
    if user == bot.user or reaction.message.author == bot.user: 
        return 
    psql.log_message_reaction(reaction, user)

# Messages but be in the internal cache to trigger this
@bot.event
async def on_reaction_remove(reaction: Reaction, user: User) -> None:
    if user == bot.user or reaction.message.author == bot.user: 
        return 
    psql.log_reaction_deletion(reaction, user)

# Messages but be in the internal cache to trigger this
@bot.event
async def on_reaction_clear(reactions: list[Reaction], message: Message) -> None:
    psql.log_reaction_clear(reactions, message)

# @bot.event
# async def on_reaction_clear_emoji(reaction: Reaction) -> None:
#     psql.log_reaction_emoji_clear() # same as on_reaction_clear but I need to check emoji is the same. Need to add emoji id to table and likely an emoji table. If emoji is a str, it won't have an id

# Commands
@bot.hybrid_command(name='get_message_count_by_user')
async def message_count_by_user(ctx: commands.Context):
    await ctx.send('Here is your graph:', file=psql.get_message_counts(ctx.guild))

# TODO update to include images. Get the urls from the attachments table and then copy url embed logic from get_astronomy_by_date
@bot.hybrid_command(name="snipe") # returns last updated message's content for that channel
async def snipe(ctx: commands.Context):

    before, after, username, action = psql.get_last_updated_message(ctx.channel.id)
    ending_periods_after = '...' if len(after) > 1000 else '' 
    ending_periods_before = '...' if before and len(before) > 1000 else ''
    if action == 'deleted':
        embed = Embed(title=f'Last deleted message: {username}', description=f'{after[:1000]}{ending_periods_after}')
        await ctx.send(embed=embed)
    elif action == 'edited':
        embed = Embed(title=f'Last edited message: {username}', description=f'**Before:**\n{before[:1000]}{ending_periods_before}\n\n**After:** \n{after[:1000]}{ending_periods_after}')
        await ctx.send(embed=embed)

# Requires the interaction to be defered beforehand
async def send_paginated_embed(ctx: commands.Context, pages: list[Embed], timeout: float):

    # Make sure pages is not null 
    if not pages:
        await ctx.interaction.followup.send("No pages to display because Foxy is a lil silly")
        return 
    
    # Create embed based off first page
    current_page = 0
    message = await ctx.interaction.followup.send(embed=pages[current_page])

    # Add "buttons" 
    await message.add_reaction('⬅️')
    await message.add_reaction('➡️')
    await message.add_reaction('⏹️')

    # Define a basic check to make sure user == command user and message == bot embed
    def check(reaction: Reaction, user: User):
        test = True
        if test: return reaction.message.id == message.id 
        else: return user == ctx.author and reaction.message.id == message.id
        
    # Use a while loop that expires after a while or can be manually exited
    while True:

        try:
            # Await reaction and make python accept that reaction and user are specific types
            reaction: Reaction 
            user: User
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=timeout)

            # Once a reaction is added to the message, remove it then check it
            await reaction.remove(user)

            if reaction.emoji == '⬅️' and current_page > 0:
                current_page -= 1
                try: 
                    await message.edit(embed=pages[current_page])
                except Exception as e:
                    print(f'Error in paginated backwards with exception {e}')
            elif reaction.emoji == '➡️' and current_page < len(pages) - 1:
                current_page += 1
                try:
                    await message.edit(embed=pages[current_page])
                except Exception as e:
                    print(f'Error in paginated forwards with exception {e}')
            elif reaction.emoji == '⏹️':
                try:
                    await message.clear_reaction('⬅️')
                    await message.clear_reaction('➡️')
                    await message.clear_reaction('⏹️')
                except Exception as e:
                    print(f'Error removing paginated recations with exception {e}')
                break
            else:
                # Invalid reaction
                continue
        except asyncio.TimeoutError:
            # Time out and break after set time
            await message.clear_reaction('⬅️')
            await message.clear_reaction('➡️')
            await message.clear_reaction('⏹️')
            break
            
@bot.hybrid_command(name='get_weather') # takes in lat lon and returns a paginated embed of the NWS API response
async def get_weather(ctx: commands.Context, latitude: float, longitude: float, units: str):

    # Clean units input
    units = 'si' if units.lower() in ('celcius, c, si, standard, metric') else 'us'

    try: 
        data = await api.get_usa_weather(lat=latitude, lon=longitude, unit_type=units)
        if data == None:
            raise Exception('Error Getting Weather from API')
        else:
            city, state, forecast = data
    except:
        ctx.send('Error getting weather, please try again')
    forecast = forecast[:6]
    # I only want to return 6 pages of forecasts. Create embeds then append them
    pages: list[Embed] = list()
    colours: list[Colour] = [Colour.red(), Colour.orange(), Colour.yellow(), Colour.green(), Colour.blue(), Colour.purple()]

    # Clean some null values for user readability
    def none_to_na(var) -> str:
        return 'N/A' if not var else var

    for data in forecast:
        embed = Embed(title=f"{data['name']} - {city}, {state}", 
            description=(
            f"**Temperature**: {none_to_na(data['temperature'])}{data['temperatureUnit']}\n"
            f"**Precipitation**: {none_to_na(data['probabilityOfPrecipitation']['value'])}%\n"
            f"**Wind Speed**: {none_to_na(data['windSpeed'])}\n"
            f"**Wind Direction**: {none_to_na(data['windDirection'])}\n"
            f"**Short Forecast**: {data['shortForecast']}\n"
            f"**Detailed Forecast**: {data['detailedForecast']}"
            ),
            color=colours[data['number'] -1] # starts at 1 so have to subtract 1
        )
        pages.append(embed)

    # Defer before sending
    await ctx.interaction.response.defer()
    await send_paginated_embed(ctx=ctx, pages=pages, timeout=60.0)
    
@bot.hybrid_command(name='get_astronomy')
async def get_astronomy_by_date(ctx: commands.Context, start_day: Optional[int], start_month: Optional[int], start_year: Optional[int], end_day: Optional[int], end_month: Optional[int], end_year: Optional[int]):

    start_date = None
    end_date = None    

    if start_day and start_month and start_year:
        try:
            start_date_obj = dt(start_year, start_month, start_day)
            start_date = start_date_obj.strftime("%Y-%m-%d")
        except:
            start_date = None
    if end_day and end_month and end_year:
        try:
            end_date_obj = dt(end_year, end_month, end_day)

            # Make sure end date is after start date
            if end_date_obj.date() > start_date_obj.date(): # If end > start assign normally
                # Limit to one year
                end_date = end_date_obj.strftime("%Y-%m-%d") if (start_date_obj - end_date_obj).days <= 365 else (start_date_obj + timedelta(days=365)).strftime("%Y-%m-%d")
            else: # Else assign opposites
                start_date = end_date_obj.strftime("%Y-%m-%d")
                # Limit to one year
                end_date = start_date_obj.strftime("%Y-%m-%d") if (start_date_obj - end_date_obj).days <= 365 else (start_date_obj + timedelta(days=365)).strftime("%Y-%m-%d")

        except:
            end_date = None

    # Defer because other stuff assumes it is defered 
    await ctx.interaction.response.defer(ephemeral=False)
    if start_date: # If it is a range, defer so discord doesn't expire the interaction
        await asyncio.sleep(5)

    try: 
        data = await api.get_astronomy_picture(start_date, end_date)
        if data == None:
            raise Exception('API Error, Please Try Again')
        else:
            urls, dates, titles, explanations = data
    except ConnectionError as e:
        print(f'Connection Error with {e}')
        await ctx.interaction.followup.send('Could not resolve host', ephemeral=True)
        return
    except Exception as e:
        await ctx.interaction.followup.send(f'**Unexpected Exception:** {e}', ephemeral=True)
        return

    if not urls: ctx.interaction.command_failed = True

    pages: list[Embed] = list()

    for url, date, title, explanation in zip(urls, dates, titles, explanations):

        embed = Embed(
            title=f'[APOD] {title}: {date}',
            description=explanation,
            colour=Colour.random()
        )
        embed.set_image(url=url)
        pages.append(embed)
    
    # 30 seconds per page, max of 5 minutes.
    timeout = float(30.0 * len(pages)) if len(pages) <= 10 else 300.0
    await send_paginated_embed(ctx, pages, timeout=timeout) if len(pages) > 1 else await ctx.send(embed=pages[0])
   

# Entry point >:3
def main() -> None:
    bot.run(token=TOKEN) # start the session with the auth token

if __name__ == '__main__': # run the program
    main()
