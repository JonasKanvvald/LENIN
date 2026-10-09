import os
import asyncio
from databases import Database

# Извлекаем URL подключения из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/music_db")
database = Database(DATABASE_URL)

async def check_and_create_schema():
    print("🔄 Проверка и обновление структуры базы данных PostgreSQL...")
    
    # 1. Гарантируем наличие новых полей в таблице треков/файлов
    # Замените 'tracks' на имя вашей реальной таблицы, если оно отличается
    alter_tracks_query = """
    ALTER TABLE tracks 
    ADD COLUMN IF NOT EXISTS mbid VARCHAR(36),
    ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS lyrics TEXT;
    """
    
    # 2. Перенос данных или создание таблицы artists (согласно Citation 2)
    create_artists_query = """
    CREATE TABLE IF NOT EXISTS artists (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        mbid VARCHAR(36),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        print("⚡ Выполнение миграций ALTER TABLE...")
        await database.execute(query=alter_tracks_query)
        await database.execute(query=create_artists_query)
        print("✅ Структура БД успешно синхронизирована!")
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции структуры: {e}")

async def migrate_old_data():
    print("🚚 Запуск переноса данных из старых таблиц в новую таблицу artists...")
    
    # Пример логики: переносим уникальных артистов из таблицы треков в таблицу artists
    select_query = "SELECT DISTINCT artist FROM tracks WHERE artist IS NOT NULL;"
    insert_query = "INSERT INTO artists (name) VALUES (:name) ON CONFLICT (name) DO NOTHING;"
    
    try:
        rows = await database.fetch_all(query=select_query)
        for row in rows:
            artist_name = row["artist"]
            await database.execute(query=insert_query, values={"name": artist_name})
        print(f"✅ Перенос завершен. Обработано артистов: {len(rows)}")
    except Exception as e:
        print(f"❌ Ошибка при переносе данных: {e}")

async def main():
    # Подключаемся к PostgreSQL
    await database.connect()
    
    # Запускаем миграцию структуры
    await check_and_create_schema()
    
    # Запускаем миграцию данных
    await migrate_old_data()
    
    # Отключаемся
    await database.disconnect()

if __name__ == "__main__":
    # Запуск асинхронного цикла
    asyncio.run(main())
