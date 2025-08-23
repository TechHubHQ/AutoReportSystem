"""Jobs and Scheduler Dashboard UI."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, time, date
import pytz
import asyncio
from app.ui.navbar import navbar
from app.core.interface.job_interface import (
    get_all_jobs, get_job_statistics, get_scheduler_status,
    get_job_execution_history, get_job_health_metrics, run_job_now
)
from app.security.route_protection import RouteProtection
from app.ui.components.loader import LoaderContext

# --- Time helpers (IST-aware and schedule-aware) ---
IST_TZ = pytz.timezone('Asia/Kolkata')
RUN_TIME_IST = time(hour=21, minute=50)

def ist_now() -> datetime:
    return datetime.now(IST_TZ)

def last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    first_next = date(year + (1 if month == 12 else 0), (1 if month == 12 else month + 1), 1)
    return first_next - timedelta(days=1)

def compute_last_friday(year: int, month: int) -> date:
    last_dom = last_day_of_month(year, month)
    # Friday=4
    offset = (last_dom.weekday() - 4) % 7
    return last_dom - timedelta(days=offset)

def combine_ist(d: date, t: time) -> datetime:
    return IST_TZ.localize(datetime(d.year, d.month, d.day, t.hour, t.minute, t.second))

def next_month(year: int, month: int) -> tuple[int, int]:
    return (year + (1 if month == 12 else 0), 1 if month == 12 else month + 1)

def get_next_monthly_run_ist(now: datetime) -> datetime:
    # Monthly reporter runs on the last Friday of the month at 21:50 IST
    y, m = now.year, now.month
    last_fri = compute_last_friday(y, m)
    candidate = combine_ist(last_fri, RUN_TIME_IST)
    if now >= candidate:
        y2, m2 = next_month(y, m)
        last_fri = compute_last_friday(y2, m2)
        candidate = combine_ist(last_fri, RUN_TIME_IST)
    return candidate

def is_last_friday(d: date) -> bool:
    return d == compute_last_friday(d.year, d.month)

def get_next_weekly_run_ist(now: datetime) -> datetime:
    # Weekly reporter runs every Friday except last Friday at 21:50 IST
    today = now.date()
    # If today is Friday
    if today.weekday() == 4:
        candidate_date = today
        candidate_dt = combine_ist(candidate_date, RUN_TIME_IST)
        # If already past today's run time or today is last Friday, move to next Friday
        if now >= candidate_dt or is_last_friday(candidate_date):
            days_ahead = 7
        else:
            days_ahead = 0
    else:
        # Days until Friday (4)
        days_ahead = (4 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
    candidate_date = today + timedelta(days=days_ahead)
    # Skip last Friday
    if is_last_friday(candidate_date):
        candidate_date = candidate_date + timedelta(days=7)
    return combine_ist(candidate_date, RUN_TIME_IST)

def format_time_until(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds <= 0:
        return "very soon"
    days = total_seconds // 86400
    remainder = total_seconds % 86400
    hours = remainder // 3600
    minutes = (remainder % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes and not days:  # Show minutes; if many days, hours/mins may be noisy
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return "in " + " ".join(parts) if parts else "very soon"

def get_display_next_run(job: dict, now: datetime) -> datetime | None:
    if not job.get('is_active'):
        return None
    job_id = job.get('id') or job.get('name', '').lower()
    # Normalize id/name
    jid = str(job_id).lower() if job_id else ''
    if 'monthly_reporter' in jid:
        return get_next_monthly_run_ist(now)
    if 'weekly_reporter' in jid:
        return get_next_weekly_run_ist(now)
    # Fallback to scheduler-provided next_run (already tz-aware ideally)
    return job.get('next_run')


def render_job_result(job_result):
    """Render detailed job execution results."""
    status = job_result.get('status', 'unknown')
    
    # Status color mapping
    status_colors = {
        'success': '#4CAF50',
        'partial_success': '#ff9800', 
        'error': '#f44336',
        'skipped': '#2196F3'
    }
    
    status_icons = {
        'success': '✅',
        'partial_success': '⚠️',
        'error': '❌',
        'skipped': '⏭️'
    }
    
    color = status_colors.get(status, '#666')
    icon = status_icons.get(status, '🔄')
    
    st.markdown(f"""
    <div style="background: linear-gradient(145deg, {color}10 0%, {color}05 100%); 
               border: 1px solid {color}30; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h4 style="margin: 0; color: {color};">Job Execution Result</h4>
            <span style="margin-left: auto; background: {color}20; color: {color}; 
                        padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.8rem; font-weight: 600;">
                {status.replace('_', ' ').title()}
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Users Processed", job_result.get('users_processed', 0))
    with col2:
        st.metric("Emails Sent", job_result.get('emails_sent', 0))
    with col3:
        st.metric("Errors", len(job_result.get('errors', [])))
    with col4:
        execution_time = job_result.get('execution_time')
        if execution_time:
            # Handle both string and datetime objects
            if isinstance(execution_time, str):
                try:
                    # Try parsing ISO format string
                    from datetime import datetime
                    if 'T' in execution_time:
                        # ISO format with T separator
                        dt = datetime.fromisoformat(execution_time.replace('Z', '+00:00'))
                    else:
                        # Try other common formats
                        try:
                            dt = datetime.strptime(execution_time, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            dt = datetime.strptime(execution_time, '%H:%M:%S')
                    time_str = dt.strftime('%H:%M:%S')
                except (ValueError, AttributeError) as e:
                    # If parsing fails, just show the string
                    time_str = str(execution_time)[:8] if len(str(execution_time)) > 8 else str(execution_time)
            elif hasattr(execution_time, 'strftime'):
                # It's already a datetime object
                time_str = execution_time.strftime('%H:%M:%S')
            else:
                # Fallback for any other type
                time_str = str(execution_time)[:8] if len(str(execution_time)) > 8 else str(execution_time)
            st.metric("Executed At", time_str)
        else:
            st.metric("Executed At", "N/A")
    
    # Main message
    st.markdown(f"""
    <div style="background: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; 
               border-left: 4px solid {color};">
        <strong>Result:</strong> {job_result.get('message', 'No message available')}
    </div>
    """, unsafe_allow_html=True)
    
    # Execution details
    if job_result.get('details'):
        st.markdown("**Execution Details:**")
        details_container = st.container()
        with details_container:
            for detail in job_result['details']:
                st.markdown(f"• {detail}")
    
    # Errors section
    if job_result.get('errors'):
        st.markdown("**Errors:**")
        for error in job_result['errors']:
            st.error(f"❌ {error}")
    
    # Force execution indicator
    if job_result.get('forced'):
        st.info("⚡ This was a forced execution (schedule checks were bypassed)")
    
    # Close button (removed since we're in expanders now)
    # Users can just collapse the expander to "close" the results
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_job_results_tab():
    """Render the job results tab showing all recent job executions."""
    from app.core.jobs.job_results_store import get_all_job_results, get_job_results_summary, clear_job_results, debug_storage_state
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: #333; margin-bottom: 0.5rem;">📊 Job Execution Results</h2>
        <p style="color: #666; font-size: 1.1rem;">View detailed results from recent job executions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get job results from global storage
    job_results = get_all_job_results()
    
    # Check if there are any job results
    if not job_results:
        st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem; 
                   background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                   border-radius: 20px; margin: 2rem 0; border: 2px dashed #dee2e6;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <h3 style="color: #666; margin-bottom: 1rem;">No Job Results Yet</h3>
            <p style="color: #888; margin-bottom: 2rem; font-size: 1.1rem;">
                Execute jobs using the "Run Now" button to see detailed results here.
            </p>
            <p style="color: #888; font-size: 0.9rem;">
                Results will show execution status, emails sent, errors, and detailed logs.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Filter and sort results to avoid duplicates
    from datetime import datetime
    
    # Group results by base job type (weekly_reporter, monthly_reporter)
    base_job_results = {}
    for job_id, result in job_results.items():
        # Extract base job type
        if 'weekly_reporter' in job_id:
            base_type = 'weekly_reporter'
        elif 'monthly_reporter' in job_id:
            base_type = 'monthly_reporter'
        else:
            base_type = job_id
        
        # Keep only the most recent result for each base type
        if base_type not in base_job_results:
            base_job_results[base_type] = (job_id, result)
        else:
            current_time = base_job_results[base_type][1].get('execution_time', datetime.min)
            new_time = result.get('execution_time', datetime.min)
            if new_time > current_time:
                base_job_results[base_type] = (job_id, result)
    
    # Display summary metrics (calculate from filtered results to avoid duplicates)
    st.markdown("### 📈 Results Summary")
    
    # Calculate summary from filtered results
    total_jobs = len(base_job_results)
    status_counts = {'success': 0, 'partial_success': 0, 'error': 0, 'skipped': 0}
    
    for _, result in base_job_results.values():
        status = result.get('status', 'unknown')
        if status in status_counts:
            status_counts[status] += 1
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Jobs", total_jobs)
    with col2:
        st.metric("Successful", status_counts['success'])
    with col3:
        st.metric("Partial Success", status_counts['partial_success'])
    with col4:
        st.metric("Failed", status_counts['error'])
    with col5:
        st.metric("Skipped", status_counts['skipped'])
    
    # Display job results
    st.markdown("### 📈 Recent Job Executions")
    
    # Sort results by execution time (most recent first)
    sorted_results = sorted(
        base_job_results.values(),
        key=lambda x: x[1].get('execution_time', datetime.min),
        reverse=True
    )
    
    for job_id, result in sorted_results:
        # Extract display name from base job type
        display_name = job_id.replace('_', ' ').title()
        if 'manual' in job_id:
            base_name = job_id.split('_manual')[0].replace('_', ' ').title()
            display_name = f"{base_name} (Manual Run)"
        
        with st.expander(f"📄 {display_name} - {result.get('status', 'unknown').replace('_', ' ').title()}", expanded=False):
            render_job_result(result)
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 Refresh Results", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear All Results", type="secondary", use_container_width=True):
            if st.session_state.get('confirm_clear_results', False):
                clear_job_results()
                st.session_state.confirm_clear_results = False
                st.success("✅ All job results cleared!")
                st.rerun()
            else:
                st.session_state.confirm_clear_results = True
                st.warning("⚠️ Click again to confirm clearing all results")


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
        justify-content: center;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem 0;
        text-align: center;
        width: 100%;
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
    
    /* Enhanced Tab styling - matching dashboard */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 0 1.5rem;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
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

        # Derive display next run using schedule rules for weekly/monthly
        now_ist = ist_now()
        upcoming_jobs = []
        for job in jobs:
            if job.get('is_active'):
                disp_next = get_display_next_run(job, now_ist)
                if disp_next:
                    # Clone dict to avoid mutating original
                    job_copy = dict(job)
                    job_copy['display_next_run'] = disp_next
                    upcoming_jobs.append(job_copy)
        # Sort by display_next_run
        upcoming_jobs.sort(key=lambda x: x['display_next_run'])

        if upcoming_jobs:
            for i, job in enumerate(upcoming_jobs[:3]):  # Show next 3 jobs
                next_run_dt = job.get('display_next_run')
                next_run_str = next_run_dt.strftime('%Y-%m-%d %H:%M:%S %Z') if next_run_dt else "Not scheduled"

                # Compute time until using IST now
                time_until = (next_run_dt - now_ist) if next_run_dt else None

                if time_until:
                    time_str = format_time_until(time_until)
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

        # Enhanced time formatting with schedule-aware next run
        now_ist = ist_now()
        display_next = get_display_next_run(job, now_ist)
        if display_next:
            next_run = display_next.strftime('%Y-%m-%d %H:%M:%S %Z')
            time_until = display_next - now_ist
            countdown = format_time_until(time_until) if time_until else "very soon"
        else:
            next_run = "Not scheduled"
            countdown = "N/A"

        # Handle last_run safely
        last_run_value = job.get('last_run')
        if last_run_value:
            if hasattr(last_run_value, 'strftime'):
                last_run = last_run_value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # It's a string, try to parse and format it
                try:
                    if isinstance(last_run_value, str):
                        from datetime import datetime
                        if 'T' in last_run_value:
                            dt = datetime.fromisoformat(last_run_value.replace('Z', '+00:00'))
                        else:
                            dt = datetime.strptime(last_run_value, '%Y-%m-%d %H:%M:%S')
                        last_run = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        last_run = str(last_run_value)
                except (ValueError, AttributeError):
                    last_run = str(last_run_value)
        else:
            last_run = "Never executed"

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

        # Inline actions
        action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
        with action_col1:
            if job['is_active'] and st.button("▶️ Run Now", key=f"run_now_{job['id']}"):
                with LoaderContext("Executing job...", "inline"):
                    try:
                        result = await run_job_now(job['id'])
                        if result.get('ok'):
                            st.success(f"✅ {result.get('message')}")
                            # Set flag to show results
                            st.session_state[f"show_results_{job['id']}"] = True
                            # Force refresh to show updated results
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('message')}")
                            # Show error details if available
                            if result.get('error'):
                                st.error(f"Error details: {result.get('error')}")
                    except Exception as e:
                        st.error(f"❌ Failed to execute job: {e}")
                        import traceback
                        st.error(f"Traceback: {traceback.format_exc()}")
                        
                        # Store error result for display
                        error_result = {
                            'job_id': job['id'],
                            'status': 'error',
                            'message': f'Job execution failed: {str(e)}',
                            'details': [f'Error: {str(e)}', f'Traceback: {traceback.format_exc()}'],
                            'users_processed': 0,
                            'emails_sent': 0,
                            'errors': [str(e)],
                            'execution_time': datetime.now().isoformat(),
                            'forced': True
                        }
                        
                        from app.core.jobs.job_results_store import store_job_result
                        store_job_result(job['id'], error_result)
        
        with action_col2:
            # Check if results are available in global storage
            from app.core.jobs.job_results_store import get_job_result
            has_results = get_job_result(job['id']) is not None
            
            if st.button("📊 View Results", key=f"view_results_{job['id']}", disabled=not has_results):
                st.session_state[f"show_results_{job['id']}"] = not st.session_state.get(f"show_results_{job['id']}", False)
        
        # Show job execution results if available
        if st.session_state.get(f"show_results_{job['id']}", False):
            from app.core.jobs.job_results_store import get_job_result
            job_result = get_job_result(job['id'])
            if job_result:
                render_job_result(job_result)

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
            fig.update_xaxes(title_text="Hour of Day")
            fig.update_yaxes(title_text="Number of Executions")
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
            fig.update_xaxes(title_text="Job ID")
            fig.update_yaxes(title_text="Success Rate (%)")
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔧 Scheduler Status",
        "📋 Jobs Overview",
        "📈 Execution History",
        "📊 Performance",
        "📊 Job Results"
    ])

    with tab1:
        asyncio.run(render_scheduler_overview())

    with tab2:
        asyncio.run(render_jobs_list())

    with tab3:
        asyncio.run(render_execution_history())

    with tab4:
        asyncio.run(render_performance_charts())
    
    with tab5:
        render_job_results_tab()


if __name__ == "__main__":
    jobs_dashboard()
