# -*- coding: utf-8 -*-
import streamlit as st


def render_section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class='section-header'>
        <h2>{title}</h2>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_insight(message: str, icon: str = "📈"):
    st.markdown(f"""
    <div class='insight-card'>
        <span>{icon}</span>
        <div>{message}</div>
    </div>
    """, unsafe_allow_html=True)
