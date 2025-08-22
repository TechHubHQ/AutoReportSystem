"""Enhanced system monitor with database health checks and tools integration."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from app.ui.navbar import navbar
from app.ui.components.loader import LoaderContext
from app.core.interface.metrics_interface import (
    get_current_system_status, get_historical_metrics, get_system_info
)
from app.core.interface.database_health_interface import (
    get_comprehensive_database_health, check_database_connection,
    check_database_tables, check_alembic_migration_status
)
from app.core.interface.tools_interface import tools_manager


def apply_system_monitor_css():
    """Apply custom CSS for system monitor page."""
    st.markdown("""
    <style>
    .monitor-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }
    
    .health-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .health-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.15);
    }
    
    .health-card.healthy {
        border-left-color: #4CAF50;
    }
    
    .health-card.warning {
        border-left-color: #FF9800;
    }
    
    .health-card.unhealthy {
        border-left-color: #F44336;
    }
    
    .health-card.error {
        border-left-color: #9C27B0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin: 0.5rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-healthy { color: #4CAF50; }
    .status-warning { color: #FF9800; }
    .status-unhealthy { color: #F44336; }
    .status-error { color: #9C27B0; }
    
    .tool-card {
        background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .tool-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    .tool-card.risk-low {
        border-left: 4px solid #4CAF50;
    }
    
    .tool-card.risk-medium {
        border-left: 4px solid #FF9800;
    }
    
    .tool-card.risk-high {
        border-left: 4px solid #F44336;
    }
    
    .db-section {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid #2196f3;
    }
    
    .system-section {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid #9c27b0;
    }
    </style>
    """, unsafe_allow_html=True)


async def render_database_health():
    """Render database health monitoring section."""
    st.markdown('<div class="db-section">', unsafe_allow_html=True)
    st.markdown("### 🗄️ Database Health & Management")
    
    # Get database health
    with LoaderContext("Checking database health...", "inline"):
        db_health = await get_comprehensive_database_health()
    
    # Overall status
    status_color_map = {
        "healthy": "status-healthy",
        "warning": "status-warning", 
        "unhealthy": "status-unhealthy",
        "error": "status-error"
    }
    
    status_icon_map = {
        "healthy": "✅",
        "warning": "⚠️",
        "unhealthy": "❌", 
        "error": "🚫"
    }
    
    overall_status = db_health.get("overall_status", "error")
    status_class = status_color_map.get(overall_status, "status-error")
    status_icon = status_icon_map.get(overall_status, "🚫")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="health-card {overall_status}">
            <h3 class="metric-value {status_class}">{status_icon} {overall_status.title()}</h3>
            <p class="metric-label">Overall Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Connection health
    connection = db_health.get("connection", {})
    conn_time = connection.get("connection_time_ms", 0)
    with col2:
        conn_color = "status-healthy" if conn_time < 100 else "status-warning" if conn_time < 500 else "status-unhealthy"
        st.markdown(f"""
        <div class="health-card">
            <h3 class="metric-value {conn_color}">{conn_time:.1f}ms</h3>
            <p class="metric-label">Connection Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Tables status
    tables = db_health.get("tables", {})
    tables_status = tables.get("status", "error")
    with col3:
        tables_class = status_color_map.get(tables_status, "status-error")
        expected = tables.get("expected_tables", 0)
        actual = tables.get("actual_tables", 0)
        st.markdown(f"""
        <div class="health-card">
            <h3 class="metric-value {tables_class}">{actual}/{expected}</h3>
            <p class="metric-label">Tables Present</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Migration status
    migrations = db_health.get("migrations", {})
    migration_status = migrations.get("status", "error")
    with col4:
        migration_class = status_color_map.get(migration_status, "status-error")
        migration_icon = "✅" if migration_status == "up_to_date" else "⚠️" if migration_status == "pending" else "❌"
        st.markdown(f"""
        <div class="health-card">
            <h3 class="metric-value {migration_class}">{migration_icon}</h3>
            <p class="metric-label">Migrations</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed health information
    st.markdown("#### 📊 Detailed Health Information")
    
    health_col1, health_col2 = st.columns(2)
    
    with health_col1:
        st.markdown("**Connection Details:**")
        if connection.get("status") == "healthy":
            st.success(f"✅ {connection.get('message', 'Connected')}")
        else:
            st.error(f"❌ {connection.get('message', 'Connection failed')}")
        
        st.markdown("**Table Status:**")
        if tables.get("missing_tables"):
            st.warning(f"⚠️ Missing tables: {', '.join(tables['missing_tables'])}")
        else:
            st.success("✅ All expected tables present")
        
        if tables.get("table_tests"):
            for table, test in tables["table_tests"].items():
                if test["status"] == "healthy":
                    st.info(f"📊 {table}: {test['record_count']} records ({test['query_time_ms']:.1f}ms)")
                else:
                    st.error(f"❌ {table}: {test.get('error', 'Unknown error')}")
    
    with health_col2:
        st.markdown("**Migration Status:**")
        current_version = migrations.get("current_version", "Unknown")
        st.info(f"📋 Current version: {current_version}")
        
        if migrations.get("status") == "up_to_date":
            st.success("✅ Migrations are up to date")
        elif migrations.get("status") == "pending":
            st.warning(f"⚠️ {migrations.get('message', 'Pending migrations')}")
        else:
            st.error(f"❌ {migrations.get('message', 'Migration error')}")
    
    # Database management tools
    st.markdown("#### 🛠️ Database Management Tools")
    
    tool_col1, tool_col2, tool_col3 = st.columns(3)
    
    with tool_col1:
        if st.button("🔄 Sync Migrations", help="Run comprehensive migration sync"):
            with st.spinner("Running migration sync..."):
                result = tools_manager.run_tool("sync_migrations")
                if result["success"]:
                    st.success("✅ Migration sync completed successfully!")
                    if result["stdout"]:
                        st.code(result["stdout"])
                else:
                    st.error(f"❌ Migration sync failed: {result.get('error', 'Unknown error')}")
                    if result.get("stderr"):
                        st.code(result["stderr"])
    
    with tool_col2:
        if st.button("⚡ Quick Sync", help="Run quick migration sync"):
            with st.spinner("Running quick sync..."):
                result = tools_manager.run_tool("quick_sync")
                if result["success"]:
                    st.success("✅ Quick sync completed!")
                    if result["stdout"]:
                        st.code(result["stdout"])
                else:
                    st.error(f"❌ Quick sync failed: {result.get('error', 'Unknown error')}")
    
    with tool_col3:
        if st.button("🔍 Check Status", help="Check migration status"):
            with st.spinner("Checking migration status..."):
                result = tools_manager.run_alembic_command("current")
                if result["success"]:
                    st.success("✅ Status check completed!")
                    st.code(result["stdout"])
                else:
                    st.error(f"❌ Status check failed: {result.get('error', 'Unknown error')}")
    
    # Alembic commands
    st.markdown("#### ⚙️ Alembic Commands")
    
    alembic_col1, alembic_col2, alembic_col3, alembic_col4 = st.columns(4)
    
    with alembic_col1:
        if st.button("📋 Current Version"):
            result = tools_manager.run_alembic_command("current")
            if result["success"]:
                st.code(result["stdout"])
            else:
                st.error(result.get("error", "Command failed"))
    
    with alembic_col2:
        if st.button("📚 History"):
            result = tools_manager.run_alembic_command("history")
            if result["success"]:
                st.code(result["stdout"])
            else:
                st.error(result.get("error", "Command failed"))
    
    with alembic_col3:
        if st.button("🚀 Upgrade Head"):
            if st.session_state.get("confirm_upgrade", False):
                result = tools_manager.run_alembic_command("upgrade", ["head"])
                if result["success"]:
                    st.success("✅ Upgrade completed!")
                    st.code(result["stdout"])
                else:
                    st.error(f"❌ Upgrade failed: {result.get('error', 'Unknown error')}")
                st.session_state.confirm_upgrade = False
            else:
                st.session_state.confirm_upgrade = True
                st.warning("⚠️ Click again to confirm upgrade to head")
    
    with alembic_col4:
        if st.button("🏷️ Stamp Head"):
            if st.session_state.get("confirm_stamp", False):
                result = tools_manager.run_alembic_command("stamp", ["head"])
                if result["success"]:
                    st.success("✅ Stamp completed!")
                    st.code(result["stdout"])
                else:
                    st.error(f"❌ Stamp failed: {result.get('error', 'Unknown error')}")
                st.session_state.confirm_stamp = False
            else:
                st.session_state.confirm_stamp = True
                st.warning("⚠️ Click again to confirm stamp head")
    
    st.markdown('</div>', unsafe_allow_html=True)


async def render_system_health():
    """Render system health monitoring section."""
    st.markdown('<div class="system-section">', unsafe_allow_html=True)
    st.markdown("### 🖥️ System Health & Performance")
    
    # Get system status
    with LoaderContext("Collecting system metrics...", "inline"):
        system_status = await get_current_system_status()
        system_info = await get_system_info()
    
    # System metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_color = "status-healthy" if system_status['cpu_usage'] < 70 else "status-warning" if system_status['cpu_usage'] < 90 else "status-unhealthy"
        st.markdown(f"""
        <div class="health-card">
            <h3 class="metric-value {cpu_color}">💻 {system_status['cpu_usage']:.1f}%</h3>
            <p class="metric-label">CPU Usage</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        mem_color = "status-healthy" if system_status['memory_usage'] < 70 else "status-warning" if system_status['memory_usage'] < 90 else "status-unhealthy"
        st.markdown(f"""
        <div class="health-card">
            <h3 class="metric-value {mem_color}">🧠 {system_status['memory_usage']:.1f}%</h3>
            <p class="metric-label">Memory Usage</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        disk_color = "status-healthy" if system_status['disk_usage'] < 80 else "status-warning" if system_status['disk_usage'] < 95 else "status-unhealthy"
        st.markdown(f"""
        <div class="health-card">
            <h3 class="metric-value {disk_color}">💾 {system_status['disk_usage']:.1f}%</h3>
            <p class="metric-label">Disk Usage</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        health_color = "status-healthy" if system_status['health_score'] == "Excellent" else "status-warning" if system_status['health_score'] == "Good" else "status-unhealthy"
        st.markdown(f"""
        <div class="health-card">
            <h3 class="metric-value {health_color}">❤️ {system_status['health_score']}</h3>
            <p class="metric-label">Health Score</p>
        </div>
        """, unsafe_allow_html=True)
    
    # System alerts
    if system_status['alerts']:
        st.markdown("#### 🚨 System Alerts")
        for alert in system_status['alerts']:
            if "Critical" in alert:
                st.error(alert)
            elif "Warning" in alert:
                st.warning(alert)
            else:
                st.success(alert)
    
    # Historical metrics chart
    st.markdown("#### 📊 Resource Usage Trends")
    with LoaderContext("Loading historical data...", "inline"):
        historical_data = await get_historical_metrics(hours=12)
    
    if historical_data['data']:
        df_metrics = pd.DataFrame(historical_data['data'])
        df_metrics['timestamp'] = pd.to_datetime(df_metrics['timestamp'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_metrics['timestamp'],
            y=df_metrics['cpu_usage'],
            mode='lines+markers',
            name='CPU Usage (%)',
            line=dict(color='#667eea')
        ))
        fig.add_trace(go.Scatter(
            x=df_metrics['timestamp'],
            y=df_metrics['memory_usage'],
            mode='lines+markers',
            name='Memory Usage (%)',
            line=dict(color='#764ba2')
        ))
        fig.add_trace(go.Scatter(
            x=df_metrics['timestamp'],
            y=df_metrics['disk_usage'],
            mode='lines+markers',
            name='Disk Usage (%)',
            line=dict(color='#ff9800')
        ))
        
        fig.update_layout(
            title="System Resource Usage (Last 12 Hours)",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # System information
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown("#### ℹ️ System Information")
        st.markdown(f"""
        <div class="health-card">
            <strong>System Details</strong><br>
            <small>🔧 CPU Cores: {system_info['cpu_cores']}</small><br>
            <small>⚡ CPU Frequency: {system_info['cpu_frequency']}</small><br>
            <small>🧠 Total Memory: {system_info['total_memory']}</small><br>
            <small>💾 Total Disk: {system_info['total_disk']}</small><br>
            <small>⏱️ Uptime: {system_info['system_uptime']}</small><br>
            <small>🐍 Platform: {system_info['platform']}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with info_col2:
        st.markdown("#### 🛠️ System Tools")
        if st.button("🔄 Refresh Metrics"):
            st.rerun()
        
        if st.button("📊 Generate Report"):
            st.info("System report generation feature coming soon!")
    
    st.markdown('</div>', unsafe_allow_html=True)


def system_monitor(go_to_page):
    """Main system monitor page."""
    apply_system_monitor_css()
    
    navbar(go_to_page, "system_monitor")
    
    # Header
    st.markdown("""
    <div class="monitor-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🖥️ System Monitor</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Real-time monitoring and database management dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🗄️ Database Health", "🖥️ System Health", "🛠️ Tools Management"])
    
    with tab1:
        asyncio.run(render_database_health())
    
    with tab2:
        asyncio.run(render_system_health())
    
    with tab3:
        st.markdown("### 🛠️ Available Tools")
        
        tools = tools_manager.get_available_tools()
        
        # Database tools
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
                            st.success(f"✅ {tool['name']} completed successfully!")
                            if result["stdout"]:
                                st.code(result["stdout"])
                        else:
                            st.error(f"❌ {tool['name']} failed: {result.get('error', 'Unknown error')}")
                            if result.get("stderr"):
                                st.code(result["stderr"])
            else:
                st.error(f"Tool not available: {tool.get('error', 'Unknown error')}")


if __name__ == "__main__":
    system_monitor(lambda x: None)