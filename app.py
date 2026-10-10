import os
import json

# УБРАЛИ HTTPX, так как он не нужен для этого скрипта
# Используем стандартные возможности Python и requests вместо него


def load_existing_albums():
    """
    Загружает существующие данные из albums_db.json.
    Если файл отсутствует или поврежден - создает новый пустой список.
    """
    db_filename = "albums_db.json"
    
    try:
        if os.path.exists(db_filename):
            with open(db_filename, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Создаем файл базы данных при отсутствии
        new_database = []
        with open(db_filename, "w", encoding="utf-8") as f:
            json.dump(new_database, f, indent=2)
            
        print("✅ Файл базы данных создан.")
        return []
        
    except Exception as e:
        # Создаем пустой список при любой ошибке
        new_database = []
        with open(db_filename, "w", encoding="utf-8") as f:
            json.dump(new_database, f, indent=2)
        print(f"⚠️ Ошибка при загрузке/создании базы: {e}")
        return []

def fetch_musicbrainz_album(artist_payload, album_payload):
    """
    Выкачивает данные альбома из MusicBrainz API и возвращает payload.
    """
    # Используем requests для выполнения HTTP-запросов к MusicBrainz
    import requests
    
    headers = {
        "User-Agent": f"MusicParserBot/1.0 ({os.environ.get('INPUT_ARTIST_PAYLOAD', 'fallback')} - {os.environ.get('INPUT_ALBUM_PAYLOAD', 'fallback')})",
        "Accept": "application/json"
    }
    
    # Формируем URL запроса
    query = f'artist:"{artist_payload}" recording:"{album_payload}"'
    url = f"https://musicbrainz.org/ws/2/release/?query={requests.utils.quote(query.replace(' ', '+'))}&fmt=json&limit=1"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Обрабатываем данные (проверяем наличие альбома и треклиста)
            releases = data["releases"]
            
            if not releases:
                return None
                
            release = releases[0]
            mbid = release["id"].split("/")[-1]  # Извлекаем MBID из URL
            tracks = []
            
            for medium in release["media"]:
                for track in medium["tracks"]:
                    duration_ms = int(track.get("length", "0"))
                    tracks.append({
                        "title": track["title"],
                        "artist": artist_payload,
                        "duration": duration_ms // 1000 if duration_ms > 0 else None
                    })
                    
            return {
                "album_name": album_payload,
                "artist": artist_payload,
                "year": release.get("date", "")[:4] if release.get("date") else "N/A",
                "tracks": tracks,
                "mbid": mbid
            }
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Произошла ошибка при получении данных: {e}")
        return None

def main():
    # Получаем аргументы из окружения (GitHub Actions)
    artist_payload = os.getenv("ARTIST_PAYLOAD", "The Offspring")
    album_payload = os.getenv("ALBUM_PAYLOAD", "Americana")
    
    print(f"🚀 Начало сбора данных для альбома: {artist_payload} - {album_payload}")
    
    # Загружаем существующие данные
    albums_db = load_existing_albums()
    
    if not albums_db:
        print("❌ Не удалось загрузить базу. Создаем новую...")
        
    try:
        # Получаем новые данные из MusicBrainz API
        album_data = fetch_musicbrainz_album(artist_payload, album_payload)
        
        if album_data and 'tracks' in album_data:
            print("✅ Данные треклиста получены успешно.")
            
            # Проверяем на дубликаты (по MBID) и обновляем базу
            existing_index = None
            for idx, item in enumerate(albums_db):
                if 'mbid' in item and item['mbid'] == album_data['mbid']:
                    existing_index = idx
                    break
                    
            if existing_index is not None:
                albums_db[existing_index] = album_data
                print("🔄 Существующий альбом обновлен.")
            else:
                albums_db.append(album_data)
                
        # Сохраняем базу данных (записываем в файл)
        with open("albums_db.json", "w", encoding="utf-8") as f:
            json.dump(albums_db, f, ensure_ascii=False, indent=2)
            
        print(f"✅ База успешно сохранена. Всего записей: {len(albums_db)}")
        
    except Exception as e:
        print(f"❌ Произошла ошибка при обработке данных: {e}")

if __name__ == "__main__":
    main()
