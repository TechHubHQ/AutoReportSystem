import streamlit as st
import time


def show_loader(message="Loading...", duration=None):
    """Display a beautiful animated loader"""
    loader_html = f"""
    <div class="loader-container">
        <div class="loader-wrapper">
            <div class="loader-spinner"></div>
            <div class="loader-text">{message}</div>
        </div>
    </div>

    <style>
    .loader-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(5px);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }}

    .loader-wrapper {{
        text-align: center;
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        border: 1px solid rgba(102, 126, 234, 0.1);
    }}

    .loader-spinner {{
        width: 50px;
        height: 50px;
        margin: 0 auto 1rem auto;
        border: 4px solid #f3f3f3;
        border-top: 4px solid transparent;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        animation: spin 1s linear infinite;
        position: relative;
    }}

    .loader-spinner::before {{
        content: '';
        position: absolute;
        top: -4px;
        left: -4px;
        right: -4px;
        bottom: -4px;
        border-radius: 50%;
        border: 4px solid transparent;
        border-top: 4px solid #667eea;
        animation: spin 2s linear infinite reverse;
    }}

    .loader-text {{
        color: #667eea;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
        animation: pulse 1.5s ease-in-out infinite;
    }}

    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 0.7; }}
        50% {{ opacity: 1; }}
    }}
    </style>
    """

    placeholder = st.empty()
    placeholder.markdown(loader_html, unsafe_allow_html=True)

    if duration:
        time.sleep(duration)
        placeholder.empty()

    return placeholder


def show_inline_loader(message="Loading...", key=None):
    """Display an inline loader for smaller components"""
    loader_html = f"""
    <div class="inline-loader" style="text-align: center; padding: 1rem;">
        <div class="inline-spinner"></div>
        <div class="inline-text">{message}</div>
    </div>

    <style>
    .inline-spinner {{
        width: 30px;
        height: 30px;
        margin: 0 auto 0.5rem auto;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }}

    .inline-text {{
        color: #667eea;
        font-size: 0.9rem;
        font-weight: 500;
    }}
    </style>
    """

    return st.markdown(loader_html, unsafe_allow_html=True)


def show_progress_loader(progress, message="Processing...", key=None):
    """Display a progress bar loader"""
    progress_html = f"""
    <div class="progress-loader">
        <div class="progress-text">{message}</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%"></div>
        </div>
        <div class="progress-percent">{progress}%</div>
    </div>

    <style>
    .progress-loader {{
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e1e5e9;
        margin: 1rem 0;
    }}

    .progress-text {{
        color: #667eea;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }}

    .progress-bar {{
        width: 100%;
        height: 8px;
        background: #f3f3f3;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }}

    .progress-fill {{
        height: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
        transition: width 0.3s ease;
        animation: shimmer 2s infinite;
    }}

    .progress-percent {{
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        font-weight: 500;
    }}

    @keyframes shimmer {{
        0% {{ opacity: 0.8; }}
        50% {{ opacity: 1; }}
        100% {{ opacity: 0.8; }}
    }}
    </style>
    """

    return st.markdown(progress_html, unsafe_allow_html=True)


def show_skeleton_loader(lines=3, key=None):
    """Display a skeleton loader for content placeholders"""
    skeleton_html = f"""
    <div class="skeleton-loader">
        {''.join([f'<div class="skeleton-line" style="width: {85 + (i * 5)}%; animation-delay: {i * 0.1}s;"></div>' for i in range(lines)])}
    </div>

    <style>
    .skeleton-loader {{
        padding: 1rem;
    }}

    .skeleton-line {{
        height: 16px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        animation: skeleton-loading 1.5s infinite;
    }}

    .skeleton-line:last-child {{
        margin-bottom: 0;
    }}

    @keyframes skeleton-loading {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    </style>
    """

    return st.markdown(skeleton_html, unsafe_allow_html=True)


class LoaderContext:
    """Context manager for showing loaders during operations"""

    def __init__(self, message="Loading...", loader_type="full"):
        self.message = message
        self.loader_type = loader_type
        self.placeholder = None

    def __enter__(self):
        if self.loader_type == "full":
            self.placeholder = show_loader(self.message)
        elif self.loader_type == "inline":
            self.placeholder = st.empty()
            with self.placeholder:
                show_inline_loader(self.message)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.placeholder:
            self.placeholder.empty()
