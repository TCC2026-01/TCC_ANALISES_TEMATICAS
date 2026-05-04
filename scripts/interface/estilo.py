# -*- coding: utf-8 -*-
import streamlit as st


def aplicar_estilo():
    """Tema visual moderno e consistente."""
    st.markdown("""
    <style>
    :root {
        --primary: #2563EB;
        --primary-soft: #DBEAFE;
        --background: #F8FAFC;
        --surface: #FFFFFF;
        --text: #0F172A;
        --border: #E2E8F0;
    }

    .stApp {
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2FF 100%);
        color: var(--text);
    }

    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.92);
        border-right: 1px solid var(--border);
    }

    .main-header {
        background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 55%, #60A5FA 100%);
        padding: 2rem;
        border-radius: 24px;
        color: white !important;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(37,99,235,0.18);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255,255,255,0.75);
        padding: 0.75rem;
        border-radius: 18px;
        border: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        height: 52px;
        border-radius: 14px;
        font-weight: 700;
        background: transparent;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%) !important;
        color: white !important;
        box-shadow: 0 6px 18px rgba(37,99,235,0.24);
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.95);
        border: 1px solid var(--border);
        padding: 1rem;
        border-radius: 18px;
        box-shadow: 0 4px 16px rgba(15,23,42,0.04);
    }

    .stPlotlyChart, div[data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.94);
        border-radius: 18px;
        border: 1px solid var(--border);
        padding: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
