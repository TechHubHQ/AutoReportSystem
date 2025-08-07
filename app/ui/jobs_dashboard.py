"""Jobs and Scheduler Dashboard UI."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }
    
    .jobs-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .status-healthy { color: #4CAF50; }
    .status-unhealthy { color: #f44336; }
    .status-warning { color: #ff9800; }
    
    .enhanced-metric-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .enhanced-metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #4CAF50, #2196F3, #FF9800, #9C27B0);
        background-size: 300% 100%;
        animation: gradient-shift 3s ease infinite;
    }
    
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .enhanced-metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .metric-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        display: block;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-align: center;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-detail {
        font-size: 0.8rem;
        color: #888;
        text-align: center;
        margin-top: 0.5rem;
    }
    
    .job-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border-left: 6px solid #4CAF50;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .job-card::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(76, 175, 80, 0.1) 0%, transparent 70%);
        border-radius: 50%;
        transform: translate(30px, -30px);
    }
    
    .job-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.12);
    }
    
    .job-inactive { 
        border-left-color: #f44336 !important; 
    }
    
    .job-inactive::after {
        background: radial-gradient(circle, rgba(244, 67, 54, 0.1) 0%, transparent 70%) !important;
    }
    
    .job-custom { 
        border-left-color: #2196F3 !important; 
    }
    
    .job-custom::after {
        background: radial-gradient(circle, rgba(33, 150, 243, 0.1) 0%, transparent 70%) !important;
    }
    
    .scheduler-status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .status-running {
        background: rgba(76, 175, 80, 0.1);
        color: #4CAF50;
        border: 1px solid rgba(76, 175, 80, 0.3);
    }
    
    .status-stopped {
        background: rgba(244, 67, 54, 0.1);
        color: #f44336;
        border: 1px solid rgba(244, 67, 54, 0.3);
    }
    
    .status-warning {
        background: rgba(255, 152, 0, 0.1);
        color: #ff9800;
        border: 1px solid rgba(255, 152, 0, 0.3);
    }
    
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse-dot 2s infinite;
    }
    
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }
    
    .info-tooltip {
        position: relative;
        cursor: help;
    }
    
    .info-tooltip:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        white-space: nowrap;
        z-index: 1000;
    }
    
    .progress-ring {
        transform: rotate(-90deg);
    }
    
    .progress-ring-circle {
        transition: stroke-dashoffset 0.35s;
        transform-origin: 50% 50%;
    }
    </style>
    """, unsafe_allow_html=True)


# Removed create_progress_ring function - using CSS conic-gradient instead


async def render_scheduler_overview():
    """Render enhanced scheduler status overview."""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: #333; margin-bottom: 0.5rem;">🔧 Scheduler Control Center</h2>
        <p style="color: #666; font-size: 1.1rem;">Real-time monitoring and system health dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    with LoaderContext("Analyzing scheduler performance...", "inline"):
        scheduler_status = await get_scheduler_status()
        job_stats = await get_job_statistics()
        health_metrics = await get_job_health_metrics()
        jobs = await get_all_jobs()

    # Enhanced status indicators with more details
    st.markdown('<div class="scheduler-status-grid">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_class = "status-running" if scheduler_status['running'] else "status-stopped"
        status_icon = "⚡" if scheduler_status['running'] else "⏸️"
        pulse_color = "#4CAF50" if scheduler_status['running'] else "#f44336"

        st.markdown(f"""
        <div class="enhanced-metric-card">
            <div class="metric-icon">{status_icon}</div>
            <div class="metric-value" style="color: {'#4CAF50' if scheduler_status['running'] else '#f44336'};">
                {'ONLINE' if scheduler_status['running'] else 'OFFLINE'}
            </div>
            <div class="metric-label">Scheduler Status</div>
            <div class="status-indicator {status_class}">
                <div class="pulse-dot" style="background-color: {pulse_color};"></div>
                {'Actively Processing' if scheduler_status['running'] else 'System Stopped'}
            </div>
            <div class="metric-detail">
                Health: {scheduler_status['health'].title()}<br>
                Jobs Loaded: {scheduler_status['jobs_count']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        active_percentage = (
            job_stats['active'] / max(job_stats['total'], 1)) * 100

        st.markdown(f"""
        <div class="enhanced-metric-card">
            <div class="metric-icon">🚀</div>
            <div class="metric-value" style="color: #4CAF50;">{job_stats['active']}</div>
            <div class="metric-label">Active Jobs</div>
            <div style="text-align: center; margin: 1rem 0;">
                <div style="background: conic-gradient(#4CAF50 {active_percentage * 3.6}deg, #e6e6e6 0deg); 
                           width: 60px; height: 60px; border-radius: 50%; margin: 0 auto; 
                           display: flex; align-items: center; justify-content: center;">
                    <div style="background: white; width: 40px; height: 40px; border-radius: 50%; 
                               display: flex; align-items: center; justify-content: center; 
                               font-size: 12px; font-weight: bold; color: #333;">
                        {active_percentage:.0f}%
                    </div>
                </div>
            </div>
            <div class="metric-detail">
                Total: {job_stats['total']} | Inactive: {job_stats['inactive']}<br>
                System: {job_stats['system']} | Custom: {job_stats['custom']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        success_color = "#4CAF50" if health_metrics[
            'success_rate'] >= 90 else "#ff9800" if health_metrics['success_rate'] >= 70 else "#f44336"

        st.markdown(f"""
        <div class="enhanced-metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-value" style="color: {success_color};">{health_metrics['success_rate']:.1f}%</div>
            <div class="metric-label">Success Rate</div>
            <div style="text-align: center; margin: 1rem 0;">
                <div style="background: conic-gradient({success_color} {health_metrics['success_rate'] * 3.6}deg, #e6e6e6 0deg); 
                           width: 60px; height: 60px; border-radius: 50%; margin: 0 auto; 
                           display: flex; align-items: center; justify-content: center;">
                    <div style="background: white; width: 40px; height: 40px; border-radius: 50%; 
                               display: flex; align-items: center; justify-content: center; 
                               font-size: 12px; font-weight: bold; color: #333;">
                        {health_metrics['success_rate']:.0f}%
                    </div>
                </div>
            </div>
            <div class="metric-detail">
                Successful: {health_metrics['successful_executions']}<br>
                Failed: {health_metrics['failed_executions']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="enhanced-metric-card">
            <div class="metric-icon">⏱️</div>
            <div class="metric-value" style="color: #2196F3;">{scheduler_status['uptime']}</div>
            <div class="metric-label">System Uptime</div>
            <div class="metric-detail">
                Avg Duration: {health_metrics['avg_execution_time']}<br>
                Total Executions: {health_metrics['total_executions']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Next scheduled jobs timeline
    if jobs:
        st.markdown("### 📅 Upcoming Schedule")

        upcoming_jobs = [
            job for job in jobs if job['next_run'] and job['is_active']]
        upcoming_jobs.sort(key=lambda x: x['next_run'])

        if upcoming_jobs:
            for i, job in enumerate(upcoming_jobs[:3]):  # Show next 3 jobs
                next_run_str = job['next_run'].strftime(
                    '%Y-%m-%d %H:%M:%S %Z') if job['next_run'] else "Not scheduled"

                # Use timezone-aware datetime for comparison
                if job['next_run']:
                    # Get current time in IST timezone
                    ist_tz = pytz.timezone('Asia/Kolkata')
                    current_time_ist = datetime.now(ist_tz)
                    time_until = job['next_run'] - current_time_ist
                else:
                    time_until = None

                if time_until:
                    if time_until.days > 0:
                        time_str = f"in {time_until.days} days"
                    elif time_until.seconds > 3600:
                        hours = time_until.seconds // 3600
                        time_str = f"in {hours} hours"
                    elif time_until.seconds > 60:
                        minutes = time_until.seconds // 60
                        time_str = f"in {minutes} minutes"
                    else:
                        time_str = "very soon"
                else:
                    time_str = "Not scheduled"

                priority_color = "#4CAF50" if i == 0 else "#2196F3" if i == 1 else "#ff9800"
                priority_label = "Next" if i == 0 else "Upcoming" if i == 1 else "Later"

                st.markdown(f"""
                <div style="background: linear-gradient(90deg, {priority_color}15 0%, transparent 100%); 
                           padding: 1rem; border-radius: 10px; margin: 0.5rem 0; 
                           border-left: 4px solid {priority_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: {priority_color};">{priority_label}: {job['name']}</strong><br>
                            <small style="color: #666;">{next_run_str}</small>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: {priority_color}20; color: {priority_color}; 
                                        padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.9rem;">
                                {time_str}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📅 No upcoming jobs scheduled")

    # System information
    st.markdown("### 🖥️ System Information")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown("""
        <div class="enhanced-metric-card" style="padding: 1.5rem;">
            <h4 style="margin-top: 0; color: #333;">📡 Scheduler Details</h4>
            <div style="font-size: 0.9rem; line-height: 1.6;">
                <strong>Engine:</strong> APScheduler AsyncIO<br>
                <strong>Thread Safety:</strong> ✅ Enabled<br>
                <strong>Timezone:</strong> Asia/Kolkata (IST)<br>
                <strong>Job Store:</strong> Memory (Default)<br>
                <strong>Max Instances:</strong> 1 per job
            </div>
        </div>
        """, unsafe_allow_html=True)

    with info_col2:
        # Use IST timezone for current time display
        ist_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist_tz)
        st.markdown(f"""
        <div class="enhanced-metric-card" style="padding: 1.5rem;">
            <h4 style="margin-top: 0; color: #333;">🕐 Time Information</h4>
            <div style="font-size: 0.9rem; line-height: 1.6;">
                <strong>Current Time:</strong> {current_time.strftime('%Y-%m-%d %H:%M:%S')}<br>
                <strong>Timezone:</strong> {current_time.strftime('%Z %z')}<br>
                <strong>Day of Week:</strong> {current_time.strftime('%A')}<br>
                <strong>Week of Year:</strong> {current_time.strftime('%U')}<br>
                <strong>Last Refresh:</strong> Just now
            </div>
        </div>
        """, unsafe_allow_html=True)


async def render_jobs_list():
    """Render enhanced list of all jobs."""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: #333; margin-bottom: 0.5rem;">📋 Jobs Management Center</h2>
        <p style="color: #666; font-size: 1.1rem;">Monitor and manage all scheduled automation tasks</p>
    </div>
    """, unsafe_allow_html=True)

    with LoaderContext("Loading job configurations...", "inline"):
        jobs = await get_all_jobs()
        job_stats = await get_job_statistics()

    if not jobs:
        st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem; 
                   background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                   border-radius: 20px; margin: 2rem 0; border: 2px dashed #dee2e6;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🤖</div>
            <h3 style="color: #666; margin-bottom: 1rem;">No Jobs Configured Yet</h3>
            <p style="color: #888; margin-bottom: 2rem; font-size: 1.1rem;">
                Your scheduler is ready and waiting for automation tasks.
            </p>
            <p style="color: #888; font-size: 0.9rem;">
                Jobs will appear here once they are discovered or manually configured.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Enhanced job statistics summary
    st.markdown("### 📊 Quick Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="enhanced-metric-card" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: #333;">{job_stats['total']}</div>
            <div style="color: #666; font-size: 0.9rem;">Total Jobs</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        delta_color = "#4CAF50" if job_stats['active'] > job_stats['inactive'] else "#ff9800"
        st.markdown(f"""
        <div class="enhanced-metric-card" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: {delta_color};">{job_stats['active']}</div>
            <div style="color: #666; font-size: 0.9rem;">Active Jobs</div>
            <div style="font-size: 0.8rem; color: {delta_color};">+{job_stats['active'] - job_stats['inactive']} vs inactive</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="enhanced-metric-card" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🛠️</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: #2196F3;">{job_stats['system']}</div>
            <div style="color: #666; font-size: 0.9rem;">System Jobs</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="enhanced-metric-card" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎨</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: #9C27B0;">{job_stats['custom']}</div>
            <div style="color: #666; font-size: 0.9rem;">Custom Jobs</div>
        </div>
        """, unsafe_allow_html=True)

    # Enhanced jobs display
    st.markdown("### 🔧 Job Details & Status")

    for i, job in enumerate(jobs):
        status_class = "job-inactive" if not job['is_active'] else (
            "job-custom" if job['is_custom'] else "")

        # Enhanced status indicators
        if job['is_active']:
            status_icon = "🟢"
            status_text = "ACTIVE"
            status_color = "#4CAF50"
        else:
            status_icon = "🔴"
            status_text = "INACTIVE"
            status_color = "#f44336"

        job_type = "Custom" if job['is_custom'] else "System"
        job_type_color = "#9C27B0" if job['is_custom'] else "#2196F3"
        job_type_icon = "🎨" if job['is_custom'] else "🛠️"

        # Enhanced time formatting
        if job['next_run']:
            next_run = job['next_run'].strftime('%Y-%m-%d %H:%M:%S %Z')

            # Use timezone-aware datetime for comparison
            ist_tz = pytz.timezone('Asia/Kolkata')
            current_time_ist = datetime.now(ist_tz)
            time_until = job['next_run'] - current_time_ist

            if time_until and time_until.total_seconds() > 0:
                if time_until.days > 0:
                    countdown = f"in {time_until.days} days"
                elif time_until.seconds > 3600:
                    hours = time_until.seconds // 3600
                    countdown = f"in {hours} hours"
                elif time_until.seconds > 60:
                    minutes = time_until.seconds // 60
                    countdown = f"in {minutes} minutes"
                else:
                    countdown = "very soon"
            else:
                countdown = "overdue"
        else:
            next_run = "Not scheduled"
            countdown = "N/A"

        last_run = job['last_run'].strftime(
            '%Y-%m-%d %H:%M:%S') if job['last_run'] else "Never executed"

        # Enhanced job card - broken into smaller parts to avoid HTML escaping
        # Job header with title and badges
        st.markdown(f"""
        <div class="job-card {status_class}" style="margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: #333; margin-right: 1rem;">{status_icon} {job['name']}</h3>
                <span style="background: {status_color}20; color: {status_color}; 
                            padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.8rem; font-weight: 600;">
                    {status_text}
                </span>
                <span style="background: {job_type_color}20; color: {job_type_color}; 
                            padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.8rem; 
                            font-weight: 600; margin-left: 0.5rem;">
                    {job_type_icon} {job_type}
                </span>
            </div>
        """, unsafe_allow_html=True)

        # Job description
        st.markdown(f"""
            <p style="margin: 0 0 1.5rem 0; color: #666; font-size: 1rem; line-height: 1.5;">
                {job['description'] or 'Automated task with no description provided'}
            </p>
        """, unsafe_allow_html=True)

        # Job details grid
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; height: 100%;">
                <strong style="color: #333;">📅 Schedule Configuration</strong><br>
                <span style="color: #666;">{str(job['schedule_type'])[:50]}{'...' if len(str(job['schedule_type'])) > 50 else ''}</span>
            </div>
            """, unsafe_allow_html=True)

        with col_b:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; height: 100%;">
                <strong style="color: #333;">⏰ Next Execution</strong><br>
                <span style="color: #666;">{next_run}</span><br>
                <small style="color: {status_color}; font-weight: 600;">{countdown}</small>
            </div>
            """, unsafe_allow_html=True)

        with col_c:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; height: 100%;">
                <strong style="color: #333;">🕐 Last Execution</strong><br>
                <span style="color: #666;">{last_run}</span>
            </div>
            """, unsafe_allow_html=True)

        # Close the job card
        st.markdown("</div>", unsafe_allow_html=True)


async def render_execution_history():
    """Render job execution history."""
    st.markdown("### 📈 Execution History")

    with LoaderContext("Loading execution history...", "inline"):
        history = await get_job_execution_history(limit=20)
        health_metrics = await get_job_health_metrics()

    if not history:
        st.info(
            "No execution history available yet. Jobs will appear here once they start running.")
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
        df_history['status_icon'] = df_history['successful'].apply(
            lambda x: "✅" if x else "❌")
        df_history['execution_time_str'] = df_history['execution_time'].dt.strftime(
            '%Y-%m-%d %H:%M:%S')

        # Display as table
        display_df = df_history[['status_icon', 'job_id',
                                 'execution_time_str', 'duration']].copy()
        display_df.columns = ['Status', 'Job ID', 'Execution Time', 'Duration']

        st.dataframe(display_df, use_container_width=True, hide_index=True)


async def render_performance_charts():
    """Render performance charts."""
    st.markdown("### 📊 Performance Analytics")

    with LoaderContext("Generating performance charts...", "inline"):
        history = await get_job_execution_history(limit=100)
        health_metrics = await get_job_health_metrics()

    if not history:
        st.info(
            "No execution data available for charts. Run some jobs to see performance analytics.")
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
                color_discrete_map={
                    'Successful': '#4CAF50', 'Failed': '#f44336'}
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Execution timeline
        if history:
            df_history = pd.DataFrame(history)
            df_history['hour'] = df_history['execution_time'].dt.hour
            hourly_counts = df_history.groupby(
                'hour').size().reset_index(name='count')

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
        job_performance['Success Rate'] = (
            job_performance['Successful'] / job_performance['Total'] * 100).round(1)
        job_performance = job_performance.sort_values(
            'Success Rate', ascending=False)

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


def jobs_dashboard(go_to_page):
    """Main jobs dashboard function."""
    apply_jobs_css()

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
