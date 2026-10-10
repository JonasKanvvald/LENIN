import os
import json
import sys
import httpx
from datetime import datetime

# --- Константы ---
BASE_URL = "https://musicbrainz.org/ws/2"
HEADERS = {
    'User-Agent': 'MusicParserBot/1.0 (contact@your-email.com)',
    # Дополнительные заголовки можно добавить, если нужно
}

async def main():
    global database
    db_filename = "albums_db.json"

    # Получаем артиста и альбом из переменных окружения
    artist_env = os.getenv("ARTIST", "")
    album_env = os.getenv("ALBUM", "")

    if not artist_env or not album_env:
        print("Usage: This script requires ARTIST and ALBUM environment variables.")
        sys.exit(1)

    # Вызываем функцию из downloader.py (используем асинхронный вариант или драйвер)
    album_data = await fetch_musicbrainz_album(artist_env, album_env)

    if not album_data:
        print(f"❌ Альбом '{album_env}' артиста '{artist_env}' не найден на MusicBrainz.")
        sys.exit(1)

    # Загружаем текущую базу
    if os.path.exists(db_filename):
        try:
            with open(db_filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                database = json.loads(content) if content else []
        except Exception as e:
            print(f"⚠️ Ошибка чтения базы: {e}")
            sys.exit(1)
    else:
        database = []

    # Проверяем наличие дубликата по mbid
    existing_index = None
    for idx, item in enumerate(database):
        if item.get('mbid') == album_data['mbid']:
            existing_index = idx
            break

    if existing_index is not None:
        print(f"🔄 Обновляем существующую запись для альбома: {artist_env} — {album_env}")
        database[existing_index] = album_data
    else:
        print(f"➕ Добавляем новый альбом в базу. MBID: {album_data['mbid']}")
        database.append(album_data)

    # Сохраняем базу данных
    try:
        with open(db_filename, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        print(f"✅ База успешно обновлена. Всего записей: {len(database)}")
    except Exception as e:
        print(f"❌ Ошибка записи базы: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Используем асинхронный драйвер для совместимости с миграцией
    import asyncio
    asyncio.run(main())
