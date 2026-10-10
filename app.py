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
    
    if not os.path.exists(db_filename):
        print(f"❌ Файл {db_filename} не найден. Создаем новую базу...")
        # Создаем файл базы данных
        try:
            with open(db_filename, "w", encoding="utf-8") as f:
                json.dump([], f)  # Пустой список треков
                
            albums_db = []
            print("✅ Файл базы данных создан.")
            return albums_db
            
        except Exception as e:
            print(f"⚠️ Ошибка при создании базы: {e}")
            return None
    
    try:
        with open(db_filename, "r", encoding="utf-8") as f:
            albums_db = json.load(f)
            
        if not isinstance(albums_db, list):
            albums_db = []
            print("🔄 Пересоздаем файл базы данных из корота...")
            
            # Проверяем и пересоздаем файл
            with open(db_filename, "w", encoding="utf-8") as f:
                json.dump(albums_db, f)
                
        return albums_db
        
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке базы: {e}")
        
        # Пересоздаем файл
        new_albums_db = []
        with open(db_filename, "w", encoding="utf-8) as f:
            json.dump(new_albums_db, f)
            
        return new_albums_db


def fetch_musicbrainz_album(artist_payload, album_payload):
    """
    Выкачивает данные альбома из MusicBrainz API и возвращает payload.
    """
    import requests
    
    headers = {
        "User-Agent": f"MusicParserBot/1.0 ({os.environ.get('INPUT_ARTIST_PAYLOAD', 'fallback')} - {os.getenv('INPUT_ALBUM_PAYLOAD', '')})",
        "Accept": "application/json"
    }
    
    # Формируем URL запроса
    query = f'artist:"{artist_payload}" recording:"{album_payload}"'
    url = f"https://musicbrainz.org/ws/2/release/?query={requests.utils.quote(query)}&fmt=json&limit=1"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Обрабатываем данные (проверяем наличие альбома и треклиста)
            releases = data.get("releases")
            
            if not releases or len(releases) == 0:
                print(f"❌ Не найдено релизов для '{album_payload}' артиста '{artist_payload}'.")
                return None
                
            release_data = releases[0]
            mbid = ""
            # Проверяем, есть ли информация о треках
            if 'media' in release_data:
                for medium in release_data['media']:
                    print(f"💿 Среда {medium.get('position')} из {len(medium.get('tracks', []))}")
                    tracks_list = []
                    
                    position_counter = 0
                    
                    # Итерируемся по трекам
                    if 'tracks' in medium:
                        for track_info in medium['tracks']:
                            title = track_info.get('title', '')
                            
                            duration_ms = int(track_info.get('length', 0)) if 'length' in track_info else None
                            
                            tracks_list.append({
                                "position": position_counter,
                                "title": title,
                                "duration": duration_ms // 1000 if duration_ms is not None and duration_ms > 0 else None
                            })
                            
                            position_counter += 1
                        
                        album_result = {
                            "album_name": album_payload,
                            "artist": artist_payload,
                            "year": release_data.get('date', '')[:4] if release_data.get('date') else "N/A",
                            "tracks": tracks_list,
                            "mbid": mbid
                        }
                        
                        return album_result
                    
                    # Если треки отсутствуют, возвращаем None
                    print("❌ Для этого альбома нет информации о треках.")
                    
            else:
                print("❌ В релизе не найдена информация о треклисте")
                
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
