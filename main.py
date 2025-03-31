from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp
import asyncio

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Initialize YTMusic API
ytmusic = YTMusic()

# Function to fetch songs (for search & onload)
async def fetch_songs(q: str):
    search_results = ytmusic.search(q, filter="songs")
    songs = []
    
    for result in search_results:
        if "videoId" in result:
            songs.append({
                "title": result["title"],
                "artist": result["artists"][0]["name"] if "artists" in result else "Unknown",
                "videoId": result["videoId"],
                "thumbnail": result["thumbnails"][-1]["url"] if "thumbnails" in result else None
            })
    
    return songs

# Onload API (Default Song List)
@app.get("/onload")
async def onload_songs():
    return await fetch_songs("Tamil songs 2025")

# Search API
@app.get("/search")
async def search_songs(q: str):
    return await fetch_songs(q)

# Extract Audio URL using yt-dlp
async def get_audio_url(video_id):
    """Extracts the direct audio URL from a YouTube video asynchronously."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "extract_flat": False,
        "force_generic_extractor": False,
    }

    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await loop.run_in_executor(None, ydl.extract_info, url, False)
        return info.get("url") if "url" in info else None

# Get Audio + Metadata API
@app.get("/get_audio")
async def get_audio(video_id: str):
    """Returns the direct audio URL, title, artist, and thumbnail."""
    # Fetch song details from YouTube Music API
    song_details = ytmusic.get_song(video_id)
    if not song_details or "videoDetails" not in song_details:
        return {"error": "Song details not found"}

    # Extract metadata
    title = song_details["videoDetails"]["title"]
    artist = song_details["videoDetails"].get("author", "Unknown")

    # Extract highest-quality thumbnail
    thumbnails = song_details.get("videoDetails", {}).get("thumbnail", {}).get("thumbnails", [])
    thumbnail = thumbnails[-1]["url"] if thumbnails else None  # Get highest-quality image

    # Get direct audio URL
    audio_url = await get_audio_url(video_id)
    if not audio_url:
        return {"error": "server Error try again later"}

    return {
        "audio_url": audio_url,
        "title": title,
        "artist": artist,
        "thumbnail": thumbnail,
    }