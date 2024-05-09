import os
import discord
import requests
import whois
import json
import random
import asyncio
import string
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("TOKEN")
INVITES_CHANNEL_ID = os.getenv("INVITES_CHANNEL_ID")
INVITES_FORUM_CHANNEL_ID = os.getenv("INVITES_FORUM_CHANNEL_ID")
URL_CHANNEL_ID = os.getenv("URL_CHANNEL_ID")
URL_FORUM_CHANNEL_ID = os.getenv("URL_FORUM_CHANNEL_ID")
USER_ID_CHANNEL_ID = os.getenv("USER_ID_CHANNEL_ID")
USER_FORUM_CHANNEL_ID = os.getenv("USER_FORUM_CHANNEL_ID")

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Discord's API"))
    print(f'Bot is ready! Monitoring channels for invites and URLs.')


@client.event
async def on_message(message):
    if message.channel.id == int(INVITES_CHANNEL_ID):
        await process_invites(message)
    elif message.channel.id == int(URL_CHANNEL_ID):
        await process_urls(message)
    elif message.channel.id == int(USER_ID_CHANNEL_ID):
        await process_user_ids(message)


def extract_user_ids(content):
    user_ids = []
    for word in content.split():
        if word.startswith('`') and word.endswith('`'):
            potential_id = word.strip('`')
            if potential_id.isdigit():
                user_ids.append(potential_id)
    return user_ids


async def process_user_ids(message):
    print(f'Message received in user ID channel: {message.content}')
    user_ids = extract_user_ids(message.content)
    for user_id in user_ids:
        print(f'Extracted user ID: {user_id}')
        user_info = get_user_info(user_id)
        if user_info:
            print(f'User information retrieved for user: {user_id}')
            existing_post = await check_existing_user_post(user_id)
            if not existing_post:
                await create_user_post(message, user_info, user_id)
            else:
                await message.channel.send(f'A post for this user already exists: {existing_post.jump_url}')
        else:
            print(f'Failed to retrieve user information for user ID: {user_id}')


def get_user_info(user_id):
    url = f'https://discord.com/api/v9/users/{user_id}'
    headers = {'Authorization': f'Bot {TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


async def check_existing_user_post(user_id):
    forum_channel = client.get_channel(int(USER_FORUM_CHANNEL_ID))
    if forum_channel:
        for thread in forum_channel.threads:
            thread_message = await thread.fetch_message(thread.id)
            if f'[USER-' in thread.name and f'**User ID**: {user_id}' in thread_message.content:
                return thread_message
    return None


async def create_user_post(message, user_info, user_id):
    forum_channel = client.get_channel(int(USER_FORUM_CHANNEL_ID))
    if forum_channel:
        random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        title = f'[USER-{random_code}] - {message.created_at.strftime("%m/%d/%Y")}'
        message_content = format_user_info(user_info, user_id, message.author.mention)
        thread = await forum_channel.create_thread(name=title, content=message_content, auto_archive_duration=60)
        return thread
    else:
        print('Failed to find the user forum channel.')
        return None


def format_user_info(user_info, user_id, author_mention):
    message = f"**User ID**: {user_id}\n"
    message += f"**Username**: {user_info['username']}\n"
    # Global Name
    global_name = user_info.get('global_name', 'None')
    message += f"**Global Name**: {global_name}\n"
    message += f"**Discriminator**: {user_info['discriminator']}\n"
    # Avatar
    if 'avatar' in user_info:
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{user_info['avatar']}?size=1024"
        message += f"**Avatar URL**: {avatar_url}\n"
    else:
        message += "**Avatar URL**: None\n"
    # Banner
    if 'banner' in user_info:
        banner_url = f"https://cdn.discordapp.com/banners/{user_id}/{user_info['banner']}?size=1024"
        message += f"**Banner URL**: {banner_url}\n"
    else:
        message += "**Banner URL**: None\n"
    # Avatar Decoration
    if 'avatar_decoration' in user_info:
        avatar_decoration_url = f"https://cdn.discordapp.com/avatars/{user_id}/{user_info['avatar_decoration']}?size=1024"
        message += f"**Avatar Decoration URL**: {avatar_decoration_url}\n"
    else:
        message += "**Avatar Decoration URL**: None\n"
    # Banner Color
    banner_color = user_info.get('banner_color', 'None')
    message += f"**Banner Color**: {banner_color}\n"
    # Accent Color
    accent_color = user_info.get('accent_color', 'None')
    message += f"**Accent Color**: {accent_color}\n"
    # Profile Colors
    profile_colors = user_info.get('profile_colors', {})
    message += "**Profile Colors**:\n"
    for color_name, color_value in profile_colors.items():
        message += f"- {color_name.replace('_', ' ').title()}: {color_value}\n"
    # Flags
    flags = user_info.get('flags', 0)
    message += f"**Flags**: {flags}\n"
    message += parse_user_flags(flags)
    # Public Flags
    public_flags = user_info.get('public_flags', 0)
    message += f"**Public Flags**: {public_flags}\n"
    message += parse_user_flags(public_flags, is_public=True)
    # Premium Type
    premium_type = user_info.get('premium_type', 0)
    message += f"**Premium Type**: {get_premium_type_name(premium_type)}\n"
    # MFA Enabled
    mfa_enabled = user_info.get('mfa_enabled', False)
    message += f"**MFA Enabled**: {mfa_enabled}\n"
    # System
    is_system = user_info.get('system', False)
    message += f"**System**: {is_system}\n"
    # Verification
    message += f"**Verified**: {user_info.get('verified', False)}\n"
    # Email
    message += f"**Email**: {user_info.get('email', 'None')}\n"
    # Clan
    clan = user_info.get('clan', 'None')
    message += f"**Clan**: {clan}\n"
    message += f"\n**Report started by**: {author_mention}"
    # Bot
    is_bot = user_info.get('bot', False)
    message += f"**Bot**: {is_bot}\n"

    return message


def parse_user_flags(flags, is_public=False):
    flag_descriptions = ""
    flag_values = {
        1 << 0: ("STAFF", "Discord Employee"),
        1 << 1: ("PARTNER", "Partnered Server Owner"),
        1 << 2: ("HYPESQUAD", "HypeSquad Events Member"),
        1 << 3: ("BUG_HUNTER_LEVEL_1", "Bug Hunter Level 1"),
        1 << 6: ("HYPESQUAD_ONLINE_HOUSE_1", "House Bravery Member"),
        1 << 7: ("HYPESQUAD_ONLINE_HOUSE_2", "House Brilliance Member"),
        1 << 8: ("HYPESQUAD_ONLINE_HOUSE_3", "House Balance Member"),
        1 << 9: ("PREMIUM_EARLY_SUPPORTER", "Early Nitro Supporter"),
        1 << 10: ("TEAM_PSEUDO_USER", "User is a team"),
        1 << 14: ("BUG_HUNTER_LEVEL_2", "Bug Hunter Level 2"),
        1 << 16: ("VERIFIED_BOT", "Verified Bot"),
        1 << 17: ("VERIFIED_DEVELOPER", "Early Verified Bot Developer"),
        1 << 18: ("CERTIFIED_MODERATOR", "Moderator Programs Alumni"),
        1 << 19: ("BOT_HTTP_INTERACTIONS", "Bot uses only HTTP interactions and is shown in the online member list"),
        1 << 22: ("ACTIVE_DEVELOPER", "User is an Active Developer"),
    }

    for flag_value, (flag_name, flag_description) in flag_values.items():
        if is_public and flag_name in ["PREMIUM_EARLY_SUPPORTER", "TEAM_PSEUDO_USER", "VERIFIED_DEVELOPER",
                                       "CERTIFIED_MODERATOR", "BOT_HTTP_INTERACTIONS"]:
            continue
        if flags & flag_value:
            flag_descriptions += f"- {flag_name}: {flag_description}\n"
    return flag_descriptions


def get_premium_type_name(premium_type):
    premium_type_names = {
        0: "None",
        1: "Nitro Classic",
        2: "Nitro",
        3: "Nitro Basic"
    }
    return premium_type_names.get(premium_type, "Unknown")


async def process_invites(message):
    print(f'Message received in invite channel: {message.content}')
    invite_links = extract_invite_links(message.content)
    for link in invite_links:
        invite_code = extract_invite_code(link)
        if invite_code:
            print(f'Extracted invite code: {invite_code}')
            invite_info = get_invite_info(invite_code)
            if invite_info:
                guild_id = invite_info['guild']['id']
                print(f'Invite information retrieved for server: {guild_id}')
                existing_post = await check_existing_post(guild_id)
                if not existing_post:
                    await create_invite_post(message, invite_info, link)
                else:
                    await message.channel.send(f'A post for this server already exists: {existing_post.jump_url}')
            else:
                print(f'Failed to retrieve invite information for invite code: {invite_code}')
        else:
            print(f'Invalid invite link: {link}')


async def check_existing_url_post(url):
    forum_channel = client.get_channel(int(URL_FORUM_CHANNEL_ID))
    if forum_channel:
        for thread in forum_channel.threads:
            thread_message = await thread.fetch_message(thread.id)
            if f'**URL**: `{url}`' in thread_message.content:
                return thread_message
    return None


async def process_urls(message):
    print(f'Message received in URL channel: {message.content}')
    urls = extract_urls(message.content)
    for url in urls:
        url_info = get_url_info(url)
        if url_info:
            existing_post = await check_existing_url_post(url)
            if not existing_post:
                await create_url_post(message, url, url_info)
            else:
                await message.channel.send(f'A post for this URL already exists: {existing_post.jump_url}')
        else:
            print(f'Failed to retrieve information for URL: {url}')


def extract_invite_links(content):
    links = []
    for word in content.split():
        if word.startswith('`') and word.endswith('`'):
            potential_link = word.strip('`')
            if potential_link.startswith(('https://discord.gg/', 'https://discord.com/invite/')):
                links.append(potential_link)
    return links


def extract_urls(content):
    urls = []
    for word in content.split():
        if word.startswith('`') and word.endswith('`'):
            potential_url = word.strip('`')
            if potential_url.startswith('http://') or potential_url.startswith('https://'):
                urls.append(potential_url)
    return urls


def extract_invite_code(invite_link):
    try:
        invite_code = invite_link.split('/')[-1]
        return invite_code
    except:
        return None


def get_invite_info(invite_code):
    url = f'https://discord.com/api/v9/invites/{invite_code}'
    headers = {'Authorization': f'Bot {TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


async def check_existing_post(guild_id):
    forum_channel = client.get_channel(int(INVITES_FORUM_CHANNEL_ID))
    if forum_channel:
        for thread in forum_channel.threads:
            thread_message = await thread.fetch_message(thread.id)
            if f'[SERVER-' in thread.name and f'**Server ID**: {guild_id}' in thread_message.content:
                return thread_message
    return None


async def create_invite_post(message, invite_info, invite_link):
    forum_channel = client.get_channel(int(INVITES_FORUM_CHANNEL_ID))
    if forum_channel:
        random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        title = f'[SERVER-{random_code}] - {message.created_at.strftime("%m/%d/%Y")}'
        message_content = format_invite_info(invite_info, invite_link, message.author.mention)
        thread = await forum_channel.create_thread(name=title, content=message_content, auto_archive_duration=60)
        return thread
    else:
        print('Failed to find the forum channel.')
        return None


def format_invite_info(invite_info, invite_link, author_mention):
    guild = invite_info['guild']
    guild_id = guild['id']
    icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{guild.get('icon', 'None')}?size=1024" if guild.get('banner') else "None"
    splash_url = f"https://cdn.discordapp.com/splashes/{guild_id}/{guild.get('splash', 'None')}?size=1024" if guild.get('splash') else "None"
    banner_url = f"https://cdn.discordapp.com/banners/{guild_id}/{guild.get('banner', 'None')}?size=1024" if guild.get('banner') else "None"

    inviter = invite_info.get('inviter', {'username': 'UNKNOWN', 'discriminator': '0000', 'avatar': None, 'banner_color': 'UNKNOWN', 'flags': 'UNKNOWN', 'public_flags': 'UNKNOWN', 'global_name': 'UNKNOWN', 'clan': 'UNKNOWN'})
    inviter_username = inviter['username']
    inviter_discriminator = inviter['discriminator']
    inviter_avatar = f"https://cdn.discordapp.com/avatars/{inviter['id']}/{inviter.get('avatar', 'None')}?size=1024" if inviter.get('avatar') else "UNKNOWN"
    inviter_banner_color = inviter['banner_color']
    inviter_flags = inviter['flags']
    inviter_public_flags = inviter['public_flags']
    inviter_global_name = inviter['global_name']
    inviter_clan = inviter['clan']

    message = f"**Server Name**: {guild['name']}\n"
    message += f"**Server ID**: {guild_id}\n"
    message += f"**Channel ID**: {invite_info['channel']['id']}\n"
    message += f"**Channel Type**: {invite_info['channel']['type']}\n"
    message += f"**Channel Name**: {invite_info['channel']['name']}\n"
    message += f"**Server Description**: {guild['description']}\n"
    message += f"**Verification Level**: {guild['verification_level']}\n"
    message += f"**Invite Link**: `{invite_link}`\n\n"

    message += f"**Premium Subscription Count**: {guild['premium_subscription_count']}\n"
    message += f"**Vanity URL Code**: {guild['vanity_url_code']}\n"
    message += f"**NSFW**: {guild['nsfw']}\n"
    message += f"**NSFW Level**: {guild['nsfw_level']}\n\n"

    message += f"**Icon URL**: {icon_url}\n"
    message += f"**Splash URL**: {splash_url}\n"
    message += f"**Banner URL**: {banner_url}\n\n"

    message += "\n**Inviter Details**:\n"
    message += f"- Username: {inviter_username}#{inviter_discriminator}\n"
    message += f"- Avatar: {inviter_avatar}\n"
    message += f"- Banner Color: {inviter_banner_color}\n"
    message += f"- Flags: {inviter_flags}\n"
    message += f"- Public Flags: {inviter_public_flags}\n"
    message += f"- Global Name: {inviter_global_name}\n"
    message += f"- Clan: {inviter_clan}\n\n"

    message += f"**Server Features**:\n"
    for feature in guild['features']:
        message += f"- {feature.replace('_', ' ').title()}\n"

    message += f"\n**Report started by**: {author_mention}\n"

    return message


def get_url_info(url):
    try:
        if url.startswith('http://') or url.startswith('https://'):
            if url.startswith('http://'):
                url = 'https://' + url[7:]  # Add https:// if missing
            response = whois.whois(url)
            ip_address = response.get('query', url.split('/')[2])
            ip_info = get_ip_info(ip_address)
            return {'whois': response, 'ip_info': ip_info}
    except Exception as e:
        print(f'Error fetching URL info: {e}')
    return None


def get_ip_info(ip_address):
    try:
        url = f'http://ip-api.com/json/{ip_address}?fields=status,message,continent,continentCode,country,countryCode,' \
              f'region,regionName,city,district,zip,lat,lon,timezone,offset,isp,org,as,asname,reverse,mobile,proxy,' \
              f'hosting,query'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f'Error fetching IP info: {e}')
    return None


async def create_url_post(message, url, url_info):
    forum_channel = client.get_channel(int(URL_FORUM_CHANNEL_ID))
    if forum_channel:
        random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        title = f'[URL-{random_code}] - {message.created_at.strftime("%m/%d/%Y")}'
        message_content = format_url_info(url, url_info, message.author.mention)
        thread = await forum_channel.create_thread(name=title, content=message_content, auto_archive_duration=60)
        return thread
    else:
        print('Failed to find the URL forum channel.')
        return None


def format_url_info(url, url_info, author_mention):
    whois_info = url_info['whois']
    ip_info = url_info['ip_info']

    # Output
    message = f"## Detailed Scan:\n"
    message += f"**URL**: `{url}`\n"
    message += f"**IP**: {ip_info.get('query', 'None')}\n"
    message += f"**Domain Name**: {whois_info.get('domain_name', 'None')}\n"
    message += f"**Registrar**: {whois_info.get('registrar', 'None')}\n"
    message += f"**Creation Date**: {whois_info.get('creation_date', 'None')}\n"
    message += f"**Expiration Date**: {whois_info.get('expiration_date', 'None')}\n"
    message += f"**Name Servers**: {', '.join(whois_info.get('name_servers', ['None']))}\n"
    message += f"**Status**: {whois_info.get('status', 'None')}\n"
    message += f"**ISP**: {ip_info.get('isp', 'None')}\n"
    message += f"**Organization**: {ip_info.get('org', 'None')}\n"
    message += f"**AS**: {ip_info.get('as', 'None')}\n"
    message += f"**AS Name**: {ip_info.get('asname', 'None')}\n"
    message += f"**Continent**: {ip_info.get('continent', 'None')}\n"
    message += f"**Country**: {ip_info.get('country', 'None')}\n"
    message += f"**City**: {ip_info.get('city', 'None')}\n"
    message += f"**Reverse DNS**: {ip_info.get('reverse', 'None')}\n"
    message += f"**Mobile**: {ip_info.get('mobile', 'None')}\n"
    message += f"**Proxy**: {ip_info.get('proxy', 'None')}\n"
    message += f"**Hosting**: {ip_info.get('hosting', 'None')}\n"

    message += f"\n**Report started by**: {author_mention}"

    return message


client.run(TOKEN)
