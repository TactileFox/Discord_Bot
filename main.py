import os 
import asyncio
import api_requests as api
import psql_connection as psql
from datetime import datetime as dt, timedelta, timezone
from typing import Final, Optional
from dotenv import load_dotenv
from discord import Intents, Message, Reaction, User, Embed, Colour
from discord.ext import commands
from requests.exceptions import HTTPError, ConnectionError
from socket import gaierror

# Load Bot Token
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Setup the bot object with all default and priveleged intents
intents: Intents = Intents.default()
intents.message_content = True 
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

    
# Event Methods
@bot.event 
async def on_ready() -> None: 
    await bot.tree.sync() # Sync Commands
    print(f'{bot.user} is now running!') 

# Incoming Messages
@bot.event 
async def on_message(message: Message) -> None:

    if message.author == bot.user: 
        return
    
    await psql.create_message_log(message)

    print(f'[{message.channel.name}] {message.author.name}: "{message.content[:50]}"')

# Messages must be in the internal cache to trigger this
@bot.event
async def on_message_edit(before: Message, after: Message) -> None:
    
    if before.author == bot.user: 
        return 
    await psql.log_message_edit(before, after)

# Messages must be in the internal cache to trigger this
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
    await psql.log_message_reaction(reaction, user)

# Messages but be in the internal cache to trigger this
@bot.event
async def on_reaction_remove(reaction: Reaction, user: User) -> None:
    
    if user == bot.user or reaction.message.author == bot.user: 
        return 
    await psql.log_reaction_deletion(reaction, user)

# Messages but be in the internal cache to trigger this
@bot.event
async def on_reaction_clear(reactions: list[Reaction], message: Message) -> None:
    # TODO turn this into a for loop here instead of in the psql function.
    # TODO make sure message.author is not the bot, 
    # don't need to check if reaction is from bot.
    await psql.log_reaction_clear(reactions, message)

# @bot.event
# async def on_reaction_clear_emoji(reaction: Reaction) -> None:
#     psql.log_reaction_emoji_clear() 
        # same as on_reaction_clear but I need to check emoji is the same. Need to add emoji id to table and likely an emoji table. If emoji is a str, it won't have an id

# Commands
@bot.hybrid_command(name='get_message_count_by_user')
async def message_count_by_user(ctx: commands.Context):
    await ctx.send('Here is your graph:', file= await psql.get_message_counts(ctx.guild))

# TODO update to include images. Get the urls from the attachments table and then copy url embed logic from get_astronomy_by_date
@bot.hybrid_command(name="snipe") # returns last updated message's content for that channel
async def snipe(ctx: commands.Context):

    #TODO add handling for when these are NULL
    before, after, username, action = await psql.get_last_updated_message(ctx.channel.id)
    ending_periods_after = '...' if len(after) > 1000 else '' 
    ending_periods_before = '...' if before and len(before) > 1000 else '' #TODO I think this doesn't need to check that before exists?
    if action == 'deleted':
        embed = Embed(title=f'Last deleted message: {username}', description=f'{after[:1000]}{ending_periods_after}')
        await ctx.send(embed=embed)
    elif action == 'edited':
        embed = Embed(title=f'Last edited message: {username}', description=f'**Before:**\n{before[:1000]}{ending_periods_before}\n\n**After:** \n{after[:1000]}{ending_periods_after}')
        await ctx.send(embed=embed)

# Requires the interaction to be defered beforehand
async def send_paginated_embed(ctx: commands.Context, pages: list[Embed], timeout: float):

    if not pages:
        await ctx.interaction.followup.send("No pages to display because Foxy is a lil silly :3")
        return 
    
    # Create response
    current_page = 0
    message = await ctx.interaction.followup.send(embed=pages[current_page])

    # Add "buttons" 
    await message.add_reaction('⬅️')
    await message.add_reaction('➡️')
    await message.add_reaction('⏹️')

    def check(reaction: Reaction, user: User):
        test = True
        if test: return reaction.message.id == message.id 
        else: return user == ctx.author and reaction.message.id == message.id
        
    while True:

        try:
            reaction: Reaction 
            user: User
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=timeout)

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
                continue
        # Raised by timeout parameter in wait_for
        except asyncio.TimeoutError:
            await message.clear_reaction('⬅️')
            await message.clear_reaction('➡️')
            await message.clear_reaction('⏹️')
            break

# Paginated Embed of NWS Weather Data            
@bot.hybrid_command(name='get_weather') # takes in lat lon and returns a paginated embed of the NWS API response
async def get_weather(ctx: commands.Context, latitude: float, longitude: float, units: str):

    await ctx.interaction.response.defer()

    units = 'si' if units.lower() in ('celcius, c, si, standard, metric') else 'us'

    async def send_error_message(text: str):
        await ctx.interaction.followup.send(f'**Unexpected Exception:** {text}')

    try: 
        city, state, forecast = await api.get_usa_weather(lat=latitude, lon=longitude, unit_type=units)

    except ConnectionError as e:
        await send_error_message('API Could Not Connect')
        return 
    except gaierror as e:
        await send_error_message('DNS Could Not Be Resolved')
        return 
    except HTTPError as e:
        await send_error_message(str(e))
        return
    except KeyError as e:
        await send_error_message(str(e))
        return
    except Exception as e:
        await send_error_message("Unknown Error")
        raise e
    
    forecast = forecast[:6]
    pages: list[Embed] = list()
    colours: list[Colour] = [Colour.red(), Colour.orange(), Colour.yellow(), Colour.green(), Colour.blue(), Colour.purple()]

    def none_to_na(var) -> str:
        return 'N/A' if not var else var

    for data in forecast:
        embed = Embed(title=f"{data['name']} - {city}, {state}", 
            description=(
            f"**Temperature**: {none_to_na(data['temperature'])}{data['temperatureUnit']}\n"
            f"**Precipitation**: {none_to_na(data['probabilityOfPrecipitation']['value'])}%\n"
            f"**Wind Speed**: {none_to_na(data['windSpeed'])}\n"
            f"**Wind Direction**: {none_to_na(data['windDirection'])}\n"
            f"**Short Forecast**: {none_to_na(data['shortForecast'])}\n"
            f"**Detailed Forecast**: {none_to_na(data['detailedForecast'])}"
            ),
            color=colours[data['number'] -1]
        )
        pages.append(embed)

    await send_paginated_embed(ctx=ctx, pages=pages, timeout=60.0)

# Paginated Embed of NASA APOD Data  
@bot.hybrid_command(name='get_astronomy')
async def get_astronomy_by_date(ctx: commands.Context, start_day: Optional[int], start_month: Optional[int], start_year: Optional[int], end_day: Optional[int], end_month: Optional[int], end_year: Optional[int]):

    start_date = None
    end_date = None    
    current_date = dt.now(timezone.utc).replace(tzinfo=None)

    if start_day and start_month and start_year:
        try:
            start_date_obj = dt(start_year, start_month, start_day)

            if start_date_obj > current_date: start_date_obj = current_date
            else: start_date = start_date_obj.strftime("%Y-%m-%d")

            if (not end_day or not end_month or not end_year) and (start_date_obj + timedelta(days=90)) < current_date:
                end_date = (start_date_obj + timedelta(days=90)).strftime("%Y-%m-%d")
            else: end_date = current_date.strftime("%Y-%m-%d")
            
        except ValueError:
            start_date = None

    if end_day and end_month and end_year:
        try:
            end_date_obj = dt(end_year, end_month, end_day)
            if end_date_obj > current_date:
                end_date = end_date = current_date.strftime("%Y-%m-%d")
            elif end_date_obj.date() > start_date_obj.date():
                end_date = end_date_obj.strftime("%Y-%m-%d") if (start_date_obj - end_date_obj).days <= 365 else (start_date_obj + timedelta(days=365)).strftime("%Y-%m-%d")
            else:
                start_date = end_date_obj.strftime("%Y-%m-%d")
                end_date = start_date_obj.strftime("%Y-%m-%d") if (start_date_obj - end_date_obj).days <= 365 else (start_date_obj + timedelta(days=365)).strftime("%Y-%m-%d")
        except ValueError:
            end_date = None


    await ctx.interaction.response.defer()

    async def send_error_message(text: str):
        await ctx.interaction.followup.send(f'**Unexpected Exception:** {text}')

    try: 
        data = await api.get_astronomy_picture(start_date, end_date)
        urls, dates, titles, explanations = data
    except ConnectionError as e:
        await send_error_message('API Could Not Connect')
        return 
    except gaierror as e:
        await send_error_message('DNS Could Not Be Resolved')
        return 
    except HTTPError as e:
        await send_error_message(str(e))
        return
    except KeyError as e:
        await send_error_message(str(e))
        return
    except Exception as e:
        await send_error_message("Unknown Error")
        raise e

    pages: list[Embed] = list()

    for url, date, title, explanation in zip(urls, dates, titles, explanations):

        embed = Embed(
            title=f'[APOD] {title}: {date}',
            description=explanation,
            colour=Colour.random()
        )
        embed.set_image(url=url)
        pages.append(embed)
    
    timeout = float(30.0 * len(pages)) if len(pages) <= 10 else 300.0
    await send_paginated_embed(ctx, pages, timeout=timeout) if len(pages) > 1 else await ctx.interaction.followup.send(embed=pages[0])

# Start Bot
def main() -> None:
    bot.run(token=TOKEN)

if __name__ == '__main__': 
    main()
