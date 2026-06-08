import os
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

WEEKLY_FILE = "weekly_data.json"
MONTHLY_FILE = "monthly_data.json"

def get_spotify_client():
    scope = "user-read-recently-played"
    auth_manager = SpotifyOAuth(scope=scope)
    return spotipy.Spotify(auth_manager=auth_manager)

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_to_history(new_records, filename):
    existing_data = load_data(filename)
    existing_timestamps = {item['played_at'] for item in existing_data}
    
    added_count = 0
    for record in new_records:
        if record['played_at'] not in existing_timestamps:
            existing_data.append(record)
            added_count += 1
            
    if added_count > 0:
        existing_data.sort(key=lambda x: x['played_at'])
        save_data(filename, existing_data)
        
    return added_count

def main():
    sp = get_spotify_client()
    
    try:
        results = sp.current_user_recently_played(limit=50)
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return

    # Extraer todos los récords de la API
    new_records = []
    for item in results['items']:
        track = item['track']
        record = {
            "played_at": item['played_at'],
            "track_id": track['id'],
            "track_name": track['name'],
            "artist_id": track['artists'][0]['id'],
            "artist_name": track['artists'][0]['name'],
            "duration_ms": track.get('duration_ms', 0)
        }
        new_records.append(record)
        
    # Guardar en ambas cajas (semanal y mensual)
    added_weekly = append_to_history(new_records, WEEKLY_FILE)
    added_monthly = append_to_history(new_records, MONTHLY_FILE)
    
    if added_weekly > 0 or added_monthly > 0:
        print(f"✅ Canciones guardadas. Semanal: +{added_weekly} | Mensual: +{added_monthly}")
    else:
        print("ℹ️ No hay nuevas canciones desde la última recolección.")

if __name__ == "__main__":
    main()
