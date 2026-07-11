<div align="center">

# YouTubeShortsAuto

**Automatizacion completa de YouTube Shorts con Inteligencia Artificial**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-black?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web_UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

---

Genera automaticamente YouTube Shorts completos: topic, script, imagenes, voz, subtitulos y upload a YouTube.

</div>

---

## Funcionalidades

| Feature | Descripcion |
|---------|-------------|
| **Generador de Topics** | IA crea topics unicos basados en tu nicho, evitando repeticiones |
| **Scripts con IA** | Genera guiones completos en espanol con Ollama (100% local) |
| **Imagenes AI** | Genera imagenes cinematicas con Pollinations AI (gratis) o Gemini |
| **Voz Natural** | Edge TTS con voces en espanol latino (mexicano, colombiano, etc.) |
| **Subtitulos** | Generacion automatica con Whisper o AssemblyAI |
| **Upload Automatico** | Sube directamente a YouTube como No Listado via Selenium |
| **Web UI** | Interfaz grafica con Streamlit para control total |

---

## Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Ollama    │────▶│  Pipeline   │────▶│   YouTube   │
│  (Local)    │     │   Principal │     │   Upload    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
     ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
     │  Images   │   │    TTS    │   │ Subtitles │
     │Pollinations│  │Edge TTS   │   │ Whisper   │
     └───────────┘   └───────────┘   └───────────┘
```

---

## Instalacion Rapida

### 1. Clonar repositorio

```bash
git clone https://github.com/nredondo26/YouTubeShortsAuto.git
cd YouTubeShortsAuto
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Instalar Ollama

```bash
# Instalar Ollama (https://ollama.ai)
ollama pull llama3.2:3b
```

### 4. Configurar

```bash
cp config.example.json config.json
```

Editar `config.json` con tu configuracion.

---

## Configuracion

### Archivo `config.json`

```json
{
  "verbose": true,
  "headless": false,
  "threads": 2,
  "is_for_kids": false,
  "firefox_profile": "C:\\Users\\TU_USUARIO\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\XXXXX.default",
  "ollama_base_url": "http://127.0.0.1:11434",
  "ollama_model": "",
  "tts_voice": "es-CO-GonzaloNeural",
  "script_sentence_length": 4,
  "subtitle_max_chars": 40
}
```

### Perfil de Firefox

1. Abrir Firefox con el Administrador de Perfiles:
```bash
firefox -P
```

2. Crear un perfil nuevo para YouTube (ej: "YouTubeAuto")

3. Iniciar sesion en YouTube con ese perfil

4. Copiar la ruta del perfil en `config.json`

---

## Uso

### Opcion 1: CLI (Recomendado)

Genera un video y lo sube a YouTube automaticamente:

```bash
py generar_y_subir.py
```

> **Importante:** Cerrar Firefox antes de ejecutar.

### Opcion 2: Web UI

Interfaz grafica para control total:

```bash
py -m streamlit run web.py
```

Abrir en: **http://localhost:8501**

### Opcion 3: Windows Batch

Doble clic en `iniciar_web.bat`

---

## Voz en Espanol

Voces disponibles con Edge TTS:

| Voz | Pais | Genero | Estilo |
|-----|------|--------|--------|
| `es-MX-JorgeNeural` | Mexico | Masculina | Natural, versatil |
| `es-CO-GonzaloNeural` | Colombia | Masculina | Grave, serio |
| `es-PE-CamilaNeural` | Peru | Femenina | Suave, clara |
| `es-AR-ElenaNeural` | Argentina | Femenina | Profesional |
| `es-VE-SebastianNeural` | Venezuela | Masculina | Profesional |

Cambiar en `config.json`:
```json
{
  "tts_voice": "es-CO-GonzaloNeural"
}
```

---

## Generacion de Imagenes

### Opcion 1: Pollinations AI (Gratis)

No requiere configuracion. Funciona por defecto.

### Opcion 2: Gemini (Requiere API Key)

```json
{
  "nanobanana2_api_key": "TU_API_KEY_AQUI",
  "nanobanana2_model": "gemini-2.5-flash-image"
}
```

Obtener API Key: https://makersuite.google.com/app/apikey

---

## Estructura del Proyecto

```
YouTubeShortsAuto/
├── src/
│   ├── cache.py          # Cache de cuentas y videos
│   ├── config.py         # Configuracion del proyecto
│   ├── constants.py      # Constantes de YouTube
│   ├── llm.py            # Integracion con Ollama
│   ├── main.py           # CLI interactivo
│   ├── status.py         # Sistema de logging
│   ├── tts.py            # Text-to-Speech con Edge TTS
│   ├── utils.py          # Utilidades generales
│   └── youtube.py        # Pipeline principal
├── config.example.json   # Ejemplo de configuracion
├── web.py                # Interfaz web con Streamlit
├── generar_y_subir.py    # Script CLI para generar y subir
├── iniciar_web.bat       # Iniciar web UI en Windows
├── requirements.txt      # Dependencias de Python
└── .gitignore
```

---

## Solucion de Problemas

| Problema | Solucion |
|----------|----------|
| Firefox no inicia | Cerrar todas las ventanas de Firefox y verificar la ruta del perfil |
| Error CSP en upload | Actualizar: `pip install --upgrade webdriver-manager` |
| Subtitulos no aparecen | Instalar Whisper: `pip install faster-whisper` |
| Ollama no responde | Verificar que este corriendo: `ollama list` |
| Imagenes no generan | Verificar conexion a internet (Pollinations AI) |

---

## Roadmap

- [ ] Soporte para multiples canales
- [ ] Programacion de uploads (cron)
- [ ] Soporte para TikTok e Instagram Reels
- [ ] Generacion de thumbnails
- [ ] Analytics y estadisticas

---

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una branch para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Add nueva funcionalidad'`)
4. Push a la branch (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para mas informacion.

---

<div align="center">

**Hecho con Python + Ollama + Selenium**

[![GitHub](https://img.shields.io/badge/GitHub-nredondo26-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/nredondo26)

</div>
