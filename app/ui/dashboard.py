import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import random
import uuid
from typing import List
from app.ui.navbar import navbar
from app.core.interface.task_interface import (
    get_tasks, create_task, update_task, delete_task, get_task_statistics
)
from app.core.interface.analytics_interface import (
    get_task_completion_trends, get_productivity_insights
)
from app.core.interface.metrics_interface import (
    get_current_system_status, get_historical_metrics, get_system_info
)
from app.security.route_protection import RouteProtection
from app.ui.components.loader import LoaderContext


class DashboardManager:
    def __init__(self):
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state"""
        if "selected_task" not in st.session_state:
            st.session_state.selected_task = None

    async def get_user_tasks(self):
        """Get tasks for current user"""
        user = RouteProtection.get_current_user()
        if user:
            return await get_tasks(user_id=user.get('id'))
        return []



def apply_custom_css():
    """Apply custom CSS for modern UI styling"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e1e5e9;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    .task-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #667eea;
        margin-bottom: 0.8rem;
        transition: all 0.2s ease;
    }
    
    .task-card:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transform: translateX(2px);
    }
    
    .priority-high { border-left-color: #ff6b6b !important; }
    .priority-urgent { border-left-color: #d32f2f !important; }
    .priority-medium { border-left-color: #ffd93d !important; }
    .priority-low { border-left-color: #6bcf7f !important; }
    
    .status-todo { background: #fff3cd; }
    .status-in_progress { background: #d1ecf1; }
    .status-pending { background: #f8d7da; }
    .status-completed { background: #d4edda; }
    
    .job-progress {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
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
    
    /* Custom loader styles */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    .stSpinner {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)


async def render_kanban_board(dashboard_manager):
    """Render the Kanban board interface"""
    st.markdown("### 📋 Kanban Board")

    # Get current user tasks with loader
    with LoaderContext("Loading tasks...", "inline"):
        tasks = await dashboard_manager.get_user_tasks()

    # Add new task button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("➕ New Task", type="primary"):
            st.session_state.show_task_modal = True

    # Task creation modal
    if st.session_state.get("show_task_modal", False):
        with st.expander("Create New Task", expanded=True):
            with st.form("new_task_form"):
                title = st.text_input("Task Title")
                description = st.text_area("Description")
                col1, col2 = st.columns(2)
                with col1:
                    priority = st.selectbox(
                        "Priority", ["low", "medium", "high", "urgent"])
                with col2:
                    category = st.selectbox(
                        "Category", ["in progress", "accomplishments", "highlights"])
                due_date = st.date_input("Due Date")

                if st.form_submit_button("Create Task"):
                    with LoaderContext("Creating task...", "inline"):
                        try:
                            user = RouteProtection.get_current_user()
                            await create_task(
                                title=title,
                                description=description,
                                status="todo",
                                priority=priority,
                                category=category,
                                due_date=datetime.combine(
                                    due_date, datetime.min.time()) if due_date else None,
                                created_by=user.get('id')
                            )
                            st.session_state.show_task_modal = False
                            st.success("Task created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating task: {str(e)}")

    # Kanban columns
    col1, col2, col3, col4 = st.columns(4)

    columns = {
        "todo": ("📝 To Do", col1),
        "inprogress": ("🔄 In Progress", col2),
        "pending": ("⏳ Pending", col3),
        "completed": ("✅ Completed", col4)
    }

    for status, (title, column) in columns.items():
        with column:
            st.markdown(f"**{title}**")
            status_tasks = [task for task in tasks if task.status == status]

            for task in status_tasks:
                priority_class = f"priority-{task.priority}"
                due_date_str = task.due_date.strftime(
                    '%Y-%m-%d') if task.due_date else "No due date"
                description_preview = (task.description[:50] + "...") if task.description and len(
                    task.description) > 50 else (task.description or "No description")

                st.markdown(f"""
                <div class="task-card {priority_class}">
                    <strong>{task.title}</strong><br>
                    <small>{description_preview}</small><br>
                    <small>📅 {due_date_str}</small><br>
                    <small>🏷️ {task.category}</small>
                </div>
                """, unsafe_allow_html=True)

                # Task actions
                col_edit, col_move = st.columns(2)
                with col_edit:
                    if st.button("✏️", key=f"edit_{task.id}", help="Edit task"):
                        st.session_state.selected_task = task
                with col_move:
                    new_status = st.selectbox(
                        "Move to:",
                        ["todo", "inprogress", "pending", "completed"],
                        index=["todo", "inprogress", "pending",
                               "completed"].index(task.status),
                        key=f"status_{task.id}",
                        label_visibility="collapsed"
                    )
                    if new_status != task.status:
                        with LoaderContext("Updating task...", "inline"):
                            try:
                                await update_task(task.id, status=new_status)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating task: {str(e)}")

    # Edit task modal
    if st.session_state.get("selected_task"):
        task = st.session_state.selected_task
        with st.expander(f"Edit Task: {task.title}", expanded=True):
            with st.form("edit_task_form"):
                new_title = st.text_input("Title", value=task.title)
                new_description = st.text_area(
                    "Description", value=task.description or "")
                col1, col2 = st.columns(2)
                with col1:
                    new_priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"],
                                                index=["low", "medium", "high", "urgent"].index(task.priority))
                with col2:
                    new_category = st.selectbox("Category", ["in progress", "accomplishments"],
                                                index=["in progress", "accomplishments"].index(task.category))

                due_date_value = task.due_date.date() if task.due_date else None
                new_due_date = st.date_input("Due Date", value=due_date_value)

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("Update Task"):
                        with LoaderContext("Updating task...", "inline"):
                            try:
                                await update_task(
                                    task.id,
                                    title=new_title,
                                    description=new_description,
                                    priority=new_priority,
                                    category=new_category,
                                    due_date=datetime.combine(
                                        new_due_date, datetime.min.time()) if new_due_date else None
                                )
                                st.session_state.selected_task = None
                                st.success("Task updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating task: {str(e)}")
                with col2:
                    if st.form_submit_button("Delete Task", type="secondary"):
                        with LoaderContext("Deleting task...", "inline"):
                            try:
                                await delete_task(task.id)
                                st.session_state.selected_task = None
                                st.success("Task deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting task: {str(e)}")
                with col3:
                    if st.form_submit_button("Cancel"):
                        st.session_state.selected_task = None
                        st.rerun()


async def render_productivity_analytics(dashboard_manager):
    """Render productivity analytics dashboard"""
    st.markdown("### 📊 Productivity Analytics")

    with LoaderContext("Loading analytics data...", "inline"):
        tasks = await dashboard_manager.get_user_tasks()
        user = RouteProtection.get_current_user()
        stats = await get_task_statistics(user_id=user.get('id') if user else None)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">📋 {stats['total']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Total Tasks</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #6bcf7f; margin: 0;">✅ {stats['completed']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Completed</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4fc3f7; margin: 0;">🔄 {stats['inprogress']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">In Progress</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #ff9800; margin: 0;">⏳ {stats['pending']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Pending</p>
        </div>
        """, unsafe_allow_html=True)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        # Task status distribution
        status_counts = {
            'todo': stats['todo'],
            'inprogress': stats['inprogress'],
            'pending': stats['pending'],
            'completed': stats['completed']
        }
        status_counts = {k: v for k, v in status_counts.items() if v > 0}

        if status_counts:
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Task Status Distribution",
                color_discrete_map={
                    'todo': '#ffd93d',
                    'inprogress': '#4fc3f7',
                    'pending': '#ff9800',
                    'completed': '#6bcf7f'
                }
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Priority distribution
        priority_counts = {
            'low': len([t for t in tasks if t.priority == 'low']),
            'medium': len([t for t in tasks if t.priority == 'medium']),
            'high': len([t for t in tasks if t.priority == 'high']),
            'urgent': len([t for t in tasks if t.priority == 'urgent'])
        }
        priority_counts = {k: v for k, v in priority_counts.items() if v > 0}

        if priority_counts:
            fig = px.bar(
                x=list(priority_counts.keys()),
                y=list(priority_counts.values()),
                title="Task Priority Distribution",
                color=list(priority_counts.keys()),
                color_discrete_map={
                    'low': '#6bcf7f',
                    'medium': '#ffd93d',
                    'high': '#ff6b6b',
                    'urgent': '#d32f2f'
                }
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # Completion trend
    st.markdown("#### 📈 Task Completion Trend")

    # Generate completion data for the last 7 days
    dates = [datetime.now() - timedelta(days=i) for i in range(6, -1, -1)]
    completed_per_day = []

    for date in dates:
        completed_count = len([
            task for task in tasks
            if task.status == 'completed' and task.updated_at and task.updated_at.date() == date.date()
        ])
        completed_per_day.append(completed_count)

    fig = px.line(
        x=[d.strftime('%Y-%m-%d') for d in dates],
        y=completed_per_day,
        title="Tasks Completed (Last 7 Days)",
        markers=True
    )
    fig.update_traces(line_color='#667eea', marker_color='#667eea')
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    # User productivity summary
    st.markdown("#### 👤 Your Productivity Summary")

    if tasks:
        user_data = {
            'Category': ['Total Tasks', 'Completed', 'In Progress', 'Pending', 'Todo'],
            'Count': [stats['total'], stats['completed'], stats['inprogress'], stats['pending'], stats['todo']]
        }

        fig = px.bar(
            x=user_data['Category'],
            y=user_data['Count'],
            title="Your Task Overview",
            color=user_data['Category'],
            color_discrete_map={
                'Total Tasks': '#667eea',
                'Completed': '#6bcf7f',
                'In Progress': '#4fc3f7',
                'Pending': '#ff9800',
                'Todo': '#ffd93d'
            }
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks found. Create your first task to see productivity analytics!")

    # Add productivity insights section
    st.markdown("#### 💡 Productivity Insights")
    with LoaderContext("Analyzing productivity patterns...", "inline"):
        insights = await get_productivity_insights(user_id=user.get('id') if user else None)

    if insights['insights']:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📈 Key Insights**")
            for insight in insights['insights']:
                st.info(f"• {insight}")

        with col2:
            st.markdown("**💡 Recommendations**")
            for recommendation in insights['recommendations']:
                st.success(f"• {recommendation}")

    # Task completion trends
    st.markdown("#### 📈 Completion Trends (Last 30 Days)")
    with LoaderContext("Generating trend analysis...", "inline"):
        trends = await get_task_completion_trends(user_id=user.get('id') if user else None, days=30)

    if trends['daily_trends']:
        df_trends = pd.DataFrame(trends['daily_trends'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_trends['date'],
            y=df_trends['created'],
            mode='lines+markers',
            name='Tasks Created',
            line=dict(color='#667eea')
        ))
        fig.add_trace(go.Scatter(
            x=df_trends['date'],
            y=df_trends['completed'],
            mode='lines+markers',
            name='Tasks Completed',
            line=dict(color='#6bcf7f')
        ))

        fig.update_layout(
            title="Task Creation vs Completion Trends",
            xaxis_title="Date",
            yaxis_title="Number of Tasks",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)


async def render_system_monitoring(dashboard_manager):
    """Render system monitoring dashboard"""
    st.markdown("### 🖥️ System Monitoring")

    # Get current system status with loader
    with LoaderContext("Collecting system metrics...", "inline"):
        system_status = await get_current_system_status()
        system_info = await get_system_info()

    # System health overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {system_status['status_color']}; margin: 0;">💻 {system_status['cpu_usage']:.1f}%</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">CPU Usage</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {system_status['status_color']}; margin: 0;">🧠 {system_status['memory_usage']:.1f}%</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Memory Usage</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {system_status['status_color']}; margin: 0;">💾 {system_status['disk_usage']:.1f}%</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Disk Usage</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {system_status['status_color']}; margin: 0;">❤️ {system_status['health_score']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Health Score</p>
        </div>
        """, unsafe_allow_html=True)

    # System alerts
    st.markdown("#### 🚨 System Alerts")
    for alert in system_status['alerts']:
        if "Critical" in alert:
            st.error(alert)
        elif "Warning" in alert:
            st.warning(alert)
        else:
            st.success(alert)

    # Historical metrics chart
    col1, col2 = st.columns(2)

    with col1:
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

    with col2:
        st.markdown("#### ℹ️ System Information")
        st.markdown(f"""
        <div class="task-card">
            <strong>System Details</strong><br>
            <small>🔧 CPU Cores: {system_info['cpu_cores']}</small><br>
            <small>⚡ CPU Frequency: {system_info['cpu_frequency']}</small><br>
            <small>🧠 Total Memory: {system_info['total_memory']}</small><br>
            <small>💾 Total Disk: {system_info['total_disk']}</small><br>
            <small>⏱️ Uptime: {system_info['system_uptime']}</small><br>
            <small>🐍 Platform: {system_info['platform']}</small>
        </div>
        """, unsafe_allow_html=True)


def dashboard():
    """Main dashboard function"""
    apply_custom_css()

    # Add navigation
    def go_to_page(page_name):
        st.session_state.page = page_name
        st.query_params["page"] = page_name
        st.rerun()

    navbar(go_to_page, "dashboard")

    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">📊 AutoReportSystem Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Comprehensive project management and system monitoring
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize dashboard manager
    dashboard_manager = DashboardManager()

    # Tabs
    tab1, tab2, tab3 = st.tabs(
        ["📋 Kanban Board", "📊 Productivity Analytics", "🖥️ System Monitor"])

    with tab1:
        asyncio.run(render_kanban_board(dashboard_manager))

    with tab2:
        asyncio.run(render_productivity_analytics(dashboard_manager))

    with tab3:
        asyncio.run(render_system_monitoring(dashboard_manager))


if __name__ == "__main__":
    # For standalone testing
    dashboard()
