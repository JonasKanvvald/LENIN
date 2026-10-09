import os
import json
import sys
import httpx
from datetime import datetime

# --- Константы ---
BASE_URL = "https://musicbrainz.org"
# Обязательный User-Agent согласно MusicBrainz API spec.
HEADERS = {
    "User-Agent": "MusicParserBot/1.0 (contact@your-email.com)" 
}

def fetch_album_from_musicbrainz(artist: str, album_name: str) -> dict or None:
    """
    Выкачивает официальный релиз и полный треклист из MusicBrainz API 
    и возвращает структурированный словарь с данными альбома.
    """
    print(f"🔍 Поиск альбома '{album_name}' от '{artist}' в глобальной базе MusicBrainz...")

    # --- Шаг 1: Поиск MBID Релиза (Search) ---
    query = f'artist:"{artist}" AND release:"{album_name}"'
    search_url = f"{BASE_URL}/ws/2/release?query={query.replace(' ', '+')}&fmt=json&limit=3"

    try:
        # Используем httpx для более надежного API взаимодействия (Как в Citation 1)
        with httpx.Client(timeout=15.0, headers=HEADERS) as client:
            response = client.get(search_url)
            response.raise_for_status() # Вызовет исключение при ошибке 4xx/5xx

            search_data = response.json()
            releases = search_data.get("releases", [])

            if not releases:
                print("❌ Альбом не найден в базе данных MusicBrainz.")
                return None

            # Берем первый наиболее подходящий релиз
            best_match = releases[0]
            release_id = best_match.get("id")
            
            print(f"✅ Успешно! Найден MBID Релиза: {release_id}")
    
    except httpx.HTTPStatusError as e:
        print(f"🚨 Ошибка API MusicBrainz (HTTP): {e.response.status_code} - Проверьте User-Agent и лимиты запросов.")
        return None
    except Exception as e:
        print(f"💥 Критическая ошибка при поиске альбома: {e}")
        return None

    # --- Шаг 2: Запрос детальной информации о релизе и его треклисте (Lookup) ---
    lookup_url = f"{BASE_URL}/ws/2/release/{release_id}?inc=recordings&fmt=json"
    print(f"\n🎵 Выполнение глубокого Lookup запроса для MBID: {release_id}...")

    try:
        with httpx.Client(timeout=15.0, headers=HEADERS) as client:
            response = client.get(lookup_url)
            response.raise_for_status()

            lookup_data = response.json()
            media = lookup_data.get("media", [])

            if not media:
                print("❌ Треклист пуст или данные недоступны.")
                return None

    except httpx.HTTPStatusError as e:
        print(f"🚨 Ошибка Lookup API MusicBrainz: {e.response.status_code}")
        return None
    except Exception as e:
        print(f"💥 Критическая ошибка при получении треклиста: {e}")
        return None

    # --- Шаг 3: Адаптация данных и возврат результата ---
    tracks = []
    for disc in media:
        raw_tracks = disc.get("tracks", [])
        for t in raw_tracks:
            duration_ms = int(t.get("length", 0) or 0)
            duration_sec = duration_ms // 1000 if duration_ms > 0 else None
            recording = t.get("recording", {})

            tracks.append({
                "position": int(t.get("position", len(tracks) + 1)),
                "title": t.get("title", "Unknown Track"),
                "artist": artist,
                "duration": duration_sec, # Возвращаем seconds (более удобно для БД)
                "disc_number": int(disc.get("position", 1))
            })

    # Подготовка финального payload'а
    output_payload = {
        "title": album_name,
        "artist": artist,
        "year": best_match.get("date")[:4] if best_match.get("date") else "N/A",
        "album_type": best_match.get("release-group", {}).get("primary-type", "studio").lower(),
        "tracks": tracks,
        "source": "musicbrainz"
    }

    return output_payload


if __name__ == "__main__":
    # Получение аргументов из окружения GitHub Actions (Job context)
    artist = os.getenv("ARTIST", "").strip()
    album = os.getenv("ALBUM", "").strip()
    
    if not artist or not album:
        print("Usage: This script requires ARTIST and ALBUM environment variables.")
        sys.exit(1)

    # Выполнение логики и сохранение результата
    final_payload = fetch_album_from_musicbrainz(artist, album)
    
    if final_payload:
        output_filename = "tracklist_result.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, ensure_ascii=False, indent=2)
        print(f"\n🚀 PAYLOAD УСПЕШНО СГЕНЕРИРОВАН и сохранен в {output_filename}!")
    else:
        print("\n🛑 ОШИБКА: Не удалось получить полный payload. Проверка завершена.")

