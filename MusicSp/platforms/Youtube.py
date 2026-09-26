import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch, Playlist
import aiohttp
import config

API_URL = config.API_URL or os.environ.get("MusicSp_API_URL", "https://apisparrow.site")
if API_URL:
    API_URL = API_URL.rstrip("/")
API_KEY = config.API_KEY or os.environ.get("MusicSp_API_KEY", None)

DOWNLOAD_DIR = "downloads"


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


async def download_song(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    if not API_URL:
        return None

    params = {"url": video_id, "type": "audio"}
    if API_KEY:
        params["api_key"] = API_KEY

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=180)
            ) as resp:
                if resp.status != 200:
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


async def download_video(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    if not API_URL:
        return None

    params = {"url": video_id, "type": "video"}
    if API_KEY:
        params["api_key"] = API_KEY

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        res = await results.next()
        if not res or not res.get("result"):
            return "", "0:00", 0, "", ""
        for result in res["result"]:
            title = result.get("title", "")
            duration_min = result.get("duration", "0:00")
            thumbnails = result.get("thumbnails", [])
            thumbnail = thumbnails[0]["url"].split("?")[0] if thumbnails else ""
            vidid = result.get("id", "")
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        res = await results.next()
        if res and res.get("result"):
            for result in res["result"]:
                return result.get("title", "")
        return ""

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        res = await results.next()
        if res and res.get("result"):
            for result in res["result"]:
                return result.get("duration", "0:00")
        return "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        res = await results.next()
        if res and res.get("result"):
            for result in res["result"]:
                thumbnails = result.get("thumbnails", [])
                return thumbnails[0]["url"].split("?")[0] if thumbnails else ""
        return ""

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            plist = await Playlist.get(link)
        except Exception:
            return []
        videos = plist.get("videos") or []
        ids = []
        for data in videos[:limit]:
            if not data:
                continue
            vid = data.get("id")
            if not vid:
                continue
            ids.append(vid)
        return ids

    async def _innertube_request(self, endpoint: str, payload: dict):
        api_key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        timeout = aiohttp.ClientTimeout(total=15)
        last_error = None

        # Retry transient failures and use more than one YouTube endpoint.
        for attempt in range(3):
            hosts = ("www.youtube.com", "m.youtube.com") if attempt == 0 else ("m.youtube.com", "www.youtube.com")
            for host in hosts:
                try:
                    url = f"https://{host}/youtubei/v1/{endpoint}?key={api_key}"
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(url, json=payload, headers=headers) as resp:
                            if resp.status != 200:
                                body = await resp.text()
                                raise RuntimeError(
                                    f"InnerTube {endpoint} HTTP {resp.status}: {body[:160]}"
                                )
                            return await resp.json(content_type=None)
                except Exception as e:
                    last_error = e
                    if attempt < 2:
                        await asyncio.sleep(0.7 * (attempt + 1))

        raise last_error or RuntimeError(f"InnerTube {endpoint} request failed")

    @staticmethod
    def _valid_track(details):
        if not isinstance(details, dict):
            return False
        title = str(details.get("title") or "").strip()
        vidid = str(details.get("vidid") or "").strip()
        link = str(details.get("link") or "").strip()
        return bool(title and re.fullmatch(r"[A-Za-z0-9_-]{11}", vidid) and link)

    async def _innertube_track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        match = re.search(
            r"(?:v=|youtu\.be/|youtube\.com/(?:embed/|shorts/|live/))([A-Za-z0-9_-]{11})",
            link,
        )
        if not match:
            return None

        vidid = match.group(1)
        clients = [
            {
                "clientName": "WEB",
                "clientVersion": "2.20260708.00.00",
            },
            {
                "clientName": "MWEB",
                "clientVersion": "2.20260708.05.00",
            },
            {
                "clientName": "ANDROID",
                "clientVersion": "21.26.364",
                "androidSdkVersion": 30,
                "userAgent": "com.google.android.youtube/21.26.364 (Linux; U; Android 11) gzip",
                "osName": "Android",
                "osVersion": "11",
            },
        ]

        last_error = None
        for client in clients:
            try:
                payload = {
                    "context": {
                        "client": {
                            **client,
                        }
                    },
                    "videoId": vidid,
                }
                data = await self._innertube_request("player", payload)
                details = data.get("videoDetails") or {}
                title = str(details.get("title") or "").strip()
                if not title:
                    status = (data.get("playabilityStatus") or {}).get("status", "NO_TITLE")
                    raise RuntimeError(f"player {client['clientName']} returned {status}")

                duration_sec = int(details.get("lengthSeconds", 0) or 0)
                duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                thumbs = ((details.get("thumbnail") or {}).get("thumbnails") or [])
                thumbnail = thumbs[-1].get("url", "").split("?")[0] if thumbs else ""
                result = {
                    "title": title,
                    "link": self.base + vidid,
                    "vidid": vidid,
                    "duration_min": duration_min,
                    "thumb": thumbnail,
                }
                if self._valid_track(result):
                    return result
            except Exception as e:
                last_error = e
                print(
                    f"[YOUTUBE][PLAYER] client={client['clientName']} failed: {e}",
                    flush=True,
                )

        if last_error:
            raise last_error
        return None

    async def _innertube_search(self, query: str):
        clients = [
            ("WEB", "2.20260708.00.00"),
            ("MWEB", "2.20260708.05.00"),
        ]
        last_error = None

        for client_name, client_version in clients:
            for use_params in (True, False):
                try:
                    client = {
                        "clientName": client_name,
                        "clientVersion": client_version,
                        "hl": "en-IN",
                        "gl": "IN",
                    }
                    payload = {
                        "context": {"client": client},
                        "query": query,
                    }
                    if use_params:
                        payload["params"] = "CAASAhAB"

                    data = await self._innertube_request("search", payload)
                    tracks = []

                    def walk(node):
                        if tracks:
                            return
                        if isinstance(node, dict):
                            renderer = node.get("videoRenderer")
                            if isinstance(renderer, dict):
                                vidid = renderer.get("videoId", "")
                                title_data = renderer.get("title") or {}
                                runs = title_data.get("runs") or []
                                title = runs[0].get("text", "") if runs else ""
                                if not title:
                                    title = title_data.get("simpleText", "")
                                if vidid and title:
                                    length = (
                                        (renderer.get("lengthText") or {}).get("simpleText")
                                        or "0:00"
                                    )
                                    thumbs = (
                                        (renderer.get("thumbnail") or {}).get("thumbnails")
                                        or []
                                    )
                                    thumb = (
                                        thumbs[-1].get("url", "").split("?")[0]
                                        if thumbs
                                        else ""
                                    )
                                    tracks.append(
                                        {
                                            "title": title,
                                            "link": self.base + vidid,
                                            "vidid": vidid,
                                            "duration_min": length,
                                            "thumb": thumb,
                                        }
                                    )
                                    return
                            for value in node.values():
                                walk(value)
                        elif isinstance(node, list):
                            for value in node:
                                walk(value)
                                if tracks:
                                    return

                    walk(data)
                    if tracks and self._valid_track(tracks[0]):
                        return tracks[0]
                    raise RuntimeError(
                        f"search {client_name} returned no valid video for {query!r}"
                    )
                except Exception as e:
                    last_error = e
                    print(
                        f"[YOUTUBE][SEARCH] client={client_name} params={use_params} failed: {e}",
                        flush=True,
                    )

        if last_error:
            raise last_error
        return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        # 1. Direct video URL: resolve metadata through several InnerTube clients.
        try:
            direct = await self._innertube_track(link)
            if direct and self._valid_track(direct):
                return direct, direct["vidid"]
        except Exception as e:
            print(f"[YOUTUBE][TRACK] direct resolution failed: {e}", flush=True)

        # 2. Search: retry with alternate InnerTube clients/request shapes.
        try:
            searched = await self._innertube_search(link)
            if searched and self._valid_track(searched):
                return searched, searched["vidid"]
        except Exception as e:
            print(f"[YOUTUBE][TRACK] InnerTube search failed: {e}", flush=True)

        # 3. py-yt fallback with its own retries.
        last_error = None
        for attempt in range(2):
            try:
                results = VideosSearch(link, limit=1)
                res = await results.next()
                if res and res.get("result"):
                    result = res["result"][0]
                    details = {
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "vidid": result.get("id", ""),
                        "duration_min": result.get("duration", "0:00"),
                        "thumb": (
                            (result.get("thumbnails") or [{}])[0]
                            .get("url", "")
                            .split("?")[0]
                        ),
                    }
                    if self._valid_track(details):
                        return details, details["vidid"]
                    raise RuntimeError("py-yt returned an invalid video result")
                raise RuntimeError("py-yt returned no results")
            except Exception as e:
                last_error = e
                print(f"[YOUTUBE][PY-YT] attempt={attempt + 1} failed: {e}", flush=True)
                if attempt == 0:
                    await asyncio.sleep(1.0)

        if last_error:
            print(f"[YOUTUBE][TRACK] all resolution methods failed: {last_error}", flush=True)
        return {}, ""

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except Exception:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        res = await a.next()
        result = res.get("result") if res else []
        if not result or query_type >= len(result):
            return "", "0:00", "", ""
        title = result[query_type].get("title", "")
        duration_min = result[query_type].get("duration", "0:00")
        vidid = result[query_type].get("id", "")
        thumbnails = result[query_type].get("thumbnails", [])
        thumbnail = thumbnails[0]["url"].split("?")[0] if thumbnails else ""
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            if downloaded_file:
                return downloaded_file, True
            return None, False
        except Exception:
            return None, False


YouTube = YouTubeAPI()
