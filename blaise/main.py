import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

from database import Database

load_dotenv()

TOKEN = os.getenv("DISK_TOKEN_TEST")

GUILD_ID = 1462882277125259450

intents = discord.Intents.all()

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

        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        print("✅ Slash commands synced instantly.")


bot = BlaiseBot()


@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    bot.add_view(ApplyButton(bot))
    bot.add_view(StaffButtons())


async def main():
    async with bot:
        await bot.start(TOKEN)


asyncio.run(main())