<div align="center">

# 🎬 YouTubeShortsAuto

**Automatizacion completa de YouTube Shorts con Inteligencia Artificial**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-black?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web_UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

---

Genera automaticamente YouTube Shorts completos: **topic, script, imagenes, voz, subtitulos y upload** a YouTube, TikTok e Instagram.

[🚀 Instalacion Rapida](#-instalacion-rapida) | [📖 Documentacion](#-documentacion) | [🎨 Funcionalidades](#-funcionalidades) | [🐳 Docker](#-docker)

</div>

---

## 📋 Tabla de Contenidos

- [Funcionalidades](#-funcionalidades)
- [Arquitectura](#-arquitectura)
- [Instalacion Rapida](#-instalacion-rapida)
- [Configuracion](#-configuracion)
- [Uso](#-uso)
- [Documentacion](#-documentacion)
- [Multi-idioma](#-multi-idioma)
- [Docker](#-docker)
- [Solucion de Problemas](#-solucion-de-problemas)
- [Roadmap](#-roadmap)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## 🎯 Funcionalidades

### Pipeline Principal
| Feature | Descripcion | Estado |
|---------|-------------|--------|
| **Generador de Topics** | IA crea topics unicos basados en tu nicho, evitando repeticiones | ✅ |
| **Scripts con IA** | Genera guiones completos con Ollama (100% local) | ✅ |
| **Imagenes AI** | Genera imagenes cinematicas con Pollinations AI (gratis) o Gemini | ✅ |
| **Voz Natural** | Edge TTS con voces en 10+ idiomas | ✅ |
| **Subtitulos** | Generacion automatica con Whisper o AssemblyAI + personalizacion completa | ✅ |
| **Upload Automatico** | Sube a YouTube, TikTok o Instagram via Selenium | ✅ |

### Funciones Avanzadas
| Feature | Descripcion | Estado |
|---------|-------------|--------|
| **Web UI** | Interfaz grafica con Streamlit, dark mode, mobile responsive | ✅ |
| **Multi-canal** | Gestiona multiples canales con diferentes nichos | ✅ |
| **Batch Generation** | Genera videos para varios canales simultaneamente | ✅ |
| **Programador de Uploads** | Programa uploads automaticos a horas pico | ✅ |
| **Historial y Analytics** | Estadisticas completas con graficas interactivas | ✅ |
| **Subtitulos Personalizados** | Colores, fuentes, posicion, tamano | ✅ |
| **Multi-idioma** | Soporte para ES, EN, PT, FR, DE, IT, JA, KO, ZH, HI | ✅ |
| **Sonidos Ambientales** | Lluvia, truenos, viento, susurros para horror | ✅ |
| **Musica Automatica** | Descarga musica libre si no hay archivos locales | ✅ |
| **Notificaciones** | Desktop push y email al completar | ✅ |
| **Drag & Drop** | Sube imagenes y musica personalizadas | ✅ |
| **Rate Limiting** | Proteccion contra bans de APIs | ✅ |
| **Encriptar Credenciales** | Seguridad con encriptacion AES | ✅ |
| **YouTube Analytics** | Estadisticas de canal y videos | ✅ |
| **Docker** | Despliegue facil con Docker Compose | ✅ |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        YouTubeShortsAuto                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│  │   Streamlit │────▶│   Pipeline  │────▶│  Plataformas │      │
│  │   Web UI    │     │   Principal │     │  YouTube/TikTok│    │
│  └─────────────┘     └─────────────┘     └─────────────┘      │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         │                  │                  │                │
│   ┌─────┴─────┐      ┌─────┴─────┐      ┌─────┴─────┐        │
│   │  Ollama   │      │  Images   │      │    TTS    │        │
│   │  (Local)  │      │Pollinations│     │ Edge TTS  │        │
│   └───────────┘      └───────────┘      └───────────┘        │
│         │                  │                  │                │
│   ┌─────┴─────┐      ┌─────┴─────┐      ┌─────┴─────┐        │
│   │  Script   │      │  Subtitles│      │   Music   │        │
│   │  IA       │      │ Whisper   │      │   + SFX   │        │
│   └───────────┘      └───────────┘      └───────────┘        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  📊 Analytics │ 🛡️ Rate Limiting │ 🔐 Encryption │ 📱 Mobile   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Instalacion Rapida

### Opcion 1: Instalacion Local

#### 1. Clonar repositorio

```bash
git clone https://github.com/nredondo26/YouTubeShortsAuto.git
cd YouTubeShortsAuto
```

#### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 3. Instalar Ollama

```bash
# Instalar Ollama (https://ollama.ai)
# Windows: descargar desde https://ollama.ai/download
# Linux/Mac:
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo
ollama pull llama3.2:3b
```

#### 4. Configurar

```bash
cp config.example.json config.json
```

Editar `config.json` con tu configuracion (ver [Configuracion](#-configuracion)).

#### 5. Ejecutar

```bash
# Web UI
py -m streamlit run web.py

# CLI
py generar_y_subir.py
```

---

### Opcion 2: Docker (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/nredondo26/YouTubeShortsAuto.git
cd YouTubeShortsAuto

# Copiar configuracion
cp config.example.json config.json
# Editar config.json...

# Ejecutar con Docker Compose
docker-compose up -d

# Con Whisper tambien:
docker-compose --profile with-whisper up -d
```

Abrir en: **http://localhost:8501**

---

## ⚙️ Configuracion

### Archivo `config.json`

```json
{
  "verbose": true,
  "headless": false,
  "threads": 2,
  "is_for_kids": false,
  
  "ollama_base_url": "http://127.0.0.1:11434",
  "ollama_model": "llama3.2:3b",
  
  "firefox_profile": "C:\\Users\\TU_USUARIO\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\XXXXX.default",
  
  "tts_voice": "es-CO-GonzaloNeural",
  "tts_rate": "-10%",
  
  "script_sentence_length": 4,
  "subtitle_max_chars": 40,
  "subtitle_color": "#FFFF00",
  "subtitle_stroke_color": "#000000",
  "subtitle_stroke_width": 4,
  "subtitle_font_size": 80,
  "subtitle_position": "center",
  
  "nanobanana2_api_key": "",
  "nanobanana2_model": "gemini-2.5-flash-image"
}
```

### Perfil de Firefox

1. Abrir Firefox con el Administrador de Perfiles:
```bash
firefox -P
```

2. Crear un perfil nuevo para YouTube (ej: "YouTubeAuto")

3. **Iniciar sesion en YouTube** con ese perfil

4. Copiar la ruta del perfil en `config.json`

> ⚠️ **Importante:** Cerrar Firefox antes de ejecutar el script.

---

## 📖 Uso

### Web UI (Recomendado)

```bash
py -m streamlit run web.py
```

Abrir **http://localhost:8501** en tu navegador.

**Funciones disponibles:**
- 🏠 Dashboard con graficas de analytics
- 🎥 Generar Short con preview antes de subir
- 👤 Gestionar multiples cuentas
- 📅 Programar uploads automaticos
- 🚀 Generacion batch multi-canal
- 📜 Historial y estadisticas
- ⚙️ Configuracion visual

### CLI

```bash
# Generar y subir video
py generar_y_subir.py

# Solo generar (sin subir)
py -c "from src.youtube import YouTube; yt = YouTube(...); yt.generate_video()"
```

### Windows Batch

Doble clic en `iniciar_web.bat`

---

## 📖 Documentacion

### Subtitulos Personalizados

Configura el estilo de los subtitulos en `config.json`:

```json
{
  "subtitle_color": "#FFFF00",
  "subtitle_stroke_color": "#000000",
  "subtitle_stroke_width": 4,
  "subtitle_font_size": 80,
  "subtitle_position": "center",
  "subtitle_max_width": 1000
}
```

| Parametro | Valores | Default |
|-----------|---------|---------|
| `subtitle_color` | Cualquier color hex | `#FFFF00` |
| `subtitle_stroke_color` | Color del borde | `#000000` |
| `subtitle_stroke_width` | Ancho del borde (px) | `4` |
| `subtitle_font_size` | Tamano de fuente (px) | `80` |
| `subtitle_position` | `top`, `center`, `bottom` | `center` |

### Rate Limiting

El sistema incluye rate limiting automatico para evitar bans:

```python
from src.rate_limit import rate_limit, get_rate_limits

# Usar decorador
@rate_limit("ollama")
def call_llm():
    ...

# Verificar manualmente
limits = get_rate_limits()
if limits.check_rate_limit("gemini"):
    # Hacer request
    pass
```

**Limites por defecto:**
- Ollama: 10 req/60s
- Gemini: 15 req/60s
- YouTube Upload: 5 req/5min

### Encriptar Credenciales

```python
from src.credentials import migrate_to_encrypted
migrate_to_encrypted()  # Encripta config.json
```

### YouTube Analytics

```python
from src.analytics import get_analytics

analytics = get_analytics()
if analytics.authenticate():
    stats = analytics.get_channel_stats()
    videos = analytics.get_recent_videos()
    report = analytics.get_analytics_report(days=30)
```

### Notificaciones

Configurar en `notifications.json`:

```json
{
  "desktop_enabled": true,
  "email_enabled": true,
  "email_config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "tu@email.com",
    "sender_password": "tu-password",
    "recipient_email": "destino@email.com"
  }
}
```

---

## 🌍 Multi-idioma

Soporte para 10 idiomas con voces naturales:

| Codigo | Idioma | Voz Default |
|--------|--------|-------------|
| `es` | Espanol | es-CO-GonzaloNeural |
| `en` | English | en-US-GuyNeural |
| `pt` | Portugues | pt-BR-AntonioNeural |
| `fr` | Francais | fr-FR-HenriNeural |
| `de` | Deutsch | de-DE-ConradNeural |
| `it` | Italiano | it-IT-DiegoNeural |
| `ja` | 日本語 | ja-JP-KeitaNeural |
| `ko` | 한국어 | ko-KR-InJoonNeural |
| `zh` | 中文 | zh-CN-YunxiNeural |
| `hi` | हिन्दी | hi-IN-MadhurNeural |

Cambiar en `config.json`:
```json
{
  "tts_voice": "en-US-GuyNeural"
}
```

---

## 🐳 Docker

### Servicios incluidos

| Servicio | Puerto | Descripcion |
|----------|--------|-------------|
| `app` | 8501 | Streamlit Web UI |
| `ollama` | 11434 | LLM Local |
| `whisper` | 9000 | Speech-to-Text (opcional) |

### Comandos

```bash
# Iniciar todo
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Con Whisper
docker-compose --profile with-whisper up -d

# Reconstruir
docker-compose build --no-cache
```

### Volumenes montados

- `config.json` → Configuracion
- `fonts/` → Fuentes personalizadas
- `Songs/` → Musica de fondo
- `.mp/` → Cache y archivos temporales

---

## 📱 Estructura del Proyecto

```
YouTubeShortsAuto/
├── src/
│   ├── ambient.py        # Sonidos ambientales
│   ├── analytics.py      # YouTube Analytics API
│   ├── batch.py          # Multi-canal batch
│   ├── cache.py          # Cache de cuentas/videos
│   ├── config.py         # Configuracion
│   ├── constants.py      # Constantes
│   ├── credentials.py    # Encriptar credenciales
│   ├── languages.py      # Multi-idioma
│   ├── llm.py            # Integracion Ollama
│   ├── main.py           # CLI interactivo
│   ├── music.py          # Musica automatica
│   ├── notifications.py  # Notificaciones
│   ├── platforms.py      # TikTok/Instagram
│   ├── rate_limit.py     # Rate limiting
│   ├── scheduler.py      # Programador uploads
│   ├── status.py         # Logging
│   ├── tts.py            # Text-to-Speech
│   ├── utils.py          # Utilidades
│   └── youtube.py        # Pipeline principal
├── tests/                # Tests unitarios
│   ├── test_config.py
│   ├── test_cache.py
│   ├── test_languages.py
│   ├── test_notifications.py
│   └── test_scheduler.py
├── web.py                # Streamlit Web UI
├── generar_y_subir.py    # CLI script
├── Dockerfile            # Docker
├── docker-compose.yml    # Docker Compose
├── config.example.json   # Ejemplo config
├── requirements.txt      # Dependencias
└── .gitignore
```

---

## 🔧 Solucion de Problemas

| Problema | Solucion |
|----------|----------|
| Firefox no inicia | Cerrar todas las ventanas y verificar ruta del perfil |
| Error CSP en upload | `pip install --upgrade webdriver-manager` |
| Subtitulos no aparecen | `pip install faster-whisper srt srt_equalizer` |
| Ollama no responde | Verificar: `ollama list` y `ollama serve` |
| Imagenes no generan | Verificar conexion a internet |
| Docker no inicia | Verificar Docker Desktop esta corriendo |
| Rate limit excedido | Esperar o ajustar limites en `rate_limits.json` |

---

## 🗺️ Roadmap

- [x] Multi-canal con batch generation
- [x] Programacion de uploads
- [x] Soporte TikTok e Instagram
- [x] Generacion de thumbnails
- [x] Analytics y estadisticas con graficas
- [x] Subtitulos personalizados
- [x] Multi-idioma (10 idiomas)
- [x] Docker + Docker Compose
- [x] Tests unitarios
- [x] Encriptar credenciales
- [x] Rate limiting
- [x] Notificaciones
- [ ] CI/CD con GitHub Actions
- [ ] Telegram Bot para control remoto
- [ ] Webhook para integraciones
- [ ] Soporte para mas plataformas (Twitch, Kick)

---

## 🤝 Contribuir

Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea una branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Add nueva funcionalidad'`)
4. Push (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Ejecutar Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=src
```

---

## 📄 Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para mas informacion.

---

<div align="center">

**Hecho con Python + Ollama + Selenium + Streamlit**

[![GitHub](https://img.shields.io/badge/GitHub-nredondo26-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/nredondo26)

⭐ Star este repositorio si te fue util!

</div>
