import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

from database import Database

load_dotenv(".env")

TOKEN = os.getenv("DISK_TOKEN_TEST")

GUILD_ID = 1462882277125259450

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

class BlaiseBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

        self.db = Database()

    async def setup_hook(self):

        await self.db.connect()

        # load cogs
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")



        # instant slash command sync
        guild = discord.Object(id=GUILD_ID)

        await self.tree.sync(guild=guild)

        print("✅ Slash commands synced instantly.")


bot = BlaiseBot()


@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    await bot.process_commands(message)

async def main():

    while True:
        try:
            async with bot:
                await bot.start(TOKEN)
        except Exception as e:
            print("Bot crashed:", e)
            await asyncio.sleep(5)


asyncio.run(main())