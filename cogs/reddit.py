import asyncio
import json
import logging as lg
import os
import random
import re
import textwrap
from typing import List

import asyncpraw
import discord
from aiocron import crontab
from asyncpraw.models import Submission, Subreddit
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss
from util.util import get_file
from util.vars.eind_vars import (
    CAR_SUBS,
    CAT_SUBS,
    CHANNEL_IGNORE_LIST,
    DOG_SUBS,
    REDDIT_USER_AGENT,
)
from util.vars.periodics import REDDIT_EINDHOVEN_DT

# random commands
SUBREDDIT_REGEX = "(?<!reddit.com)/r/[a-zA-Z0-9]{3,}"
I_REDDIT_REGEX = (
    r"https://(v|www).redd(it)*.(com|it)/(gallery/)*[a-zA-Z0-9]*(.jpeg|.png)*"
)
I_IMGUR_REGEX = r"https://(i|www).imgur.com/(a/)*[\S]*.(png|jpg)*"
CATS = "cats"
DOGS = "rarepuppers"
CARS = "carporn"
FOOD = "foodporn"
RANDOM_STR = "Sends a random %s picture off of reddit."

# eindhoven subreddit feed
EINDHOVEN = "eindhoven"
BASE_URL = "https://discord.com/api/webhooks/"
EINDJE_SUBREDDIT_FILE = "eindjesubreddit.json"
AUTHOR_NAME = "New post on /r/eindhoven"
AUTHOR_URL = "https://www.reddit.com/r/eindhoven"
EINDJE_ICON_URL = "https://i.imgur.com/ACCxKOr.png"

try:
    with open(get_file(EINDJE_SUBREDDIT_FILE)) as db_file:
        db = json.load(db_file)
except FileNotFoundError:
    db = []

reddit = asyncpraw.Reddit(
    client_id=os.getenv("REDDIT_ID"),
    client_secret=os.getenv("REDDIT_SECRET"),
    user_agent=REDDIT_USER_AGENT,
)


class Reddit(commands.GroupCog, group_name="random"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info("[%s] Cog is ready", __name__)
        crontab(REDDIT_EINDHOVEN_DT, self.monitor_feed, start=True)

    async def monitor_feed(self):
        if not await self.bot.get_setting("monitor_reddit"):
            return
        guild_id = await self.bot.get_setting("guild_id")
        reddit_channel_id = await self.bot.get_setting("reddit_channel_id")
        guild = await self.bot.fetch_guild(guild_id)
        channel = await guild.fetch_channel(reddit_channel_id)

        posts: List[Submission] = []

        e_subreddit: Subreddit = await reddit.subreddit(EINDHOVEN)

        async for submission in e_subreddit.new(limit=20):
            posts.append(submission)

        for post in posts:
            p_id = post.id
            if p_id not in db:
                lg.info("Found new reddit post: %s", p_id)

                await post.load()
                p_perm = f"https://old.reddit.com{post.permalink}"
                p_title = post.title
                p_author = post.author
                p_thumb = post.thumbnail
                p_self = post.is_self
                p_vid = post.is_video

                if p_self:
                    emb = mk_embed(p_title, p_perm, post.selftext)
                    emb.set_footer(text=f"Posted by {p_author}")
                elif p_vid:
                    emb = mk_embed(p_title, p_perm)
                    emb.set_image(
                        url=p_thumb if p_thumb.startswith("https://") else None
                    )
                    emb.set_footer(text=f"Video posted by {p_author}")
                else:
                    p_url = post.url

                    if not p_url.startswith("https://"):
                        if p_url.startswith("/r/"):
                            p_url = "https://www.reddit.com%s" % p_url
                        else:
                            p_url = None

                    emb = mk_embed(p_title, p_perm)
                    emb.set_image(url=p_url)
                    emb.set_footer(text=f"Image posted by {p_author}")

                await channel.send(embed=emb)

                db.append(p_id)

                with open(get_file(EINDJE_SUBREDDIT_FILE), "w") as outfile:
                    json.dump(db[-100:], outfile)

                await asyncio.sleep(3)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.channel.name in CHANNEL_IGNORE_LIST:
            return

        message_content = message.content.lower()
        matches = set(re.findall(SUBREDDIT_REGEX, message_content))

        if matches:
            await self.handle_reddit_matches(matches, message)

    @app_commands.command(name="cat", description=RANDOM_STR % "cat")
    async def send_random_cat(self, intr: discord.Interaction):
        await intr.response.defer()
        post_info = await self.get_red_post(CAT_SUBS, 50)
        await intr.followup.send(post_info)

    @app_commands.command(name="dog", description=RANDOM_STR % "dog")
    async def send_random_dog(self, intr: discord.Interaction):
        await intr.response.defer()
        post_info = await self.get_red_post(DOG_SUBS, 50)
        await intr.followup.send(post_info)

    @app_commands.command(name="car", description=RANDOM_STR % "car")
    async def send_random_car(self, intr: discord.Interaction):
        await intr.response.defer()
        post_info = await self.get_red_post(CAR_SUBS, 50)
        await intr.followup.send(post_info)

    async def get_red_post(self, subreddits, limit):
        posts = []
        while not posts:
            chosen_sub = random.choice(subreddits)
            sub = await reddit.subreddit(chosen_sub)
            hot_posts = sub.hot(limit=limit)
            posts = [
                post
                async for post in hot_posts
                if not re.match(I_REDDIT_REGEX, post.url)
                and not re.match(I_IMGUR_REGEX, post.url)
            ]

        chosen_post = random.choice(posts)
        return chosen_post.url

    async def handle_reddit_matches(self, matches, message):
        m_cnt = len(matches)
        ext = "s"[: m_cnt ^ 1]
        payload = f"Found {m_cnt} subreddit link{ext} in your message:\n"
        safe_matches = await self.get_safe_matches(matches)

        if not safe_matches:
            return

        for match in safe_matches:
            payload = payload + f"https://www.reddit.com{match}\n"

        await message.reply(payload, suppress_embeds=len(safe_matches) > 1)

    async def get_safe_matches(self, matches):
        safe_matches = []
        for match in matches:
            subreddit = await reddit.subreddit(match[3:], fetch=True)
            if not subreddit.over18:
                safe_matches.append(match)

        return safe_matches


def mk_embed(title, emb_url, description=None):
    title = textwrap.shorten(title, 256)
    embed = discord.Embed(title=title, url=emb_url)
    embed.set_author(name=AUTHOR_NAME, url=AUTHOR_URL, icon_url=EINDJE_ICON_URL)
    embed.color = discord.Color.red()
    if description:
        description = textwrap.shorten(description, 1024)
        embed.description = description
    return embed


async def setup(client: Eindjeboss):
    await client.add_cog(Reddit(client))
