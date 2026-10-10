import os
from databases import Database

# Извлекаем URL подключения из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/music_db")
database = Database(DATABASE_URL)

async def check_and_create_schema():
    print("🔄 Проверка и обновление структуры базы данных PostgreSQL...")
    
    # 1. Гарантируем наличие новых полей в таблице треков/файлов
    alter_tracks_query = """
    ALTER TABLE tracks 
    ADD COLUMN IF NOT EXISTS mbid VARCHAR(36),
    ADD COLUMN IF NOT EXISTS file_hash BYTEA,
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
        print("⚡ Выполнение миграции структуры...")
        await database.execute(query=alter_tracks_query)
        await database.execute(query=create_artists_query)
        print("✅ Структура БД успешно синхронизирована!")
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
