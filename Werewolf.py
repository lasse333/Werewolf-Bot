import discord
from discord.ext import commands
import random  # Imported Rasmus
import asyncio
import math
import os

prefix = "w!"

Client = discord.Client()
bot = commands.Bot(command_prefix=prefix)

token_file = open("discord_client_keys3.txt", "r", encoding="utf-8")
token = token_file.read()


# Variables and Objects


phase = ""
prev_phase = ""
roles = []
players = []
running = False
night_roles = ["Werewolf", "Seer", "Cupid", "Bodyguard"]
seems_good = ["Seer", "Villager", "Cupid", "Bodyguard", "Cursed", "Tanner", "Hunter"]
next_phase = False
channel = None
day_talk_time = 30
player_on_trial = None
trials = 3
trials_left = 0
lynching = False
targets = []
display_roles = []
display_players = []



class PlayerObject:
    name = None
    id = None
    role = None
    event = None
    voted_for = None
    against = []
    lover = None
    last_target = None
    protected = False


# Discord detection


@bot.event
async def on_ready():
    global phase
    global trials_left
    os.system("cls")
    os.system("title Werewolf")
    print("Werewolf running")
    phase = "join"
    trials_left = trials


@bot.event
async def on_message(message):
    global phase


    if (message.channel.type == discord.ChannelType.text and message.channel.name == "werewolf") or message.channel.type == discord.ChannelType.private:
        if message.content.lower().startswith(prefix + "list all"):
            await listallplayers(message.channel)
        elif message.content.lower().startswith(prefix + "list roles"):
            await listroles(message.channel)
        elif message.content.lower().startswith(prefix + "list"):
            await listplayers(message.author, message.channel, False)
        elif message.content.lower().startswith(prefix + "clear"):
            await clear(message.channel)
        elif message.content.lower().startswith(prefix + "reset"):
            await clear(message.channel)
            restart()
        elif message.content.lower().startswith(prefix + "restart"):
            await clear(message.channel)
            restart()
        elif message.content.lower().startswith(prefix + "reload"):
            await clear(message.channel)
            restart()
        elif message.content.lower().startswith(prefix + "kick") and phase != "kick":
            args = message.content.split(" ")
            if int(args[1]) < len(players):
                await kick(int(args[1]))
        elif message.content.lower().startswith(prefix + "setphase"):
            await changephase("vote")
        elif message.content.lower().startswith(prefix + "setrole"):
            players[findplayer(message.author.id)].role = "Seer"
        elif message.content.lower().startswith(prefix + "stop"):
            await bot.close()
        else:
            if phase == "join":
                await phase_join(message)
            elif phase == "first night":
                await phase_first_night(message)
            elif phase == "day":
                phase_day(message)
            elif phase == "vote":
                await phase_vote(message)
            elif phase == "trial":
                await phase_trial(message)
            elif phase == "night":
                await phase_night(message)
            elif phase == "hunter":
                await phase_hunter(message)
            else:
                print("Oops invalid phase: " + phase)



# Phases


async def phase_join(message):
    if message.content.lower().startswith(prefix + "join"):
        x = findplayer(message.author.id)
        if x is None:
            await join(message)

    if message.content.lower().startswith(prefix + "leave"):
        await leave(message)

    if message.content.lower().startswith(prefix + "start"):
        if not running and len(players) >= 4:
#        if not running:
            await start(message)


async def phase_first_night(message):
    if message.content.lower().startswith(prefix + "seer") and players[findplayer(message.author.id)].role == "Seer" and message.channel.type == discord.ChannelType.private:
        args = message.content.split(" ")
        await seer(message.author, int(args[1])-1)
    elif message.content.lower().startswith(prefix + "cupid") and players[findplayer(message.author.id)].role == "Cupid" and message.channel.type == discord.ChannelType.private:
        args = message.content.split(" ")
        await cupid(message.author, int(args[1])-1, int(args[2])-1)
    elif message.content.lower().startswith(prefix + "bodyguard") and players[findplayer(message.author.id)].role == "Bodyguard" and message.channel.type == discord.ChannelType.private:
        args = message.content.split(" ")
        await bodyguard(message.author, int(args[1])-1)


def phase_day(message):
    print(message.author.display_name + ": " + message.content)


async def phase_vote(message):
    if message.content.lower().startswith(prefix + "vote"):
        args = message.content.split(" ")
        await vote(message.author, target=int(args[1])-1)


async def phase_trial(message):
    if message.content.lower().startswith(prefix + "vote yes"):
        await vote(message.author, trial=True)
    elif message.content.lower().startswith(prefix + "vote no"):
        await vote(message.author, trial=False)


async def phase_night(message):
    if message.content.lower().startswith(prefix + "seer") and players[findplayer(message.author.id)].role == "Seer" and message.channel.type == discord.ChannelType.private:
        args = message.content.split(" ")
        await seer(message.author, int(args[1])-1)
    elif message.content.lower().startswith(prefix + "werewolf") and players[findplayer(message.author.id)].role == "Werewolf" and message.channel.type == discord.ChannelType.private:
        args = message.content.split(" ")
        await werewolf(message.author, int(args[1])-1)
    elif message.content.lower().startswith(prefix + "bodyguard") and players[findplayer(message.author.id)].role == "Bodyguard" and message.channel.type == discord.ChannelType.private:
        args = message.content.split(" ")
        await bodyguard(message.author, int(args[1])-1)


# Extra Phases


async def phase_hunter(message):
    if message.content.lower().startswith(prefix + "Hunter") and players[findplayer(message.author.id)].role == "Hunter":
        args = message.content.split(" ")
        await hunter(message.author, int(args[1]) - 1)


# Functions


def findplayer(user_id):
    for x in range(0, len(players)):
        if user_id == players[x].id:
            return x
    return None


async def join(message):
    global display_players
    global display_roles

    player = PlayerObject()

    player.name = message.author.display_name.replace("_", "\_")
    player.id = message.author.id

    players.append(player)

    if len(players) % 8 == 1:
        roles.append("Werewolf")
    elif len(players) == 2:
        roles.append("Seer")
    elif len(players) == 5:
        roles.append("Lycan")
    elif len(players) == 6:
        roles.append("Bodyguard")
    elif len(players) == 7:
        roles.append("Tanner")
    elif len(players) == 8:
        roles.append("Cupid")
    elif len(players) == 10:
        roles.append("Cursed")
    elif len(players) == 11:
        roles.append("Villager") # Hunter
    else:
        roles.append("Villager")

    if message.author.id == 201698178179923968:
        await message.channel.send("The not so secret Hitler aka <@" + str(message.author.id) + "> joined the game")
    elif message.author.id == 283153621770829824:
        await message.channel.send("import <@" + str(message.author.id) + ">\n<@" + str(message.author.id) + ">.randint(0, " + str(len(players)+2) + ")\n" + str(len(players)))
    elif message.author.id == 186169263126609920:
        await message.channel.send("With all the peace and love here comes <@" + str(message.author.id) + "> :heart:")
    elif message.author.id == 341547992840404992:
        await message.channel.send("<@" + str(message.author.id) + "> has joined the game, but which Rasmus?")
    elif message.author.id == 212285794335850496:
        await message.channel.send("<@" + str(message.author.id) + "> IS HERE AND HE IS DEFINITELY NOT THE WEREWOLF")
    else:
        await message.channel.send("<@" + str(message.author.id) + "> has joined the game")

    display_players = []
    display_roles = []

    for x in range(0, len(players)):
        display_players.append(players[x])
        display_roles.append(roles[x])


async def leave(message):
    print("leave")
    players.pop(findplayer(message.author.id))
    roles.pop(len(roles) - 1)
    await message.channel.send("<@" + str(message.author.id) + "> has left the game")


async def kick(number):
    global phase

    return_phase = phase

    phase = "kick"

    await channel.send("The sky is getting covered by grey clouds...")
    await channel.send("The village suspects that the gods are furious...")
    await asyncio.sleep(5)
    await channel.send("Lightning strikes...")
    await asyncio.sleep(1)
    await channel.send("and it hits <@" + str(players[int(number)-1].id) + ">...")
    await asyncio.sleep(5)
    await channel.send("<@" + str(players[int(number)-1].id) + ">'s role was **" + players[int(number)-1].role + "**...")
    players.pop(int(number)-1)
    await asyncio.sleep(5)
    await channel.send("The sky is clearing up again")
    await channel.send("The village is shocked but they continue on with their business")

    phase = return_phase


async def listplayers(user, chat, private):
    if len(players) >= 1:
        playernames = ""

        if phase == "join":
            title = "Joined Players"
        elif phase == "vote":
            title = "Vote for one of these to get lynched"
        else:
            title = "List of all the alive villagers"

        for x in range(0, len(players)):
            playernames += "**" + str(x+1) + ".** " + players[x].name + "\n"

        embed = discord.Embed(title=title, description=playernames[:-1], color=0x750000)

        if phase == "vote":
            embed.set_footer(text=prefix + "vote [number]")
        elif phase == "hunter":
            embed.set_footer(text=prefix + "hunter [number]")

        elif (phase == "night" or phase == "first night") and players[findplayer(user.id)].role in night_roles and private:

            if players[findplayer(user.id)].role == "Cupid":
                embed.set_footer(text=prefix + players[findplayer(user.id)].role.lower() + " [number] [number]")
            else:
                embed.set_footer(text=prefix + players[findplayer(user.id)].role.lower() + " [number]")

        else:
            if len(players) == 1:
                embed.set_footer(text=str(len(players)) + " player")
            else:
                embed.set_footer(text=str(len(players)) + " players")

        # embed.set_image(url="https://orig15.deviantart.net/1146/f/2017/048/8/3/brianne_by_ploopie-dazes2a.jpg")

        await chat.send(embed=embed)
    else:
        await chat.send("There are no players yet")


async def listallplayers(chat):

    if len(display_players) >= 1:
        list = ""

        title = "List of all players who where in the game"

        for x in range(0, len(display_players)):
            if findplayer(display_players[x].id) is None:
                list += "~~" + display_players[x].name + "~~\n"
            else:
                list += display_players[x].name + "\n"

        embed = discord.Embed(title=title, description=list[:-1], color=0x750000)

        await chat.send(embed=embed)
    else:
        await chat.send("There are no players atm")


async def listroles(chat):
    if len(display_roles) >= 1:
        list = ""

        title = "List of all the roles in the game"

        for x in range(0, len(display_roles)):
            list += display_roles[x] + "\n"

        embed = discord.Embed(title=title, description=list[:-1], color=0x750000)

        await chat.send(embed=embed)
    else:
        await chat.send("Nobody has joined the game")


async def clear(chat):
    await chat.purge(limit=100)


async def start(message):
    global running
    global channel
    global phase
    global roles

    running = True
    await message.channel.send("Starting the game...")

    channel = message.channel

    for x in range(0, len(players)):
        r = random.randint(0, len(roles) - 1)
        players[x].role = roles[r]
        roles.pop(r)

    await clear(channel)
    del roles

    phase = "first night"

    await channel.send(":first_quarter_moon_with_face:__**NIGHT TIME**__:last_quarter_moon_with_face:")

    for x in range(0, len(players)):
        user = bot.get_user(players[x].id)
        await user.send("\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n_ _\n" + "Your role is **" + players[x].role + "**")

        if players[x].role == "Seer":
            await listplayers(user, user, True)
            players[x].event = False
        elif players[x].role == "Werewolf":
            buddies = ""
            for y in range(0, len(players)):
                if players[y].role == "Werewolf":
                    buddies += players[y].name + "\n"

            embed = discord.Embed(title="Werewolves", description=buddies[:-1], color=0x750000)

            await user.send(embed=embed)
            await user.send("You can't do anything atm GO TO SLEEP")
            players[x].event = True
        elif players[x].role == "Bodyguard":
            await listplayers(user, user, True)
            players[x].event = False
        elif players[x].role == "Cupid":
            await listplayers(user, user, True)
            players[x].event = False
        else:
            await user.send("You can't do anything atm GO TO SLEEP")
            players[x].event = True


def restart():
    os.system(".\\Guild\\ShadowFall_Werewolf.py")


def checkevent():
    for x in range(0, len(players)):
        if not players[x].event:
            return False
    return True


async def kill(targetid, attacker):
    global trials_left

    if players[findplayer(targetid)].role == "Cursed" and attacker == "Werewolf":

        if attacker == "Werewolf":
            players[findplayer(targetid)].role = "Werewolf"
            bot.get_user(targetid).send("Your role is **Werewolf**")

            buddies = ""

            for y in range(0, len(players)):
                if players[y].role == "Werewolf":
                    buddies += players[y].name + "\n"

            embed = discord.Embed(title="Werewolf Buddies", description=buddies[:-1], color=0x750000)

            await bot.get_user(targetid).send(embed=embed)


    else:

        if attacker == "Werewolf":
            await channel.send("**" + players[findplayer(targetid)].name + "** was killed by werewolves last night")

        elif attacker == "lynch":
            await channel.send("Lynching **" + players[findplayer(targetid)].name + "**...")
            trials_left = trials
        elif attacker == "lover":
            await channel.send("**" + players[findplayer(targetid)].name + "** could not imagine a life with out their special one so they decided to end themselves")
        elif attacker == "Hunter":
            await channel.send("**" + players[findplayer(targetid)].name + "** is now lying on the ground with a bullet hole in their head")

        await asyncio.sleep(2)
        await channel.send("**" + players[findplayer(targetid)].name + "**'s role was **" + players[findplayer(targetid)].role + "**")

        if players[findplayer(targetid)].lover is not None:
            players[findplayer(players[findplayer(targetid)].lover)].lover = None
            await kill(players[findplayer(targetid)].lover, "lover")

        if players[findplayer(targetid)].role == "Tanner":
            await channel.send("**Tanner** won the game but the game goes on")

        if players[findplayer(targetid)].role == "Hunter":
            await channel.send("But before the Hunter was killed they quickly graped their gun, loaded it and pulled the trigger...")
            await asyncio.sleep(4)
            await changephase("hunter")
        else:
            players.pop(findplayer(targetid))


    await checkvictory()


async def changephase(newphase):
    global channel
    global phase
    global targets
    global player_on_trial
    global prev_phase


    await clear(channel)

    prev_phase = phase

    phase = newphase

    if newphase == "day":
        await channel.send(":sun_with_face:__**DAY TIME**__:sun_with_face:")

        if len(targets) > 0:
            r = random.randint(0, len(targets) - 1)
            if not players[findplayer(targets[r])].protected:
                await kill(players[findplayer(targets[r])].id, "Werewolf")
            targets = []

        await asyncio.sleep(day_talk_time)

        if phase == "day":
            await changephase("vote")

    elif newphase == "vote":
        dummy = bot.get_user(players[0].id)
        await channel.send(":thumbsdown:__**VOTING PHASE**__:thumbsup:")
        await listplayers(dummy, channel, False)

        for x in range(0, len(players)):
            players[x].event = False
            players[x].voted_for = None
            players[x].against = []
            players[x].protected = False

    elif newphase == "trial":
        await channel.send(":thumbsdown:__**TRIAL OF " + players[findplayer(player_on_trial)].name.upper() + "**__:thumbsup:")

        embed = discord.Embed(title="Trial", description=prefix + "vote yes - if you think **" + players[findplayer(player_on_trial)].name + "** is guilty\n" + prefix + "vote no - if you think **" + players[findplayer(player_on_trial)].name + "** is innocent", color=0x750000)

        await channel.send(embed=embed)

    elif newphase == "night":
        await channel.send(":first_quarter_moon_with_face:__**NIGHT TIME**__:last_quarter_moon_with_face:")

        for x in range(0, len(players)):
            user = bot.get_user(players[x].id)

            if players[x].role == "Seer":
                await listplayers(user, user, True)
                players[x].event = False
            elif players[x].role == "Werewolf":
                buddies = ""
                for y in range(0, len(players)):
                    if players[y].role == "Werewolf":
                        buddies += players[y].name + "\n"

                embed = discord.Embed(title="Werewolf Buddies", description=buddies[:-1], color=0x750000)

                await user.send(embed=embed)
                await listplayers(user, user, True)
                players[x].event = False
            elif players[x].role == "Bodyguard":
                await listplayers(user, user, True)
                players[x].event = False
            else:
                await user.send("You can't do anything atm GO TO SLEEP")
                players[x].event = True

    elif newphase == "hunter":
        dummy = bot.get_user(players[0].id)
        await channel.send(":bow_and_arrow:__**HUNTERS DILEMMA**__:gun:")
        await listplayers(dummy, channel, False)

        for x in range(0, len(players)):
            players[x].event = True
            players[x].protected = False


async def vote(user, target=None, trial=None):
    global channel
    global player_on_trial
    global trials_left

    if not players[findplayer(user.id)].event:

        if phase == "vote":
            if players[target].id != user.id:
                if players[findplayer(user.id)].voted_for is not None:
                    for x in range(0, len(players[findplayer(players[findplayer(user.id)].voted_for)].against)):
                        if players[findplayer(players[findplayer(user.id)].voted_for)].against[x] == players[findplayer(user.id)].id:
                            players[findplayer(players[findplayer(user.id)].voted_for)].against.pop(x)
                            break

                players[findplayer(user.id)].voted_for = players[target].id
                players[target].against.append(players[findplayer(user.id)].id)

                await channel.send("**" + players[findplayer(user.id)].name + "** has voted for **" + players[target].name + "** (" + str(len(players[target].against)) + " votes out of " + str(math.floor(len(players)/2)+1) + ")")

                if len(players[target].against) > len(players) / 2:
                    players[target].against = []
                    player_on_trial = players[target].id
                    players[target].event = True
                    await changephase("trial")

        elif phase == "trial":
            if trial:
                players[findplayer(player_on_trial)].against.append(players[findplayer(user.id)].id)
                await channel.send("**" + players[findplayer(user.id)].name + "** voted **Guilty**")
            else:
                await channel.send("**" + players[findplayer(user.id)].name + "** voted **Innocent**")

            players[findplayer(user.id)].event = True

            if checkevent():
                print("lets lynch this person ma boys")
                if len(players[findplayer(player_on_trial)].against) > (len(players) - 1) / 2:
                    await kill(player_on_trial, "lynch")

                    await asyncio.sleep(7)
                    await changephase("night")
                else:
                    trials_left = trials_left - 1
                    if trials_left >= 1:
                        await channel.send("Not enough voted guilty returning to the vote phase (" + str(trials_left) + " Trials left)")
                    else:
                        await channel.send("Not enough voted guilty (" + str(trials_left) + " Trials left)")

                    await asyncio.sleep(3)

                    if trials_left == 0:
                        trials_left = trials
                        await changephase("night")
                    else:
                        await changephase("vote")


async def checkvictory():
    global channel

    werewolves = 0
    town = 0
    lovers = 0

    for x in range(0, len(players)):
        if players[x].role == "Werewolf":
            werewolves += 1

        else:
            town += 1

        if players[x].lover is not None:
            lovers += 1


    if lovers == len(players):
        await channel.send("**Lovers** won the game")

        await asyncio.sleep(3)
        await clear(channel)
        restart()

    elif werewolves <= 0:
        await channel.send("**Town** won the game")

        await asyncio.sleep(3)
        await clear(channel)
        restart()

    elif town < 2 and len(players) <= 2:
        await channel.send("**Werewolves** won the game")

        await asyncio.sleep(3)
        await clear(channel)
        restart()


# Roles


async def seer(user, target):
    if players[target].id != user.id or not players[findplayer(user.id)].event:
        if players[target].role in seems_good:
            await user.send("**" + players[target].name + "** seems **good**")
        else:
            await user.send("**" + players[target].name + "** seems **evil**")

        players[findplayer(user.id)].event = True

        if checkevent():
            await changephase("day")


async def werewolf(user, target):
    global targets

    if players[target].id != user.id or not players[findplayer(user.id)].event and players[target].role != "Werewolf":
        print(user.name + " " + str(target))

        targets.append(players[target].id)

        for x in range(0, len(players)):
            if players[x].role == "Werewolf":
                friends = bot.get_user(players[x].id)
                await friends.send("**" + players[findplayer(user.id)].name + "** wants to kill **" + players[target].name + "**")

        players[findplayer(user.id)].event = True

        if checkevent():
            await changephase("day")


async def cupid(user, target1, target2):
    if not players[findplayer(user.id)].event and target1 != target2:

        players[target1].lover = players[target2].id
        players[target2].lover = players[target1].id

        for x in range(0, len(players)):
            if players[x].role == "Cupid" or players[x].lover is not None:
                lovers_team = bot.get_user(players[x].id)

                lovers = ""
                for y in range(0, len(players)):
                    if players[y].lover is not None:
                        lovers += players[y].name + "\n"

                embed = discord.Embed(title="Lovers ❤", description=lovers[:-1], color=0x750000)

                await lovers_team.send(embed=embed)

        players[findplayer(user.id)].event = True

        if checkevent():
            await changephase("day")


async def bodyguard(user, target):
    if players[target].id != user.id and not players[findplayer(user.id)].event and players[target].id != players[findplayer(user.id)].last_target:

        players[target].protected = True
        players[findplayer(user.id)].last_target = players[target].id

        await user.send("You have chosen to protect **" + players[target].name + "** this night")

        players[findplayer(user.id)].event = True

        if checkevent():
            await changephase("day")


async def hunter(user, target):
    global prev_phase
    
    if players[target].id != user.id:

        await user.send("The hunters gun was pointed towards **" + players[target].name + "**'s head when they pulled the trigger")

        await kill(players[target].id, "Hunter")

        players.pop(findplayer(user.id))

        if prev_phase == "trial":
            await changephase("night")
        else:
            await changephase(prev_phase)




# ignore this \/

bot.run(token)
