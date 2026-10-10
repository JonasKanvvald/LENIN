import os
import json
import sys
import httpx

# --- Константы ---
BASE_URL = "https://musicbrainz.org/ws/2"
HEADERS = {
    'User-Agent': 'GlobalMusicProxyWorker/1.0',
}

async def fetch_musicbrainz_album(artist: str, album: str):
    # Поиск релиза
    search_query = f'artist:"{artist}" recording:"{album}"'
    search_url = f"{BASE_URL}/release/?query={search_query.replace(' ', '+')}&inc=recordings&fmt=json"
    
    try:
        async with httpx.AsyncClient(headers=HEADERS) as client:
            response = await client.get(search_url)
            response.raise_for_status()
            
            data = response.json()
            releases = data.get("releases", [])
            
            if not releases:
                print(f"❌ Релиз '{album}' артиста '{artist}' не найден на MusicBrainz.")
                return None
                
            best_match = releases[0]
            release_id = best_match["id"]
            mbid = release_id.split("/")[-1]  # Извлекаем MBID
            
            # Получаем треклист и дополнительную информацию
            lookup_url = f"{BASE_URL}/release/{mbid}?inc=recordings&fmt=json"
            
            response_track = await client.get(lookup_url)
            response_track.raise_for_status()
            track_data = response_track.json()

            media = track_data.get("media", [])
            if not media:
                print(f"❌ Для альбома '{album}' нет треклиста на MusicBrainz.")
                return None

            tracks_list = []
            for disc in media:
                disc_number = int(disc["position"])
                recording_list = disc["recordings"]
                position_counter = 0
                for track in recording_list:
                    duration_ms = int(track["length"]) if "length" in track else None
                    
                    # Обрабатываем треки (каждая секция может быть разной)
                    tracks_list.append({
                        "title": track["title"],
                        "artist": artist,
                        "duration": duration_ms // 1000 if duration_ms is not None and duration_ms > 0 else None
                    })
                position_counter += len(tracks_list)

            return {
                "album_name": album,
                "mbid": mbid, 
                # ... другие поля ...
            }
    except httpx.HTTPError as e:
        print(f"🚨 Ошибка API MusicBrainz: {e}")
        return None
