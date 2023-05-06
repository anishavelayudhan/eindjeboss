import discord
import logging as lg
from imdb import Cinemagoer
from discord import app_commands
from discord.ext import commands

ia = Cinemagoer()


class IMDB(commands.Cog):

    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="imdb",
                          description="Search for a movie/series on IMDb.")
    async def imdb(self, intr: discord.Interaction, query: str):
        movies = ia.search_movie(query)
        if not movies:
            await intr.response.send_message('No results found for "' +
                                             query + '" on IMDB.',
                                             ephemeral=True)
            return
        movie_id = movies[0].movieID
        await intr.response.send_message(
            "https://www.imdb.com/title/tt{id}/".format(id=movie_id))
        lg.info("Sent movie to %s", intr.user.name)


async def setup(client: commands.Bot):
    await client.add_cog(IMDB(client))
