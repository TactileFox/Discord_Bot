import os
import logging
import asyncpg as psy
import matplotlib.pyplot as plt
from asyncpg import Connection
from io import BytesIO
from typing import Final
from discord import Message, Guild, User, Attachment, File, Reaction
from datetime import datetime, timezone
import queries as query

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('psql.log', encoding='utf-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.WARNING)
logger.addHandler(stream_handler)


async def execute(conn: Connection, query: str, *args):
    try:
        await conn.execute(query, *args)
    except psy.exceptions:
        logger.exception(f'Exception occured with args: {args}')
    except Exception:
        logger.exception(f'Unknwon exception occured with args: {args}')
        raise
    logger.info(f'Executed query with {args}')


# done
async def log_user(user: User) -> None:
    conn = await get_db_connection()
    row = await conn.fetchrow(query.get_user(), user.id)
    if row is None:
        await execute(
            conn, query.insert_user(), user.id, user.name, get_date()
        )
        logger.info('inserted user')
    elif (row['Username'] != user.name):
        await execute(
            conn, query.update_user(), user.name, get_date(), user.id
        )
        logger.info('updated user')
    await conn.close()


async def create_message_log(message: Message) -> None:

    await log_user(message.author)
    await log_guild(message.guild)
    await log_channel(message)
    await log_message(message)
    conn = await get_db_connection()
    for attachment in message.attachments:
        await execute(
            conn, query.insert_attachment(),
            attachment.id, attachment.filename,
            attachment.content_type, attachment.url,
            message.id, get_date()
        )
        logger.info(f'Attachment Inserted: {attachment.filename}')
    await conn.close()
    for user in message.mentions:
        await log_user(user)
        await log_user_mention(
            user, message.id, message.author.id
        )
    logger.info(f'Message Logged: {message.id}')


# done
async def log_guild(guild: Guild) -> None:
    conn = await get_db_connection()
    row = await conn.fetchrow(query.get_guild(), guild.id)
    if not row:
        await execute(
            conn, query.insert_guild(),
            guild.id, guild.name,
            guild.description, get_date()
        )
        logger.info(f'Guild Inserted: {guild.name}')
    elif (
        row['Name'] != guild.name
        or row['Description'] != guild.description
    ):
        await execute(
            conn, query.update_guild(),
            guild.name, guild.description,
            get_date(), guild.id
        )
        logger.info(f'Guild Updated: {guild.name}')
    await conn.close()


# Done
async def log_channel(message: Message) -> None:
    conn = await get_db_connection()
    channel = message.channel
    channel_name = create_channel_name(message)
    row = await conn.fetchrow(query.get_channel(), channel.id)
    if not row:
        await execute(
            conn, query.insert_channel(), channel.id,
            channel.type.value, channel_name,
            channel.guild.id, channel.category.name,
            get_date(), channel.nsfw
        )
        logger.info(f'Channel Inserted: {channel.name} {channel.id}')
    elif (
        row['Name'] != channel_name
        or row['CategoryName'] != channel.category.name
        or row['NSFW'] != channel.nsfw
    ):
        await execute(
            conn, query.update_channel(), channel_name,
            channel.category.name, get_date(),
            channel.nsfw, channel.id
        )
        logger.info(f'Channel Updated: {channel.name} {channel.id}')
    await conn.close()


# Done
async def log_message(message: Message) -> None:
    conn = await get_db_connection()
    await execute(
        conn, query.insert_message(),
        message.id, message.author.id,
        message.guild.id, message.content,
        message.channel.id, get_date()
    )
    await conn.close()
    logger.info(
        f'Message Inserted: {message.id} {message.content[:20]}...'
    )


# Done
async def log_attachment(attachment: Attachment, message_id) -> None:
    conn = await get_db_connection()
    row = await conn.fetchrow(query.get_attachment(), attachment.id)
    if not row:
        await execute(
            conn, query.insert_attachment(),
            attachment.id, attachment.filename,
            attachment.content_type, attachment.url,
            message_id, get_date()
        )
        logger.info(f'Attachment Inserted: {attachment.filename[:20]}')
    elif (row['URL'] != attachment.url):
        await execute(
            conn, query.update_attachment(),
            attachment.url, get_date(), attachment.id
        )
        logger.info(f'Attachment Updated: {attachment.filename[:20]}')
    await conn.close()


# Done
async def log_user_mention(
        user: User, message_id: int, author_id: int
) -> None:

    # TODO Don't log bot mentions
    # if message_sender_id == bot.id: return
    conn = await get_db_connection()
    row = await conn.fetchrow(
        query.get_user_mention(), message_id, user.id
    )
    if not row:
        await execute(
            conn, query.insert_user_mention(),
            message_id, author_id,
            user.id, get_date()
        )
        logger.info(f'User Mention Inserted: {user.name} {message_id}')
    await conn.close()


# Done
async def get_message_counts(guild: Guild) -> File:

    conn = await get_db_connection()
    data = await conn.fetch(query.message_counts(), guild.id)
    await conn.close()
    if data is None:
        logger.error(f'No Messages to Graph: {guild.name} {guild.id}')
        raise ValueError('No Records')

    # Create matplotlib graph
    fig, ax = plt.subplots()
    ax.bar(
        [point['Username'] for point in data],
        [point['count'] for point in data],
        color='blue'
    )
    ax.set_xlabel('User')
    ax.set_ylabel('Message Count')
    ax.set_title('Message Count by User')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    file = File(buf, 'message_count_graph.png')
    plt.close()
    buf.close()
    logger.info('Graph Returned')
    return file


# Done, TODO: Fix comments
async def log_message_edit(before: Message, after: Message) -> None:

    conn = await get_db_connection()
    await execute(
        conn, query.update_message(), after.content,
        get_date(), after.id
    )
    for attachment in before.attachments:
        if attachment not in after.attachments:
            await execute(
                conn, query.update_attachment(deletion=True),
                attachment.url, get_date(), attachment.id
            )
            logger.info(
                f'Deleted Attachment: {attachment.filename[:20]} '
                f'{attachment.id}'
            )
    for attachment in after.attachments:
        if attachment not in before.attachments:
            await execute(
                conn, query.insert_attachment(),
                attachment.id, attachment.filename,
                attachment.content_type, attachment.url,
                after.id, get_date()
            )
    for mention in before.mentions:
        if mention not in after.mentions:
            await execute(
                conn, query.delete_user_mention(),
                get_date(), after.id, mention.id
            )
            logger.info(
                f'Deleted User Mention: {mention.name} {mention.id}'
            )
    for mention in after.mentions:
        if mention not in before.mentions:
            await execute(
                conn, query.insert_user_mention(),
                after.id, after.author.id,
                mention.id, get_date()
            )
    await execute(
        conn, query.insert_message_edit(),
        after.id, before.content,
        after.content, get_date()
    )
    await conn.close()


# Done
async def log_message_deletion(message: Message) -> None:

    conn = await get_db_connection()
    await execute(
        conn, query.update_message(deletion=True),
        get_date(), message.id
    )
    for mention in message.mentions:
        await execute(
            conn, query.delete_user_mention(),
            get_date(), message.id, mention.id
        )
    for attachment in message.attachments:
        await execute(
            conn, query.update_attachment(deletion=True),
            attachment.url, get_date(), attachment.id
        )
    logger.info(
        f'Deleted Message: {message.author.name} {message.content[:20]}...'
        f' {message.id}')
    await conn.close()


# Done
async def log_message_reaction(reaction: Reaction, user: User) -> None:

    conn = await get_db_connection()
    await log_user(user)
    self_react = int(reaction.message.author.id == user.id)
    emoji_name = get_emoji_name(reaction)
    await execute(
        conn, query.insert_reaction(),
        reaction.message.id, user.id,
        emoji_name, self_react, get_date()
    )
    logger.info(f'Inserted Reaction: {emoji_name} {reaction.message.id}')
    await conn.close()


# Done
async def log_reaction_deletion(reaction: Reaction, user: User) -> None:

    conn = await get_db_connection()
    emoji_name = get_emoji_name(reaction)
    await execute(
        conn, query.delete_reaction(),
        get_date(), reaction.message.id,
        emoji_name, user.id
    )
    logger.info(
        f'Deleted Reaction: {emoji_name} {reaction.message.id} {user.name}'
    )
    await conn.close()


# Done
async def log_reaction_clear(message: Message) -> None:

    conn = await get_db_connection()
    await execute(
        conn, query.delete_reaction(all=True),
        get_date(), message.id
    )
    logger.info(f'Deleted Reactions: {message.id}')
    await conn.close()


# Done
async def log_reaction_clear_emoji(
        reaction: Reaction, message: Message
) -> None:

    emoji_name = get_emoji_name(reaction)
    conn = await get_db_connection()
    await execute(
        conn, query.delete_reaction(emoji=True),
        get_date(), message.id, emoji_name
    )
    logger.info(f'Deleted Reactions: {emoji_name} {reaction.message.id}')
    await conn.close()


# Done
async def get_last_updated_message(channel_id) -> tuple:

    conn = await get_db_connection()
    row = await conn.fetchrow(query.snipe(), channel_id)
    await conn.close()
    if not row:
        logger.error('No Edited/Deleted Messages to Return')
        raise ValueError('No Records')
    else:
        return (
            row['BeforeText'], row['CurrentText'],
            row['Username'], row['Action'], row['URL']
        )


# Helpers
def create_channel_name(message: Message):
    if message.channel.type in ('private', 'group'):
        return f'DM with {message.author}'
    else:
        return message.channel.name


def get_date():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_emoji_name(reaction: Reaction) -> str:
    if isinstance(reaction.emoji, str):
        emoji_name = reaction.emoji
    else:
        emoji_name = reaction.emoji.name
    return emoji_name


async def get_db_connection() -> Connection:

    DB_NAME: Final[str] = os.getenv('DB_NAME')
    DB_USER: Final[str] = os.getenv('DB_USER')
    DB_PASS: Final[str] = os.getenv('DB_PASS')
    DB_HOST: Final[str] = os.getenv('DB_HOST')
    DB_PORT: Final[str] = os.getenv('DB_PORT')
    logger.debug('Connection Retrieved')
    conn = await psy.connect(
        database=DB_NAME, user=DB_USER,
        password=DB_PASS, host=DB_HOST,
        port=DB_PORT
    )
    return conn
