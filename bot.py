import aiohttp
import telethon
import os
from queries import request_aniplaylist
from telethon.tl.custom import Button
import re

bot = telethon.TelegramClient(
    'bot', int(os.getenv('API_ID')), os.getenv('API_HASH')
).start(bot_token=os.getenv('BOT_TOKEN'))
bot.parse_mode = 'html'

session = aiohttp.ClientSession(headers={'Referer': 'https://aniplaylist.com/'})

help_re = re.compile(r"^/(help|start)($|[\n @].*$)", re.DOTALL)
empty_link_re = re.compile(r'<a href="(\S*?)">\u200b</a>')


def is_help(text):
    return re.match(help_re, text) is not None


def is_search(text):
    return not is_help(text)


@bot.on(telethon.events.CallbackQuery())
async def callback(e):
    msg = await e.get_message()

    empty_links = list(re.finditer(empty_link_re, msg.text))
    if len(empty_links) == 0:
        return
    url = empty_links[-1].group(1)
    if not url.endswith('#audio-preview'):
        return

    data = {}

    for line in ''.join(re.split(empty_link_re, msg.text)[::2]).split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            if all(ord('a') <= ord(c) <= ord('z') for c in key.lower()):
                data[key] = val

    answer = "Preview of\n"
    answer += "\n".join(f"{key}: {data[key]}" for key in ("Title", "Anime") if data[key].removeprefix('N/A'))
    await e.respond(answer, file=url, supports_streaming=True)


@bot.on(telethon.events.NewMessage(func=lambda e: is_search(e.raw_text)))
async def handler_search(e):
    text = e.raw_text
    results = await request_aniplaylist(text, session, hit_limit=1)
    if len(results) == 0:
        await e.respond('No results found')
        return
    result = results[0]
    if (result["anime"] or {}).get('match', 0) < 0.7:
        result["anime"] = None
    link = result["link"] or ""
    title = result["title"] or "N/A"
    artists = [f'<a href="{artist["link"] or ""}">{artist["name"] or "N/A"}</a>' for artist in result["artists"]]
    anime_link = (result["anime"] or {}).get("url") or ""
    anime_title = result["anime_title"] or "N/A"
    song_type = result["song_type"] or "N/A"
    preview_link = result["preview_link"]
    answer = f"""
<a href="{anime_link}">\u200b</a>\
Title: <a href="{link}">{title}</a>
Artists: {" & ".join(artists or ["N/A"])}
Anime: <a href="{anime_link}">{anime_title}</a>
Type: {song_type}
    """.strip()
    buttons = None
    if preview_link:
        buttons = [Button.inline('Audio preview')]
        answer += f'<a href="{preview_link}#audio-preview">\u200b</a>'
    await e.respond(answer, buttons=buttons)


@bot.on(telethon.events.NewMessage(func=lambda e: is_help(e.raw_text)))
async def handler_help(e):
    await e.respond("""
This is the unofficial search bot for AniPlaylist.com.

👉  Queries
- Send me a text query and I'll try to find the opening/ending by anime or vice versa. 
- If I found something wrong, try refining the query (like adding "opening 1").
- Also you can send me Spotify/Apple Music audio link.

👉 Results
- On each query I'll send you best search result from AniPlaylist.
- Also I'll search for found anime on MyAnimeList.net.
- I'll add Spotify links to the track/playlist and artists. 
- If Spotify isn't available, I'll try to find Apple Music links.

👉 Audio Preview
- If an audio preview is available, I'll add a button to listen to it.

👉 Help
- To see this message again, send <code>/help</code>

Good searching!
""".strip())


bot.run_until_disconnected()
