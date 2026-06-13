import discord
from discord.ext import commands
from discord import app_commands
from renderer import render_board, sudoku_to_grid
from storage import save_games, load_games
import time
import os

from sudoku import (
    SudokuGame,
    create_sudoku,
    DIFFICULTIES
)


COOLDOWNS = {}

COOLDOWN_TIERS = [30,60,120,200,300,450]
MAX_TIER = len(COOLDOWN_TIERS) - 1

GUILD_IDS = [
    1514625466244534272,
    1501492936175521802,
    1162929561466581152
]

GUILDS = [
    discord.Object(id=guild_id)
    for guild_id in GUILD_IDS
]


ACTIVE_GAMES = {}

class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

        try:
            total_synced = 0

            for guild in GUILDS:
                synced = await self.tree.sync(guild=guild)
                total_synced += len(synced)
                print(f"Synced {len(synced)} commands to guild {guild.id}")

            print(f"Total synced commands: {total_synced}")

            load_active_games()

        except Exception as e:
            print("error syncing commands:", e)

    async def on_message(self,message):
        if message.author == self.user:
            return
    

# -----------------------------------
# HELPER FUNCTIONS - MAIN
# -----------------------------------

def check_channel(interaction: discord.Interaction):

    guild_id = interaction.guild.id
    allowed_channel = ALLOWED_CHANNELS.get(guild_id)

    return interaction.channel.id == allowed_channel

def is_on_cooldown(channel_id: int, user_id: int):
    now = time.time()

    if channel_id not in COOLDOWNS:
        return False, 0

    user = COOLDOWNS[channel_id].get(user_id)

    if not user:
        return False, 0

    if now >= user["unlock"]:
        return False, 0

    return True, int(user["unlock"] - now)


def set_cooldown(channel_id: int, user_id: int):
    now = time.time()

    if channel_id not in COOLDOWNS:
        COOLDOWNS[channel_id] = {}

    user = COOLDOWNS[channel_id].get(user_id)

    if user:
        tier = min(user["tier"] + 1, MAX_TIER)
    else:
        tier = 0

    cooldown_time = COOLDOWN_TIERS[tier]

    COOLDOWNS[channel_id][user_id] = {
        "unlock": now + cooldown_time,
        "tier": tier
    }

    return cooldown_time


def reset_cooldown(channel_id: int, user_id: int):
    if channel_id not in COOLDOWNS:
        return

    if user_id in COOLDOWNS[channel_id]:
        del COOLDOWNS[channel_id][user_id]
def save_active_games():

    data = {}

    for channel_id, game in ACTIVE_GAMES.items():
        data[str(channel_id)] = game.to_dict()

    save_games(data)

def load_active_games():

    ACTIVE_GAMES.clear()

    data = load_games()

    for channel_id, game_data in data.items():

        ACTIVE_GAMES[int(channel_id)] = (
            SudokuGame.from_dict(game_data)
        )

intents = discord.Intents.default()
intents.message_content = True

client = Client(command_prefix = "!", intents = intents)



ALLOWED_CHANNELS = {
    1514625466244534272: 1514625575472468049,
    1501492936175521802: 1514297063519813772,
    1162929561466581152: 1514738152294715614
}

@client.tree.command(name="sudoku-bot", description = "Connection Check ")
@app_commands.guilds(*GUILDS)
async def sayHello(interaction : discord.Interaction):
    await interaction.response.send_message("Check bot connection - **HELLO**")



class difficultyMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Easy", emoji="🟩"),
            discord.SelectOption(label="Medium", emoji="🟨"),
            discord.SelectOption(label="Hard", emoji="🟥")
        ]

        super().__init__(
            placeholder="Select Difficulty...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        
        if interaction.channel.id in ACTIVE_GAMES:
            await interaction.channel.send(
                "🧩 A Sudoku game is already active in this channel!\n"
            )
            return
        
        await interaction.response.send_message(
            f"You Picked {self.values[0]} Difficulty!"
        )



        difficulty = self.values[0]

        game = create_sudoku(
            DIFFICULTIES[difficulty],
            difficulty,
            interaction.user.display_name
        )

        ACTIVE_GAMES[
            interaction.channel.id
        ] = game

        path = render_board(
            game.board,
            game.original_board
        )

        embed, file = create_board_embed(path, game)

        await interaction.channel.send(
            embed=embed,
            file=file
        )
        save_active_games()


@client.tree.command(
    name="sudoku-place",
    description="Attempt to place a digit",
)
@app_commands.guilds(*GUILDS)
async def sudoku_place(
    interaction: discord.Interaction,
    cell: str,
    value: int
):
    player_name = interaction.user.display_name
    game = ACTIVE_GAMES.get(
        interaction.channel.id
    )

    if not check_channel(interaction):
        await interaction.response.send_message(
            "🧩 Please use the Sudoku channel for this command.",
            ephemeral=True
        )
        return

    if game is None:
        await interaction.response.send_message(
            "🧩 No active Sudoku game use ***/sudoku-new*** to start one !"
        )
        return

    cell = cell.upper()

    try:
        col = ord(cell[0]) - ord("A")
        row = int(cell[1]) - 1
    except:
        await interaction.response.send_message(
            "Coordinates must look like A1, C5, etc."
        )
        return

    if row < 0 or row > 8:
        await interaction.response.send_message(
            "Invalid row."
        )
        return

    if col < 0 or col > 8:
        await interaction.response.send_message(
            "Invalid column."
        )
        return

    if value < 1 or value > 9:
        await interaction.response.send_message(
            "Value must be between 1 and 9."
        )
        return

    if game.original_board[row][col] != 0:
        await interaction.response.send_message(
            f"🔒 **{player_name}** tried modifying **{cell}**, but that's one of the original clues."
        )
        return
    on_cd, remaining = is_on_cooldown(interaction.channel.id, interaction.user.id)

    if on_cd:
        await interaction.response.send_message(
            f"⏳ You're on cooldown for **{remaining}s** due to a wrong attempt.",
            ephemeral=True
        )
        return
    if value != game.solution_board[row][col]:
        cooldown = set_cooldown(interaction.channel.id, interaction.user.id)

        await interaction.response.send_message(
                f"❌ **{player_name}** tried placing **{value}** at **{cell}**, but it was incorrect.\n"
                f"⏳ Locked for **{cooldown}s**."
        )
        return

    if game.board[row][col] == value:
        await interaction.response.send_message(
        f"{cell} already contains {value}."
        )
        return

    game.board[row][col] = value

    reset_cooldown(
    interaction.channel.id,
    interaction.user.id
    )

    solved = (
    game.board == game.solution_board
    )

    path = render_board(
        game.board,
        game.original_board
    )

    embed, file = create_board_embed(path, game)

    await interaction.response.send_message(
        embed=embed,
        file=file
    )
    if solved:

        embed_final = discord.Embed(title = "🎉 Sudoku Solved!", description = f"**{player_name}** placed the final number !", color = 0x9C88FF)
        embed.set_footer(
            text=f"Difficulty: {game.difficulty}"
        )
        await interaction.channel.send(embed=embed_final)

        del ACTIVE_GAMES[
            interaction.channel.id
        ]
    else:   
        await interaction.channel.send(
            f"✅ **{player_name}** placed **{value}** at **{cell}**."
    )
    save_active_games()

@client.tree.command(
    name="sudoku-board",
    description="View active board"
)
@app_commands.guilds(*GUILDS)
async def sudoku_show(
    interaction: discord.Interaction
):

    game = ACTIVE_GAMES.get(
        interaction.channel.id
    )

    if not check_channel(interaction):
        await interaction.response.send_message(
            "🧩 Please use the Sudoku channel for this command.",
            ephemeral=True
        )
        return

    if game is None:
        await interaction.response.send_message(
            "🧩 No active Sudoku game in this channel!"
        )
        return

    path = render_board(
        game.board,
        game.original_board
    )

    embed, file = create_board_embed(
        path,
        game
    )

    await interaction.response.send_message(
        embed=embed,
        file=file
    )

# @client.tree.command(
#     name="sudoku-end",
#     description="End the current Sudoku game"
# )
# @app_commands.default_permissions(manage_guild=True)
# @app_commands.guilds(*GUILDS)
# async def sudoku_end(
#     interaction: discord.Interaction
# ):

#     game = ACTIVE_GAMES.get(
#         interaction.channel.id
#     )

#     if game is None:
#         await interaction.response.send_message(
#             "🧩 No active Sudoku session here."
#         )
#         return

#     del ACTIVE_GAMES[
#         interaction.channel.id
#     ]

#     save_active_games()

#     await interaction.response.send_message(
#         f"🛑 Sudoku ended by **{interaction.user.display_name}**."
#     )

def create_board_embed(path, game):

    embed = discord.Embed(
        title="🧩 𝗦𝘂𝗱𝗼𝗸𝘂",
        description="Solve together. One grid at a time.",
        color=0x9C88FF
    )

    file = discord.File(
        path,
        filename="current_board.png"
    )

    embed.set_image(
        url="attachment://current_board.png"
    )

    filled = sum(
        1
        for row in game.board
        for cell in row
        if cell != 0
    )

    embed.set_footer(
        text=(
            f"• 🧩 𝗙𝗶𝗹𝗹𝗲𝗱 : {filled}/81 \n"
            f"• 🧠 𝗗𝗶𝗳𝗳𝗶𝗰𝘂𝗹𝘁𝘆 :  {game.difficulty} \n"
            f"• 👤 𝗦𝘁𝗮𝗿𝘁𝗲𝗱 𝗕𝘆 : {game.started_by}"
        )
    )

    return embed, file

class difficultySelector(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(difficultyMenu())

 
@client.tree.command(name="sudoku-new", description = "Start a new Sudoku game !")
@app_commands.guilds(*GUILDS)
async def tryTest(interaction: discord.Interaction):
    if not check_channel(interaction):
        await interaction.response.send_message(
            "🧩 Please use the Sudoku channel for this command.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        view = difficultySelector()
    )





token = os.getenv("DISCORD_TOKEN")

if not token:
    raise RuntimeError("DISCORD_TOKEN environment variable not found")

client.run(token)