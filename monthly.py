import os
import io
import json
import datetime
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from collections import Counter, defaultdict
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

load_dotenv()

DATA_FILE = "monthly_data.json"

def get_spotify_client():
    # Se usa el mismo scope que el recolector por consistencia, 
    # aunque main.py ahora podría no necesitar tokens si solo lee JSON, 
    # pero lo usamos para bajar la foto de alta calidad del artista.
    scope = "user-read-recently-played"
    auth_manager = SpotifyOAuth(scope=scope)
    return spotipy.Spotify(auth_manager=auth_manager)

def create_instagram_story_image(sp, top_artist_id, top_artists_data, top_tracks_data):
    # Intentar descargar la imagen del artista número 1 usando la API de Spotify
    bg_image = None
    if top_artist_id:
        try:
            artist_info = sp.artist(top_artist_id)
            if artist_info['images']:
                img_url = artist_info['images'][0]['url']
                response = requests.get(img_url)
                bg_image = Image.open(io.BytesIO(response.content)).convert("RGBA")
        except Exception as e:
            print("Error descargando la imagen del artista:", e)

    # Crear lienzo 1080x1920
    width, height = 1080, 1920
    img = Image.new('RGBA', (width, height), color=(20, 20, 20, 255))

    # Pegar y escalar imagen de fondo si existe
    if bg_image:
        bg_ratio = bg_image.width / bg_image.height
        canvas_ratio = width / height
        if bg_ratio > canvas_ratio:
            new_h = height
            new_w = int(new_h * bg_ratio)
        else:
            new_w = width
            new_h = int(new_w / bg_ratio)
            
        bg_image = bg_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        x = (width - new_w) // 2
        y = (height - new_h) // 2
        img.paste(bg_image, (x, y))

    # Oscurecer fondo (40% de brillo)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.4)

    draw = ImageDraw.Draw(img)
    
    # Fuentes
    try:
        font_title = ImageFont.truetype("fonts/font.ttf", 90)
        font_header = ImageFont.truetype("fonts/font.ttf", 60)
        font_text = ImageFont.truetype("fonts/font.ttf", 45)
        font_small = ImageFont.truetype("fonts/font.ttf", 35)
    except IOError:
        font_title = font_header = font_text = font_small = ImageFont.load_default()

    # Título
    title = "Mi Mes"
    title2 = "en Spotify"
    draw.text((width/2, 200), title, fill=(30, 215, 96, 255), font=font_title, anchor="mm")
    draw.text((width/2, 300), title2, fill=(255, 255, 255, 255), font=font_title, anchor="mm")
    
    # Top Artistas (Top 5)
    draw.text((100, 450), "Top Artistas", fill=(30, 215, 96, 255), font=font_header)
    y_offset = 550
    for idx, artist in enumerate(top_artists_data[:5]):
        name = artist['name']
        minutes = artist['count']
        draw.text((100, y_offset), f"{idx + 1}. {name}", fill=(255, 255, 255, 255), font=font_text)
        draw.text((150, y_offset + 55), f"{minutes} mins escuchados", fill=(180, 180, 180, 255), font=font_small)
        y_offset += 120

    # Top Canciones (Top 5)
    draw.text((100, y_offset + 50), "Top Canciones", fill=(30, 215, 96, 255), font=font_header)
    y_offset += 150
    for idx, track in enumerate(top_tracks_data[:5]):
        track_name = track['name']
        if len(track_name) > 30:
            track_name = track_name[:27] + "..."
        artist_name = track['artist_name']
        plays = track['count']
        draw.text((100, y_offset), f"{idx + 1}. {track_name}", fill=(255, 255, 255, 255), font=font_text)
        draw.text((150, y_offset + 55), f"{artist_name} • {plays} plays", fill=(180, 180, 180, 255), font=font_small)
        y_offset += 120

    output_path = f"historial_mensual_{int(datetime.datetime.now().timestamp())}.jpg"
    img.convert("RGB").save(output_path, "JPEG", quality=90)
    return output_path

def send_telegram_photo(photo_path, caption):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Faltan credenciales de Telegram.")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": chat_id, "caption": caption}
        response = requests.post(url, files=files, data=data)
        
    if response.status_code == 200:
        print("✅ Foto enviada a Telegram.")
    else:
        print("❌ Error Telegram:", response.text)

def main():
    if not os.path.exists(DATA_FILE):
        print("No hay datos recolectados esta semana.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    if not data:
        print("El historial está vacío.")
        return

    sp = get_spotify_client()
    
    # --- ANÁLISIS DE DATOS ---
    # Calcular minutos totales por artista
    artist_duration_ms = defaultdict(int)
    for item in data:
        artist_duration_ms[item['artist_id']] += item.get('duration_ms', 0)
        
    # Convertir a minutos (ms // 60000)
    artist_minutes = {aid: ms // 60000 for aid, ms in artist_duration_ms.items()}
    
    # Counter usa la estructura dict internamente, así que sirve perfecto para most_common
    artist_counter = Counter(artist_minutes)
    
    # Las canciones sí las rankeamos por cantidad de reproducciones
    track_counter = Counter(item['track_id'] for item in data)
    
    # Diccionarios para resolver ID -> Nombre rápidamente
    artist_names = {item['artist_id']: item['artist_name'] for item in data}
    track_names = {item['track_id']: item['track_name'] for item in data}
    track_to_artist = {item['track_id']: item['artist_name'] for item in data}

    # Extraer Tops
    top_artists_ids = [k for k, v in artist_counter.most_common(15)]
    top_tracks_ids = [k for k, v in track_counter.most_common(15)]
    
    # Aquí "count" guarda los MINUTOS para los artistas
    top_artists_data = [{"id": aid, "name": artist_names[aid], "count": artist_counter[aid]} for aid in top_artists_ids]
    # Aquí "count" guarda las REPRODUCCIONES para las canciones
    top_tracks_data = [{"id": tid, "name": track_names[tid], "artist_name": track_to_artist[tid], "count": track_counter[tid]} for tid in top_tracks_ids]
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Crear Markdown
    artists_md = "### 🎤 Top Artistas del Mes (Por tiempo)\n\n"
    for idx, artist in enumerate(top_artists_data):
        artists_md += f"{idx + 1}. **{artist['name']}** ({artist['count']} minutos escuchados)\n"
        
    tracks_md = "### 🎵 Top Canciones del Mes (Por reproducciones)\n\n"
    for idx, track in enumerate(top_tracks_data):
        tracks_md += f"{idx + 1}. **{track['name']}** - {track['artist_name']} ({track['count']} reproducciones)\n"
        
    content = f"## 🎧 Historial Real del Mes - {now}\n\n{artists_md}\n{tracks_md}\nTotal de canciones escuchadas: {len(data)}\n\n---\n\n"
    
    md_file = "historial_mensual.md"
    existing_content = ""
    if os.path.exists(md_file):
        with open(md_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
            
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content + existing_content)
        
    print(f"✅ Markdown actualizado: {md_file}")
    
    # Imagen y Telegram
    try:
        top_artist_id = top_artists_data[0]['id'] if top_artists_data else None
        img_path = create_instagram_story_image(sp, top_artist_id, top_artists_data, top_tracks_data)
        caption = f"🎵 ¡Tu resumen REAL MENSUAL está listo! ({now.split()[0]})\nEscuchaste {len(data)} canciones en total."
        send_telegram_photo(img_path, caption)
    except Exception as e:
        print(f"Error generando imagen/telegram: {e}")
        
    # Vaciar el JSON para la nueva semana
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    print("🧹 Datos de la semana vaciados exitosamente.")

if __name__ == "__main__":
    main()
