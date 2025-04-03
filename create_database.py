import asyncpg as psy
import os
from typing import Final


async def create_database() -> None:
    DB_NAME: Final[str] = os.getenv('DB_NAME')
    DB_USER: Final[str] = os.getenv('DB_USER')
    DB_PASS: Final[str] = os.getenv('DB_PASS')
    DB_HOST: Final[str] = os.getenv('DB_HOST')
    DB_PORT: Final[str] = os.getenv('DB_PORT')
    conn: psy.Connection = await psy.connect(
        database=DB_NAME, user=DB_USER,
        password=DB_PASS, host=DB_HOST,
        port=DB_PORT
    )
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."Guild"
        (
            "Id" bigint NOT NULL,
            "Name" character varying(255) COLLATE pg_catalog."default"
                NOT NULL,
            "Description" character varying(255) COLLATE pg_catalog."default",
            "CreateDateUTC" timestamp(0) without time zone NOT NULL,
            "UpdateDateUTC" timestamp(0) without time zone,
            CONSTRAINT "Guild_pkey" PRIMARY KEY ("Id")
        )
        """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."ChannelType"
        (
            "Id" smallint NOT NULL,
            "Name" character varying(255) COLLATE pg_catalog."default"
                NOT NULL,
            "Description" character varying(255) COLLATE pg_catalog."default"
                NOT NULL,
            CONSTRAINT "ChannelType_pkey" PRIMARY KEY ("Id")
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."Channel"
        (
            "Id" bigint NOT NULL,
            "ChannelTypeId" smallint NOT NULL,
            "Name" character varying(255) COLLATE pg_catalog."default"
                NOT NULL,
            "GuildId" bigint,
            "CategoryName" character varying(255) COLLATE pg_catalog."default",
            "CreateDateUTC" timestamp(0) without time zone NOT NULL,
            "UpdateDateUTC" timestamp(0) without time zone,
            "NSFW" boolean,
            CONSTRAINT "Channel_pkey" PRIMARY KEY ("Id"),
            CONSTRAINT "ChannelType" FOREIGN KEY ("ChannelTypeId")
                REFERENCES public."ChannelType" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
                NOT VALID,
            CONSTRAINT guild FOREIGN KEY ("GuildId")
                REFERENCES public."Guild" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
                NOT VALID
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."User"
        (
            "Id" bigint NOT NULL,
            "Username" character varying(255) COLLATE pg_catalog."default"
                NOT NULL,
            "CreateDateUTC" timestamp(0) without time zone NOT NULL,
            "UpdateDateUTC" timestamp(0) without time zone,
            CONSTRAINT "User_pkey" PRIMARY KEY ("Id")
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."Message"
        (
            "Id" bigint NOT NULL,
            "UserId" bigint NOT NULL,
            "GuildId" bigint,
            "Content" text COLLATE pg_catalog."default" NOT NULL,
            "ChannelId" bigint NOT NULL,
            "CreateDateUTC" timestamp(6) without time zone NOT NULL,
            "UpdateDateUTC" timestamp(6) without time zone,
            "DeleteDateUTC" timestamp(6) without time zone,
            "Deleted" integer NOT NULL DEFAULT 0,
            "Edited" integer NOT NULL DEFAULT 0,
            CONSTRAINT "Message_pkey" PRIMARY KEY ("Id"),
            CONSTRAINT "Channel" FOREIGN KEY ("ChannelId")
                REFERENCES public."Channel" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
                NOT VALID,
            CONSTRAINT "Guild_Relationship" FOREIGN KEY ("GuildId")
                REFERENCES public."Guild" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION,
            CONSTRAINT "User_Relationship" FOREIGN KEY ("UserId")
                REFERENCES public."User" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."Attachments"
        (
            "Id" bigint NOT NULL,
            "Filename" character varying(255) COLLATE pg_catalog."default"
                NOT NULL,
            "ContentType" character varying(255) COLLATE pg_catalog."default",
            "URL" character varying(255) COLLATE pg_catalog."default" NOT NULL,
            "MessageId" bigint NOT NULL,
            "CreateDateUTC" timestamp(0) without time zone NOT NULL,
            "UpdateDateUTC" timestamp(0) without time zone,
            "DeleteDateUTC" timestamp(6) without time zone,
            "Deleted" integer NOT NULL DEFAULT 0,
            CONSTRAINT "Attachments_pkey" PRIMARY KEY ("Id"),
            CONSTRAINT "Message" FOREIGN KEY ("MessageId")
                REFERENCES public."Message" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."MessageEditHistory"
        (
            "Id" integer NOT NULL GENERATED ALWAYS AS IDENTITY
                ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
            "MessageId" bigint NOT NULL,
            "BeforeContent" text COLLATE pg_catalog."default" NOT NULL,
            "AfterContent" text COLLATE pg_catalog."default" NOT NULL,
            "CreateDateUTC" timestamp(0) without time zone NOT NULL,
            CONSTRAINT "MessageUpdateHistory_pkey" PRIMARY KEY ("Id"),
            CONSTRAINT message FOREIGN KEY ("MessageId")
                REFERENCES public."Message" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
                NOT VALID
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."Reactions"
        (
            "Id" integer NOT NULL GENERATED ALWAYS AS IDENTITY
                ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
            "MessageId" bigint NOT NULL,
            "UserId" bigint NOT NULL,
            "Emoji" character varying(255) COLLATE pg_catalog."default"
                NOT NULL,
            "SelfReact" smallint NOT NULL,
            "CreateDateUTC" timestamp(0) without time zone NOT NULL,
            "DeleteDateUTC" timestamp(0) without time zone,
            "Deleted" smallint NOT NULL DEFAULT 0,
            CONSTRAINT "Reactions_pkey" PRIMARY KEY ("Id"),
            CONSTRAINT message FOREIGN KEY ("MessageId")
                REFERENCES public."Message" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION,
            CONSTRAINT "user" FOREIGN KEY ("UserId")
                REFERENCES public."User" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public."UserMentions"
        (
            "Id" integer NOT NULL GENERATED ALWAYS AS IDENTITY
                ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
            "MessageId" bigint NOT NULL,
            "AuthorId" bigint NOT NULL,
            "RecipientId" bigint NOT NULL,
            "CreateDateUTC" timestamp(0) without time zone NOT NULL,
            "UpdateDateUTC" timestamp(0) without time zone,
            "DeleteDateUTC" timestamp(0) without time zone,
            "Deleted" integer NOT NULL DEFAULT 0,
            CONSTRAINT "UserMentions_pkey" PRIMARY KEY ("Id"),
            CONSTRAINT author FOREIGN KEY ("AuthorId")
                REFERENCES public."User" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION,
            CONSTRAINT message FOREIGN KEY ("MessageId")
                REFERENCES public."Message" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION,
            CONSTRAINT recipient FOREIGN KEY ("RecipientId")
                REFERENCES public."User" ("Id") MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
        )
    """)
