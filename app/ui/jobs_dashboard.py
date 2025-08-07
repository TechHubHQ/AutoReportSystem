"""Jobs and Scheduler Dashboard UI."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
from app.ui.navbar import navbar
from app.core.interface.job_interface import (
    get_all_jobs, get_job_statistics, get_scheduler_status,
    get_job_execution_history, get_job_health_metrics
)
from app.security.route_protection import RouteProtection
from app.ui.components.loader import LoaderContext


def apply_jobs_css():
    """Apply custom CSS for jobs dashboard."""
    st.markdown("""
    <style>
    .jobs-header {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .status-healthy { color: #4CAF50; }
    .status-unhealthy { color: #f44336; }
    .status-warning { color: #ff9800; }
    
    .job-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #4CAF50;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    .job-inactive { border-left-color: #f44336 !important; }
    .job-custom { border-left-color: #2196F3 !important; }
    
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .health-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .health-healthy { background-color: #4CAF50; }
    .health-unhealthy { background-color: #f44336; }
    .health-warning { background-color: #ff9800; }
    </style>
    """, unsafe_allow_html=True)


async def render_scheduler_overview():
    """Render scheduler status overview."""
    st.markdown("### 🔧 Scheduler Status")
    
    with LoaderContext("Checking scheduler status...", "inline"):
        scheduler_status = await get_scheduler_status()
        job_stats = await get_job_statistics()
        health_metrics = await get_job_health_metrics()
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = "🟢" if scheduler_status['running'] else "🔴"
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0;">{status_color} Scheduler</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">
                {'Running' if scheduler_status['running'] else 'Stopped'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4CAF50; margin: 0;">⚡ {job_stats['active']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Active Jobs</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #2196F3; margin: 0;">📊 {health_metrics['success_rate']:.1f}%</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Success Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #ff9800; margin: 0;">🕐 {scheduler_status['uptime']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Uptime</p>
        </div>
        """, unsafe_allow_html=True)


async def render_jobs_list():
    """Render list of all jobs."""
    st.markdown("### 📋 Jobs Overview")
    
    with LoaderContext("Loading jobs...", "inline"):
        jobs = await get_all_jobs()
        job_stats = await get_job_statistics()
    
    if not jobs:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: #f8f9fa; border-radius: 10px; margin: 2rem 0;">
            <h3 style="color: #666; margin-bottom: 1rem;">🤖 No Jobs Configured</h3>
            <p style="color: #888; margin-bottom: 2rem;">
                Your scheduler is ready, but no jobs have been configured yet.
            </p>
            <p style="color: #888;">
                Jobs will appear here once they are discovered or manually added.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Job statistics summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Jobs", job_stats['total'])
    with col2:
        st.metric("Active", job_stats['active'], delta=job_stats['active'] - job_stats['inactive'])
    with col3:
        st.metric("Custom Jobs", job_stats['custom'])
    
    # Jobs table
    st.markdown("#### 📊 Job Details")
    
    for job in jobs:
        status_class = "job-inactive" if not job['is_active'] else ("job-custom" if job['is_custom'] else "")
        status_icon = "🟢" if job['is_active'] else "🔴"
        job_type = "Custom" if job['is_custom'] else "System"
        
        next_run = job['next_run'].strftime('%Y-%m-%d %H:%M') if job['next_run'] else "Not scheduled"
        last_run = job['last_run'].strftime('%Y-%m-%d %H:%M') if job['last_run'] else "Never"
        
        st.markdown(f"""
        <div class="job-card {status_class}">
            <div style="display: flex; justify-content: between; align-items: center;">
                <div style="flex: 1;">
                    <h4 style="margin: 0; color: #333;">{status_icon} {job['name']}</h4>
                    <p style="margin: 0.5rem 0; color: #666; font-size: 0.9rem;">
                        {job['description'] or 'No description available'}
                    </p>
                    <div style="display: flex; gap: 1rem; font-size: 0.8rem; color: #888;">
                        <span>📅 Schedule: {job['schedule_type']}</span>
                        <span>🏷️ Type: {job_type}</span>
                        <span>⏰ Next: {next_run}</span>
                        <span>🕐 Last: {last_run}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


async def render_execution_history():
    """Render job execution history."""
    st.markdown("### 📈 Execution History")
    
    with LoaderContext("Loading execution history...", "inline"):
        history = await get_job_execution_history(limit=20)
        health_metrics = await get_job_health_metrics()
    
    if not history:
        st.info("No execution history available yet. Jobs will appear here once they start running.")
        return
    
    # Execution metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Executions", health_metrics['total_executions'])
    with col2:
        st.metric("Successful", health_metrics['successful_executions'], 
                 delta=health_metrics['successful_executions'] - health_metrics['failed_executions'])
    with col3:
        st.metric("Failed", health_metrics['failed_executions'])
    with col4:
        st.metric("Avg Duration", health_metrics['avg_execution_time'])
    
    # Recent executions
    st.markdown("#### 🕐 Recent Executions")
    
    df_history = pd.DataFrame(history)
    if not df_history.empty:
        df_history['status_icon'] = df_history['successful'].apply(lambda x: "✅" if x else "❌")
        df_history['execution_time_str'] = df_history['execution_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Display as table
        display_df = df_history[['status_icon', 'job_id', 'execution_time_str', 'duration']].copy()
        display_df.columns = ['Status', 'Job ID', 'Execution Time', 'Duration']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)


async def render_performance_charts():
    """Render performance charts."""
    st.markdown("### 📊 Performance Analytics")
    
    with LoaderContext("Generating performance charts...", "inline"):
        history = await get_job_execution_history(limit=100)
        health_metrics = await get_job_health_metrics()
    
    if not history:
        st.info("No execution data available for charts. Run some jobs to see performance analytics.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Success rate pie chart
        success_data = {
            'Status': ['Successful', 'Failed'],
            'Count': [health_metrics['successful_executions'], health_metrics['failed_executions']]
        }
        
        if sum(success_data['Count']) > 0:
            fig = px.pie(
                values=success_data['Count'],
                names=success_data['Status'],
                title="Execution Success Rate",
                color_discrete_map={'Successful': '#4CAF50', 'Failed': '#f44336'}
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Execution timeline
        if history:
            df_history = pd.DataFrame(history)
            df_history['hour'] = df_history['execution_time'].dt.hour
            hourly_counts = df_history.groupby('hour').size().reset_index(name='count')
            
            fig = px.bar(
                hourly_counts,
                x='hour',
                y='count',
                title="Executions by Hour",
                color='count',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400, showlegend=False)
            fig.update_xaxis(title="Hour of Day")
            fig.update_yaxis(title="Number of Executions")
            st.plotly_chart(fig, use_container_width=True)
    
    # Job performance comparison
    if history:
        st.markdown("#### 🏆 Job Performance Comparison")
        df_history = pd.DataFrame(history)
        job_performance = df_history.groupby('job_id').agg({
            'successful': ['count', 'sum'],
            'execution_time': 'count'
        }).round(2)
        
        job_performance.columns = ['Total', 'Successful', 'Executions']
        job_performance['Success Rate'] = (job_performance['Successful'] / job_performance['Total'] * 100).round(1)
        job_performance = job_performance.sort_values('Success Rate', ascending=False)
        
        if not job_performance.empty:
            fig = px.bar(
                x=job_performance.index,
                y=job_performance['Success Rate'],
                title="Job Success Rates",
                color=job_performance['Success Rate'],
                color_continuous_scale='RdYlGn',
                range_color=[0, 100]
            )
            fig.update_layout(height=400)
            fig.update_xaxis(title="Job ID")
            fig.update_yaxis(title="Success Rate (%)")
            st.plotly_chart(fig, use_container_width=True)


def jobs_dashboard():
    """Main jobs dashboard function."""
    apply_jobs_css()
    
    # Navigation
    def go_to_page(page_name):
        st.session_state.page = page_name
        st.query_params["page"] = page_name
        st.rerun()
    
    navbar(go_to_page, "jobs")
    
    # Header
    st.markdown("""
    <div class="jobs-header">
        <h1 style="margin: 0; font-size: 2.5rem;">⚙️ Jobs & Scheduler Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Monitor and manage automated jobs and scheduler health
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔧 Scheduler Status", 
        "📋 Jobs Overview", 
        "📈 Execution History", 
        "📊 Performance"
    ])
    
    with tab1:
        asyncio.run(render_scheduler_overview())
    
    with tab2:
        asyncio.run(render_jobs_list())
    
    with tab3:
        asyncio.run(render_execution_history())
    
    with tab4:
        asyncio.run(render_performance_charts())


if __name__ == "__main__":
    jobs_dashboard()