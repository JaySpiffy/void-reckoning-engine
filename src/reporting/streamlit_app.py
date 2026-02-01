import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import sys
import requests
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.reporting.dashboard_data_provider import DashboardDataProvider
from src.reporting.dashboard.state import get_dashboard_service

# --- Page Config ---
st.set_page_config(
    page_title="Campaign Command Center (HUD)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Styling (The HUD Look) ---
st.markdown("""
<style>
    :root {
        --accent: #ffb800; /* Amber */
        --bg: #0a0e14;
        --border: #1e293b;
        --text-dim: #94a3b8;
    }
    
    .stApp {
        background-color: var(--bg);
        color: #e2e8f0;
        font-family: 'Courier New', Courier, monospace;
    }
    
    .stHeader, .stMetric {
        border-bottom: 2px solid var(--accent);
    }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.4);
        padding: 1rem;
        border-radius: 4px;
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
    }
    
    .stButton>button {
        background-color: transparent !important;
        color: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        border-radius: 2px !important;
        font-weight: bold;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background-color: var(--accent) !important;
        color: black !important;
    }
    
    h1, h2, h3 {
        color: var(--accent) !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bg);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-dim);
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialization ---
@st.cache_resource
def get_provider():
    # Detect DB Path
    db_path = "reports/db/index.db"
    if not os.path.exists(db_path):
        db_path = "campaign_data.db"
        
    from src.reporting.live_dashboard import get_latest_run_context
    universe, run_id = get_latest_run_context(db_path)
    
    # Defaults if discovery fails
    if not universe: universe = "void_reckoning"
    if not run_id: run_id = f"live_{int(time.time())}"
    
    provider = DashboardDataProvider(db_path=db_path)
    return provider, universe, run_id

provider, default_universe, default_run_id = get_provider()

# --- Sidebar / Header ---
st.title("🛡️ CAMPAIGN COMMAND")
col1, col2, col3 = st.columns([2, 2, 4])
with col1:
    universe = st.text_input("UNIVERSE", value=default_universe)
with col2:
    run_id = st.text_input("RUN ID", value=default_run_id)
with col3:
    st.write("") # Padding
    st.write(f"**STATUS:** System Nominal | **TIME:** {datetime.now().strftime('%H:%M:%S')}")

# --- Control Functions ---
def send_control(action):
    try:
        url = f"http://localhost:5000/api/control/{action}"
        resp = requests.post(url)
        return resp.status_code == 200
    except:
        return False

def get_control_status():
    try:
        url = "http://localhost:5000/api/control/status"
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {"paused": True} # Default to paused if server down

# --- Sidebar Telemetry ---
with st.sidebar:
    st.markdown("### 📡 LIVE TELEMETRY")
    event_container = st.empty()
    
    # Fetch recent events
    recent_events = provider.get_metrics_paginated(universe, 'events', limit=15)
    if recent_events and 'items' in recent_events:
        events_html = ""
        for ev in recent_events['items']:
            color = "#ffb800" if ev.get('severity') == 'warning' else "#94a3b8"
            events_html += f'<div style="font-size: 0.75rem; border-bottom: 1px solid #1e293b; padding: 4px;"><span style="color: {color}">[{ev.get("turn", "??")}]</span> {ev.get("message")}</div>'
        event_container.markdown(events_html, unsafe_allow_html=True)
    else:
        event_container.info("No events detected.")

# --- Control Toolbar ---
st.markdown("### 🎮 SIMULATION CONTROL")
control_col1, control_col2, control_col3, control_col4 = st.columns(4)

# Sync with backend state
status = get_control_status()
st.session_state.paused = status.get('paused', True)

with control_col1:
    action = "resume" if st.session_state.paused else "pause"
    if st.button(action.upper(), use_container_width=True):
        if send_control(action):
             st.session_state.paused = not st.session_state.paused
             st.rerun()

with control_col2:
    if st.button("NEXT TURN", use_container_width=True, disabled=not st.session_state.paused):
        if send_control("step"):
            st.toast("Authorization Sent")
            time.sleep(0.5)
            st.rerun()

with control_col3:
    st.metric("CURRENT TURN", provider.get_run_max_turn(universe, run_id))

# --- Dashboard Layout ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 METRICS", "🌌 GALAXY MAP", "⚔️ MILITARY", "💰 ECONOMY"])

with tab1:
    st.markdown("#### PERFORMANCE PULSE")
    m_col1, m_col2, m_col3 = st.columns(3)
    # Placeholder metrics
    m_col1.metric("Battles/Sec", "0.42", delta="0.05")
    m_col2.metric("Spawn Rate", "12.5/m", delta="-1.2")
    m_col3.metric("Loss Rate", "8.2/m", delta="0.5")
    
    # Real data chart (Economic for now as example)
    factions = provider.get_factions(universe, run_id)
    if factions:
        df_profit = provider.get_economic_net_profit(universe, run_id, faction=factions)
        if df_profit and 'turns' in df_profit:
             data = []
             for f, vals in df_profit['factions'].items():
                 for t, v in zip(vals['turns'], vals['values']):
                     data.append({"Turn": t, "Profit": v, "Faction": f})
             df = pd.DataFrame(data)
             fig = px.line(df, x="Turn", y="Profit", color="Faction", 
                          template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Antique)
             fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
             st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("#### GALACTIC TOPOLOGY")
    # Simple Galaxy Scatter Map
    topology = provider.get_galaxy_topology(universe, run_id)
    if topology and 'systems' in topology:
        sys_df = pd.DataFrame(topology['systems'])
        fig_map = px.scatter(sys_df, x="x", y="y", text="name", color="owner",
                           hover_data=["x", "y"], 
                           template="plotly_dark")
        fig_map.update_layout(height=600)
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Waiting for galaxy data...")

with tab3:
    st.write("Military detailed analysis goes here...")
    
with tab4:
    st.write("Economic detailed analysis goes here...")

# --- Live Refresh ---
if not st.session_state.paused:
    time.sleep(1)
    st.rerun()
