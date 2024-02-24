import logging as lg
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

MONTH_CHOICES = [
    app_commands.Choice(name=month, value=idx + 1) for idx, month in enumerate(MONTHS)
]


class Users(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.users = self.bot.dbmanager.get_collection("users")

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="birthday", description="Enter/change your birthday.")
    @app_commands.choices(month=MONTH_CHOICES)
    async def birthday(self, intr: discord.Interaction, month: int, day: int, year: int = 0):
        yr = year
        if not yr:
            yr = 2000
        try:
            datetime(year=yr, month=month, day=day)
            await self.users.update_one(
                {"_id": intr.user.id},
                [{"$set":
                 {"birthday": self.get_bday_data(month, day, year)}}],
                 upsert=True
            )
            await intr.response.send_message("Birthday saved!", ephemeral=True)
            lg.info("Saved birthday for %s", intr.user.name)
        except:
            await intr.response.send_message("Date invalid. Please try again", ephemeral=True)

    def get_bday_data(self, month: int, day: int, year: int):
        data = {"month": month, "day": day}
        if year:
            data["year"] = year
        return data


async def setup(client: Eindjeboss):
    await client.add_cog(Users(client))
