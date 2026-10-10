import os
import json

def fetch_musicbrainz_album(artist_payload, album_payload):
    """
    Выкачивает данные альбома из MusicBrainz API.
    """
    # Создаем уникальный User-Agent для каждого вызова
    user_agent = "MusicParserBot/1.0 (contact@yourdomain.com)"
    
    # Формируем URL запроса
    query_str = f'artist:"{artist_payload}" recording:"{album_payload}"'
    encoded_query = urllib.parse.quote_plus(query_str)
    url = f"https://musicbrainz.org/ws/2/release/?query={encoded_query}&fmt=json&limit=1"
    
    # Формируем заголовки
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            
            # Обрабатываем данные (проверяем наличие альбома и треклиста)
            releases = data.get("releases", [])
            
            if not releases or len(releases) == 0:
                print(f"❌ Не найдено релизов для '{album_payload}' от '{artist_payload}'.")
                return None
                
            # Берем первый результат
            release_data = releases[0]
            
            # Извлекаем информацию о треках (заголовки)
            tracks_info = []
            for medium in release_data.get("media", []):
                disc_number = medium.get("position")
                
                for track in medium.get("recordings", [])[:]:
                    duration_ms = int(track.get("length", 0)) if "length" in track else None
                    
                    # Форматируем данные трека
                    track_data = {
                        "artist": artist_payload,
                        "title": track["title"],
                        "duration": duration_ms // 1000 if duration_ms is not None and duration_ms > 0 else None,
                        "disc_number": disc_number
                    }
                    
                    tracks_info.append(track_data)
            
            # Формируем результат для сохранения в albums_db.json
            result = {
                "album_name": album_payload,
                "artist": artist_payload,
                "tracks": tracks_info
            }
            
            return result
            
        else:
            print(f"❌ Ошибка HTTP: {response.getcode()}")
            return None
            
    except Exception as e:
        print(f"❌ Произошла ошибка при получении данных: {e}")
        sys.exit(1)
