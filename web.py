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
_upload_url = None

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
# Custom CSS (Professional Dark Theme)
# ──────────────────────────────────────────────

st.markdown("""
<style>
    /* ═══════════════════════════════════════════════
       BASE & TYPOGRAPHY
       ═══════════════════════════════════════════════ */
    .stApp {
        background-color: #0f0f1a;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Global text size reduction */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {
        font-size: 0.875rem !important;
        line-height: 1.5;
    }
    
    /* Headers - compact */
    .main-header {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        margin-bottom: 0.25rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1e1e3a;
    }
    .sub-header {
        color: #6b7280 !important;
        font-size: 0.8rem !important;
        margin-bottom: 1rem !important;
        margin-top: 0 !important;
    }
    
    /* ═══════════════════════════════════════════════
       CARDS & CONTAINERS
       ═══════════════════════════════════════════════ */
    .metric-card {
        background: #1a1a2e;
        border: 1px solid #252540;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.2s ease;
    }
    .metric-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 0 0 1px #3b82f620;
    }
    .metric-value {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        line-height: 1.2;
    }
    .metric-label {
        color: #6b7280 !important;
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }
    
    /* Section cards */
    .section-card {
        background: #1a1a2e;
        border: 1px solid #252540;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .section-title {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #9ca3af !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #252540;
    }
    
    /* Status indicators */
    .success-box {
        background: #0f2f1a;
        border: 1px solid #166534;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        color: #22c55e;
        font-size: 0.8rem;
    }
    .error-box {
        background: #2f0f1a;
        border: 1px solid #991b1b;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        color: #ef4444;
        font-size: 0.8rem;
    }
    .warning-box {
        background: #2f2f0f;
        border: 1px solid #854d0e;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        color: #eab308;
        font-size: 0.8rem;
    }
    
    /* ═══════════════════════════════════════════════
       FORM ELEMENTS
       ═══════════════════════════════════════════════ */
    
    /* Buttons */
    .stButton > button {
        background: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background: #2563eb !important;
    }
    .stButton > button:active {
        background: #1d4ed8 !important;
    }
    
    /* Primary button */
    .stButton > button[data-testid="stBaseButton-primary"],
    .stButton > button:has(span:contains("GENERAR")),
    .stButton > button:has(span:contains("Guardar")) {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1a1a2e !important;
        border: 1px solid #252540 !important;
        border-radius: 6px !important;
        color: #ffffff !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 0.75rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f640 !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background-color: #1a1a2e !important;
        border: 1px solid #252540 !important;
        border-radius: 6px !important;
    }
    
    /* Slider */
    .stSlider > div > div > div > div {
        background: #3b82f6 !important;
    }
    
    /* Checkbox & Toggle */
    .stCheckbox > label {
        font-size: 0.8rem !important;
    }
    
    /* ═══════════════════════════════════════════════
       LAYOUT COMPONENTS
       ═══════════════════════════════════════════════ */
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        background: #1a1a2e !important;
        border-radius: 6px !important;
        padding: 4px !important;
        border: 1px solid #252540 !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.8rem !important;
        color: #6b7280 !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background: #3b82f6 !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1a2e !important;
        border: 1px solid #252540 !important;
        border-radius: 6px !important;
        font-size: 0.8rem !important;
        padding: 0.5rem 0.75rem !important;
    }
    
    /* Divider */
    hr {
        border-color: #252540 !important;
        margin: 1rem 0 !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
    }
    
    /* ═══════════════════════════════════════════════
       SIDEBAR
       ═══════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background-color: #0a0a14 !important;
        border-right: 1px solid #1e1e3a !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li {
        font-size: 0.8rem !important;
    }
    [data-testid="stSidebar"] .stRadio > label {
        font-size: 0.8rem !important;
    }
    
    /* ═══════════════════════════════════════════════
       TABLES & DATA
       ═══════════════════════════════════════════════ */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* ═══════════════════════════════════════════════
       MOBILE RESPONSIVE
       ═══════════════════════════════════════════════ */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.25rem !important;
        }
        .metric-card {
            padding: 0.75rem !important;
        }
        .metric-value {
            font-size: 1.25rem !important;
        }
        .stButton > button {
            padding: 0.4rem 0.75rem !important;
        }
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
    }
    
    /* ═══════════════════════════════════════════════
       SCROLLBAR
       ═══════════════════════════════════════════════ */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0f0f1a;
    }
    ::-webkit-scrollbar-thumb {
        background: #252540;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #3b82f6;
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
    """Main dashboard with overview and charts."""
    st.markdown('<h1 class="main-header">Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Resumen general del sistema</p>', unsafe_allow_html=True)

    # Metrics
    accounts = get_accounts("youtube")
    total_videos = sum(len(a.get("videos", [])) for a in accounts)
    uploaded_videos = sum(1 for a in accounts for v in a.get("videos", []) if v.get("url"))
    pending_videos = total_videos - uploaded_videos

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Cuentas</div>
        </div>
        """.format(len(accounts)), unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Generados</div>
        </div>
        """.format(total_videos), unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Subidos</div>
        </div>
        """.format(uploaded_videos), unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Pendientes</div>
        </div>
        """.format(pending_videos), unsafe_allow_html=True)

    st.markdown("---")

    # Charts section
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown('<div class="section-title">Analisis de Videos</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-title">Videos Recientes</div>', unsafe_allow_html=True)

    if total_videos > 0:
        import plotly.express as px
        import plotly.graph_objects as go
        from datetime import datetime, timedelta

        # Collect all video data
        all_videos = []
        for acc in accounts:
            for v in acc.get("videos", []):
                v["account"] = acc.get("nickname", "?")
                v["niche"] = acc.get("niche", "?")
                all_videos.append(v)

        col_left, col_right = st.columns([2, 1])

        with col_left:
            # Charts in 2x2 grid
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                # Videos per account (Pie chart)
                account_counts = {}
                for v in all_videos:
                    acc_name = v.get("account", "Unknown")
                    account_counts[acc_name] = account_counts.get(acc_name, 0) + 1

                fig_pie = px.pie(
                    values=list(account_counts.values()),
                    names=list(account_counts.keys()),
                    title="Videos por Cuenta",
                    color_discrete_sequence=px.colors.sequential.Plasma,
                    hole=0.4
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    height=280,
                    margin=dict(t=40, b=20, l=20, r=20)
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent')
                st.plotly_chart(fig_pie, use_container_width=True)

            with chart_col2:
                # Upload status (Donut chart)
                status_data = {"Subidos": uploaded_videos, "Pendientes": pending_videos}

                fig_status = px.pie(
                    values=list(status_data.values()),
                    names=list(status_data.keys()),
                    title="Estado de Uploads",
                    color_discrete_sequence=["#4ade80", "#fbbf24"],
                    hole=0.6
                )
                fig_status.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    height=280,
                    margin=dict(t=40, b=20, l=20, r=20)
                )
                fig_status.update_traces(textposition='inside', textinfo='percent')
                st.plotly_chart(fig_status, use_container_width=True)

            # Timeline chart
            daily_counts = {}
            for v in all_videos:
                date_str = v.get("date", "")
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
                        daily_counts[date] = daily_counts.get(date, 0) + 1
                    except:
                        pass

            if daily_counts:
                dates = sorted(daily_counts.keys())
                counts = [daily_counts[d] for d in dates]

                fig_timeline = px.bar(
                    x=dates,
                    y=counts,
                    title="Videos por Dia",
                    labels={"x": "Fecha", "y": "Videos"},
                    color_discrete_sequence=["#3b82f6"]
                )
                fig_timeline.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    height=200,
                    margin=dict(t=40, b=40, l=40, r=20),
                    xaxis=dict(tickangle=-45)
                )
                st.plotly_chart(fig_timeline, use_container_width=True)

            # Niche distribution
            niche_counts = {}
            for v in all_videos:
                niche = v.get("niche", "Unknown")
                niche_counts[niche] = niche_counts.get(niche, 0) + 1

            fig_niche = px.bar(
                x=list(niche_counts.keys()),
                y=list(niche_counts.values()),
                title="Videos por Nicho",
                labels={"x": "Nicho", "y": "Videos"},
                color=list(niche_counts.keys()),
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig_niche.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                height=200,
                margin=dict(t=40, b=40, l=40, r=20),
                showlegend=False
            )
            st.plotly_chart(fig_niche, use_container_width=True)

        with col_right:
            # Recent videos - compact list
            all_videos.sort(key=lambda x: x.get("date", ""), reverse=True)
            for v in all_videos[:8]:
                status = "✅" if v.get("url") else "⏳"
                st.markdown(f"""
                <div style="padding:0.5rem 0;border-bottom:1px solid #252540;">
                    <div style="font-size:0.8rem;color:#fff;">{status} {v.get('title', 'Sin titulo')[:45]}</div>
                    <div style="font-size:0.7rem;color:#6b7280;">{v.get('account', '?')} | {v.get('date', '?')[:10]}</div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.info("Las graficas apareceran cuando tengas videos generados.")

    # System status
    st.markdown("---")
    st.markdown('<div class="section-title">Estado del Sistema</div>', unsafe_allow_html=True)

    sys_col1, sys_col2, sys_col3 = st.columns(3)
    with sys_col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1rem;color:#4ade80;">Activo</div>
            <div class="metric-label">Sistema</div>
        </div>
        """, unsafe_allow_html=True)
    with sys_col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1rem;color:#3b82f6;">{}</div>
            <div class="metric-label">Cuentas Activas</div>
        </div>
        """.format(len(accounts)), unsafe_allow_html=True)
    with sys_col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1rem;color:#8b5cf6;">Auto</div>
            <div class="metric-label">Modo</div>
        </div>
        """, unsafe_allow_html=True)


def page_generate():
    """Video generation page."""
    global _pipeline_status, _pipeline_result, _upload_status, _upload_error, _upload_account

    st.markdown('<h1 class="main-header">Generar Short</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Genera un video completo con IA</p>', unsafe_allow_html=True)

    accounts = get_accounts("youtube")

    if not accounts:
        st.warning("No hay cuentas configuradas. Ve a **Cuentas** primero.")
        return

    # Account selection
    account_names = [f"{a['nickname']} ({a['niche']})" for a in accounts]
    selected_idx = st.selectbox("Cuenta", range(len(accounts)), format_func=lambda i: account_names[i])
    account = accounts[selected_idx]

    # Auto-upload option
    auto_upload = st.checkbox("Subir automaticamente a YouTube despues de generar", value=True, key="auto_upload")

    # Genre/Topic selection
    GENRES = {
        "Nicho de la cuenta": "",
        "Historias de terror": "historias de terror, misterio, leyendas urbanas, lo paranormal",
        "Misterio y conspiraciones": "misterio, conspiraciones, secretos oscuros, fenomenos inexplicables",
        "Ciencia y naturaleza": "ciencia, naturaleza, curiosidades, descubrimientos asombrosos",
        "Historia y cultura": "historia, cultura, civilizaciones antiguas, eventos historicos",
        "Tecnologia y futuro": "tecnologia, inteligencia artificial, futuro, innovacion",
        "Filosofia y psicologia": "filosofia, psicologia, mente humana, reflexiones profundas",
        "Crimen real": "crimen real, casos policiacos, investigaciones, justicia",
        "Mitologia y leyendas": "mitologia, leyendas antiguas, dioses, criaturas mitologicas",
        "Misterio espacial": "espacio, universo, agujeros negros, vida extraterrestre",
        "Terror psicologico": "terror psicologico, suspense, manipulacion, mente oscura",
    }

    col_genre, col_account = st.columns([2, 1])
    with col_genre:
        selected_genre = st.selectbox("Genero / Tema", options=list(GENRES.keys()), index=0)
        custom_topic = ""
        if selected_genre == "Nicho de la cuenta":
            st.caption(f"Usara el nicho de la cuenta: **{account.get('niche', '?')}**")
        else:
            custom_topic = st.text_input("Tema personalizado (opcional)", placeholder="Ej: La leyenda del Silbon en Venezuela")
    
    with col_account:
        with st.expander("Info de la cuenta", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.metric("Nick", account.get("nickname", "?"))
            c2.metric("Nicho", account.get("niche", "?"))
            c3.metric("Idioma", account.get("language", "?"))

    st.markdown("---")

    # Main controls
    col_config, col_subtitle = st.columns([1, 1])

    with col_config:
        st.markdown('<div class="section-title">Configuracion del Video</div>', unsafe_allow_html=True)
        sentence_length = st.slider("Oraciones del guion", 2, 10, cfg_get("script_sentence_length", 4))
        subtitle_chars = st.slider("Caracteres por subtitulo", 10, 80, cfg_get("subtitle_max_chars", 40))
        c1, c2 = st.columns(2)
        is_for_kids = c1.checkbox("Para ninos", value=cfg_get("is_for_kids", False))
        headless = c2.checkbox("Headless", value=cfg_get("headless", False))

    with col_subtitle:
        st.markdown('<div class="section-title">Subtitulos</div>', unsafe_allow_html=True)
        
        # Subtitle style presets
        SUBTITLE_STYLES = {
            "Personalizado": {},
            "Clasico (Amarillo)": {"color": "#FFFF00", "stroke": "#000000", "width": 4, "bg_alpha": 60},
            "Moderno (Blanco)": {"color": "#FFFFFF", "stroke": "#000000", "width": 3, "bg_alpha": 50},
            "Horror (Rojo)": {"color": "#FF0000", "stroke": "#000000", "width": 5, "bg_alpha": 70},
            "Neon (Cyan)": {"color": "#00FFFF", "stroke": "#FF00FF", "width": 3, "bg_alpha": 40},
            "Golden": {"color": "#FFD700", "stroke": "#8B4513", "width": 4, "bg_alpha": 55},
            "Minimal (Gris)": {"color": "#CCCCCC", "stroke": "#333333", "width": 2, "bg_alpha": 30},
            "Cyberpunk": {"color": "#FF00FF", "stroke": "#00FFFF", "width": 4, "bg_alpha": 60},
            "Retro": {"color": "#FFA500", "stroke": "#000000", "width": 5, "bg_alpha": 65},
        }
        
        selected_style = st.selectbox("Estilo predefinido", options=list(SUBTITLE_STYLES.keys()), key="sub_style")
        
        # Apply preset or use custom values
        if selected_style != "Personalizado" and SUBTITLE_STYLES[selected_style]:
            preset = SUBTITLE_STYLES[selected_style]
            default_color = preset["color"]
            default_stroke = preset["stroke"]
            default_width = preset["width"]
            default_bg_alpha = preset["bg_alpha"]
        else:
            default_color = cfg_get("subtitle_color", "#FFFF00")
            default_stroke = cfg_get("subtitle_stroke_color", "#000000")
            default_width = cfg_get("subtitle_stroke_width", 4)
            default_bg_alpha = cfg_get("subtitle_bg_alpha", 60)
        
        c1, c2 = st.columns(2)
        subtitle_color = c1.color_picker("Color texto", value=default_color, key="sub_color")
        subtitle_stroke_color = c2.color_picker("Color borde", value=default_stroke, key="sub_stroke_color")
        c1, c2 = st.columns(2)
        subtitle_font_size = c1.slider("Fuente", 20, 150, cfg_get("subtitle_font_size", 80), key="sub_font_size")
        subtitle_stroke_width = c2.slider("Borde", 0, 10, default_width, key="sub_stroke_width")
        c1, c2 = st.columns(2)
        subtitle_position = c1.selectbox("Posicion", ["top", "center", "bottom"], index=["top", "center", "bottom"].index(cfg_get("subtitle_position", "center")), key="sub_position")
        subtitle_max_width = c2.slider("Ancho max", 400, 1200, cfg_get("subtitle_max_width", 1000), step=100, key="sub_max_width")
        
        # Transparency controls
        st.markdown('<div class="section-title">Transparencia</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        subtitle_bg_alpha = c1.slider("Fondo subtitulos %", 0, 100, default_bg_alpha, key="sub_bg_alpha", help="0 = transparente, 100 = opaco")
        subtitle_text_alpha = c2.slider("Opacidad texto %", 0, 100, cfg_get("subtitle_text_alpha", 100), key="sub_text_alpha", help="100 = completamente visible")

    # Preview
    with st.expander("Vista previa de subtitulos", expanded=False):
        bg_alpha_hex = format(int(subtitle_bg_alpha * 2.55), '02x')
        text_alpha_hex = format(int(subtitle_text_alpha * 2.55), '02x')
        
        phone_html = f'''
        <div style="display:flex;justify-content:center;padding:10px 0;">
            <div style="width:240px;height:430px;background:#000;border-radius:24px;padding:8px;box-shadow:0 0 0 2px #333,0 10px 40px rgba(0,0,0,0.5);position:relative;">
                <div style="width:100%;height:100%;background:linear-gradient(180deg,#1a1a2e 0%,#16213e 50%,#0f0f23 100%);border-radius:18px;overflow:hidden;position:relative;display:flex;flex-direction:column;">
                    <div style="flex:1;position:relative;display:flex;flex-direction:column;justify-content:{'flex-start' if subtitle_position == 'top' else 'center' if subtitle_position == 'center' else 'flex-end'};align-items:center;padding:30px 12px 50px 12px;">
                        <div style="position:relative;z-index:2;text-align:center;padding:6px 10px;background:rgba(0,0,0,{subtitle_bg_alpha/100});border-radius:4px;max-width:90%;{'margin-top:12px;' if subtitle_position == 'top' else ''}{'' if subtitle_position == 'center' else ''}{'' if subtitle_position == 'bottom' else ''}{'margin-bottom:12px;' if subtitle_position == 'bottom' else ''}">
                            <span style="font-family:Impact,Arial Black,sans-serif;font-size:{min(subtitle_font_size * 0.35, 20)}px;color:{subtitle_color}{text_alpha_hex};opacity:{subtitle_text_alpha/100};text-shadow:-{subtitle_stroke_width * 0.4}px -{subtitle_stroke_width * 0.4}px 0 {subtitle_stroke_color},{subtitle_stroke_width * 0.4}px -{subtitle_stroke_width * 0.4}px 0 {subtitle_stroke_color},-{subtitle_stroke_width * 0.4}px {subtitle_stroke_width * 0.4}px 0 {subtitle_stroke_color},{subtitle_stroke_width * 0.4}px {subtitle_stroke_width * 0.4}px 0 {subtitle_stroke_color};letter-spacing:1px;line-height:1.2;display:inline-block;word-wrap:break-word;">Ejemplo de subtitulos</span>
                        </div>
                    </div>
                    <div style="position:absolute;right:6px;bottom:60px;display:flex;flex-direction:column;gap:12px;z-index:5;">
                        <div style="text-align:center;"><div style="font-size:16px;">&#x2764;&#xFE0F;</div><div style="font-size:8px;color:white;">1.2K</div></div>
                        <div style="text-align:center;"><div style="font-size:16px;">&#x1F4AC;</div><div style="font-size:8px;color:white;">89</div></div>
                        <div style="text-align:center;"><div style="font-size:16px;">&#x2197;&#xFE0F;</div><div style="font-size:8px;color:white;">Share</div></div>
                    </div>
                    <div style="position:absolute;bottom:0;left:0;right:0;padding:8px 10px;background:linear-gradient(transparent,rgba(0,0,0,0.8));z-index:5;">
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                            <div style="width:24px;height:24px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);border-radius:50%;"></div>
                            <span style="color:white;font-size:10px;font-weight:bold;">@tucanal</span>
                            <span style="background:#ff0000;color:white;font-size:7px;padding:2px 5px;border-radius:3px;font-weight:bold;">SUSCRIBIRSE</span>
                        </div>
                        <div style="color:white;font-size:9px;line-height:1.3;">Historia de terror #shorts</div>
                    </div>
                    <div style="position:absolute;top:40px;left:8px;background:rgba(59,130,246,0.9);padding:2px 6px;border-radius:3px;font-size:8px;color:white;z-index:10;font-weight:bold;">{subtitle_position.upper()}</div>
                </div>
            </div>
        </div>
        '''
        st.markdown(phone_html, unsafe_allow_html=True)
        
        # Show current settings
        c1, c2, c3, c4 = st.columns(4)
        c1.caption(f"Texto: {subtitle_color}")
        c2.caption(f"Borde: {subtitle_stroke_color}")
        c3.caption(f"Fondo: {subtitle_bg_alpha}%")
        c4.caption(f"Opacidad: {subtitle_text_alpha}%")

    with st.expander("Archivos personalizados (Opcional)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            uploaded_images = st.file_uploader("Imagenes", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="custom_images")
            if uploaded_images:
                st.success(f"{len(uploaded_images)} imagenes seleccionadas")
        with c2:
            uploaded_music = st.file_uploader("Musica de fondo", type=["mp3", "wav", "ogg", "m4a"], accept_multiple_files=False, key="custom_music")
            if uploaded_music:
                st.success(f"Musica: {uploaded_music.name}")

    st.markdown("---")

    # Generation button
    if _pipeline_status == "running":
        _render_running()
    elif _pipeline_status == "done":
        _render_result()
        
        # Video preview
        if _pipeline_result and _pipeline_result.get("video_path"):
            st.markdown('<div class="section-title">Preview del Video</div>', unsafe_allow_html=True)
            video_path = _pipeline_result["video_path"]
            if os.path.exists(video_path):
                st.video(video_path)
                
                # Show metadata
                if _pipeline_result.get("metadata"):
                    meta = _pipeline_result["metadata"]
                    c1, c2 = st.columns(2)
                    with c1:
                        st.text_input("Titulo", value=meta.get("title", ""), disabled=True)
                    with c2:
                        st.text_area("Descripcion", value=meta.get("description", ""), disabled=True, height=100)
        
        if st.button("Generar otro video", use_container_width=True):
            _pipeline_status = "idle"
            _pipeline_result = None
            with _log_lock:
                _pipeline_logs.clear()
            st.rerun()
    elif _pipeline_status == "error":
        _render_result()
        if st.button("Reintentar", use_container_width=True):
            _pipeline_status = "idle"
            _pipeline_result = None
            with _log_lock:
                _pipeline_logs.clear()
            st.rerun()
    else:
        if st.button("GENERAR VIDEO", type="primary", use_container_width=True):
            # Determine the niche/topic to use
            if selected_genre == "Nicho de la cuenta":
                final_niche = account.get("niche", "")
            elif custom_topic:
                final_niche = f"{selected_genre}: {custom_topic}"
            else:
                final_niche = GENRES[selected_genre]
            
            _start_pipeline(
                account, sentence_length, is_for_kids, subtitle_chars, headless,
                subtitle_color, subtitle_stroke_color, subtitle_font_size,
                subtitle_stroke_width, subtitle_position, subtitle_max_width,
                subtitle_bg_alpha, subtitle_text_alpha, final_niche, auto_upload
            )
            st.rerun()


def _start_pipeline(account, sentence_length, is_for_kids, subtitle_chars, headless,
                    subtitle_color="#FFFF00", subtitle_stroke_color="#000000",
                    subtitle_font_size=80, subtitle_stroke_width=4,
                    subtitle_position="center", subtitle_max_width=1000,
                    subtitle_bg_alpha=60, subtitle_text_alpha=100, custom_niche=None,
                    auto_upload=True):
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
        global _pipeline_status, _pipeline_result, _upload_status, _upload_url, _upload_error
        try:
            from src import config
            config._config_cache = None
            reload_config()

            config._config_cache["script_sentence_length"] = sentence_length
            config._config_cache["is_for_kids"] = is_for_kids
            config._config_cache["subtitle_max_chars"] = subtitle_chars
            config._config_cache["headless"] = headless
            config._config_cache["subtitle_color"] = subtitle_color
            config._config_cache["subtitle_stroke_color"] = subtitle_stroke_color
            config._config_cache["subtitle_font_size"] = subtitle_font_size
            config._config_cache["subtitle_stroke_width"] = subtitle_stroke_width
            config._config_cache["subtitle_position"] = subtitle_position
            config._config_cache["subtitle_max_width"] = subtitle_max_width
            config._config_cache["subtitle_bg_alpha"] = subtitle_bg_alpha
            config._config_cache["subtitle_text_alpha"] = subtitle_text_alpha

            model = get_active_model() or get_ollama_model()
            if model:
                select_model(model)

            tts = TTS()
            
            # Use custom niche if provided
            niche = custom_niche if custom_niche else account["niche"]
            
            yt = YouTube(
                account_uuid=account["id"],
                account_nickname=account["nickname"],
                fp_profile_path=account["firefox_profile"],
                niche=niche,
                language=account["language"],
            )

            try:
                yt.generate_video(tts)
                _pipeline_result = {
                    "success": True,
                    "video_path": yt.video_path,
                    "metadata": yt.metadata,
                    "topic": yt.subject,
                    "thumbnail": yt.thumbnail_path if hasattr(yt, 'thumbnail_path') else "",
                }
                _pipeline_status = "done"
                
                # Auto-upload to YouTube if enabled
                if auto_upload:
                    info("Auto-upload enabled, uploading to YouTube...")
                    _upload_status = "uploading"
                    try:
                        upload_success = yt.upload_video()
                        if upload_success:
                            _upload_status = "done"
                            _upload_url = f"https://youtube.com/watch?v={yt.video_id}" if hasattr(yt, 'video_id') else ""
                            success("Video uploaded to YouTube!")
                        else:
                            _upload_status = "error"
                            _upload_error = "Upload failed"
                            warning("YouTube upload failed")
                    except Exception as upload_err:
                        _upload_status = "error"
                        _upload_error = str(upload_err)
                        warning(f"Upload error: {upload_err}")
                
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
        
        # Video Preview Section
        st.markdown("### 🎬 Preview del Video")
        
        video_path = _pipeline_result.get("video_path", "")
        thumbnail_path = _pipeline_result.get("thumbnail", "")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if video_path and os.path.exists(video_path):
                st.video(video_path)
                
                # Video info
                try:
                    from moviepy import VideoFileClip
                    clip = VideoFileClip(video_path)
                    duration = clip.duration
                    size = os.path.getsize(video_path) / (1024 * 1024)
                    clip.close()
                    
                    st.caption(f"Duracion: {duration:.1f}s | Tamano: {size:.1f}MB")
                except:
                    pass
            else:
                st.warning("Video no encontrado")
        
        with col2:
            st.markdown("**Metadatos:**")
            st.markdown(f"**Tema:** {_pipeline_result.get('topic', '?')}")
            st.markdown(f"**Titulo:** {metadata.get('title', '?')}")
            st.markdown(f"**Descripcion:**")
            st.text_area("Desc", value=metadata.get('description', '?'), height=150, disabled=True, label_visibility="collapsed")
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                st.markdown("**Thumbnail:**")
                st.image(thumbnail_path, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📤 Subir a Plataformas")

        if _upload_status == "uploading":
            st.info("⏳ Subiendo...")
            _render_logs_from_buffer(_upload_logs, max_lines=20)
            time.sleep(2)
            st.rerun()
        elif _upload_status == "done":
            st.success("✅ Video subido exitosamente!")
            if _upload_url:
                st.markdown(f"🔗 [{_upload_url}]({_upload_url})")
        elif _upload_status == "error":
            st.error(f"❌ Error al subir: {_upload_error}")
        else:
            # Platform selection
            platform = st.selectbox(
                "Seleccionar plataforma",
                ["YouTube", "TikTok", "Instagram Reels", "Multi-plataforma"],
                key="upload_platform"
            )
            
            if platform == "Multi-plataforma":
                st.info("Sube el mismo video a multiples plataformas simultaneamente")
                platforms = st.multiselect(
                    "Seleccionar plataformas",
                    ["YouTube", "TikTok", "Instagram"],
                    default=["YouTube"],
                    key="multi_platforms"
                )
            else:
                platforms = [platform]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📤 Subir Ahora", type="primary", use_container_width=True):
                    if not _upload_account:
                        st.error("No se encontro la cuenta.")
                        return
                    
                    for p in platforms:
                        platform_key = p.lower().replace(" ", "_").replace("_reels", "")
                        if platform_key == "youtube":
                            _start_upload(_upload_account, _pipeline_result, metadata)
                        else:
                            # For other platforms, use the platforms module
                            from src.platforms import upload_to_platform
                            result = upload_to_platform(
                                platform=platform_key,
                                video_path=_pipeline_result.get("video_path", ""),
                                caption=metadata.get("title", ""),
                                tags=metadata.get("tags", []),
                                firefox_profile_path=_upload_account.get("firefox_profile", ""),
                            )
                            if result["success"]:
                                st.success(f"✅ Subido a {p}!")
                            else:
                                st.error(f"❌ Error en {p}: {result.get('error')}")
                    st.rerun()
            
            with col2:
                if st.button("📅 Programar Upload", use_container_width=True):
                    st.session_state["show_scheduler_modal"] = True
            with col3:
                if st.button("💾 Solo Guardar", use_container_width=True):
                    st.success(f"Video guardado en: {video_path}")
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
    """Video history page with analytics."""
    st.markdown('<h1 class="main-header">📜 Historial</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Videos generados, subidos y estadisticas</p>', unsafe_allow_html=True)

    accounts = get_accounts("youtube")
    all_videos = []

    for acc in accounts:
        for v in acc.get("videos", []):
            v["account_nickname"] = acc.get("nickname", "?")
            v["account_id"] = acc.get("id", "?")
            v["account_niche"] = acc.get("niche", "?")
            all_videos.append(v)

    if not all_videos:
        st.info("Aun no hay videos en el historial.")
        return

    all_videos.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Analytics Summary
    st.markdown("### 📊 Estadisticas")
    col1, col2, col3, col4 = st.columns(4)
    
    total_videos = len(all_videos)
    uploaded_videos = len([v for v in all_videos if v.get("url")])
    pending_videos = len([v for v in all_videos if not v.get("url")])
    unique_accounts = len(set(v["account_nickname"] for v in all_videos))
    
    with col1:
        st.metric("Total Videos", total_videos)
    with col2:
        st.metric("Subidos", uploaded_videos)
    with col3:
        st.metric("Pendientes", pending_videos)
    with col4:
        st.metric("Cuentas Activas", unique_accounts)

    st.divider()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        account_filter = st.selectbox(
            "Filtrar por cuenta",
            ["Todas"] + list(set(v["account_nickname"] for v in all_videos))
        )
    with col2:
        status_filter = st.selectbox(
            "Filtrar por estado",
            ["Todos", "Subidos", "Pendientes"]
        )
    with col3:
        search = st.text_input("🔍 Buscar por titulo", placeholder="VHS...")

    filtered = all_videos
    
    if account_filter != "Todas":
        filtered = [v for v in filtered if v["account_nickname"] == account_filter]
    
    if status_filter == "Subidos":
        filtered = [v for v in filtered if v.get("url")]
    elif status_filter == "Pendientes":
        filtered = [v for v in filtered if not v.get("url")]
    
    if search:
        filtered = [v for v in filtered if search.lower() in v.get("title", "").lower()]

    st.markdown(f"**{len(filtered)} videos encontrados**")

    for v in filtered:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            # Title and niche
            title = v.get('title', 'Sin titulo')
            col1.markdown(f"**{title[:50]}**")
            col1.caption(f"🏷️ {v.get('account_niche', '?')}")
            
            # Account and date
            col2.write(f"📁 {v.get('account_nickname', '?')}")
            col2.caption(f"📅 {v.get('date', '?')}")
            
            # Status
            if v.get("url"):
                col3.success("✅ Subido")
            else:
                col3.warning("⏳ Pendiente")
            
            # View button
            if v.get("url"):
                col4.link_button("▶️ Ver", v["url"])
            
            # Description preview
            desc = v.get('description', '')[:80]
            col5.caption(f"📄 {desc}...")

    # Export option
    if st.button("📥 Exportar historial como JSON", use_container_width=False):
        import json
        export_data = [{
            "title": v.get("title"),
            "account": v.get("account_nickname"),
            "date": v.get("date"),
            "url": v.get("url"),
            "description": v.get("description", "")[:200],
        } for v in filtered]
        
        st.download_button(
            label="⬇️ Descargar JSON",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


def page_scheduler():
    """Upload scheduler page."""
    st.markdown('<h1 class="main-header">📅 Programador de Uploads</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Programa uploads automaticos a horas pico</p>', unsafe_allow_html=True)

    from src.scheduler import (
        get_schedule_status,
        update_schedule_settings,
        schedule_upload,
        cancel_scheduled_upload,
        clear_completed_uploads,
        start_scheduler,
        stop_scheduler,
    )

    # Schedule status
    status = get_schedule_status()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Estado", "🟢 Activo" if status["enabled"] else "🔴 Inactivo")
    with col2:
        st.metric("Pendientes", status["pending"])
    with col3:
        st.metric("Subidos", status["uploaded"])
    with col4:
        st.metric("Errores", status["errors"])

    st.divider()

    # Settings
    st.markdown("### ⚙️ Configuracion del Programador")

    col1, col2 = st.columns(2)
    with col1:
        enabled = st.toggle("Activar programador", value=status["enabled"])
    with col2:
        hours_options = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        selected_hours = st.multiselect(
            "Horas de upload (hora local)",
            options=hours_options,
            default=[h for h in status["upload_hours"] if h in hours_options],
            format_func=lambda x: f"{x:02d}:00"
        )

    if st.button("💾 Guardar configuracion", use_container_width=True):
        update_schedule_settings(enabled=enabled, upload_hours=selected_hours)
        if enabled:
            start_scheduler()
            st.success("Programador activado!")
        else:
            stop_scheduler()
            st.info("Programador desactivado")
        st.rerun()

    st.divider()

    # Schedule upload manually
    st.markdown("### 📤 Programar Upload Manual")

    accounts = get_accounts("youtube")
    if accounts:
        with st.form("schedule_form"):
            col1, col2 = st.columns(2)
            with col1:
                account_select = st.selectbox(
                    "Cuenta",
                    options=[a["id"] for a in accounts],
                    format_func=lambda x: next((a["nickname"] for a in accounts if a["id"] == x), x)
                )
            with col2:
                video_path = st.text_input("Ruta del video")

            title = st.text_input("Titulo")
            description = st.text_area("Descripcion", height=100)
            tags = st.text_input("Tags (separados por coma)")

            submitted = st.form_submit_button("📅 Programar", use_container_width=True)

            if submitted:
                if not video_path or not title:
                    st.error("Video path y titulo son requeridos")
                else:
                    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
                    schedule_upload(video_path, account_select, title, description, tags_list)
                    st.success("Video programado!")
                    st.rerun()
    else:
        st.warning("No hay cuentas disponibles. Crea una cuenta primero.")

    st.divider()

    # Pending uploads
    st.markdown("### 📋 Uploads Pendientes")

    import json
    schedule_file = os.path.join(PROJ_ROOT, "schedule.json")
    if os.path.exists(schedule_file):
        with open(schedule_file, "r", encoding="utf-8") as f:
            schedule_data = json.load(f)

        pending = [u for u in schedule_data.get("scheduled_uploads", []) if u["status"] == "pending"]

        if pending:
            for i, upload in enumerate(pending):
                with st.container():
                    col1, col2, col3 = st.columns([4, 2, 1])
                    col1.markdown(f"**{upload.get('title', 'Sin titulo')[:50]}**")
                    col1.caption(f"📁 {upload.get('account_id', '?')[:8]}...")
                    col2.caption(f"📅 Creado: {upload.get('created_at', '?')[:16]}")
                    if col3.button("❌", key=f"cancel_{i}"):
                        cancel_scheduled_upload(i)
                        st.rerun()
        else:
            st.info("No hay uploads pendientes")

        if st.button("🗑️ Limpiar completados", use_container_width=False):
            clear_completed_uploads()
            st.rerun()
    else:
        st.info("No hay programa de uploads")


def page_multichannel():
    """Multi-channel batch generation page."""
    st.markdown('<h1 class="main-header">🚀 Multi-Canal</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Genera videos para multiples canales simultaneamente</p>', unsafe_allow_html=True)

    from src.batch import generate_batch, BatchWorker
    from src.cache import get_accounts

    accounts = get_accounts("youtube")

    if not accounts:
        st.warning("No hay cuentas disponibles. Crea al menos una cuenta en la pagina de Cuentas.")
        return

    # Account selection
    st.markdown("### 👥 Seleccionar Cuentas")

    account_options = {a["id"]: f"{a['nickname']} ({a['niche']})" for a in accounts}
    selected_accounts = st.multiselect(
        "Selecciona cuentas para generar videos",
        options=list(account_options.keys()),
        format_func=lambda x: account_options[x],
        default=list(account_options.keys())
    )

    # Settings
    col1, col2 = st.columns(2)
    with col1:
        videos_per_account = st.number_input(
            "Videos por cuenta",
            min_value=1,
            max_value=10,
            value=1,
        )
    with col2:
        delay_between = st.slider(
            "Segundos entre videos",
            min_value=10,
            max_value=300,
            value=30,
        )

    st.divider()

    # Generate button
    if st.button("🚀 Generar Batch", use_container_width=True, type="primary"):
        if not selected_accounts:
            st.error("Selecciona al menos una cuenta")
        else:
            selected = [a for a in accounts if a["id"] in selected_accounts]

            st.info(f"Generando {videos_per_account} video(s) para {len(selected)} cuentas...")

            # Create progress placeholders
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()

            total_videos = len(selected) * videos_per_account
            completed = 0

            for account in selected:
                for i in range(videos_per_account):
                    status_text.text(f"Generando video {completed + 1}/{total_videos} para {account['nickname']}...")

                    try:
                        result = generate_video_for_account(account)
                        
                        with results_container:
                            if result["success"]:
                                st.success(f"✅ {account['nickname']}: {result.get('topic', 'Video generado')}")
                            else:
                                st.error(f"❌ {account['nickname']}: {result.get('error', 'Error desconocido')}")
                    except Exception as e:
                        with results_container:
                            st.error(f"❌ {account['nickname']}: {str(e)}")

                    completed += 1
                    progress_bar.progress(completed / total_videos)

                    # Delay between videos
                    if i < videos_per_account - 1:
                        time.sleep(delay_between)

            status_text.text("✅ Batch completado!")
            st.balloons()

    st.divider()

    # Quick actions
    st.markdown("### ⚡ Acciones Rapidas")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Generar 1 video por cuenta", use_container_width=True):
            st.session_state["batch_quick"] = {"videos": 1}

    with col2:
        if st.button("🔄 Generar 3 videos por cuenta", use_container_width=True):
            st.session_state["batch_quick"] = {"videos": 3}

    with col3:
        if st.button("🔄 Generar 5 videos por cuenta", use_container_width=True):
            st.session_state["batch_quick"] = {"videos": 5}

    # Handle quick actions
    if "batch_quick" in st.session_state:
        quick = st.session_state.pop("batch_quick")
        selected = [a for a in accounts if a["id"] in selected_accounts]

        if selected:
            with st.spinner(f"Generando {quick['videos']} video(s) por cuenta..."):
                results = generate_batch(selected, quick["videos"])

            successful = len([r for r in results if r["success"]])
            failed = len([r for r in results if not r["success"]])

            if successful > 0:
                st.success(f"✅ {successful} videos generados exitosamente!")
            if failed > 0:
                st.error(f"❌ {failed} videos fallaron")


def generate_video_for_account(account):
    """Helper function for multi-channel generation."""
    import time as _time
    from src.config import get as cfg_get, reload_config
    from src.llm import select_model, get_active_model
    from src.tts import TTS
    from src.youtube import YouTube

    try:
        # Reload config
        from src import config
        config._config_cache = None
        reload_config()

        model = get_active_model() or cfg_get("ollama_model", "")
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
            return {
                "success": True,
                "account": account["nickname"],
                "video_path": yt.video_path,
                "metadata": yt.metadata,
                "topic": yt.subject,
            }
        finally:
            yt.close()

    except Exception as e:
        return {
            "success": False,
            "account": account["nickname"],
            "error": str(e),
        }


def page_config():
    """Configuration page."""
    st.markdown('<h1 class="main-header">Configuracion</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Edita la configuracion del proyecto</p>', unsafe_allow_html=True)

    config_path = os.path.join(PROJ_ROOT, "config.json")

    if not os.path.exists(config_path):
        st.error("config.json no encontrado. Copia config.example.json a config.json.")
        return

    import json

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    tab1, tab2, tab3, tab4 = st.tabs(["IA", "Video", "Voces", "Avanzado"])

    with tab1:
        st.markdown('<div class="section-title">Configuracion de IA</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            config_data["ollama_base_url"] = st.text_input("Ollama URL", value=config_data.get("ollama_base_url", ""))
            config_data["ollama_model"] = st.text_input("Modelo Ollama", value=config_data.get("ollama_model", ""))
        with c2:
            config_data["nanobanana2_api_key"] = st.text_input("Gemini API Key", value=config_data.get("nanobanana2_api_key", ""), type="password")
            config_data["nanobanana2_model"] = st.text_input("Modelo Gemini", value=config_data.get("nanobanana2_model", ""))
        config_data["nanobanana2_aspect_ratio"] = st.selectbox("Aspect Ratio", ["9:16", "16:9", "1:1", "4:3"], index=0)

    with tab2:
        st.markdown('<div class="section-title">Configuracion de Video</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            config_data["script_sentence_length"] = st.slider("Oraciones guion", 2, 10, config_data.get("script_sentence_length", 4))
            config_data["threads"] = st.slider("Hilos render", 1, 8, config_data.get("threads", 2))
        with c2:
            config_data["subtitle_max_chars"] = st.slider("Caracteres subtitulo", 10, 80, config_data.get("subtitle_max_chars", 40))
            config_data["tts_rate"] = st.text_input("Velocidad voz", value=config_data.get("tts_rate", "+0%"), help="+0% normal, -10% lento, +10% rapido")
        with c3:
            config_data["is_for_kids"] = st.checkbox("Para ninos", value=config_data.get("is_for_kids", False))
            config_data["headless"] = st.checkbox("Firefox headless", value=config_data.get("headless", False))

    with tab3:
        st.markdown('<div class="section-title">Panel de Voces</div>', unsafe_allow_html=True)

        col_lang, col_voice = st.columns([1, 3])
        with col_lang:
            voice_language = st.selectbox("Idioma", ["es", "en", "pt", "fr", "de", "it", "ja", "ko", "zh", "hi"], index=0, key="voice_lang")

        from src.tts import list_voices

        try:
            voices = list_voices(voice_language)
        except:
            voices = []

        if voices:
            voice_options = {v["ShortName"]: f"{v['ShortName']} ({v.get('Gender', '?')})" for v in voices}

            with col_voice:
                selected_voice = st.selectbox("Seleccionar voz", options=list(voice_options.keys()), format_func=lambda x: voice_options[x], key="voice_select")

            voice_info = next((v for v in voices if v["ShortName"] == selected_voice), None)
            if voice_info:
                c1, c2, c3, c4 = st.columns(4)
                c1.write(f"**Nombre:** {voice_info.get('ShortName', '?')}")
                c2.write(f"**Genero:** {voice_info.get('Gender', '?')}")
                c3.write(f"**Idioma:** {voice_info.get('Locale', '?')}")
                c4.write(f"**Estilo:** {voice_info.get('VoiceType', '?')}")

            # Audio preview
            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                sample_rate = st.selectbox("Velocidad prueba", ["-20%", "-10%", "+0%", "+10%", "+20%"], index=2, key="sample_rate")
            with c2:
                if st.button("Generar Muestra", use_container_width=True):
                    with st.spinner("Generando..."):
                        from src.tts import generate_voice_sample
                        sample_path = generate_voice_sample(selected_voice, voice_language, sample_rate)
                        if sample_path:
                            st.session_state["voice_sample"] = sample_path
                            st.rerun()
            with c3:
                if "voice_sample" in st.session_state and os.path.exists(st.session_state["voice_sample"]):
                    st.audio(st.session_state["voice_sample"], format="audio/mp3")

            # Set as default
            st.caption(f"Voz actual: **{config_data.get('tts_voice', 'es-CO-GonzaloNeural')}**")
            if st.button("Usar esta voz como predeterminada"):
                config_data["tts_voice"] = selected_voice
                st.success(f"Voz cambiada a: {selected_voice}")
                st.rerun()

        else:
            st.warning("No se encontraron voces para este idioma.")

    with tab3:
        st.markdown('<div class="section-title">Configuracion Avanzada</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            config_data["verbose"] = st.checkbox("Modo verbose", value=config_data.get("verbose", True))
            config_data["whisper_model"] = st.text_input("Modelo Whisper", value=config_data.get("whisper_model", "base"))
        with c2:
            config_data["stt_provider"] = st.selectbox("Proveedor STT", ["local_whisper", "third_party_assemblyai"], index=0)
            config_data["imagemagick_path"] = st.text_input("Ruta ImageMagick", value=config_data.get("imagemagick_path", ""))
        config_data["zip_url"] = st.text_input("URL musica de fondo (.zip)", value=config_data.get("zip_url", ""))

    st.markdown("---")
    if st.button("Guardar Configuracion", type="primary", use_container_width=True):
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        reload_config()
        st.success("Configuracion guardada y recargada!")


# ──────────────────────────────────────────────
# Main App
# ──────────────────────────────────────────────

def main():
    initialize()
    render_sidebar()

    # Navigation
    page = st.sidebar.radio(
        "Navegacion",
        ["🏠 Dashboard", "🎥 Generar Short", "👤 Cuentas", "📜 Historial", "📅 Programador", "🚀 Multi-Canal", "⚙️ Configuracion"],
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
    elif page == "📅 Programador":
        page_scheduler()
    elif page == "🚀 Multi-Canal":
        page_multichannel()
    elif page == "⚙️ Configuracion":
        page_config()


if __name__ == "__main__":
    main()
