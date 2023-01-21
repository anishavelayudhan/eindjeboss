import ast
import logging
import operator as op
import re
from discord.ext import commands
from util.vars.eind_vars import *

CALC_REGEX = r"(?:calc|calculate) (.{3,})"

operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

class Utilities(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if message.channel.id in CHANNEL_IGNORE_LIST:
            return

        message_content = message.content.lower()

        calc_pattern = re.compile(CALC_REGEX)
        matches = calc_pattern.match(message_content)

        if(matches):
            try:
                expression = matches.group(1)
                result = '{0:.2f}'.format(calculate(expression))
            except TypeError as te:
                logging.error(f'Failed to calculate expression \"{expression}\" for {message.author.name}')
                logging.debug(te)
                await message.reply('Your expression could not be calculated. Please check your formatting.')
            else:
                await message.reply(f"{result}")

def calculate(expression: str):
    node = ast.parse(expression, mode='eval').body
    return eval_(node)

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp):
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)


async def setup(bot):
    await bot.add_cog(Utilities(bot))