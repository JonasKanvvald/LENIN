import os
import json

# Добавляем необходимые импорты
from urllib.request import Request, urlopen
import httpx  # Для работы с API MusicBrainz

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
        return new_database
        
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке/создании базы: {e}")
        return []

def fetch_musicbrainz_album(artist_payload, album_payload):
    """
    Выкачивает данные альбома из MusicBrainz API и возвращает payload.
    """
    # Пример функции для получения данных альбома (замените на свою реализацию)
    headers = {
        "User-Agent": f"MusicParserBot/1.0 ({os.environ.get('INPUT_ARTIST_PAYLOAD', 'fallback')} - {os.environ.get('INPUT_ALBUM_PAYLOAD', 'fallback')})"
    }
    
    # Формируем URL запроса к MusicBrainz API
    query = f'artist:"{artist_payload}" AND release:"{album_payload}"'
    url = f"https://musicbrainz.org/ws/2/release/?query={query.replace(' ', '+')}&fmt=json&limit=1"
    
    try:
        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Обрабатываем данные...
            return data
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Произошла ошибка при получении данных: {e}")
        return None

# Основная функция
def main():
    # Получаем аргументы из окружения (GitHub Actions)
    artist_payload = os.getenv("ARTIST_PAYLOAD", "The Offspring")
    album_payload = os.getenv("ALBUM_PAYLOAD", "Americana")
    
    print(f"🚀 Начало сбора данных для альбома: {artist_payload} - {album_payload}")
    
    # Загружаем существующие данные
    albums_db = load_existing_albums()
    
    if not albums_db:
        print("❌ Не удалось загрузить базу. Создаем новую...")
        albums_db = []
        
    try:
        # Получаем новые данные из MusicBrainz API
        album_data = fetch_musicbrainz_album(artist_payload, album_payload)
        
        if album_data and isinstance(album_data, dict):
            print("✅ Данные треклиста получены успешно.")
            
            # Проверяем на дубликаты (по MBID) и обновляем базу
            existing_index = None
            for idx, item in enumerate(albums_db):
                if item.get('mbid') == album_data.get('mbid'):
                    existing_index = idx
                    break
                    
            if existing_index is not None:
                albums_db[existing_index] = album_data
                print("🔄 Существующий альбом обновлен.")
            else:
                albums_db.append(album_data)
                
        # Сохраняем базу данных
        with open("albums_db.json", "w", encoding="utf-8") as f:
            json.dump(albums_db, f, ensure_ascii=False, indent=2)
            
        print(f"✅ База успешно сохранена в albums_db.json. Всего записей: {len(albums_db)}")
        
    except Exception as e:
        print(f"❌ Произошла ошибка при обработке данных: {e}")

# Вызов основной функции
if __name__ == "__main__":
    main()
