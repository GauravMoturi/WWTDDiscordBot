import os
from game import Game, Card, Normal, Debate
import game
import random

import discord
import asyncio
from discord.ext import commands

# DO NOT SHARE THIS ANYONE
# DO NOT SHARE THIS WITH ANYONE
TOKEN = '' #INSERT YOUR DISCORD TOKEN HERE
# DO NOT SHARE THIS WITH ANYONE

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='@', intents=intents)

game_obj = None
nsfw = False


@bot.command(name='debug', help='debug')
async def debug(ctx):
    await ctx.send("n")


def random_card_embed():
    pass


@bot.command(name='manual', help='shows you how to play the game')
async def manual(ctx):
    await ctx.send("https://docs.google.com/document/d/1gD7qa9wNzhOcYsSZTo2kwyIs_iW1JurGggg0mgdqZw4/edit?usp=sharing"
                   )


@bot.command(
    name='random_card',
    help='Will print out a random card! Add "nsfw" for a chance to get an NSFW card.'
)
async def random_card(ctx, arg=None):
    if arg == "nsfw":
        card = Card(nsfw=True)
    else:
        card = Card(nsfw=False)
    embed = discord.Embed(title="Random Card",
                          description=card.text,
                          color=discord.Color.blue())
    embed.set_thumbnail(url='https://i.imgur.com/kWKOKVO.png')
    await ctx.send(embed=embed)


@bot.command(
    name='list_decks',
    help='Will print the decks currently in use and the decks that are currently available.'
)
async def list_decks(ctx):
    global game_obj
    if not game_obj:
        total_sfw, total_nsfw = 0,0
        decks_list = [
        dir for dir in os.listdir("decks")
        ]
        deck_numbers = []
        for deck_name in decks_list:
            dir_path = f"decks/{deck_name}/sfw"
            sfw_count = len([entry for entry in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, entry))])
            total_sfw += sfw_count
            dir_path = f"decks/{deck_name}/nsfw"
            nsfw_count = len([entry for entry in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, entry))])
            total_nsfw += nsfw_count
            deck_numbers.append((sfw_count, nsfw_count))
        full_str = []
        for i in range(len(decks_list)):
            full_str.append(f"Deck: {decks_list[i]} | {deck_numbers[i][0]} (SFW) | {deck_numbers[i][1]} (NSFW)")
        full_str.append(f"Deck: Total | {total_sfw} (SFW) | {total_nsfw} (NSFW)")
        embed = discord.Embed(title="Deck List", description="\n".join(full_str))
        await ctx.send(embed=embed)
    else:
        await game_obj.list_decks()


@bot.command(name='add_deck', help='Will a deck to the current deck list.')
async def add_deck(ctx, *args):
    global game_obj
    if game_obj:
        await game_obj.add_deck(args)
    else:
        await ctx.reply("You need to start a game to add a deck to the list.")


@bot.command(name='remove_deck',
             help='Remove a current deck in the deck list.')
async def remove_deck(ctx, *args):
    global game_obj
    if game_obj:
        await game_obj.remove_deck(args)
    else:
        await ctx.reply("You need to start a game.")


@bot.command(
    name='initiate_game',
    help='Will initiate a game. First argument enables nsfw (type anything) unless you type sfw. Second argument is point limit.'
)
async def initiate_game(ctx, mode=None, arg=None, arg2=None):
    global game_obj
    if not game_obj:
        if mode not in ["normal", "debate"]:
            await ctx.reply("That is not an appropriate mode.")
        else:
            if mode == "normal":
                game_obj = Normal(bot, ctx, 0)
            else:
                game_obj = Debate(bot, ctx, 0)
            await game_obj.initiate_game(ctx.message.author, arg, arg2)
    else:
        await ctx.reply("A game is already taking place.")


@bot.command(name='join_game', help='Join a game that is in progress.')
async def join_game(ctx):
    global game_obj
    if game_obj:
        await game_obj.join_game(ctx.message.author)
    else:
        await ctx.reply("You need to start a game.")


@bot.command(name='list_players')
async def list_players(ctx):
    global game_obj
    if game_obj:
        await game_obj.list_players()
    else:
        await ctx.reply("You need to start a game.")


@bot.command(name="start_game")
async def start_game(ctx):
    global game_obj
    if game_obj:
        await game_obj.start_game()
    else:
        await ctx.reply("You need to initiate a game.")


@bot.command(name="leave_game")
async def leave_game(ctx):
    global game_obj
    if game_obj:
        await game_obj.leave_game(ctx.message.author)
    else:
        await ctx.reply("You need to start a game.")


@bot.command(name="end_game")
async def end_game(ctx):
    global game_obj
    if game_obj:
        await game_obj.end_game()
    else:
        await ctx.reply("You need to start a game.")
    game_obj = None


@bot.command(name='scores')
async def scores(ctx):
    global game_obj
    if game_obj:
        await game_obj.scores()
    else:
        await ctx.reply("You need to start a game.")


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    # if game.evaluate_points:
    # await evaluate_points(game.current_channel)


@bot.event
async def on_reaction_add(reaction, user):
    global game_obj
    if game_obj:
        await game_obj.on_reaction_add(reaction, user)

if __name__ == '__main__':
    bot.run(TOKEN)
