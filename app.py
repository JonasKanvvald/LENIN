import os
import json
import sys
from downloader import fetch_musicbrainz_album

def main():
    # 1. Получаем артиста и альбом из переменных окружения (или берем тестовые)
    artist = os.getenv("ARTIST_PAYLOAD", "The Offspring").strip()
    album = os.getenv("ALBUM_PAYLOAD", "Americana").strip()

    if not artist or not album:
        print("❌ Ошибка: Переменные ARTIST_PAYLOAD или ALBUM_PAYLOAD пусты.")
        sys.exit(1)

    print(f"🚀 Запуск импорта альбома: {artist} — {album}")

    # 2. Вызываем логику из модуля downloader.py
    album_data = fetch_musicbrainz_album(artist, album)
    
    if not album_data:
        print(f"❌ Альбом '{album}' артиста '{artist}' не найден на MusicBrainz.")
        sys.exit(1)

    # Путь к файлу базы данных JSON
    db_filename = "albums_db.json"

    # 3. Читаем существующую базу из JSON, если файла нет — создаем пустой список
    if os.path.exists(db_filename):
        try:
            with open(db_filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                database = json.loads(content) if content else []
                if not isinstance(database, list):
                    database = []
        except json.JSONDecodeError:
            print(f"⚠️ Предупреждение: Файл {db_filename} был поврежден, перезаписываем его.")
            database = []
    else:
        database = []

    # 4. Проверяем, нет ли уже такого альбома в базе (по mbid), чтобы избежать дубликатов
    existing_index = None
    for index, item in enumerate(database):
        if item.get("mbid") == album_data["mbid"]:
            existing_index = index
            break

    if existing_index is not None:
        print(f"🔄 Альбом уже есть в базе. Обновляем данные для MBID: {album_data['mbid']}")
        database[existing_index] = album_data
    else:
        print(f"➕ Добавляем новый альбом в базу. MBID: {album_data['mbid']}")
        database.append(album_data)

    # 5. Сохраняем обновленную базу обратно в файл albums_db.json
    try:
        with open(db_filename, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        print(f"✅ Успешно сохранено в {db_filename}! Всего альбомов в базе: {len(database)}")
    except Exception as e:
        print(f"❌ Ошибка при записи в JSON-файл: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
