<div align="center">

# YouTubeShortsAuto

**Automatizacion completa de YouTube Shorts con Inteligencia Artificial**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-black?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web_UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

---

Genera automaticamente YouTube Shorts completos: **topic, script, imagenes, voz, subtitulos y upload** a YouTube, TikTok e Instagram.

[Instalacion Rapida](#instalacion-rapida) | [Funcionalidades](#funcionalidades) | [Docker](#docker)

</div>

---

## Funcionalidades

### Pipeline Principal
| Feature | Descripcion | Estado |
|---------|-------------|--------|
| **Generador de Topics** | IA crea topics unicos basados en tu nicho o genero seleccionado | OK |
| **Scripts con IA** | Genera guiones completos con Ollama (100% local) | OK |
| **Imagenes AI** | Genera imagenes cinematicas con Pollinations AI (gratis) o Gemini | OK |
| **Voz Natural** | Edge TTS con voces en 10+ idiomas | OK |
| **Subtitulos** | Generacion automatica con Whisper + personalizacion completa | OK |
| **Upload Automatico** | Sube a YouTube, TikTok o Instagram via Selenium | OK |

### Funciones Avanzadas
| Feature | Descripcion | Estado |
|---------|-------------|--------|
| **Web UI Profesional** | Interfaz oscura con Streamlit, mobile responsive | OK |
| **Selector de Generos** | 11 generos predefinidos + tema personalizado | OK |
| **Estilos de Subtitulos** | 8 estilos predefinidos (Clasico, Horror, Neon, Cyberpunk, etc.) | OK |
| **Transparencia** | Control de opacidad para fondo y texto de subtitulos | OK |
| **Preview de Video** | Reproductor integrado despues de generar | OK |
| **Auto-upload** | Sube automaticamente a YouTube al generar | OK |
| **Multi-canal** | Gestiona multiples canales con diferentes nichos | OK |
| **Batch Generation** | Genera videos para varios canales simultaneamente | OK |
| **Programador de Uploads** | Programa uploads automaticos a horas pico | OK |
| **Historial y Analytics** | Estadisticas completas con graficas interactivas | OK |
| **Multi-idioma** | Soporte para ES, EN, PT, FR, DE, IT, JA, KO, ZH, HI | OK |
| **Sonidos Ambientales** | Lluvia, truenos, viento, susurros para horror | OK |
| **Notificaciones** | Desktop push y email al completar | OK |
| **Drag and Drop** | Sube imagenes y musica personalizadas | OK |
| **Rate Limiting** | Proteccion contra bans de APIs | OK |
| **Encriptar Credenciales** | Seguridad con encriptacion AES | OK |
| **Docker** | Despliegue facil con Docker Compose | OK |

---

## Instalacion Rapida

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

Editar `config.json` con tu configuracion.

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
git clone https://github.com/nredondo26/YouTubeShortsAuto.git
cd YouTubeShortsAuto

cp config.example.json config.json
# Editar config.json...

docker-compose up -d

# Con Whisper:
docker-compose --profile with-whisper up -d
```

Abrir: **http://localhost:8501**

---

## Configuracion

### Archivo config.json

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
  "subtitle_bg_alpha": 60,
  "subtitle_text_alpha": 100,
  
  "nanobanana2_api_key": "",
  "nanobanana2_model": "gemini-2.5-flash-image"
}
```

### Perfil de Firefox

1. Abrir Firefox con el Administrador de Perfiles: `firefox -P`
2. Crear un perfil nuevo para YouTube
3. **Iniciar sesion en YouTube** con ese perfil
4. Copiar la ruta del perfil en `config.json`

**Importante:** Cerrar Firefox antes de ejecutar el script.

---

## Uso

### Web UI (Recomendado)

```bash
py -m streamlit run web.py
```

Abrir **http://localhost:8501**

**Funciones disponibles:**
- Dashboard con graficas de analytics
- Generar Short con selector de generos y preview
- Gestionar multiples cuentas
- Programar uploads automaticos
- Generacion batch multi-canal
- Historial y estadisticas
- Configuracion visual con estilos de subtitulos

### Generar Video

1. Seleccionar cuenta
2. Elegir genero/tema (o usar nicho de la cuenta)
3. Configurar subtitulos (color, estilo, transparencia)
4. Click en "GENERAR VIDEO"
5. El video se sube automaticamente a YouTube

### CLI

```bash
py generar_y_subir.py
```

---

## Subtitulos Personalizados

### Estilos Predefinidos

| Estilo | Color Texto | Color Borde | Borde |
|--------|-------------|-------------|-------|
| Clasico | #FFFF00 (Amarillo) | #000000 | 4px |
| Moderno | #FFFFFF (Blanco) | #000000 | 3px |
| Horror | #FF0000 (Rojo) | #000000 | 5px |
| Neon | #00FFFF (Cyan) | #FF00FF | 3px |
| Golden | #FFD700 (Dorado) | #8B4513 | 4px |
| Minimal | #CCCCCC (Gris) | #333333 | 2px |
| Cyberpunk | #FF00FF (Magenta) | #00FFFF | 4px |
| Retro | #FFA500 (Naranja) | #000000 | 5px |

### Transparencia

- **Fondo subtitulos**: 0% (transparente) a 100% (opaco)
- **Opacidad texto**: 0% (invisible) a 100% (completamente visible)

Configurar en `config.json`:
```json
{
  "subtitle_bg_alpha": 60,
  "subtitle_text_alpha": 100
}
```

---

## Generos Disponibles

| Genero | Tema |
|--------|------|
| Nicho de la cuenta | Usa el nicho configurado |
| Historias de terror | Terror, misterio, leyendas urbanas |
| Misterio y conspiraciones | Conspiraciones, secretos oscuros |
| Ciencia y naturaleza | Curiosidades, descubrimientos |
| Historia y cultura | Civilizaciones antiguas |
| Tecnologia y futuro | IA, innovacion |
| Filosofia y psicologia | Reflexiones profundas |
| Crimen real | Casos policiacos |
| Mitologia y leyendas | Dioses, criaturas mitologicas |
| Misterio espacial | Universo, vida extraterrestre |
| Terror psicologico | Suspense, manipulacion |

---

## Multi-idioma

Soporte para 10 idiomas con voces naturales:

| Codigo | Idioma | Voz Default |
|--------|--------|-------------|
| `es` | Espanol | es-CO-GonzaloNeural |
| `en` | English | en-US-GuyNeural |
| `pt` | Portugues | pt-BR-AntonioNeural |
| `fr` | Francais | fr-FR-HenriNeural |
| `de` | Deutsch | de-DE-ConradNeural |
| `it` | Italiano | it-IT-DiegoNeural |
| `ja` | Japones | ja-JP-KeitaNeural |
| `ko` | Coreano | ko-KR-InJoonNeural |
| `zh` | Chino | zh-CN-YunxiNeural |
| `hi` | Hindi | hi-IN-MadhurNeural |

---

## Docker

### Servicios

| Servicio | Puerto | Descripcion |
|----------|--------|-------------|
| `app` | 8501 | Streamlit Web UI |
| `ollama` | 11434 | LLM Local |
| `whisper` | 9000 | Speech-to-Text (opcional) |

### Comandos

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
docker-compose --profile with-whisper up -d
docker-compose build --no-cache
```

---

## Estructura del Proyecto

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
├── web.py                # Streamlit Web UI
├── generar_y_subir.py    # CLI script
├── Dockerfile            # Docker
├── docker-compose.yml    # Docker Compose
├── config.example.json   # Ejemplo config
├── requirements.txt      # Dependencias
└── .gitignore
```

---

## Solucion de Problemas

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

## Roadmap

- [ ] CI/CD con GitHub Actions
- [ ] Telegram Bot para control remoto
- [ ] Webhook para integraciones
- [ ] Soporte para mas plataformas (Twitch, Kick)

---

## Contribuir

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

## Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para mas informacion.

---

<div align="center">

**Hecho con Python + Ollama + Selenium + Streamlit**

[![GitHub](https://img.shields.io/badge/GitHub-nredondo26-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/nredondo26)

</div>
