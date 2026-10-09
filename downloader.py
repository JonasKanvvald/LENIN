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

    query = f'artist:"{artist}" AND release:"{album}"'
    params = urllib.parse.urlencode({"query": query, "fmt": "json"})
    search_url = f"https://musicbrainz.org?{params}"
    
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        releases = data.get("releases", [])
        if not releases:
            return None
            
        best_match = releases[0]
        release_id = best_match.get("id")
        year_released = best_match.get("date", "2026")[:4]
        
        time.sleep(1.0) # Лимит API
        
        lookup_url = f"https://musicbrainz.org/{release_id}?inc=recordings&fmt=json"
        req_track = urllib.request.Request(lookup_url, headers=headers)
        with urllib.request.urlopen(req_track) as response_track:
            track_data = json.loads(response_track.read().decode('utf-8'))
            
        media = track_data.get("media", [])
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
