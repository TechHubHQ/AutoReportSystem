import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import asyncio
from datetime import datetime
from app.ui.navbar import navbar
from app.ui.components.loader import LoaderContext
from app.core.interface.metrics_interface import (
    get_current_system_status, get_historical_metrics, get_system_info
)
from app.core.interface.database_health_interface import (
    get_comprehensive_database_health, get_database_performance_metrics, get_database_metrics_history
)
from app.core.interface.tools_interface import tools_manager

# ------------------------- Custom Styling -------------------------


def apply_modern_css():
    st.markdown("""
    <style>
    .dashboard-header {
        background: linear-gradient(120deg,#667eea,#764ba2);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .status-card {
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        background: white;
        box-shadow:0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    .status-value {
        font-size: 1.6rem;
        font-weight: 700;
    }
    .status-label {
        font-size: 0.9rem;
        color: #666;
    }
    .healthy { color:#10B981; }
    .warning { color:#F59E0B; }
    .unhealthy { color:#EF4444; }
    .error { color:#6B21A8; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------- Database Health -------------------------


async def render_database_health():
    st.markdown("### 🗄️ Database Health")
    with LoaderContext("Checking DB health...", "inline"):
        db_health = await get_comprehensive_database_health()

    # Status mappings
    status_map = {
        "healthy": ("✅", "healthy"),
        "warning": ("⚠️", "warning"),
        "unhealthy": ("❌", "unhealthy"),
        "error": ("🚫", "error")
    }

    # Top summary row
    col1, col2, col3, col4 = st.columns(4)
    overall = db_health.get("overall_status", "error")
    conn = db_health.get("connection", {})
    tables = db_health.get("tables", {})
    mig = db_health.get("migrations", {})

    with col1:
        icon, cls = status_map.get(overall, ("🚫", "error"))
        st.markdown(
            f"<div class='status-card'><div class='status-value {cls}'>{icon} {overall.title()}</div><div class='status-label'>Overall</div></div>", unsafe_allow_html=True)
    with col2:
        conn_time = conn.get("connection_time_ms", 0)
        cls = "healthy" if conn_time < 100 else "warning" if conn_time < 500 else "unhealthy"
        st.markdown(
            f"<div class='status-card'><div class='status-value {cls}'>{conn_time:.1f}ms</div><div class='status-label'>Conn. Time</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(
            f"<div class='status-card'><div class='status-value'>{tables.get('actual_tables', 0)}/{tables.get('expected_tables', 0)}</div><div class='status-label'>Tables</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(
            f"<div class='status-card'><div class='status-value'>{mig.get('status', '?').title()}</div><div class='status-label'>Migrations</div></div>", unsafe_allow_html=True)

    # Detailed sections below cards
    st.markdown("#### 📊 Detailed Database Information")
    st.subheader("🔗 Connection Details")
    st.json(conn)

    st.subheader("📊 Tables Details")
    st.json(tables)

    st.subheader("🔄 Migration Details")
    st.json(mig)

    # Performance Metrics
    st.markdown("#### 📈 Database Performance")
    with LoaderContext("Loading DB metrics...", "inline"):
        current = await get_database_performance_metrics()
        history = await get_database_metrics_history(hours=12)

    col1, col2 = st.columns(2)
    with col1:
        if current.get("query_performance"):
            qp = {k: v for k,
                  v in current["query_performance"].items() if v is not None}
            if qp:
                fig = px.bar(x=list(qp.keys()), y=list(qp.values()), labels={
                             'x': 'Query', 'y': 'Time(ms)'}, title="Query Performance", color=list(qp.values()), color_continuous_scale="RdYlGn_r")
                st.plotly_chart(fig, use_container_width=True)
    with col2:
        if tables.get("table_tests"):
            counts = {}
            for t, v in tables["table_tests"].items():
                counts[v.get("status", "unknown")] = counts.get(
                    v.get("status", "unknown"), 0)+1
            fig = px.pie(values=list(counts.values()), names=list(
                counts.keys()), title="Table Status Distribution")
            st.plotly_chart(fig, use_container_width=True)

    if history.get("data"):
        df = pd.DataFrame(history['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['connection_time_ms'], mode='lines+markers', name='Conn Time'))
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['simple_query_ms'], mode='lines+markers', name='Simple Query'))
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['complex_query_ms'], mode='lines+markers', name='Complex Query'))
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['join_query_ms'], mode='lines+markers', name='Join Query'))
        fig.update_layout(title="Performance Trends (12h)",
                          height=400, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

# ------------------------- System Health -------------------------


async def render_system_health():
    st.markdown("### 🖥️ System Health")
    with LoaderContext("Loading system metrics...", "inline"):
        status = await get_current_system_status()
        info = await get_system_info()

    col1, col2, col3 = st.columns(3)

    def gauge(val, title, color):
        fig = go.Figure(go.Indicator(mode="gauge+number", value=val, gauge={
                        'axis': {'range': [0, 100]}, 'bar': {'color': color}}, title={'text': title}))
        fig.update_layout(height=250, margin=dict(t=20, b=0, l=0, r=0))
        return fig
    with col1:
        st.plotly_chart(
            gauge(status['cpu_usage'], 'CPU %', 'blue'), use_container_width=True)
    with col2:
        st.plotly_chart(
            gauge(status['memory_usage'], 'Memory %', 'green'), use_container_width=True)
    with col3:
        st.plotly_chart(
            gauge(status['disk_usage'], 'Disk %', 'orange'), use_container_width=True)

    if status.get('alerts'):
        st.markdown("#### 🚨 Alerts")
        for a in status['alerts']:
            st.warning(a) if "Warning" in a else st.error(
                a) if "Critical" in a else st.success(a)

    # Historical trends
    with LoaderContext("Loading history...", "inline"):
        hist = await get_historical_metrics(hours=12)
    if hist['data']:
        df = pd.DataFrame(hist['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['cpu_usage'], mode='lines+markers', name='CPU'))
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['memory_usage'], mode='lines+markers', name='Memory'))
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['disk_usage'], mode='lines+markers', name='Disk'))
        fig.update_layout(title="System Usage (12h)", height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("ℹ️ System Information")
    st.json(info)

# ------------------------- Main Page -------------------------


def system_monitor(go_to_page):
    apply_modern_css()
    navbar(go_to_page, "system_monitor")
    st.markdown("<div class='dashboard-header'><h1>🖥️ System Monitor</h1><p>Real-time Database & System Dashboard</p></div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🗄️ Database", "🖥️ System", "🛠️ Tools"])
    with tab1:
        asyncio.run(render_database_health())
    with tab2:
        asyncio.run(render_system_health())
    with tab3:
        st.markdown("### 🛠️ Available Tools")
        tools = tools_manager.get_available_tools()
        st.markdown("#### 🗄️ Database Tools")
        for tool in tools["database"]:
            risk_class = f"risk-{tool['risk_level']}"
            available_text = "✅ Available" if tool["available"] else "❌ Not Available"
            st.markdown(f"""
            <div class="tool-card {risk_class}">
                <h4>{tool['name']}</h4>
                <p>{tool['description']}</p>
                <small>📁 Category: {tool['category']} | ⚠️ Risk: {tool['risk_level']} | {available_text}</small>
            </div>
            """, unsafe_allow_html=True)
            if tool["available"]:
                if st.button(f"🚀 Run {tool['name']}", key=f"run_{tool['id']}"):
                    with st.spinner(f"Running {tool['name']}..."):
                        result = tools_manager.run_tool(tool['id'])
                        if result["success"]:
                            st.success(
                                f"✅ {tool['name']} completed successfully!")
                            if result["stdout"]:
                                st.code(result["stdout"])
                        else:
                            st.error(
                                f"❌ {tool['name']} failed: {result.get('error', 'Unknown error')}")
                            if result.get("stderr"):
                                st.code(result["stderr"])
            else:
                st.error(
                    f"Tool not available: {tool.get('error', 'Unknown error')}")


if __name__ == "__main__":
    system_monitor(lambda x: None)
