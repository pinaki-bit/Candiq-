"""
frontend/styles/__init__.py

Premium HUD / Sci-Fi theme system for Resume Intelligence.
"""

from __future__ import annotations
import streamlit as st


_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
/* ============================================================
   RESUME INTELLIGENCE  —  FUTURISTIC HUD THEME
   Inspired by: Tron / Sci-Fi command-center aesthetic
   Colors: Deep dark teal + Electric cyan glows
============================================================ */

:root {
    --bg0:         #010a0f;
    --bg1:         #041218;
    --bg2:         #071e28;
    --bg3:         #0b2535;
    --cyan:        #00d4ff;
    --cyan-dim:    #0099bb;
    --cyan-glow:   rgba(0,212,255,0.25);
    --cyan-glow2:  rgba(0,212,255,0.08);
    --teal:        #00ffcc;
    --teal-dim:    #00c49a;
    --orange:      #ff6b35;
    --red:         #ff3366;
    --green:       #00ff9d;
    --yellow:      #ffe066;
    --white:       #e8f4f8;
    --grey:        #5a8a9f;
    --font-hud:    'Orbitron', monospace;
    --font-body:   'Rajdhani', sans-serif;
    --font-mono:   'Share Tech Mono', monospace;
    --r: 6px;
    --r2: 12px;
}

/* ── Reset & base ───────────────────────────────────────────── */
html, body, [data-testid="stApp"] {
    background: var(--bg0) !important;
    font-family: var(--font-body) !important;
    color: var(--white) !important;
}

/* Scanline overlay effect */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,212,255,0.012) 2px,
        rgba(0,212,255,0.012) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Hide Streamlit chrome ─────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

/* ── Scrollbar ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg0); }
::-webkit-scrollbar-thumb { background: var(--cyan-dim); border-radius: 2px; }

/* ── Main content ──────────────────────────────────────────── */
.main .block-container {
    background: var(--bg0) !important;
    padding: 1.5rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Sidebar ───────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg1) !important;
    border-right: 1px solid rgba(0,212,255,0.2) !important;
    box-shadow: 4px 0 30px rgba(0,0,0,0.6) !important;
}
[data-testid="stSidebar"] > div:first-child {
    background: var(--bg1) !important;
}
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Buttons ────────────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    color: var(--cyan) !important;
    border: 1px solid var(--cyan-dim) !important;
    border-radius: var(--r) !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.08em !important;
    padding: 0.5rem 1.1rem !important;
    text-transform: uppercase !important;
    transition: all 0.25s ease !important;
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0,212,255,0.15), transparent);
    transition: left 0.4s ease;
}
.stButton > button:hover::before { left: 100%; }
.stButton > button:hover {
    background: rgba(0,212,255,0.1) !important;
    border-color: var(--cyan) !important;
    box-shadow: 0 0 20px var(--cyan-glow), inset 0 0 20px rgba(0,212,255,0.05) !important;
    color: #fff !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(0,255,204,0.1)) !important;
    border-color: var(--cyan) !important;
    box-shadow: 0 0 15px var(--cyan-glow) !important;
}
.stButton > button[kind="secondary"] {
    border-color: rgba(0,212,255,0.3) !important;
    color: var(--grey) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--cyan-dim) !important;
    color: var(--cyan) !important;
}

/* ── Inputs ─────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: var(--bg2) !important;
    color: var(--cyan) !important;
    border: 1px solid rgba(0,212,255,0.25) !important;
    border-radius: var(--r) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.9rem !important;
    caret-color: var(--cyan) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 2px var(--cyan-glow), 0 0 20px rgba(0,212,255,0.1) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stSlider label, .stFileUploader label {
    color: var(--grey) !important;
    font-family: var(--font-body) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

/* ── Selectbox ──────────────────────────────────────────────── */
.stSelectbox > div > div {
    background: var(--bg2) !important;
    color: var(--cyan) !important;
    border: 1px solid rgba(0,212,255,0.25) !important;
    border-radius: var(--r) !important;
    font-family: var(--font-mono) !important;
}
.stSelectbox > div > div:focus-within { border-color: var(--cyan) !important; }

/* ── Metrics ─────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--bg2) !important;
    border: 1px solid rgba(0,212,255,0.2) !important;
    border-radius: var(--r2) !important;
    padding: 1.2rem 1.5rem !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
}
[data-testid="metric-container"]::after {
    content: '';
    position: absolute;
    bottom: 0; right: 0;
    width: 30px; height: 30px;
    border-right: 2px solid rgba(0,212,255,0.3);
    border-bottom: 2px solid rgba(0,212,255,0.3);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: var(--grey) !important;
    font-family: var(--font-body) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--cyan) !important;
    font-family: var(--font-hud) !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    text-shadow: 0 0 20px var(--cyan-glow) !important;
}

/* ── Tabs ───────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg2) !important;
    border: 1px solid rgba(0,212,255,0.15) !important;
    border-radius: var(--r) !important;
    padding: 3px !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--grey) !important;
    border-radius: 4px !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,212,255,0.12) !important;
    color: var(--cyan) !important;
    border: 1px solid rgba(0,212,255,0.3) !important;
    box-shadow: 0 0 10px var(--cyan-glow) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding-top: 1.5rem !important;
}

/* ── Expanders ──────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg2) !important;
    border: 1px solid rgba(0,212,255,0.15) !important;
    border-radius: var(--r) !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(0,212,255,0.4) !important;
    box-shadow: 0 0 15px rgba(0,212,255,0.08) !important;
}
[data-testid="stExpander"] summary {
    color: var(--white) !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.03em !important;
}
[data-testid="stExpander"] > div > div {
    border-top: 1px solid rgba(0,212,255,0.1) !important;
    padding: 1rem !important;
}

/* ── Forms ──────────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: var(--bg2) !important;
    border: 1px solid rgba(0,212,255,0.2) !important;
    border-radius: var(--r2) !important;
    padding: 1.5rem !important;
}

/* ── File uploader ──────────────────────────────────────────── */
[data-testid="stFileUploader"] > div {
    background: var(--bg2) !important;
    border: 2px dashed rgba(0,212,255,0.3) !important;
    border-radius: var(--r2) !important;
    transition: all 0.25s !important;
}
[data-testid="stFileUploader"] > div:hover {
    border-color: var(--cyan) !important;
    background: rgba(0,212,255,0.04) !important;
    box-shadow: 0 0 25px rgba(0,212,255,0.1) !important;
}

/* ── Divider ────────────────────────────────────────────────── */
hr { border-color: rgba(0,212,255,0.12) !important; margin: 1.5rem 0 !important; }

/* ── Text ───────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-hud) !important;
    color: var(--white) !important;
}
h1 { font-size: 1.6rem !important; letter-spacing: 0.05em !important; }
h2 { font-size: 1.1rem !important; letter-spacing: 0.08em !important; color: var(--cyan) !important; }
h3 { font-size: 0.95rem !important; letter-spacing: 0.1em !important; }
p, li { font-family: var(--font-body) !important; color: #9bc0cd !important; font-size: 0.95rem !important; }

/* ── Alerts ─────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    font-family: var(--font-body) !important;
    border-radius: var(--r) !important;
    border-width: 1px !important;
    letter-spacing: 0.02em !important;
}
.stSuccess {
    background: rgba(0,255,157,0.07) !important;
    border-color: rgba(0,255,157,0.4) !important;
    color: var(--green) !important;
}
.stError {
    background: rgba(255,51,102,0.07) !important;
    border-color: rgba(255,51,102,0.4) !important;
    color: var(--red) !important;
}
.stWarning {
    background: rgba(255,224,102,0.07) !important;
    border-color: rgba(255,224,102,0.4) !important;
    color: var(--yellow) !important;
}
.stInfo {
    background: rgba(0,212,255,0.07) !important;
    border-color: rgba(0,212,255,0.35) !important;
    color: var(--cyan) !important;
}

/* ── Spinner ────────────────────────────────────────────────── */
.stSpinner > div { border-top-color: var(--cyan) !important; }

/* ── Number input ───────────────────────────────────────────── */
.stNumberInput button {
    background: var(--bg3) !important;
    color: var(--cyan) !important;
    border-color: rgba(0,212,255,0.2) !important;
    border-radius: 4px !important;
    box-shadow: none !important;
}
.stNumberInput button:hover {
    background: rgba(0,212,255,0.15) !important;
    transform: none !important;
    box-shadow: 0 0 10px var(--cyan-glow) !important;
}

/* ── Toggle/Checkbox ────────────────────────────────────────── */
.stToggle > label > div { background: rgba(0,212,255,0.15) !important; }
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = "") -> None:
    sub = f"<p style='color:#5a8a9f;font-family:Rajdhani,sans-serif;font-size:0.95rem;margin:0.3rem 0 0 0;letter-spacing:0.04em;'>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div style="margin-bottom:1.8rem;padding-bottom:1rem;
        border-bottom:1px solid rgba(0,212,255,0.15);">
        <div style="display:flex;align-items:center;gap:0.8rem;">
            <span style="font-size:1.6rem;filter:drop-shadow(0 0 8px rgba(0,212,255,0.6));">{icon}</span>
            <h1 style="margin:0;font-family:Orbitron,monospace;font-size:1.4rem;font-weight:700;
                letter-spacing:0.12em;text-transform:uppercase;
                background:linear-gradient(90deg,#e8f4f8,#00d4ff);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text;text-shadow:none;">{title}</h1>
        </div>
        {sub}
    </div>
    """, unsafe_allow_html=True)


def hud_card(content_html: str, glow: bool = False) -> None:
    shadow = "box-shadow:0 0 25px rgba(0,212,255,0.15);" if glow else ""
    st.markdown(f"""
    <div style="background:#071e28;border:1px solid rgba(0,212,255,0.2);
        border-radius:10px;padding:1.3rem;position:relative;{shadow}">
        <div style="position:absolute;top:0;left:0;right:0;height:1px;
            background:linear-gradient(90deg,transparent,rgba(0,212,255,0.6),transparent);"></div>
        <div style="position:absolute;top:0;left:0;width:8px;height:8px;
            border-top:2px solid rgba(0,212,255,0.7);border-left:2px solid rgba(0,212,255,0.7);"></div>
        <div style="position:absolute;top:0;right:0;width:8px;height:8px;
            border-top:2px solid rgba(0,212,255,0.7);border-right:2px solid rgba(0,212,255,0.7);"></div>
        <div style="position:absolute;bottom:0;left:0;width:8px;height:8px;
            border-bottom:2px solid rgba(0,212,255,0.7);border-left:2px solid rgba(0,212,255,0.7);"></div>
        <div style="position:absolute;bottom:0;right:0;width:8px;height:8px;
            border-bottom:2px solid rgba(0,212,255,0.7);border-right:2px solid rgba(0,212,255,0.7);"></div>
        {content_html}
    </div>
    """, unsafe_allow_html=True)


def stat_card_html(label: str, value: str, icon: str = "", color: str = "#00d4ff", delta: str = "") -> str:
    delta_html = f"<div style='font-size:0.75rem;color:{color};margin-top:0.4rem;font-family:Rajdhani,sans-serif;font-weight:600;'>{delta}</div>" if delta else ""
    return f"""
    <div style="background:#071e28;border:1px solid rgba(0,212,255,0.2);border-radius:10px;
        padding:1.3rem 1.5rem;position:relative;overflow:hidden;
        box-shadow:0 4px 20px rgba(0,0,0,0.5);">
        <div style="position:absolute;top:0;left:0;right:0;height:1px;
            background:linear-gradient(90deg,transparent,{color},transparent);"></div>
        <div style="position:absolute;top:0;left:0;width:7px;height:7px;
            border-top:2px solid {color};border-left:2px solid {color};opacity:0.7;"></div>
        <div style="position:absolute;bottom:0;right:0;width:7px;height:7px;
            border-bottom:2px solid {color};border-right:2px solid {color};opacity:0.7;"></div>
        <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.14em;
            color:#5a8a9f;font-family:Rajdhani,sans-serif;font-weight:700;margin-bottom:0.5rem;">
            {icon}&nbsp;&nbsp;{label}</div>
        <div style="font-size:2rem;font-weight:700;color:{color};
            font-family:Orbitron,monospace;text-shadow:0 0 20px {color}66;line-height:1.1;">{value}</div>
        {delta_html}
    </div>
    """


def badge(text: str, color: str = "#00d4ff") -> str:
    return f"<span style='background:{color}18;color:{color};font-size:0.72rem;font-weight:700;padding:2px 10px;border-radius:3px;border:1px solid {color}44;font-family:Rajdhani,sans-serif;letter-spacing:0.08em;text-transform:uppercase;'>{text}</span>"


def tier_color(tier: str) -> str:
    return {
        "Excellent": "#00ff9d",
        "Good":      "#00d4ff",
        "Fair":      "#ffe066",
        "Low Match": "#ff3366",
    }.get(tier, "#5a8a9f")
