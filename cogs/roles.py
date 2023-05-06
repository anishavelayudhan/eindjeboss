import discord
import logging as lg
from discord.ext import commands
from discord import app_commands

FOCUS_DESC = "Limits your view to the conversation channels"


class Roles(commands.Cog):

    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="focus",
                          description=FOCUS_DESC)
    async def focus(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name="Focus")

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                "Focus mode off. Use /focus again to turn it on.",
                ephemeral=True)
            lg.info(f"Removed focus role for {interaction.user.name}")
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            "Focus mode on. Use /focus again to turn it off.",
            ephemeral=True)
        lg.info(f"Added focus role for {interaction.user.name}")


async def setup(client: commands.Bot):
    await client.add_cog(Roles(client))
