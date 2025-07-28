import streamlit as st
import time


def show_loader(message="Loading...", duration=2):
    """Display a beautiful animated loader"""
    st.markdown("""
    <style>
    .loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin: 2rem 0;
    }
    .loader {
        width: 50px;
        height: 50px;
        border: 4px solid rgba(255,255,255,0.3);
        border-top: 4px solid white;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    .loader-text {
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        text-align: center;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

    loader_placeholder = st.empty()
    with loader_placeholder.container():
        st.markdown(f"""
        <div class="loader-container">
            <div class="loader"></div>
            <div class="loader-text">{message}</div>
        </div>
        """, unsafe_allow_html=True)

    time.sleep(duration)
    loader_placeholder.empty()


def show_inline_loader(message="Processing..."):
    """Display a simple inline loader for forms"""
    return st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 1rem;">
        <div style="width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px;"></div>
        <span style="color: #667eea; font-weight: 600;">{message}</span>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)
