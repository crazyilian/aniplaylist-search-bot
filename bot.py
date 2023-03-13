from CachedSession import CachedSession
import telethon
import os
from AniPlaylistRequests import request_hit
from telethon.tl.custom import Button
import re
import urllib.parse
from ButtonDataManager import ButtonDataManager

bot = telethon.TelegramClient(
    'bot', int(os.getenv('API_ID')), os.getenv('API_HASH')
).start(bot_token=os.getenv('BOT_TOKEN'))
bot.parse_mode = 'html'

session = CachedSession(headers={'Referer': 'https://aniplaylist.com/'})

help_re = re.compile(r"^/(help|start)($|[\n @].*$)", re.DOTALL)
empty_link_re = re.compile(r'<a href="(\S*?)">\u200b</a>')

button_data_mgr = ButtonDataManager()


def encode_query(query):
    return 'https://aniplaylist.com/' + urllib.parse.quote(query)


def decode_query(url):
    return urllib.parse.unquote(url.removeprefix('https://aniplaylist.com/'))


def is_help(text):
    return re.match(help_re, text) is not None


def is_search(text):
    return not is_help(text)


def find_empty_link(text, suffix):
    urls = [m.group(1) for m in re.finditer(empty_link_re, text) if m]
    urls = [url for url in urls if url.endswith(suffix)]
    if len(urls) == 0:
        return None
    return urls[0]


def remove_empty_links(text):
    return ''.join(re.split(empty_link_re, text)[::2])


def get_result_data(text):
    data = {}
    for line in remove_empty_links(text).split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            if all(ord('a') <= ord(c) <= ord('z') or c == ' ' for c in key.lower()):
                data[key] = val
    return data


@bot.on(telethon.events.CallbackQuery(func=lambda e: button_data_mgr.check_nothing(e.data)))
async def callback_nothing(e):
    await e.answer()


@bot.on(telethon.events.CallbackQuery(func=lambda e: button_data_mgr.check_change_hit(e.data)))
async def callback_change_hit(e):
    n = button_data_mgr.decode(e.data)['data']
    msg = await e.get_message()
    url = find_empty_link(msg.text, '#aniplaylist-query').removesuffix('#aniplaylist-query')
    if not url:
        return
    query = decode_query(url)
    result = await get_search_result(query, n)
    answer = result['answer']
    buttons = result['buttons']
    hidden_query = result['hidden_query']
    if not answer:
        await msg.edit('No results found' + hidden_query, buttons=buttons, link_preview=False)
        return
    await msg.edit(answer + hidden_query, buttons=buttons, link_preview=True)


@bot.on(telethon.events.CallbackQuery(func=lambda e: button_data_mgr.check_preview(e.data)))
async def callback_preview(e):
    msg = await e.get_message()

    url = find_empty_link(msg.text, '#audio-preview')
    if not url:
        return
    data = get_result_data(msg.text)
    answer = "Preview of\n"
    answer += "\n".join(f"{key}: {data[key]}" for key in ("Title", "Anime", "Type") if data[key].removeprefix('N/A'))
    await e.respond(answer, file=url, supports_streaming=True)


def get_prev_next_buttons(n, total):
    if total <= 1:
        return []
    buttons = []
    n += 1
    if n > 1:
        buttons.append(Button.inline(f'{n - 1} ⬅️', data=button_data_mgr.change_hit(n - 2)))
    else:
        buttons.append(Button.inline(f'✖️', data=button_data_mgr.nothing()))
    if n == 1:
        buttons.append(Button.inline(f'{n} / {total}', data=button_data_mgr.nothing()))
    else:
        buttons.append(Button.inline(f'{n} / {total}', data=button_data_mgr.change_hit(0)))
    if n < total:
        buttons.append(Button.inline(f'➡️ {n + 1}', data=button_data_mgr.change_hit(n)))
    else:
        buttons.append(Button.inline(f'✖️', data=button_data_mgr.nothing()))
    return buttons


async def get_search_result(query, n):
    result = await request_hit(query, n, session)
    hit = result['hit']
    total_hits = result['total']
    prev_next_buttons = get_prev_next_buttons(n, total_hits)
    hidden_query = f'<a href="{encode_query(query)}#aniplaylist-query">\u200b</a>'
    if hit is None:
        return {
            'answer': None,
            'buttons': [prev_next_buttons],
            'hidden_query': hidden_query
        }

    link = hit["link"] or ""
    title = hit["title"] or "N/A"
    artists = [f'<a href="{artist["link"] or ""}">{artist["name"] or "N/A"}</a>' for artist in hit["artists"]]
    anime_link = (hit["anime"] or {}).get("url") or ""
    anime_title = hit["anime_title"] or "N/A"
    song_type = hit["song_type"] or "N/A"
    preview_link = hit["preview_link"]

    answer = f"""
<a href="{anime_link}">\u200b</a>\
Title: <a href="{link}">{title}</a>
Artists: {" & ".join(artists or ["N/A"])}
Anime: <a href="{anime_link}">{anime_title}</a>
Type: {song_type}
        """.strip()
    buttons = []
    if prev_next_buttons:
        buttons.append(prev_next_buttons)
    if preview_link:
        buttons.append([Button.inline('Audio preview', data=button_data_mgr.preview())])
        answer += f'<a href="{preview_link}#audio-preview">\u200b</a>'
    return {
        'answer': answer,
        'buttons': buttons,
        'hidden_query': hidden_query
    }


@bot.on(telethon.events.NewMessage(func=lambda e: is_search(e.raw_text)))
async def handler_search(e):
    result = await get_search_result(e.raw_text, 0)
    answer = result['answer']
    buttons = result['buttons']
    hidden_query = result['hidden_query']
    if not answer:
        await e.respond('No results found' + hidden_query, link_preview=False)
        return
    if not buttons:
        buttons = None
    await e.respond(answer + hidden_query, buttons=buttons, link_preview=True)


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

👉 Switch between results
- If more than one result is found, I will add next/previous buttons to jump between results.
- Pressing the middle button will take you back to the first result.

👉 Audio Preview
- If an audio preview is available, I'll add a button to listen to it.

👉 Help
- To see this message again, send <code>/help</code>

Good searching!
""".strip())


bot.run_until_disconnected()
