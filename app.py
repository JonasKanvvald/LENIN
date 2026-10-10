import os
import json

# Функция для загрузки базы данных (можно сделать асинхронной)
def load_albums_db():
    db_filename = "albums_db.json"
    
    if not os.path.exists(db_filename):
        return []
        
    try:
        with open(db_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Гарантируем, что это список
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"⚠️ Ошибка чтения базы: {e}")
        return []

# Функция сохранения в базу (можно использовать асинхронный драйвер)
def save_albums_db(album_data):
    db_filename = "albums_db.json"
    
    # Загружаем существующую базу
    database = load_albums_db()
    
    # Проверяем наличие дубликата по mbid
    new_entry = True
    for idx, entry in enumerate(database):
        if entry.get('mbid') == album_data['mbid']:
            new_entry = False
            break
            
    if not new_entry:
        database[idx] = album_data
    else:
        database.append(album_data)
        
    # Сохраняем базу
    try:
        with open(db_filename, 'w', encoding='utf-8') as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False
