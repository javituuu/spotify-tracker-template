# Spotify Weekly & Monthly Tracker 

¡Automatiza tu propio "Spotify Wrapped" durante todo el año! Este proyecto funciona como un *Data Logger* que guarda silenciosamente tu historial de reproducción en GitHub Actions cada 4 horas y te envía resúmenes generados con código (imágenes y estadísticas) directamente a Telegram cada domingo y cada principio de mes.

> [!WARNING]
> **CRÍTICO PARA TU PRIVACIDAD:** 
> Este proyecto guarda la música que escuchas en un archivo `.json` dentro del repositorio usando GitHub Actions. **Si haces tu repositorio público, todo el mundo podrá ver a qué hora exacta escuchaste cada canción.**
> ¡Por favor, asegúrate de crear tu clon (Fork) como un repositorio **PRIVADO**!

## Características 
- **Exactitud Matemática**: Mide a tus artistas más escuchados por la cantidad de **minutos** reales que los escuchaste, y a las canciones por la cantidad de **reproducciones**, justo como el Spotify Wrapped oficial.
- **Doble Reporte**: Obtén un resumen Semanal (Domingos) y un mega resumen Mensual (día 1 de cada mes).
- **100% Gratis y Automático**: Corre en la nube usando las horas gratuitas de GitHub Actions. Una vez configurado, puedes olvidarte de él.
- **Directo a Telegram**: Las imágenes listas para subir a Instagram Stories te llegan por mensaje privado.

---

## Guía de Instalación (Paso a Paso)

### 1. Clonar este proyecto
1. Dale al botón **"Use this template"** o haz un **"Fork"** de este repositorio.
2. **¡MUY IMPORTANTE!** Asegúrate de marcar la casilla para que tu nuevo repositorio sea **PRIVADO**.

### 2. Crear tu Bot de Telegram
1. Abre Telegram y busca a `@BotFather`.
2. Envíale `/newbot` y sigue los pasos para crear tu bot. Al final, te dará un **HTTP API Token**. Guárdalo bien.
3. Busca a `@userinfobot` y envíale `/start`. Te dará tu `Id` (una serie de números). Este es tu **Chat ID**.

### 3. Crear tu App de Spotify
1. Ve al [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) e inicia sesión.
2. Haz clic en "Create app". Llámala "Tracker" o como quieras.
3. En **Redirect URI**, debes poner exactamente: `http://127.0.0.1:8888/callback`
4. Ve a *Settings* en tu app y copia tu **Client ID** y tu **Client Secret**.

### 4. Generar tu Archivo de Autorización (.cache)
Para que GitHub Actions pueda leer tu historial, primero debes darle permiso desde tu computadora:
1. Clona tu repositorio privado en tu computadora local.
2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Crea un archivo llamado `.env` en la carpeta principal y pon tus credenciales de Spotify:
   ```env
   SPOTIPY_CLIENT_ID="pega_aqui_tu_client_id"
   SPOTIPY_CLIENT_SECRET="pega_aqui_tu_client_secret"
   SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"
   ```
4. Corre el script de recolección por primera vez:
   ```bash
   python collect.py
   ```
5. Esto abrirá tu navegador web. Inicia sesión en Spotify y dale a "Aceptar". Te redirigirá a una página que dice "No se puede conectar", no te preocupes, simplemente copia la URL de esa página y pégala en la terminal.
6. Si funcionó, se creará un archivo oculto llamado `.cache`. Abre este archivo y **copia todo su contenido de texto**.

### 5. Configurar los Secrets en GitHub
Ahora solo falta darle los datos a GitHub para que trabaje por ti.
1. Ve a tu repositorio privado en GitHub > **Settings** > **Secrets and variables** > **Actions**.
2. Añade los siguientes "Repository secrets":
   - `SPOTIPY_CLIENT_ID`: Pega tu Client ID.
   - `SPOTIPY_CLIENT_SECRET`: Pega tu Client Secret.
   - `SPOTIFY_CACHE`: Pega el contenido de texto de tu archivo `.cache`.
   - `TELEGRAM_BOT_TOKEN`: Pega el Token de BotFather.
   - `TELEGRAM_CHAT_ID`: Pega el ID de userinfobot.

### ¡Listo! 
Todo el sistema está operativo. GitHub Actions ejecutará automáticamente la recolección cada 4 horas y te enviará los reportes correspondientes. 

*(Si quieres forzar un envío para probar que todo funcione, puedes ir a la pestaña "Actions" en tu repositorio, seleccionar el "Spotify Weekly Tracker" y darle a "Run workflow").*
