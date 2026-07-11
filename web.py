"""YouTubeShortsAuto - Web UI con Streamlit.

Ejecutar con: streamlit run web.py
"""

import os
import sys
import time
import threading
import subprocess
import datetime
from collections import deque

import streamlit as st

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import (
    ROOT_DIR as PROJ_ROOT,
    MP_DIR,
    ensure_directories,
    get_first_time,
    get_verbose,
    get_ollama_model,
    reload_config,
    get as cfg_get,
)
from src.llm import list_models, select_model, get_active_model
from src.cache import get_accounts, add_account, remove_account, generate_uuid, get_videos
from src.utils import rem_temp_files, fetch_songs
from src.tts import TTS, list_voices
from src.youtube import YouTube
from src.status import info, success, warning, error, set_log_callback

# Thread-safe log buffer (no Streamlit dependency)
_log_lock = threading.Lock()
_pipeline_logs = deque(maxlen=200)
_upload_logs = deque(maxlen=200)
_pipeline_status = "idle"
_pipeline_result = None
_upload_status = None
_upload_error = None
_upload_account = None

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="YouTubeShortsAuto",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .status-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1.2rem;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    .metric-label {
        color: #888;
        font-size: 0.9rem;
    }
    .success-box {
        background: #1a3a1a;
        border: 1px solid #2d5a2d;
        border-radius: 8px;
        padding: 1rem;
        color: #4ade80;
    }
    .error-box {
        background: #3a1a1a;
        border: 1px solid #5a2d2d;
        border-radius: 8px;
        padding: 1rem;
        color: #f87171;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Session State
# ──────────────────────────────────────────────

if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "selected_account" not in st.session_state:
    st.session_state.selected_account = None


def initialize():
    """Initialize project directories and first-time setup."""
    if not st.session_state.initialized:
        ensure_directories()
        rem_temp_files()
        st.session_state.initialized = True


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## YouTubeShortsAuto")
        st.markdown("---")

        # Config status
        st.markdown("### ⚙️ Estado del Sistema")

        config_ok = os.path.exists(os.path.join(PROJ_ROOT, "config.json"))
        if config_ok:
            st.success("✅ config.json encontrado")
        else:
            st.error("❌ config.json no encontrado")

        model = get_ollama_model()
        if model:
            st.info(f"🤖 Modelo: `{model}`")
        else:
            st.warning("⚠️ Modelo no configurado")

        api_key = cfg_get("nanobanana2_api_key", "")
        if api_key:
            st.info("🔑 API Key: configurada")
        else:
            st.warning("⚠️ API Key no configurada")

        st.markdown("---")

        # Quick actions
        st.markdown("### 🚀 Acciones Rapidas")
        if st.button("🔄 Recargar Config", use_container_width=True):
            reload_config()
            st.success("Config recargada!")
            st.rerun()

        if st.button("🗑️ Limpiar Temporales", use_container_width=True):
            rem_temp_files()
            st.success("Temporales limpiados!")

        st.markdown("---")
        st.caption("YouTubeShortsAuto v1.0")
        st.caption("YouTube Shorts Automation")


# ──────────────────────────────────────────────
# Pages
# ──────────────────────────────────────────────

def page_dashboard():
    """Main dashboard with overview."""
    st.markdown('<h1 class="main-header">🎬 YouTubeShortsAuto</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">YouTube Shorts Automation Dashboard</p>', unsafe_allow_html=True)

    # Metrics
    accounts = get_accounts("youtube")
    total_videos = sum(len(a.get("videos", [])) for a in accounts)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Cuentas</div>
        </div>
        """.format(len(accounts)), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Videos Generados</div>
        </div>
        """.format(total_videos), unsafe_allow_html=True)

    with col3:
        model = get_ollama_model() or "No configurado"
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1rem;">🤖</div>
            <div class="metric-label">{}</div>
        </div>
        """.format(model[:20]), unsafe_allow_html=True)

    with col4:
        api_ok = bool(cfg_get("nanobanana2_api_key", ""))
        status = "✅ Listo" if api_ok else "⚠️ Falta API"
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1.2rem;">🎨</div>
            <div class="metric-label">{}</div>
        </div>
        """.format(status), unsafe_allow_html=True)

    st.markdown("---")

    # Recent videos
    st.markdown("### 📹 Videos Recientes")
    all_videos = []
    for acc in accounts:
        for v in acc.get("videos", []):
            v["account"] = acc.get("nickname", "?")
            all_videos.append(v)

    if all_videos:
        all_videos.sort(key=lambda x: x.get("date", ""), reverse=True)
        for v in all_videos[:5]:
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{v.get('title', 'Sin titulo')[:60]}**")
                c2.write(f"📁 {v.get('account', '?')} | 📅 {v.get('date', '?')}")
                if v.get("url"):
                    c3.link_button("Ver", v["url"], type="secondary")
    else:
        st.info("Aun no hay videos generados. Ve a **Generar Short** para crear el primero.")


def page_generate():
    """Video generation page."""
    global _pipeline_status, _pipeline_result, _upload_status, _upload_error, _upload_account

    st.markdown('<h1 class="main-header">🎥 Generar Short</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Genera un video completo con IA</p>', unsafe_allow_html=True)

    accounts = get_accounts("youtube")

    if not accounts:
        st.warning("No hay cuentas configuradas. Ve a **Cuentas** primero.")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        account_names = [f"{a['nickname']} ({a['niche']})" for a in accounts]
        selected_idx = st.selectbox("Seleccionar Cuenta", range(len(accounts)), format_func=lambda i: account_names[i])
        account = accounts[selected_idx]
    with col2:
        st.write("")
        st.write("")
        st.info(f"UUID: `{account['id'][:8]}...`")

    st.markdown("---")

    with st.expander("ℹ️ Informacion de la Cuenta", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Nickname", account.get("nickname", "?"))
        c2.metric("Niche", account.get("niche", "?"))
        c3.metric("Idioma", account.get("language", "?"))

    st.markdown("### ⚙️ Configuracion del Video")
    col1, col2 = st.columns(2)
    with col1:
        sentence_length = st.slider("Oraciones del guion", 2, 10, cfg_get("script_sentence_length", 4))
        is_for_kids = st.checkbox("Marcado para ninos", value=cfg_get("is_for_kids", False))
    with col2:
        subtitle_chars = st.slider("Caracteres por subtitulo", 10, 80, cfg_get("subtitle_max_chars", 40))
        headless = st.checkbox("Firefox headless (sin ventana)", value=cfg_get("headless", False))

    st.markdown("---")

    if _pipeline_status == "running":
        _render_running()
    elif _pipeline_status == "done":
        _render_result()
        if st.button("🔄 Generar otro video", use_container_width=True):
            _pipeline_status = "idle"
            _pipeline_result = None
            with _log_lock:
                _pipeline_logs.clear()
            st.rerun()
    elif _pipeline_status == "error":
        _render_result()
        if st.button("🔄 Reintentar", use_container_width=True):
            _pipeline_status = "idle"
            _pipeline_result = None
            with _log_lock:
                _pipeline_logs.clear()
            st.rerun()
    else:
        if st.button("🚀 GENERAR VIDEO", type="primary", use_container_width=True):
            _start_pipeline(account, sentence_length, is_for_kids, subtitle_chars, headless)
            st.rerun()


def _start_pipeline(account, sentence_length, is_for_kids, subtitle_chars, headless):
    global _pipeline_status, _pipeline_result, _upload_account, _upload_status

    _pipeline_status = "running"
    _pipeline_result = None
    _upload_account = account
    _upload_status = None
    with _log_lock:
        _pipeline_logs.clear()

    def log_callback(level, message):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with _log_lock:
            _pipeline_logs.append({"time": ts, "level": level, "msg": message})

    set_log_callback(log_callback)

    def pipeline_thread():
        global _pipeline_status, _pipeline_result
        try:
            from src import config
            config._config_cache = None
            reload_config()

            config._config_cache["script_sentence_length"] = sentence_length
            config._config_cache["is_for_kids"] = is_for_kids
            config._config_cache["subtitle_max_chars"] = subtitle_chars
            config._config_cache["headless"] = headless

            model = get_active_model() or get_ollama_model()
            if model:
                select_model(model)

            tts = TTS()
            yt = YouTube(
                account_uuid=account["id"],
                account_nickname=account["nickname"],
                fp_profile_path=account["firefox_profile"],
                niche=account["niche"],
                language=account["language"],
            )

            try:
                yt.generate_video(tts)
                _pipeline_result = {
                    "success": True,
                    "video_path": yt.video_path,
                    "metadata": yt.metadata,
                    "topic": yt.subject,
                }
                _pipeline_status = "done"
            except Exception as e:
                _pipeline_result = {"success": False, "error": str(e)}
                _pipeline_status = "error"
            finally:
                yt.close()
        except Exception as e:
            _pipeline_result = {"success": False, "error": str(e)}
            _pipeline_status = "error"
        finally:
            set_log_callback(None)

    thread = threading.Thread(target=pipeline_thread, daemon=True)
    thread.start()


def _render_logs_from_buffer(log_buf, max_lines=30):
    with _log_lock:
        entries = list(log_buf)
    if not entries:
        return
    lines = []
    for entry in entries[-max_lines:]:
        level = entry["level"]
        if level == "error":
            icon = "X"
        elif level == "success":
            icon = "+"
        elif level == "warning":
            icon = "!"
        else:
            icon = ">"
        lines.append(f"[{entry['time']}] {icon} {entry['msg']}")
    st.code("\n".join(lines), language=None)


def _render_running():
    st.info("⏳ Pipeline en ejecucion...")
    _render_logs_from_buffer(_pipeline_logs)
    time.sleep(2)
    st.rerun()


def _render_result():
    global _upload_status, _upload_error

    if not _pipeline_result:
        return

    with _log_lock:
        has_logs = len(_pipeline_logs) > 0
    if has_logs:
        with st.expander("📜 Log del pipeline", expanded=True):
            _render_logs_from_buffer(_pipeline_logs, max_lines=50)

    if _pipeline_result.get("success"):
        st.success("✅ Video generado exitosamente!")

        metadata = _pipeline_result.get("metadata", {})
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Tema:** {_pipeline_result.get('topic', '?')}")
            st.markdown(f"**Titulo:** {metadata.get('title', '?')}")
            st.markdown(f"**Descripcion:** {metadata.get('description', '?')[:200]}...")
        with col2:
            video_path = _pipeline_result.get("video_path", "")
            if video_path and os.path.exists(video_path):
                st.video(video_path)

        st.markdown("---")
        st.markdown("### Subir a YouTube")

        if _upload_status == "uploading":
            st.info("⏳ Subiendo a YouTube...")
            _render_logs_from_buffer(_upload_logs, max_lines=20)
            time.sleep(2)
            st.rerun()
        elif _upload_status == "done":
            st.success("✅ Video subido a YouTube como No Listado!")
        elif _upload_status == "error":
            st.error(f"❌ Error al subir: {_upload_error}")
        else:
            if st.button("📤 Subir a YouTube (No Listado)", type="primary"):
                if not _upload_account:
                    st.error("No se encontro la cuenta.")
                    return
                _start_upload(_upload_account, _pipeline_result, metadata)
                st.rerun()
    else:
        st.error(f"❌ Error: {_pipeline_result.get('error', 'Error desconocido')}")


def _start_upload(account, result, metadata):
    global _upload_status

    _upload_status = "uploading"
    with _log_lock:
        _upload_logs.clear()

    def upload_log_callback(level, message):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with _log_lock:
            _upload_logs.append({"time": ts, "level": level, "msg": message})

    set_log_callback(upload_log_callback)

    def upload_thread():
        global _upload_status, _upload_error
        try:
            from src.youtube import YouTube as YT
            yt_upload = YT(
                account_uuid=account["id"],
                account_nickname=account["nickname"],
                fp_profile_path=account["firefox_profile"],
                niche=account["niche"],
                language=account["language"],
            )
            try:
                yt_upload.video_path = result["video_path"]
                yt_upload.metadata = {
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", []),
                }
                yt_upload.upload_video()
                _upload_status = "done"
            finally:
                yt_upload.close()
        except Exception as e:
            _upload_status = "error"
            _upload_error = str(e)
        finally:
            set_log_callback(None)

    thread = threading.Thread(target=upload_thread, daemon=True)
    thread.start()


def page_accounts():
    """Account management page."""
    st.markdown('<h1 class="main-header">👤 Cuentas</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gestiona tus cuentas de YouTube</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Ver Cuentas", "➕ Crear Cuenta"])

    with tab1:
        accounts = get_accounts("youtube")
        if not accounts:
            st.info("No hay cuentas configuradas. Crea una en la pestaña 'Crear Cuenta'.")
        else:
            for acc in accounts:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    col1.markdown(f"**{acc.get('nickname', '?')}**")
                    col2.write(f"📂 {acc.get('niche', '?')}")
                    col3.write(f"🌐 {acc.get('language', '?')}")
                    videos_count = len(acc.get("videos", []))
                    col3.write(f"📹 {videos_count} videos")

                    with col4:
                        if st.button("🗑️", key=f"del_{acc['id']}"):
                            with st.spinner("Eliminando..."):
                                remove_account("youtube", acc["id"])
                                st.success(f"Cuenta '{acc.get('nickname')}' eliminada!")
                                st.rerun()

                    with st.expander(f"ℹ️ Detalles de {acc.get('nickname')}", expanded=False):
                        st.json({
                            "id": acc.get("id"),
                            "nickname": acc.get("nickname"),
                            "firefox_profile": acc.get("firefox_profile"),
                            "niche": acc.get("niche"),
                            "language": acc.get("language"),
                            "videos": acc.get("videos", []),
                        })

    with tab2:
        st.markdown("### Crear Nueva Cuenta")
        with st.form("create_account"):
            col1, col2 = st.columns(2)
            with col1:
                nickname = st.text_input("Nickname del canal", placeholder="MiCanalTech")
                firefox_profile = st.text_input(
                    "Ruta del perfil Firefox",
                    placeholder=r"C:\Users\...\Profiles\xxxxx.MoneyPrinter"
                )
            with col2:
                niche = st.text_input("Niche", placeholder="tecnologia y curiosidades")
                language = st.text_input("Idioma", value="Spanish")

            submitted = st.form_submit_button("✅ Crear Cuenta", type="primary", use_container_width=True)

            if submitted:
                if not nickname or not firefox_profile or not niche:
                    st.error("Todos los campos son obligatorios.")
                elif not os.path.isdir(firefox_profile):
                    st.error(f"La ruta del perfil Firefox no existe: {firefox_profile}")
                else:
                    uuid = generate_uuid()
                    account = {
                        "id": uuid,
                        "nickname": nickname,
                        "firefox_profile": firefox_profile,
                        "niche": niche,
                        "language": language,
                        "videos": [],
                    }
                    add_account("youtube", account)
                    st.success(f"Cuenta '{nickname}' creada exitosamente! UUID: `{uuid[:8]}...`")
                    st.rerun()


def page_history():
    """Video history page."""
    st.markdown('<h1 class="main-header">📜 Historial</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Videos generados y subidos</p>', unsafe_allow_html=True)

    accounts = get_accounts("youtube")
    all_videos = []

    for acc in accounts:
        for v in acc.get("videos", []):
            v["account_nickname"] = acc.get("nickname", "?")
            v["account_id"] = acc.get("id", "?")
            all_videos.append(v)

    if not all_videos:
        st.info("Aun no hay videos en el historial.")
        return

    all_videos.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        account_filter = st.selectbox(
            "Filtrar por cuenta",
            ["Todas"] + list(set(v["account_nickname"] for v in all_videos))
        )
    with col2:
        search = st.text_input("🔍 Buscar por titulo", placeholder="VHS...")

    filtered = all_videos
    if account_filter != "Todas":
        filtered = [v for v in filtered if v["account_nickname"] == account_filter]
    if search:
        filtered = [v for v in filtered if search.lower() in v.get("title", "").lower()]

    st.markdown(f"**{len(filtered)} videos encontrados**")

    for v in filtered:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            col1.markdown(f"**{v.get('title', 'Sin titulo')[:60]}**")
            col2.write(f"📁 {v.get('account_nickname', '?')} | 📅 {v.get('date', '?')}")
            if v.get("url"):
                col3.link_button("▶️ Ver", v["url"])
            col4.write(f"📄 {v.get('description', '')[:50]}...")


def page_config():
    """Configuration page."""
    st.markdown('<h1 class="main-header">⚙️ Configuracion</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Edita la configuracion del proyecto</p>', unsafe_allow_html=True)

    config_path = os.path.join(PROJ_ROOT, "config.json")

    if not os.path.exists(config_path):
        st.error("config.json no encontrado. Copia config.example.json a config.json.")
        return

    import json

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    tab1, tab2, tab3 = st.tabs(["🤖 IA", "🎥 Video", "🔧 Avanzado"])

    with tab1:
        st.markdown("### Configuracion de IA")
        col1, col2 = st.columns(2)
        with col1:
            config_data["ollama_base_url"] = st.text_input("Ollama URL", value=config_data.get("ollama_base_url", ""))
            config_data["ollama_model"] = st.text_input("Modelo Ollama", value=config_data.get("ollama_model", ""))
            config_data["nanobanana2_api_key"] = st.text_input(
                "Gemini API Key",
                value=config_data.get("nanobanana2_api_key", ""),
                type="password"
            )
        with col2:
            config_data["nanobanana2_model"] = st.text_input("Modelo Gemini", value=config_data.get("nanobanana2_model", ""))
            config_data["nanobanana2_aspect_ratio"] = st.selectbox(
                "Aspect Ratio",
                ["9:16", "16:9", "1:1", "4:3"],
                index=0 if config_data.get("nanobanana2_aspect_ratio") == "9:16" else 0
            )

    with tab2:
        st.markdown("### Configuracion de Video")
        col1, col2 = st.columns(2)
        with col1:
            config_data["script_sentence_length"] = st.slider(
                "Oraciones del guion", 2, 10, config_data.get("script_sentence_length", 4)
            )
            config_data["subtitle_max_chars"] = st.slider(
                "Caracteres por subtitulo", 10, 80, config_data.get("subtitle_max_chars", 40)
            )
            config_data["threads"] = st.slider("Hilos de renderizado", 1, 8, config_data.get("threads", 2))
        with col2:
            voices = ["es-MX-DaliaNeural", "es-ES-ElviraNeural", "es-AR-ElenaNeural",
                      "en-US-JennyNeural", "en-GB-SoniaNeural", "pt-BR-FranciscaNeural"]
            current_voice = config_data.get("tts_voice", "es-MX-DaliaNeural")
            voice_idx = voices.index(current_voice) if current_voice in voices else 0
            config_data["tts_voice"] = st.selectbox("Voz TTS", voices, index=voice_idx)
            config_data["is_for_kids"] = st.checkbox("Para ninos", value=config_data.get("is_for_kids", False))
            config_data["headless"] = st.checkbox("Firefox headless", value=config_data.get("headless", False))

    with tab3:
        st.markdown("### Configuracion Avanzada")
        config_data["verbose"] = st.checkbox("Modo verbose", value=config_data.get("verbose", True))
        config_data["stt_provider"] = st.selectbox(
            "Proveedor STT",
            ["local_whisper", "third_party_assemblyai"],
            index=0 if config_data.get("stt_provider") == "local_whisper" else 0
        )
        config_data["whisper_model"] = st.text_input("Modelo Whisper", value=config_data.get("whisper_model", "base"))
        config_data["zip_url"] = st.text_input("URL musica de fondo (.zip)", value=config_data.get("zip_url", ""))
        config_data["imagemagick_path"] = st.text_input("Ruta ImageMagick", value=config_data.get("imagemagick_path", ""))

    # Save button
    st.markdown("---")
    if st.button("💾 Guardar Configuracion", type="primary", use_container_width=True):
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        reload_config()
        st.success("✅ Configuracion guardada y recargada!")


# ──────────────────────────────────────────────
# Main App
# ──────────────────────────────────────────────

def main():
    initialize()
    render_sidebar()

    # Navigation
    page = st.sidebar.radio(
        "Navegacion",
        ["🏠 Dashboard", "🎥 Generar Short", "👤 Cuentas", "📜 Historial", "⚙️ Configuracion"],
        label_visibility="collapsed"
    )

    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "🎥 Generar Short":
        page_generate()
    elif page == "👤 Cuentas":
        page_accounts()
    elif page == "📜 Historial":
        page_history()
    elif page == "⚙️ Configuracion":
        page_config()


if __name__ == "__main__":
    main()
