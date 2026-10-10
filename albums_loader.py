import os
import json
from datetime import datetime

def get_environment_variables():
    """
    Возвращает артиста и альбом из переменных окружения.
    Если не заданы, использует тестовые значения.
    """
    artist = os.getenv("ARTIST", "The Offspring").strip()
    album_name = os.getenv("ALBUM", "Americana").strip()
    
    if not artist or not album_name:
        print("⚠️ Предупреждение: Переменные окружения ARTIST и ALBUM не заданы. Используются тестовые значения.")
        
    return artist, album_name

def load_existing_albums():
    """
    Загружает существующие данные из albums_db.json
    или создает новый список.
    """
    db_filename = "albums_db.json"
    
    try:
        if os.path.exists(db_filename):
            with open(db_filename, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Создаем пустой список при отсутствии файла
            new_database = []
            
            try:
                with open(db_filename, "w", encoding="utf-8") as f:
                    json.dump(new_database, f)
                
                print("✅ Файл базы данных создан.")
                return []
            except Exception as e:
                print(f"❌ Ошибка создания файла базы: {e}")
                sys.exit(1)
    except json.JSONDecodeError:
        # Если файл поврежден - пересоздаем
        new_database = []
        
        try:
            with open(db_filename, "w", encoding="utf-8") as f:
                json.dump(new_database, f)
                
            print("⚠️ Ошибка чтения. Файл базы данных пересоздан.")
            return []
        except Exception as e:
            print(f"❌ Критическая ошибка при работе с файлом: {e}")
            sys = exit(1)

def fetch_musicbrainz_data(artist, album_name):
    """
    Получает данные альбома из MusicBrainz API
    и формирует payload.
    """
    # Логика взаимодействия с MusicBrainz API...
    
    return {
        "artist": artist,
        "album": album_name,
        "tracks": [],
        "metadata": {}
    }

def save_to_albums_db(new_data):
    """
    Сохраняет данные в albums_db.json.
    Обрабатывает дубликаты по MBID.
    """
    db_filename = "albums_db.json"
    
    try:
        # Загрузка существующей базы
        if os.path.exists(db_filename):
            with open(db_filename, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        else:
            existing_data = []
            
        # Проверка на дубликат (например, по названию альбома и артиста)
        duplicate_found = False
        for data in existing_data:
            if data['artist'] == new_data['artist'] and data['album'] == new_data['album']:
                print("🔄 Найден дубликат. Обновляем данные...")
                # Заменяем старые данные на новые (или делаем слияние)
                data.update(new_data)
                duplicate_found = True
                break
                
        if not duplicate_found:
            existing_data.append(new_data)
            
        with open(db_filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)

def main():
    # Получаем аргументы из окружения или тестовые
    artist, album_name = get_environment_variables()
    
    print(f"🚀 Начало сбора данных для альбома: {artist} - {album_name}")
    
    # Загрузка существующих данных
    albums_db = load_existing_albums()
    
    if not albums_db:
        print("❌ Не удалось загрузить базу. Создаем новую...")
        albums_db = []
        
    # Получаем новые данные из MusicBrainz API
    new_data = fetch_musicbrainz_data(artist, album_name)
    
    if new_data and 'tracks' in new_data and isinstance(new_data['tracks'], list):
        print("🎵 Данные треклиста получены успешно.")
        
        # Обновление базы данных
        save_to_albums_db(album_name)
    else:
        print(f"❌ Ошибка: API вернул некорректные данные {new_data}")
