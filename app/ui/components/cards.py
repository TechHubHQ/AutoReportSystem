import streamlit as st


def metric_card(title, value, icon="📊", color="#667eea"):
    """Display a metric card with modern styling"""

    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid {color};
        margin-bottom: 1rem;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="font-size: 2rem; font-weight: 700; color: {color}; margin-bottom: 0.5rem;">
            {value}
        </div>
        <div style="color: #6c757d; font-size: 0.9rem; font-weight: 500;">
            {title}
        </div>
    </div>
    """, unsafe_allow_html=True)


def info_card(title, content, icon="ℹ️"):
    """Display an information card"""

    st.markdown(f"""
    <div style="
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #17a2b8;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h4 style="margin: 0; color: #333;">{title}</h4>
        </div>
        <div style="color: #666; line-height: 1.5;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def status_badge(status):
    """Return a styled status badge"""

    status_config = {
        "todo": {"color": "#6c757d", "bg": "#f8f9fa", "icon": "📝"},
        "inprogress": {"color": "#007bff", "bg": "#e3f2fd", "icon": "🔄"},
        "pending": {"color": "#ffc107", "bg": "#fff8e1", "icon": "⏳"},
        "completed": {"color": "#28a745", "bg": "#e8f5e9", "icon": "✅"}
    }

    config = status_config.get(status, status_config["todo"])

    return f"""
    <span style="
        background: {config['bg']};
        color: {config['color']};
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
    ">
        {config['icon']} {status.title()}
    </span>
    """


def priority_badge(priority):
    """Return a styled priority badge"""

    priority_config = {
        "low": {"color": "#0c5460", "bg": "#d1ecf1"},
        "medium": {"color": "#856404", "bg": "#fff3cd"},
        "high": {"color": "#721c24", "bg": "#f8d7da"},
        "urgent": {"color": "white", "bg": "#dc3545"}
    }

    config = priority_config.get(priority, priority_config["medium"])

    return f"""
    <span style="
        background: {config['bg']};
        color: {config['color']};
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    ">
        {priority}
    </span>
    """
