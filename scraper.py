import requests
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.utils import quote
import sys

DB_PATH = "musicbrainz.db"
BASE_URL = "https://musicbrainz.org"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            mb_id TEXT PRIMARY KEY,
            name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            mb_id TEXT PRIMARY KEY,
            title TEXT,
            release_date TEXT,
            genres TEXT,
            length_seconds REAL,
            artist_mb_id TEXT,
            FOREIGN KEY(artist_mb_id) REFERENCES artists(mb_id)
        )
    """)
    conn.commit()
    return conn

def fetch_artists(query: str = "rock", limit: int = 50):
    url = f"{BASE_URL}/search?type=artist&query={quote(query)}&limit={limit}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return [{"mb_id": a["id"], "name": a["name"]} for a in resp.json().get("artists", [])[:limit]]

def fetch_albums(artist_mb_id: str, conn):
    url = f"{BASE_URL}/release/?artist={artist_mb_id}&format=json&limit=200"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    
    albums = []
    for album in resp.json().get("releases", []):
        genres = ", ".join([g["name"] for g in album.get("genres", [])])
        albums.append({
            "mb_id": album["id"],
            "title": album.get("title"),
            "release_date": album.get("date_released", {}).get("date") or "",
            "genres": genres,
            "length_seconds": album.get("length_seconds") or 0.0,
            "artist_mb_id": artist_mb_id
        })
    return albums

def insert_albums(artist: dict, conn):
    cursor = conn.cursor()
    try:
        albums = fetch_albums(artist["mb_id"], conn)
        if not albums:
            print(f"  ⏭ {artist['name']}: без альбомов в базе")
            return
        
        data = [(a["mb_id"], a["title"], a["release_date"], a["genres"], a["length_seconds"], a["artist_mb_id"]) 
                for a in albums]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO albums (mb_id, title, release_date, genres, length_seconds, artist_mb_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, data)
        
        print(f"  ✅ {artist['name']}: +{len(albums)} альбомов")
    except Exception as e:
        print(f"  ❌ Ошибка для {artist['name']}: {e}")

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "rock"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    conn = init_db()
    
    print(f"🔍 Ищем {limit} артистов по запросу: '{query}'...")
    artists = fetch_artists(query, limit)
    print(f"📥 Найдено {len(artists)} артистов. Запуск загрузки...\n")
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(insert_albums, art) for art in artists]
        for f in as_completed(futures):
            pass
            
    conn.commit()
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM albums")
    total = cursor.fetchone()[0]
    print(f"\n🎉 Загрузка завершена! Всего в БД: {total} альбомов.")
    conn.close()

if __name__ == "__main__":
    main()
