import os
import json
import sys
import urllib.request
import urllib.parse
import time

def fetch_musicbrainz_album(artist: str, album: str):
    headers = {
        "User-Agent": "GlobalMusicProxyWorker/1.0.0 ( contact@yourdomain.com )",
        "Accept": "application/json"
    }

    # Полнотекстовый поиск релиза через Lucene-запрос
    query = f'artist:"{artist}" AND release:"{album}"'
    params = urllib.parse.urlencode({"query": query, "fmt": "json"})
    search_url = f"https://musicbrainz.org?{params}"
    
    print(f"🔍 Поиск альбома: {search_url}")
    
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        releases = data.get("releases", [])
        if not releases:
            print("❌ Релизы не найдены в результатах поиска.")
            return None
            
        # 🔥 ИСПРАВЛЕНО: Берем именно ПЕРВЫЙ релиз из списка
        best_match = releases[0]
        release_id = best_match.get("id")
        
        if not release_id:
            print("❌ Не удалось извлечь id (MBID) релиза.")
            return None
            
        year_released = best_match.get("date", "2026")[:4]
        print(f"✅ Найден MBID релиза: {release_id}")
        
        # Обязательная пауза 1 секунда, чтобы MusicBrainz не забанил по лимиту (Rate Limit)
        time.sleep(1.0)
        
        # Шаг 2: Запрос треклиста по найденному MBID
        lookup_url = f"https://musicbrainz.org/{release_id}?inc=recordings&fmt=json"
        print(f"🎵 Запрос треклиста: {lookup_url}")
        
        req_track = urllib.request.Request(lookup_url, headers=headers)
        with urllib.request.urlopen(req_track) as response_track:
            track_data = json.loads(response_track.read().decode('utf-8'))
            
        media = track_data.get("media", [])
        if not media:
            print("❌ Секция media в ответе пуста.")
            return None

        tracks = []
        for disc in media:
            disc_number = int(disc.get("position", 1))
            for t in disc.get("tracks", []):
                duration_ms = int(t.get("length", 0) or 0)
                tracks.append({
                    "position": int(t.get("position", len(tracks) + 1)),
                    "title": t.get("title", "Unknown Track"),
                    "artist": artist,
                    "duration": duration_ms // 1000 if duration_ms > 0 else None,
                    "disc_number": disc_number
                })
                
        return {
            "title": album,
            "artist": artist,
            "year": year_released,
            "album_type": best_match.get("release-group", {}).get("primary-type", "studio").lower(),
            "tracks": tracks,
            "source": "musicbrainz",
            "mbid": release_id
        }
    except Exception as e:
        print(f"Ошибка в downloader.py: {e}")
        return None
