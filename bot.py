import discord
from discord.ext import commands, tasks
import requests
import asyncio
from collections import defaultdict
import os
import aiohttp
from discord import File
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='*', intents=intents)

def generate_price_embed(current_price, price_changes):
    embed = discord.Embed(
        title="SharkBee Price",
        description=f"The current price of SharkBee is ${current_price:.8f}",
        color=0x00ff00 if price_changes['h1'] >= 0 else 0xff0000
    )
    embed.add_field(
        name="1hr Change",
        value=f"{price_changes['h1']}%"
    )
    embed.add_field(
        name="6hr Change",
        value=f"{price_changes['h6']}%"
    )
    embed.add_field(
        name="24hr Change",
        value=f"{price_changes['h24']}%"
    )
    return embed

async def check_message_for_price(message):
    if 'sbee' in message.content.lower() and 'price' in message.content.lower():
        return True
    if 'sharkbee' in message.content.lower() and 'price' in message.content.lower():
        return True
    return False

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if await check_message_for_price(message): 
        url = 'https://api.dexscreener.com/latest/dex/pairs/ethereum/0xb74eE901c2B0A04D75d38f7f4722e8a848E613B9'
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            current_price = float(data['pairs'][0]['priceUsd'])
            price_changes = data['pairs'][0]['priceChange']
            embed = generate_price_embed(current_price, price_changes)
            sent_message = await message.channel.send(embed=embed) # Delete after 2 minutes
        else:
            embed = discord.Embed(
                title="Error",
                description="Unable to fetch the price for SharkBee.",
                color=0xff0000  # Red color
            )
            sent_message = await message.channel.send(embed=embed)
            await sent_message.delete(delay=120)  # Delete after 2 minutes

    await bot.process_commands(message)

@tasks.loop(minutes=5)
async def update_description():
    url = 'https://api.dexscreener.com/latest/dex/pairs/ethereum/0xb74eE901c2B0A04D75d38f7f4722e8a848E613B9'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        current_price = float(data['pairs'][0]['priceUsd'])
        price_changes = data['pairs'][0]['priceChange']
        new_description = f"Price: ${current_price:.8f} USD, 1 Hour Change: {price_changes['h1']}%, 6 Hours Change: {price_changes['h6']}%, 24 Hours Change: {price_changes['h24']}%"
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=new_description))
    else:
        print("Error fetching price data.")

async def ask_for_confirmation(ctx):
    await ctx.send("Are you sure you want to proceed? Send y to confirm or n to cancel.")

@bot.command(name='roleadd', help='Add a role to multiple users')
async def add_role_to_users(ctx, role_id: int, *members: discord.Member):
    # Check if the user invoking the command has one of the specified user IDs
    authorized_ids = [715141099370446878, 431573985671512076]  # Add more IDs if needed
    if ctx.author.id not in authorized_ids:
        await ctx.send("You are not authorized to use this command.")
        return
    
    role = ctx.guild.get_role(role_id)
    if role is None:
        await ctx.send("Role not found.")
        return
    
    # Ask for confirmation
    await ask_for_confirmation(ctx)
    try:
        # Wait for the user's response
        message = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=30)
        if message.content.lower() == 'y':
            added_users = []
            for member in members:
                if member is None:
                    await ctx.send(f"User not found: {member}.")
                    continue
                try:
                    await member.add_roles(role)
                    added_users.append(member.display_name)
                except discord.Forbidden:
                    await ctx.send(f"I don't have permission to add roles to {member.display_name}.")
                except discord.HTTPException:
                    await ctx.send(f"Failed to add role {role.name} to {member.display_name}.")
            
            if added_users:
                added_users_str = ", ".join(added_users)
                await ctx.send(f"Added role {role.name} to: {added_users_str}.")
            else:
                await ctx.send("No roles were added.")
        else:
            await ctx.send("Command denied.")
    except asyncio.TimeoutError:
        await ctx.send("Timed out. Command denied.")


@bot.command(name='roleremove', help='Remove a role from all members who have it')
async def remove_role_from_all(ctx, role_id: int):
    # Check if the user invoking the command has the necessary permissions
    authorized_ids = [715141099370446878, 1023589469850451998, 431573985671512076]  # Add more IDs if needed
    if ctx.author.id not in authorized_ids:
        await ctx.send("You are not authorized to use this command.")
        return
    
    role = ctx.guild.get_role(role_id)
    if role is None:
        await ctx.send("Role not found.")
        return
    
    # Get the number of members with the role
    members_with_role = [member for member in ctx.guild.members if role in member.roles]
    num_members = len(members_with_role)
    
    # Ask for confirmation with the number of users mentioned
    await ctx.send(f"Are you sure you want to remove {role.mention} from *{num_members}* users? Send y to confirm or n to cancel.")
    
    try:
        # Wait for the user's response
        message = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=30)
        if message.content.lower() == 'y':
            removed_users = []
            for member in members_with_role:
                if member is None:
                    await ctx.send(f"User not found: {member}.")
                    continue
                try:
                    await member.remove_roles(role)
                    removed_users.append(member.display_name)
                except discord.Forbidden:
                    await ctx.send(f"I don't have permission to remove roles from {member.display_name}.")
                except discord.HTTPException:
                    await ctx.send(f"Failed to remove role {role.name} from {member.display_name}.")
            
            if removed_users:
                removed_users_str = ", ".join(removed_users)
                await ctx.send(f"Removed role {role.name} from: {removed_users_str}.")
            else:
                await ctx.send("No roles were removed.")
        else:
            await ctx.send("Command denied.")
    except asyncio.TimeoutError:
        await ctx.send("Timed out. Command denied.")

@update_description.before_loop
async def before_update_description():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    update_description.start()




def create_embed(title, description, fields):
    embed = discord.Embed(title=title, description=description, color=0x00ff00)
    for name, value in fields.items():
        embed.add_field(name=name, value=value, inline=False)
    return embed
@bot.command(name='react')
async def react(ctx, channel_id: int, start_message_id: int, emoji: str):
    # Check if the author of the command is authorized
    allowed_user_ids = [715141099370446878, 431573985671512076, 1023589469850451998]
    if ctx.author.id not in allowed_user_ids:
        await ctx.send("You are not authorized to use this command.")
        return
    
    # Get the channel
    channel = bot.get_channel(channel_id)
    if channel is None:
        await ctx.send("Channel not found.")
        return
    
    try:
        start_message = await channel.fetch_message(start_message_id)
    except discord.Forbidden:
        await ctx.send("I do not have permission to access messages in this channel.")
        return
    except discord.NotFound:
        await ctx.send("Start message not found.")
        return
    
    # Initialize counters
    message_reactions = defaultdict(lambda: {"total": 0, "OG": 0, "Farcaster OG": 0, "Non OG": 0})
    og_role_id = 1216143763660079184
    farcaster_og_role_id = 1220126908516143104
    
    # Iterate over messages starting from the start message and count reactions
    async for message in channel.history(after=start_message, limit=None):
        for reaction in message.reactions:
            if str(reaction.emoji) == emoji:
                async for user in reaction.users():
                    member = ctx.guild.get_member(user.id)
                    if member:
                        roles = {role.id for role in member.roles}
                        if og_role_id in roles:
                            message_reactions[message.id]["OG"] += 1
                        elif farcaster_og_role_id in roles:
                            message_reactions[message.id]["Farcaster OG"] += 1
                        else:
                            message_reactions[message.id]["Non OG"] += 1
                message_reactions[message.id]["total"] += reaction.count

    # Add the start message separately
    for reaction in start_message.reactions:
        if str(reaction.emoji) == emoji:
            async for user in reaction.users():
                member = ctx.guild.get_member(user.id)
                if member:
                    roles = {role.id for role in member.roles}
                    if og_role_id in roles:
                        message_reactions[start_message.id]["OG"] += 1
                    elif farcaster_og_role_id in roles:
                        message_reactions[start_message.id]["Farcaster OG"] += 1
                    else:
                        message_reactions[start_message.id]["Non OG"] += 1
            message_reactions[start_message.id]["total"] += reaction.count

    # Create embed fields
    fields = {}
    highest_reactions = 0
    winning_message_id = None
    
    for message_id, counts in message_reactions.items():
        message_link = f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/{message_id}"
        fields[f"Message Id {message_id}"] = (f"[Message Link]({message_link})\n"
                                                f"Votes: {counts['total']}\n"
                                                f"Valid Votes: {counts['OG'] + counts['Farcaster OG'] - counts['Non OG']}\n")
        summed_reactions = counts['OG'] + counts['Farcaster OG']
        if summed_reactions > highest_reactions:
            highest_reactions = summed_reactions
            winning_message_id = message_id

    # Create the embed
    embed = create_embed("Reaction Summary", f"Here are the reaction counts for each message using the {emoji} emoji:", fields)
    
    if winning_message_id:
        winning_message_link = f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/{winning_message_id}"
        embed.add_field(name="Winner", value=f"The message with the highest summed OG reactions is [here]({winning_message_link}) with {highest_reactions} reactions.")

    await ctx.send(embed=embed)

@bot.command(name='comms', help='Show each command and how to use it in an embed')
async def comms(ctx):
    embed = discord.Embed(title="Bot Commands Help", description="Here are the available commands and their usage:", color=0x7289DA)
    
    # Add commands and their usage to the embed
    commands_info = {
        "*roleadd <role_id> <member1> <member2> ...*": "Add a role to multiple users.",
        "*roleremove <role_id>*": "Remove a role from all members who have it.",
        "*react <channel_id> <start_message_id> <emoji>*": "Summarize reactions in a channel.",
    }
    
    for command, description in commands_info.items():
        embed.add_field(name=command, value=description, inline=False)
    
    await ctx.send(embed=embed)
bot.run("YOUR_TOKEN")
