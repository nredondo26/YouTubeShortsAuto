# YouTube Shorts Auto

Automatizacion completa para crear y subir YouTube Shorts con IA.

## Caracteristicas

- **Generacion automatica de topics** basados en el nicho del canal
- **Scripts con IA** usando Ollama (local, sin API keys)
- **Generacion de imagenes** con Pollinations AI (gratis) o Gemini
- **Voz en espanol** con Edge TTS (voces mexicanas, colombianas, etc.)
- **Subtitulos automaticos** con Whisper o AssemblyAI
- **Upload automatico** a YouTube via Selenium (como No Listado)
- **Videos unicos** - el sistema evita repetir topics anteriores

## Requisitos

- Python 3.10+
- Ollama instalado con modelo `llama3.2:3b`
- Firefox con perfil autenticado en YouTube
- Geckodriver (se instala automaticamente)

## Instalacion

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/YouTubeShortsAuto.git
cd YouTubeShortsAuto

# Instalar dependencias
pip install -r requirements.txt

# Instalar modelo de Ollama
ollama pull llama3.2:3b
```

## Configuracion

1. Copiar el archivo de configuracion de ejemplo:
```bash
cp config.example.json config.json
```

2. Editar `config.json` con tu configuracion:
```json
{
  "script_sentence_length": 4,
  "is_for_kids": false,
  "subtitle_max_chars": 40,
  "headless": false,
  "tts_voice": "es-CO-GonzaloNeural"
}
```

### Configurar perfil de Firefox

1. Abrir Firefox con tu perfil de YouTube:
```bash
firefox -P
```

2. Copiar la ruta del perfil en `config.json`:
```json
{
  "firefox_profile_path": "C:\\Users\\TU_USUARIO\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\XXXXX.default"
}
```

## Uso

### Opcion 1: CLI (recomendado)

Genera un video y lo sube a YouTube automaticamente:

```bash
py generar_y_subir.py
```

**Importante:** Cerrar Firefox antes de ejecutar (el perfil no puede estar en uso).

### Opcion 2: Web UI

Interfaz web para generar videos:

```bash
py -m streamlit run web.py
```

Abrir en: http://localhost:8501

## Estructura del Proyecto

```
YouTubeShortsAuto/
├── src/
│   ├── __init__.py
│   ├── cache.py          # Cache de cuentas y videos
│   ├── config.py         # Configuracion del proyecto
│   ├── constants.py      # Constantes de YouTube
│   ├── llm.py            # Integracion con Ollama
│   ├── main.py           # CLI interactivo
│   ├── status.py         # Sistema de logging
│   ├── tts.py            # Text-to-Speech con Edge TTS
│   ├── utils.py          # Utilidades generales
│   └── youtube.py        # Pipeline principal
├── config.json           # Tu configuracion (NO subir)
├── config.example.json   # Ejemplo de configuracion
├── web.py                # Interfaz web con Streamlit
├── generar_y_subir.py    # Script CLI para generar y subir
├── iniciar_web.bat       # Iniciar web UI en Windows
├── requirements.txt      # Dependencias de Python
└── .gitignore
```

## Configuracion de Voz

El proyecto usa Edge TTS con voces en espanol. Voces disponibles:

| Voz | Pais | Genero |
|-----|------|--------|
| `es-MX-JorgeNeural` | Mexico | Masculina |
| `es-CO-GonzaloNeural` | Colombia | Masculina |
| `es-PE-CamilaNeural` | Peru | Femenina |
| `es-AR-ElenaNeural` | Argentina | Femenina |

Cambiar en `config.json`:
```json
{
  "tts_voice": "es-CO-GonzaloNeural"
}
```

## Generacion de Imagenes

Por defecto usa **Pollinations AI** (gratis, sin API key).

Para usar **Gemini**, configurar en `config.json`:
```json
{
  "nanobanana2_api_key": "TU_API_KEY",
  "nanobanana2_model": "gemini-2.5-flash-image"
}
```

## Solucion de Problemas

### Firefox no inicia
- Cerrar todas las ventanas de Firefox
- Verificar que la ruta del perfil sea correcta

### Error CSP en upload
- Actualizar Geckodriver: `pip install --upgrade webdriver-manager`
- Usar version reciente de Firefox

### Subtitulos no aparecen
- Verificar que Whisper este instalado: `pip install faster-whisper`
- O configurar AssemblyAI en `config.json`

## Licencia

MIT
