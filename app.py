import os
import json

def load_existing_albums():
    db_filename = "albums_db.json"
    
    try:
        if os.path.exists(db_filename):
            with open(db_filename, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            new_database = []
            
            # Создаем файл базы данных
            if not os.path.exists(os.path.dirname(db_filename)):
                try:
                    os.makedirs(os.path.dirname(db_filename))
                except Exception as e:
                    print(f"❌ Ошибка создания директории: {e}")
                    
            with open(db_filename, "w", encoding="utf-8") as f:
                json.dump(new_database, f, indent=2)
                
            return new_database
            
    except json.JSONDecodeError:
        # Если файл поврежден - пересоздаем
        print("⚠️ Ошибка чтения JSON. Пересоздаем базу...")
        
        if os.path.exists(db_filename):
            try:
                os.remove(db_filename)
            except Exception as e:
                print(f"❌ Не удалось удалить старый файл: {e}")
                
        return []
    except FileNotFoundError:
        # Если нет файла - создаем новый
        new_database = []
        
        if not os.path.exists(os.path.dirname(db_filename)):
            try:
                os.makedirs(os.path.dirname(db_filename))
            except Exception as e:
                print(f"❌ Ошибка создания директории: {e}")
                
        with open(db_filename, "w", encoding="utf-8") as f:
            json.dump(new_database, f, indent=2)
            
        return new_database

def fetch_musicbrainz_album(artist: str, album_name: str):
    # Логика поиска альбома в MusicBrainz
    headers = {
        "User-Agent": "MusicParserBot/1.0 (contact@your-email.com)",
        "Accept": "application/json"
    }
    
    search_query = f'artist:"{artist}" AND release:"{album_name}"'
    params = urllib.parse.urlencode({"query": search_query.replace(" ", "+"), "fmt": "json", "limit": 1})
    base_url = os.getenv('BASE_URL', 'https://musicbrainz.org')
    search_url = f"{base_url}/ws/2/release/?{params}"

def main():
    # Получаем аргументы из окружения или тестовые
    artist_env = os.getenv("ARTIST_PAYLOAD", "The Offspring").strip()
    album_env = os.getenv("ALBUM_PAYLOAD", "Americana").strip()

    if not artist_env or not album_env:
        print("❌ Ошибка: Переменные ARTIST_PAYLOAD и ALBUM_PAYLOAD не заданы. Используются тестовые значения.")
        
    # Загружаем существующую базу
    albums_db = load_existing_albums()
    
    try:
        # Вызываем функцию поиска альбома (заменяем ваш broken downloader.py)
        album_data = fetch_musicbrainz_album(artist_env, album_env)

        if not album_data:
            print(f"❌ Альбом '{album_env}' не найден на MusicBrainz. Продолжаем работу с существующими данными.")
            return
            
        # Обновляем базу данных
        existing_index = None
        for idx, item in enumerate(albums_db):
            if (item.get("artist") == artist_env) and (item.get("album_name") == album_data["title"]):
                existing_index = idx
                break
                
        if existing_index is not None:
            albums_db[existing_index] = album_data
        else:
            albums_db.append(album_data)
            
    except Exception as e:
        print(f"❌ Ошибка при обработке: {e}")
        
    # Сохраняем базу данных
    try:
        db_filename = "albums_db.json"
        with open(db_filename, "w", encoding="utf-8") as f:
            json.dump(albums_db, f, ensure_ascii=False, indent=2)
            
        print(f"✅ База успешно сохранена в {db_filename}")
        
    except Exception as e:
        print(f"❌ Критическая ошибка при записи базы: {e}")

if __name__ == "__main__":
    main()
