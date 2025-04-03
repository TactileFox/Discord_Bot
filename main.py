import os
import asyncio
import logging
from datetime import datetime as dt, timedelta, timezone
from typing import Final, Optional
from dotenv import load_dotenv
from discord import Intents, Message, Reaction, User, Embed, Colour
from discord.ext import commands
from requests.exceptions import HTTPError, ConnectionError
from socket import gaierror
import api_requests as api
import psql_connection as psql

# Load Bot Token
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Setup the bot object with all default and priveleged intents
intents: Intents = Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Setup Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('main.log', encoding='utf-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.WARNING)
logger.addHandler(stream_handler)


# Event Methods
@bot.event
async def on_ready() -> None:
    await bot.tree.sync()  # Sync Commands
    print(f'{bot.user} is now running!')
    logger.info(f'{bot.user} is now running!')


# Incoming Messages
@bot.event
async def on_message(message: Message) -> None:

    if message.author == bot.user:
        return

    await psql.create_message_log(message)

    logger.info(
        f'[{message.channel.name}] {message.author.name}: '
        f'"{message.content[:50]}"'
        )


# Messages must be in the internal cache to trigger this
@bot.event
async def on_message_edit(before: Message, after: Message) -> None:

    if before.author == bot.user:
        return

    await psql.log_message_edit(before, after)

    logger.info(
        f'Message Edit: [{after.channel.name}] {after.author.name}: '
        f'"{after.content[:40]}"'
        )


# Messages must be in the internal cache to trigger this
@bot.event
async def on_message_delete(message: Message) -> None:

    if message.author == bot.user:
        return

    await psql.log_message_deletion(message)

    logger.info(
        f'Message Delete: [{message.channel.name}] {message.author.name}: '
        f'"{message.content[:40]}"'
        )


# Messages must be in the internal cache to trigger this
@bot.event
async def on_bulk_message_delete(messages: list[Message]) -> None:

    for message in messages:
        if message.author == bot.user:
            continue
        await psql.log_message_deletion(message)
        logger.info(
            f'Bulk Delete: [{message.channel.name}] {message.author.name}: '
            f'"{message.content[:40]}"'
            )


# Messages but be in the internal cache to trigger this
@bot.event
async def on_reaction_add(reaction: Reaction, user: User) -> None:

    if user == bot.user or reaction.message.author == bot.user:
        return

    await psql.log_message_reaction(reaction, user)

    logger.info(
        f'Reaction Add: [{reaction.message.channel.name}] {user.name}: '
        f'"{str(reaction.emoji)}"'
        )


# Messages but be in the internal cache to trigger this
@bot.event
async def on_reaction_remove(reaction: Reaction, user: User) -> None:

    if user == bot.user or reaction.message.author == bot.user:
        return

    await psql.log_reaction_deletion(reaction, user)

    logger.info(
        f'Reaction Remove: [{reaction.message.channel.name}] {user.name}: '
        f'"{str(reaction.emoji)}"'
        )


# Messages but be in the internal cache to trigger this
@bot.event
async def on_reaction_clear(
    message: Message,
    reactions: list[Reaction]
) -> None:

    if message.author == bot.user:
        return

    await psql.log_reaction_clear(message)

    logger.info(
        f'Reaction Clear: [{message.channel.name}] {message.author.name}: '
        f'"{message.content[:40]}"'
    )


@bot.event
async def on_reaction_clear_emoji(reaction: Reaction) -> None:

    if reaction.message.author == bot.user:
        return

    await psql.log_reaction_clear_emoji(reaction, reaction.message)

    logger.info(
        f'Reaction Clear: [{reaction.message.channel.name}] '
        f'{reaction.message.author.name}: "{str(reaction.emoji)}"'
    )


# Commands
@bot.hybrid_command(name='get_message_count_by_user')
async def message_count_by_user(ctx: commands.Context) -> None:

    try:
        file = await psql.get_message_counts(ctx.guild)
    except ValueError:
        await ctx.send(content='No Messages Have Been Sent')
        return
    await ctx.send(
        content='Here is your graph:',
        file=file
    )
    logger.info(
        f'Message Count By User Graph Sent. Author: {ctx.author},'
        f'Channel: {ctx.channel.name}, Guild: {ctx.guild.name}'
        )


@bot.hybrid_command(name="snipe")
async def snipe(ctx: commands.Context):

    try:
        result = await psql.get_last_updated_message(ctx.channel.id)
        before, after, username, action, url = result
    except ValueError:
        await ctx.send("No Deleted/Edited Messages in Channel", ephemeral=True)
        logger.debug('No Deleted/Edited Messages in Channel')

    ending_periods_after = '...' if len(after) > 1000 else ''
    ending_periods_before = '...' if before and len(before) > 1000 else ''

    if action == 'Deleted':
        embed = Embed(
            title=f'Last deleted message: {username}',
            description=f'{after[:1000]}{ending_periods_after}'
        )
        if url is not None:
            embed.set_image(url=url)
        await ctx.send(embed=embed)

    elif action == 'Edited':
        embed = Embed(
            title=f'Last edited message: {username}',
            description=(
                f'**After:**\n{after[:1000]}{ending_periods_after}\n\n'
                f'**Before:** \n{before[:1000]}{ending_periods_before}'
            )
        )
        if url is not None:
            embed.set_image(url=url)
        await ctx.send(embed=embed)

    logger.info(
        f'Snipe Sent. Author: {ctx.author}, Channel: {ctx.channel.name},'
        f'Guild: {ctx.guild.name}'
        )


# Requires the interaction to be defered beforehand
async def send_paginated_embed(ctx: commands.Context, pages: list[Embed],
                               timeout: float) -> None:

    if not pages:
        await ctx.interaction.followup.send('No pages to display because Foxy'
                                            'is a lil silly :3')
        logger.debug("No pages to display")
        return

    # Create response
    current_page = 0
    try:
        message = await ctx.interaction.followup.send(
            embed=pages[current_page])
    except Exception as e:
        logger.exception(f'Error sending paginated embed {str(e)})')
    else:
        logger.info('Paginated Embed Sent')

    # Add "buttons"
    await message.add_reaction('⬅️')
    await message.add_reaction('➡️')
    await message.add_reaction('⏹️')

    def check(reaction: Reaction, user: User):
        test = True
        if test:
            return reaction.message.id == message.id
        else:
            return user == ctx.author and reaction.message.id == message.id

    while True:

        try:
            reaction: Reaction
            user: User
            reaction, user = await bot.wait_for(
                'reaction_add', check=check, timeout=timeout)
            await reaction.remove(user)

            logger.info(
                f'Reaction Added: {str(reaction.emoji)} by {user.name}')

            if reaction.emoji == '⬅️' and current_page > 0:
                current_page -= 1
                try:
                    await message.edit(embed=pages[current_page])
                except Exception:
                    logger.exception('Error in paginated backwards')
            elif reaction.emoji == '➡️' and current_page < len(pages) - 1:
                current_page += 1
                try:
                    await message.edit(embed=pages[current_page])
                except Exception:
                    logger.exception('Error in paginated forwards')
            elif reaction.emoji == '⏹️':
                try:
                    await message.clear_reaction('⬅️')
                    await message.clear_reaction('➡️')
                    await message.clear_reaction('⏹️')
                except Exception:
                    logger.exception('Error removing paginated recations')
                break
            else:
                continue
        # Raised by timeout parameter in wait_for
        except asyncio.TimeoutError:
            logging.debug('Paginated embed timed out')
            await message.clear_reaction('⬅️')
            await message.clear_reaction('➡️')
            await message.clear_reaction('⏹️')
            break


# Paginated Embed of NWS Weather Data
@bot.hybrid_command(name='get_weather')
async def get_weather(
    ctx: commands.Context, latitude: float,
    longitude: float, units: str
) -> None:

    await ctx.interaction.response.defer()

    si_units = ('celcius, c, si, standard, metric')
    units = 'si' if units.lower() in si_units else 'us'

    async def send_error_message(text: str):
        await ctx.interaction.followup.send(
            f'**Unexpected Exception:** {text}')

        logger.info(f'Weather Exception Sent: {text}')

    try:
        city, state, forecast = await api.get_usa_weather(
            lat=latitude, lon=longitude, unit_type=units)

    except ConnectionError:
        await send_error_message('API Could Not Connect')
        return
    except gaierror:
        await send_error_message('DNS Could Not Be Resolved')
        return
    except HTTPError as e:
        await send_error_message(str(e))
        return
    except KeyError as e:
        await send_error_message(str(e))
        return
    except Exception as e:
        await send_error_message('Unknown Error')
        raise e

    forecast = forecast[:6]
    pages: list[Embed] = list()
    colours: list[Colour] = [Colour.red(), Colour.orange(), Colour.yellow(),
                             Colour.green(), Colour.blue(), Colour.purple()]

    def none_to_na(var) -> str:
        return 'N/A' if not var else var

    for data in forecast:
        embed = Embed(
            title=f"{data['name']} - {city}, {state}",
            description=(
                f"**Temperature**: {none_to_na(data['temperature'])}"
                f"{data['temperatureUnit']}\n"
                f"**Precipitation**: "
                f"{none_to_na(data['probabilityOfPrecipitation']['value'])}%\n"
                f"**Wind Speed**: {none_to_na(data['windSpeed'])}\n"
                f"**Wind Direction**: {none_to_na(data['windDirection'])}\n"
                f"**Short Forecast**: {none_to_na(data['shortForecast'])}\n"
                f"**Detailed Forecast**: "
                f"{none_to_na(data['detailedForecast'])}"
            ),
            color=colours[data['number'] - 1]
        )
        pages.append(embed)

    await send_paginated_embed(ctx=ctx, pages=pages, timeout=60.0)


# Paginated Embed of NASA APOD Data
@bot.hybrid_command(name='get_astronomy')
async def get_astronomy_by_date(
    ctx: commands.Context, start_day: Optional[int],
    start_month: Optional[int], start_year: Optional[int],
    end_day: Optional[int], end_month: Optional[int], end_year: Optional[int]
) -> None:

    start_date = None
    end_date = None
    current_date = dt.now(timezone.utc).replace(tzinfo=None)

    # Invalid dates are set to None.
    # End date is always greater than or equal to the start date.
    # Dates must be before or equal to the current date.
    # End date can be no greater than 365 days after the start date.
    # If no end date is given, end date is 90 days after the start date.
    if start_day and start_month and start_year:
        try:
            start_date_obj = dt(start_year, start_month, start_day)

            if start_date_obj > current_date:
                start_date_obj = current_date
            else:
                start_date = start_date_obj.strftime("%Y-%m-%d")

            end_date_provided = end_day and end_month and end_year
            if (
                end_date_provided is None
                and (start_date_obj + timedelta(days=90)) < current_date
            ):
                end_date_obj = (start_date_obj + timedelta(days=90))
                end_date = end_date_obj.strftime("%Y-%m-%d")
            else:
                end_date = current_date.strftime("%Y-%m-%d")

        except ValueError or OverflowError:
            logger.exception(
                f'Invalid Date: {start_day} {start_month} {start_year}'
            )
            start_date = None

    if end_day and end_month and end_year:
        try:
            end_date_obj = dt(end_year, end_month, end_day)
            if end_date_obj > current_date:
                end_date = current_date.strftime("%Y-%m-%d")
            elif end_date_obj.date() > start_date_obj.date():
                if (start_date_obj - end_date_obj).days <= 365:
                    end_date = end_date_obj.strftime("%Y-%m-%d")
                else:
                    end_date_obj = (start_date_obj + timedelta(days=365))
                    end_date = end_date_obj.strftime("%Y-%m-%d")
            else:
                start_date = end_date_obj.strftime("%Y-%m-%d")
                if (start_date_obj - end_date_obj).days <= 365:
                    end_date = start_date_obj.strftime("%Y-%m-%d")
                else:
                    end_date_obj = (start_date_obj + timedelta(days=365))
                    end_date = end_date_obj.strftime("%Y-%m-%d")
        except ValueError or OverflowError:
            logger.exception(f'Invalid Date: {end_day} {end_month} {end_year}')
            end_date = None

    await ctx.interaction.response.defer()

    async def send_error_message(text: str):
        await ctx.interaction.followup.send(
            f'**Unexpected Exception:** {text}'
        )
        logger.info(f'Astronomy Exception Sent: {text}')

    try:
        result = await api.get_astronomy_picture(start_date, end_date)
        urls, dates, titles, explanations = result
    except ConnectionError:
        await send_error_message('API Could Not Connect')
        return
    except gaierror:
        await send_error_message('DNS Could Not Be Resolved')
        return
    except HTTPError or KeyError as e:
        await send_error_message(str(e))
        return
    except Exception as e:
        await send_error_message("Unknown Error")
        raise e

    pages: list[Embed] = list()

    iterable = zip(urls, dates, titles, explanations)
    for url, date, title, explanation in iterable:

        embed = Embed(
            title=f'[APOD] {title}: {date}',
            description=explanation,
            colour=Colour.random()
        )
        embed.set_image(url=url)
        pages.append(embed)

    timeout = float(30.0 * len(pages)) if len(pages) <= 10 else 300.0
    if len(pages) > 1:
        await send_paginated_embed(ctx, pages, timeout=timeout)
    else:
        await ctx.interaction.followup.send(embed=pages[0])


async def verify_db_exists() -> bool:
    if await psql.verify_DB_exists() is True:
        return True
    else:
        logger.critical(
            'Missing tables preventing the bot from running.'
            ' Please see psql.log for more information.'
        )
        return False


# Start Bot
def main() -> None:
    bot.run(token=TOKEN)
    logger.info('Bot Running')


if __name__ == '__main__':
    if asyncio.run(verify_db_exists()) is True:
        main()
