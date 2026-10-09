import json
# Импортируем httpx, который гораздо лучше подходит для работы с API
import httpx 
from urllib.parse import urlencode # Оставляем только для формирования параметров

# Константы и настройки (Лучшая практика из Цитаты 3)
API_HEADERS = {
    "User-Agent": "GlobalMusicProxyWorker/1.0.0 ( contact@yourdomain.com )",
    "Accept": "application/json"
}
TIMEOUT = 15.0 # Увеличим таймаут для надежности

def fetch_musicbrainz_album(artist: str, album: str) -> dict | None:
    """
    Выкачивает данные о релизе и треклисте из MusicBrainz API с улучшенной обработкой ошибок.
    """
    # 1. Полнотекстовый поиск релиза (Search Query)
    query = f'artist:"{artist}" AND (release:"{album}" OR title:"{album}")'
    params = urlencode({"query": query, "fmt": "json", "limit": 3})
    search_url = f"https://musicbrainz.org/ws/2/release?{params}"
    
    print(f"🔍 Поиск альбома: {search_url}")

    # Используем httpx для безопасного и структурированного запроса
    try:
        with httpx.Client(timeout=TIMEOUT, headers=API_HEADERS) as client:
            response = client.get(search_url)
            
            # АБСОЛЮТНАЯ ПРОВЕРКА 1: Проверка статуса HTTP-кода (Критично!)
            if response.status_code != 200:
                print(f"❌ Ошибка API MusicBrainz (Код {response.status_code}). Попробуйте позже.")
                return None

            try:
                data = response.json() # Безопасный парсинг JSON
            except json.JSONDecodeError:
                # АБСОЛЮТНАЯ ПРОВЕРКА 2: Если ответ - это HTML, а не JSON
                print("⚠️ Ошибка декодирования JSON. Возможно, API вернул страницу ошибки.")
                return None

        releases = data.get("releases", [])
        if not releases:
            print("❌ Релизы не найдены в результатах поиска.")
            return None
            
        best_match = releases[0]
        release_id = best_match.get("id")
        
        if not release_id:
            print("❌ Не удалось извлечь id (MBID) релиза.")
            return None
            
        year_released = best_match.get("date", "2026")[:4]
        print(f"✅ Найден MBID релиза: {release_id}")

    except httpx.ConnectTimeout:
        print("❌ Ошибка сети: Превышен таймаут соединения с MusicBrainz.")
        return None
    except httpx.RequestError as e:
        # Обработка всех остальных сетевых ошибок (DNS, нет интернета и т.д.)
        print(f"❌ Критическая ошибка запроса к API: {e}")
        return None

    # --- Шаг 2: Запрос треклиста по найденному MBID ---
    
    try:
        with httpx.Client(timeout=TIMEOUT, headers=API_HEADERS) as client:
            lookup_url = f"https://musicbrainz.org/{release_id}?inc=recordings&fmt=json"
            print(f"🎵 Запрос треклиста: {lookup_url}")
            
            response_track = client.get(lookup_url)

            if response_track.status_code != 200:
                print("❌ Ошибка при получении детального треклиста релиза.")
                return None
            
            try:
                track_data = response_track.json()
            except json.JSONDecodeError:
                print("⚠️ Не удалось распарсить JSON для получения треклиста.")
                return None

        # --- Парсинг данных (Логика остается той же, она верна) ---
        media = track_data.get("media", [])
        if not media:
            print("❌ Секция media в ответе пуста или формат изменился.")
            return None

        tracks = []
        for disc in media:
             disc_number = int(disc.get("position", 1))
             # Проверка, что track-list существует перед перебором
             if 'tracks' not in disc or not disc['tracks']:
                 continue
                 
             for t in disc["tracks"]:
                duration_ms = int(t.get("length", 0) or 0)
                tracks.append({
                    "position": int(t.get("position", len(tracks) + 1)),
                    "title": t.get("title", "Unknown Track"),
                    "artist": artist,
                    "duration": duration_ms // 1000 if duration_ms > 0 else None,
                    "disc_number": disc_number
                })

    except httpx.RequestError as e:
        print(f"❌ Критическая ошибка при получении треклиста: {e}")
        return None


    # Финальная сборка и возврат данных (Успех)
    return {
        "title": album,
        "artist": artist,
        "year": year_released,
        # Проверка наличия ключа 'release-group' перед использованием.
        "album_type": best_match.get("release-group", {}).get("primary-type", "studio").lower(), 
        "tracks": tracks,
        "source": "musicbrainz",
        "mbid": release_id
    }

