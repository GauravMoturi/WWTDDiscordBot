import discord
import random
import os
import asyncio


class Card:
    text: str
    directory: str

    def __init__(self, directory=None, nsfw=None):
        if directory:
            self.directory = directory
            self.text = open(directory, 'r').read()
        else:
            decks_list = [dir for dir in os.listdir("decks")]
            rating = random.choice(['sfw', 'nsfw']) if nsfw else 'sfw'
            deck = random.choice(decks_list)
            card = random.choice(os.listdir(f"decks/{deck}/{rating}"))
            self.directory = f"decks/{deck}/{rating}/{card}"
            self.text = open(self.directory, 'r').read()


class Player:
    user: discord.User
    points: int
    answer: str

    def __init__(self, user):
        self.user = user
        self.points = 0
        self.answer = None


class Game:  # Put all constants like collecting playeres and stuff, but for collecting points and resuming games and what not, make sure that the functions are different. Also make sure to make them async def because they will be called in main.pydocs.
    #Game constants
    players: list
    index: int
    current_card: discord.Embed
    ctx = None
    bot = None  # used to store cached message
    max_points: int

    seen: list
    unseen: list
    decks: list
    nsfw: bool
    game_code: int  # Random integer from 1 to 100

    #Stages of the game
    collecting_players: bool
    game_start: bool
    need_answer: bool
    need_responses: bool
    evaluate_points: bool

    def __init__(self, bot, ctx, game_code):
        self.ctx = ctx
        self.bot = bot
        self.game_code = game_code
        self.restart_variables()
        self.players = []
        self.nsfw = False

        self.seen = []
        self.unseen = []
        self.decks = ['classic', 'original']
        self.max_points = 5
        self.game_code = 0  # Implement gamecode for later

        self.collecting_players = False
        self.game_start = False
        self.need_answer = False
        self.need_responses = False
        self.evaluate_points = False

    def restart_variables(self):
        self.players = []

        self.seen = []
        self.unseen = []
        self.decks = ['classic', 'original']
        self.game_code = 0  # Implement gamecode for later

        self.collecting_players = False
        self.game_start = False
        self.need_answer = False
        self.need_responses = False
        self.evaluate_points = False
        self.nsfw = False

    def readd_cards(self):
        """Readds cards to the unseen pile."""
        self.seen = random.sample(self.seen, len(self.seen))
        self.unseen = self.seen.copy()
        self.seen = []

    def card_embed(self, card: Card):
        embed = discord.Embed(
            title="Random Card",
            description=card.text +
            "\nSelect your answer by reacting **__A__** or **__B__**.",
            color=discord.Color.blue())
        embed.set_thumbnail(url='https://i.imgur.com/kWKOKVO.png')
        return embed

    def generate_cards(self):
        self.decks = random.sample(self.decks, len(self.decks))
        if self.nsfw:
            sfw = []
            nsfw = []
            for deck in self.decks:
                path = f"decks/{deck}/nsfw"
                list_dir = os.listdir(path)
                nsfw.extend([f"decks/{deck}/nsfw/{dir}" for dir in list_dir])

                path = f"decks/{deck}/sfw"
                list_dir = os.listdir(path)
                sfw.extend([f"decks/{deck}/sfw/{dir}" for dir in list_dir])

            min_length = min(len(sfw), len(nsfw))
            to_shuffle = nsfw[0:min_length - 1] + sfw[0:min_length - 1]
            rest = nsfw[min_length - 1:] + sfw[min_length - 1:]
            for i in range(500):
                to_shuffle = random.sample(to_shuffle, len(to_shuffle))
                rest = random.sample(rest, len(rest))
            self.unseen = to_shuffle + rest
        else:
            for deck in self.decks:
                path = f"decks/{deck}/sfw"
                list_dir = os.listdir(path)
            self.unseen = [f"decks/{deck}/sfw/{dir}" for dir in list_dir]
            for i in range(100):
                self.unseen = random.sample(self.unseen, len(self.unseen))
        self.unseen = [Card(u) for u in self.unseen]

    async def list_decks(self):
        decks_list = [
            dir for dir in os.listdir("decks") if dir not in self.decks
        ]
        use = "**Decks currently in use:**\n{}".format("\n".join(self.decks))
        available = "**Decks currently available:**\n{}".format(
            "\n".join(decks_list))
        full_str = use + "\n" + available
        embed = discord.Embed(title="Deck List", description=full_str)
        await self.ctx.send(embed=embed)

    async def add_deck(self, *args):
        if not args:
            await self.ctx.send("You have not specificed a deck.")
        else:
            decks_list = [
                dir for dir in os.listdir("decks") if dir not in self.decks
            ]
            for arg in args:
                if arg not in decks_list:
                    await self.ctx.send(
                        f"{arg} is not a deck in the list. Please try an appropriate deck."
                    )
                else:
                    self.decks.append(arg)
                    await self.send(
                        f"**{arg} was successfully added to the deck list!**")

    async def remove_deck(self, *args):
        if not args:
            await self.ctx.send(
                "You have not specified any decks to remove. Please try again!"
            )
        else:
            for arg in args:
                if arg not in self.decks:
                    await self.ctx.send(
                        "{arg} is not in the current deck list.")
                else:
                    self.decks.remove(arg)
                    await self.ctx.send(
                        f"{arg} has been removed from the current deck list.")

    async def list_players(self):
        if self.collecting_players or self.game_start:
            if self.players:
                player_names = [player.user.name for player in self.players]
                await self.ctx.reply("\n".join(player_names))
            else:
                await self.ctx.reply(
                    "There are currently no players. Players who would like to play"
                )
        else:
            await self.ctx.reply(
                "There is no game about to or currently taking place.")

    async def join_game(self, msg_author):
        if self.collecting_players:
            if msg_author not in [player.user for player in self.players]:
                self.players.append(Player(msg_author))
                await self.ctx.send(
                    f"{msg_author.mention} has been added to the list of players."
                )
            else:
                await self.ctx.send(
                    f"You are already in the list of players, {msg_author.mention}"
                )
        else:
            await self.ctx.send(
                "There is no game being initiated at this time, or you are too late."
            )

    async def join_game_reaction(self, author):
        if self.collecting_players:
            if author not in [player.user for player in self.players]:
                self.players.append(Player(author))
                await self.ctx.send(
                    f"{author.mention} has been added to the list of players.")
            else:
                await self.ctx.send(
                    f"You are already in the list of players, {author.mention}"
                )
        else:
            await self.ctx.send(
                "There is no game being initiated at this time, or you are too late."
            )

    async def leave_game(self, msg_author):
        if self.collecting_players or self.game_start:
            if msg_author in [p.user for p in self.players]:
                leaving_player = [
                    p for p in self.players if p.user == msg_author
                ][0]
                self.players.remove(leaving_player)
                await self.ctx.send(
                    f"**{msg_author} has been removed from the list of players!**"
                )
                if len(self.players) < 2:
                    await self.end_game()
                    return
                if self.turn_player.user:
                    if msg_author == self.turn_player.user:
                        await self.ctx.send(
                            "The turn player has left the self. Onto the next person."
                        )
                        await self.resume_game()
        else:
            await self.ctx.send("What game is there to leave???")

    async def end_game(
        self
    ):  # End game will delete the object. Make sure to check in main.py which games are over.
        if self.collecting_players:
            print_str = "Initiated Players:\n"
            for player in self.players:
                print_str = print_str = f"{player.user.name}"
            embed = discord.Embed(title="INITIATION END",
                                  description="Players:\n" + print_str,
                                  color=discord.Color.darker_grey())
            await self.ctx.send(embed=embed)
            self.restart_variables()
        elif self.game_start:
            winners = [
                p.user.name for p in self.players
                if p.points == self.max_points
            ]
            if winners:
                await self.ctx.send(f"{' and '.join(winners)} won the game!")

            # Sorts the players from highest scores to lowest scores
            self.players.sort(key=lambda player: player.points)
            self.players.reverse()

            print_str = ""
            for player in self.players:
                print_str = print_str + \
                    f"{player.user.name}: {player.points}\n"
            embed = discord.Embed(title="GAME END",
                                  description=print_str,
                                  color=discord.Color.darker_grey())
            await self.ctx.send(embed=embed)
            self.restart_variables()
        else:
            await self.ctx.reply(
                "There is no game about to or currently taking place.")

    async def initiate_game(
        self,
        msg_author,
        arg=None,
        arg2=None
    ):  # Use discord.util.gets in order to get reactions for message
        if not self.decks:
            await self.ctx.reply(
                "There are currently no decks so there is nothing to play!")
            return
        if self.game_start:
            await self.ctx.reply("A game is already taking place.")
            return
        if not self.collecting_players:
            self.collecting_players = True
            if arg:
                self.nsfw = True if arg.lower() != 'sfw' else False
                if self.nsfw:
                    await self.ctx.send("Trigger warning: NSFW cards have explicit mentions of sex, sexual assault, gore and other content that may make one uncomfortable. Player's discretion is strongly advised.")
                else:
                    await self.ctx.send("Only SFW cards are permitted.")
            if arg2:
                try:
                    self.max_points = int(arg2)
                    await self.ctx.send(
                        f"The amount of points needed to win this game is: {self.max_points}"
                    )
                except:
                    await self.ctx.reply(
                        "You specified an invalid argument. Please try again.")
                    return
            self.current_message = await self.ctx.reply(
                "A game initation has been started. All players who would like to join can react to this message with :video_game: or use @join_game."
            )
            self.current_message = discord.utils.get(
                self.bot.cached_messages, id=self.current_message.id)
            await self.current_message.add_reaction('🎮')
            self.players.append(Player(msg_author))
        else:
            await self.ctx.reply(
                "A game is already taking place. You may join with `@join_game`."
            )

    async def on_reaction_add(self, reaction, user):
        pass

    async def start_game(self):
        pass

    async def resume_game(self):
        pass

    async def evaluate_points(self):
        pass


class Normal(Game):
    turn_player: Player

    #Everything in base class is the same broski
    async def on_reaction_add(self, reaction, user):
        if self.collecting_players and reaction.emoji == "🎮" and reaction.message == self.current_message and not user.bot:
            await self.join_game_reaction(user)
        if self.need_responses and user in [
                p.user for p in self.players if p.user != self.turn_player.user
        ] and reaction.message == self.current_message and not user.bot and reaction.emoji in [
                "🅰️", "🇧"
        ]:
            player = [p for p in self.players if p.user == user][0]
            player.answer = "A" if reaction.emoji == "🅰️" else "B"
            await self.ctx.send(
                f"{player.user.name} has selected the answer {player.answer}")
            if not None in [p.answer for p in self.players]:
                self.need_responses = False
                self.evaluate_points = True
                await self.evaluate_points_func()

    async def evaluate_points_func(self):
        self.evaluate_points = False
        correct_players = [
            p for p in self.players
            if p != self.turn_player and p.answer == self.turn_player.answer
        ]
        for player in correct_players:
            player.points = player.points + 1
        if correct_players:
            # Make it an embed, (list of who got it right and who got it wrong. CORRECT and INCORRECT)
            correct_player_names = [c.user.name for c in correct_players]
            await self.ctx.send(
                f'**{", ".join(correct_player_names)} selected the correct answer: {self.turn_player.answer}**'
            )
        else:
            await self.ctx.send("No one has selected the correct answer of: " +
                                self.turn_player.answer)
        if self.max_points in [p.points for p in self.players]:
            await self.end_game()
        else:
            await self.resume_game()

    async def start_game(self):
        if len(self.players) < 2:
            await self.ctx.reply(
                "There are not enough players joined for the game to be started."
            )
            return
        self.generate_cards()  # Puts all cards shuffled in unseen pile.
        self.collecting_players = False
        self.game_start = True
        self.index = random.randint(0, len(self.players) - 1)
        self.turn_player = self.players[self.index]
        card = self.unseen.pop(0)
        self.current_card = self.card_embed(card)
        self.seen.append(card)
        await self.get_answers()

    async def resume_game(self):
        for p in self.players:
            p.answer = None
        self.index = self.index + 1 if self.index + 1 < len(
            self.players) else 0
        self.turn_player = self.players[self.index]
        if not self.unseen:
            self.readd_cards()
        card = self.unseen.pop(0)
        self.current_card = self.card_embed(card)
        self.seen.append(card)
        await self.get_answers()

    async def get_answers(self):
        try:
            self.current_message = await self.turn_player.user.send(
                embed=self.current_card)
            self.current_message = discord.utils.get(
                self.bot.cached_messages, id=self.current_message.id)
            #For some reason, it'll be NoneType somtimes even after these assignments. The while loop may send the message twice but it makes sure that it doesn't happen.
            while self.current_message is None:
                self.current_message = await self.turn_player.user.send(
                    embed=self.current_card)
                self.current_message = discord.utils.get(
                    self.bot.cached_messages, id=self.current_message.id)
            await self.current_message.add_reaction('🅰️')
            await self.current_message.add_reaction('🇧')
            self.need_answer = True
            await self.ctx.send(
                f"Card sent to {self.turn_player.user.name} in DMs. Awaiting a response of `A` or `B`. "
            )
        except Exception as e:
            await self.ctx.send("ERROR:" + str(e))
            await self.ctx.send(
                f"Could not directly message {self.turn_player.user.mention}, skipping their turn."
            )
            await self.resume_game()
        #Get response

        def check(reaction, user):
            return str(reaction.emoji) in [
                "🅰️", "🇧"
            ] and reaction.message == self.current_message

        try:
            reaction, user = await self.bot.wait_for('reaction_add',
                                                     timeout=200.0,
                                                     check=check)
        except asyncio.TimeoutError:
            await self.ctx.send(
                f"It has been 200 seconds and {self.turn_player.user} has not answered. Their turn has been skipped."
            )
            await self.resume_game()
        else:
            self.turn_player.answer = "A" if reaction.emoji == "🅰️" else "B"
            await self.turn_player.user.send(
                "Your answer has been received! Go back to the server!")
            await self.ctx.send(
                f"{self.turn_player.user.name} has selected an answer! All other players please pick an answer. Answers can be changed until every player has selected an answer."
            )
            self.current_card.title = f"What would {self.turn_player.user.name} do?"
            self.current_message = await self.ctx.send(embed=self.current_card)
            self.current_message = discord.utils.get(
                self.bot.cached_messages, id=self.current_message.id)
            #For some reason, it'll be NoneType somtimes even after these assignments. The while loop may send the message twice but it makes sure that it doesn't happen.
            while self.current_message is None:
                self.current_message = await self.ctx.send(
                    embed=self.current_card)
                self.current_message = discord.utils.get(
                    self.bot.cached_messages, id=self.current_message.id)
            await self.current_message.add_reaction('🅰️')
            await self.current_message.add_reaction('🇧')
            self.need_answer = False
            self.need_responses = True

    async def scores(self):
        if self.game_start:
            self.players.sort(key=lambda player: player.points)
            self.players.reverse()

            print_str = ""
            for player in self.players:
                print_str = print_str + \
                    f"{player.user.name}: {player.points}\n"
            embed = discord.Embed(title="CURRENT SCORES",
                                  description=print_str,
                                  color=discord.Color.light_grey())
            await self.ctx.send(embed=embed)
        else:
            await self.ctx.send(
                "A bot tried to run this command OR a game has not begun.")


class Debate(Game):
    a_queue: list
    b_queue: list
    a_team: list
    b_team: list

    def __init__(self, bot, ctx, game_code):
        super().__init__(bot, ctx, game_code)
        self.a_queue, self.b_queue = [], []
        self.a_team, self.b_team = [], []

    async def on_reaction_add(self, reaction, user):
        if self.collecting_players and reaction.emoji == "🎮" and reaction.message == self.current_message and not user.bot:
            await self.join_game_reaction(user)
        if self.players and self.a_team and self.b_team:
          if self.need_responses and user in [
                  p.user for p in self.players if p not in self.a_team and p not in self.b_team
          ] and reaction.message == self.current_message and not user.bot and reaction.emoji in [
                  "🅰️", "🇧"
          ]:
              player = [p for p in self.players if p.user == user][0]
              player.answer = "A" if reaction.emoji == "🅰️" else "B"
              await self.ctx.send(
                  f"{player.user.name} has selected the answer {player.answer}")
              if not None in [p.answer for p in self.players if p not in self.a_team and p not in self.b_team]:
                  self.need_responses = False
                  self.evaluate_points = True
                  await self.evaluate_points_func()

    async def start_game(self):
        if len(self.players) < 3:
            await self.ctx.reply(
                "There are not enough players joined for the game to be started."
            )
            return
        self.team_size = 1 if len(self.players) < 11 else 2

      # Get the two teams
        self.a_queue = random.sample(self.players, len(self.players))
        self.b_queue = random.sample(self.players, len(self.players))

        #Checks to make sure there are no matches between the queues
        matches = False
        while True:
          for a, b in zip(self.a_queue, self.b_queue):
            if a == b:
                matches = True
          if not matches:
            break
          else:
              self.b_queue = random.sample(self.players, len(self.players))
              matches = False

        #Note to self: a linked list is not a good idea because you may have TWO players on a team instead of one. Just have an a_queue, a_grave and b_queue, b_grave. Make sure a_queue and b_queue have no matches like up above. Pop one or two players after their team stuff is over and put them in the grave. Then once the queue is empty, set the queues to the reverse order of their respective graves and make the graves empty. Repeat for the duration of the game.

        self.generate_cards()  # Puts all cards shuffled in unseen pile.
        self.collecting_players = False
        self.game_start = True
        card = self.unseen.pop(0)
        self.current_card = self.card_embed(card)
        self.seen.append(card)
        await self.ctx.send(
            f"Team A must convince subsequent players to pick option A. Team B must convince them the opposite. Good luck!"
        )
        await self.get_answers()

    async def get_answers(self):
        try:
            self.current_message = await self.ctx.send(embed=self.current_card)
            self.current_message = discord.utils.get(
                self.bot.cached_messages, id=self.current_message.id)
            #For some reason, it'll be NoneType somtimes even after these assignments. The while loop may send the message twice but it makes sure that it doesn't happen.
            while self.current_message is None:
                self.current_message = await self.ctx.user.send(
                    embed=self.current_card)
                self.current_message = discord.utils.get(
                    self.bot.cached_messages, id=self.current_message.id)
            await self.current_message.add_reaction('🅰️')
            await self.current_message.add_reaction('🇧')
            self.need_answer = True
            self.need_responses = True
            a_team = []
            b_team = []
            #Add the random players to the team
            for i in range(self.team_size):
              player = self.a_queue.pop(0)
              self.a_queue.append(player)
              a_team.append(player)
              player = self.b_queue.pop(0)
              self.b_queue.append(player)
              b_team.append(player)

            await self.ctx.send(f"Team A is: **{', '.join(a.user.name for a in a_team)}**")
            await self.ctx.send(f"Team B is: **{', '.join(b.user.name for b in b_team)}**")
            await self.ctx.send("All other players, you must vote. Allow the two teams to convince of your their side. When you have made a decision, cast your vote.")
            self.a_team = a_team
            self.b_team = b_team
        except Exception as e:
            await self.ctx.send(
                f"ERROR: {str(e)}.\nMoving onto the next turn!.")
            await self.resume_game()

    async def resume_game(self):
        self.collecting_players = False
        if not self.unseen:
            self.readd_cards()
        for p in self.players:
            p.answer = None
        card = self.unseen.pop(0)
        self.current_card = self.card_embed(card)
        self.seen.append(card)
        await self.get_answers()

    async def evaluate_points_func(self):
        #COUNT ANSWERS AND DECIDE WINNER
        answers = [p.answer for p in self.players if p.answer !=
                   None and p not in self.a_team and p not in self.b_team]
        a_ans, b_ans = answers.count("A"), answers.count("B")
        if a_ans > b_ans:
            await self.ctx.send(
                "Team A has convinced the players! Congraulations!")
            for p in self.a_team:
              p.points += 1
        elif b_ans > a_ans:
            await self.ctx.send(
                "Team B has convinced the players! Congraulations!")
            for p in self.b_team:
              p.points += 1
        else:
            await self.ctx.send("There has been a tie!!!! Wowzers!")
        if self.max_points in [p.points for p in self.players]:
            await self.end_game()
        await self.resume_game()

    async def end_game(
        self
    ):  # End game will delete the object. Make sure to check in main.py which games are over.
        if self.collecting_players:
            print_str = "Initiated Players:\n"
            for player in self.players:
                print_str = print_str = f"{player.user.name}"
            embed = discord.Embed(title="INITIATION END",
                                  description="Players:\n" + print_str,
                                  color=discord.Color.darker_grey())
            await self.ctx.send(embed=embed)
            self.restart_variables()
        elif self.game_start:
            winners = [
                p.user.name for p in self.players if p.points == self.max_points]
            if winners:
                await self.ctx.send(f"{' and '.join(winners)} won the game!")

            # Sorts the players from highest scores to lowest scores
            players = self.players.copy()
            players.sort(key=lambda x: x.points)
            players.reverse()
            print_str = ""
            for player in players:
              print_str += f"{player.user.name}: {player.points}\n"
            embed = discord.Embed(title="GAME END",
                                  description=print_str,
                                  color=discord.Color.darker_grey())
            await self.ctx.send(embed=embed)
            self.restart_variables()
        else:
            await self.ctx.reply(
                "There is no game about to or currently taking place.")

    async def scores(self):
        if self.game_start:
            ordered_players = self.players.copy()
            ordered_players.sort(key=lambda x: x.points)
            ordered_players.reverse()
            print_str = '\n'.join(
                [f"{p.user.name}: {p.points}" for p in ordered_players])
            embed = discord.Embed(title="CURRENT SCORES",
                                  description=print_str,
                                  color=discord.Color.light_grey())
            await self.ctx.send(embed=embed)
        else:
            await self.ctx.send(
                "A bot tried to run this command OR a game has not begun.")
