import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
from app.ui.navbar import navbar
from app.core.interface.task_interface import (
    get_tasks, create_task, update_task, delete_task, get_task_statistics,
    get_current_month_tasks, get_archived_tasks, get_task
)
from app.core.interface.task_archive_interface import (
    archive_task, revive_task, get_active_tasks, get_archived_tasks_only
)
from app.core.interface.analytics_interface import (
    get_task_completion_trends, get_productivity_insights
)
from app.core.interface.metrics_interface import (
    get_current_system_status, get_historical_metrics, get_system_info
)
from app.security.route_protection import RouteProtection
from app.ui.components.loader import LoaderContext
from app.core.utils.task_color_utils import (
    get_combined_task_color, format_date_display, get_days_until_due, get_completion_date_display
)
from app.ui.components.task_modal import show_edit_task_modal
from app.ui.dashboard_task_analysis import render_task_analysis


class DashboardManager:
    def __init__(self):
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state"""
        if "selected_task" not in st.session_state:
            st.session_state.selected_task = None

    async def get_user_tasks(self):
        """Get active tasks for current user"""
        user = RouteProtection.get_current_user()
        if user:
            try:
                # Try to get active tasks first (non-archived)
                return await get_active_tasks(user_id=user.get('id'))
            except Exception:
                # Fallback to regular get_tasks if archive functionality not available
                return await get_tasks(user_id=user.get('id'))
        return []

    async def get_current_month_user_tasks(self):
        """Get current month tasks for current user"""
        user = RouteProtection.get_current_user()
        if user:
            return await get_current_month_tasks(user_id=user.get('id'))
        return []

    async def get_archived_user_tasks(self):
        """Get archived tasks for current user"""
        user = RouteProtection.get_current_user()
        if user:
            try:
                # Try to get archived tasks only
                return await get_archived_tasks_only(user_id=user.get('id'))
            except Exception:
                # Fallback to regular archived tasks (date-based)
                return await get_archived_tasks(user_id=user.get('id'))
        return []

    async def get_task_notes_counts(self, tasks):
        """Get notes counts for a list of tasks"""
        from app.core.interface.task_notes_interface import get_task_notes
        notes_counts = {}
        for task in tasks:
            try:
                task_notes = await get_task_notes(task.id)
                notes_counts[task.id] = len(task_notes) if task_notes else 0
            except:
                notes_counts[task.id] = 0
        return notes_counts

    async def get_task_notes_for_modal(self, task_id):
        """Get all notes for a specific task for modal display"""
        from app.core.interface.task_notes_interface import get_task_notes
        try:
            return await get_task_notes(task_id)
        except:
            return []

    async def handle_notes_operations(self, task_id):
        """Handle pending notes operations (create, update, delete)"""
        from app.core.interface.task_notes_interface import (
            create_task_note, update_task_note, delete_task_note,
            create_task_issue, create_task_resolution, get_task_issue, get_task_resolution
        )

        # Handle note creation
        if 'pending_note_creation' in st.session_state:
            note_data = st.session_state['pending_note_creation']
            try:
                await create_task_note(**note_data)
                # Refresh notes
                task_notes = await self.get_task_notes_for_modal(task_id)
                st.session_state[f'task_notes_{task_id}'] = task_notes
                del st.session_state['pending_note_creation']
            except Exception as e:
                st.error(f"Error creating note: {e}")

        # Handle note update
        if 'pending_note_update' in st.session_state:
            update_data = st.session_state['pending_note_update']
            try:
                await update_task_note(
                    note_id=update_data['note_id'],
                    analysis_content=update_data['analysis_content']
                )
                # Refresh notes
                task_notes = await self.get_task_notes_for_modal(task_id)
                st.session_state[f'task_notes_{task_id}'] = task_notes
                del st.session_state['pending_note_update']
            except Exception as e:
                st.error(f"Error updating note: {e}")

        # Handle note deletion
        if 'pending_note_deletion' in st.session_state:
            note_id = st.session_state['pending_note_deletion']
            try:
                await delete_task_note(note_id)
                # Refresh notes
                task_notes = await self.get_task_notes_for_modal(task_id)
                st.session_state[f'task_notes_{task_id}'] = task_notes
                del st.session_state['pending_note_deletion']
            except Exception as e:
                st.error(f"Error deleting note: {e}")

        # Handle issue update
        if 'pending_issue_update' in st.session_state:
            issue_data = st.session_state['pending_issue_update']
            try:
                await create_task_issue(
                    task_id=issue_data['task_id'],
                    issue_description=issue_data['issue_description'],
                    created_by=issue_data['created_by']
                )
                # Refresh issue data
                task_issue = await get_task_issue(task_id)
                st.session_state[f'task_issue_{task_id}'] = task_issue
                del st.session_state['pending_issue_update']
                st.success("✅ Issue description updated successfully!")
            except Exception as e:
                st.error(f"Error updating issue: {e}")

        # Handle resolution update
        if 'pending_resolution_update' in st.session_state:
            resolution_data = st.session_state['pending_resolution_update']
            try:
                await create_task_resolution(
                    task_id=resolution_data['task_id'],
                    resolution_notes=resolution_data['resolution_notes'],
                    created_by=resolution_data['created_by']
                )
                # Refresh resolution data
                task_resolution = await get_task_resolution(task_id)
                st.session_state[f'task_resolution_{task_id}'] = task_resolution
                del st.session_state['pending_resolution_update']
                st.success("✅ Resolution notes updated successfully!")
            except Exception as e:
                st.error(f"Error updating resolution: {e}")


def apply_custom_css():
    """Apply custom CSS for modern UI styling with responsive design"""
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
        padding: 1.2rem;
        border-radius: 16px;
        box-shadow: -6px 6px 20px rgba(0,0,0,0.15);
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(0,0,0,0.08);
        position: relative;
        overflow: hidden;
    }

    .task-card:hover {
        box-shadow: -8px 8px 30px rgba(0,0,0,0.25);
        transform: translateY(-3px) translateX(2px);
        border-left-width: 6px;
    }

    /* Archived task styling */
    .task-card.archived {
        opacity: 0.7;
        border-left-color: #9e9e9e !important;
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%) !important;
    }

    /* Archive button styling */
    .stButton > button[title*="Archive"] {
        background-color: #ff9800 !important;
        color: white !important;
        border: 2px solid #ff9800 !important;
    }

    .stButton > button[title*="Archive"]:hover {
        background-color: #f57c00 !important;
        border-color: #f57c00 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(255, 152, 0, 0.3) !important;
    }

    /* Revive button styling */
    .stButton > button[title*="Revive"] {
        background-color: #4caf50 !important;
        color: white !important;
        border: 2px solid #4caf50 !important;
    }

    .stButton > button[title*="Revive"]:hover {
        background-color: #388e3c !important;
        border-color: #388e3c !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3) !important;
    }

    /* Responsive breakpoints */
    @media (max-width: 768px) {
        .task-actions {
            flex-direction: column;
            gap: 0.3rem;
        }
        
        .task-actions > div {
            width: 100%;
        }
        
        .task-card {
            padding: 1rem;
        }
        
        .main-header {
            padding: 1.5rem;
        }
        
        .main-header h1 {
            font-size: 1.8rem !important;
        }
    }

    @media (max-width: 480px) {
        .task-card {
            padding: 0.8rem;
        }
        
        .task-actions {
            gap: 0.2rem;
        }
        
        .main-header {
            padding: 1rem;
        }
        
        .main-header h1 {
            font-size: 1.5rem !important;
        }
    }

    /* Button styling for consistent appearance */
    .stButton > button {
        width: 100% !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* Priority and status colors */
    .priority-high { border-left-color: #f44336 !important; }
    .priority-urgent { border-left-color: #d32f2f !important; }
    .priority-medium { border-left-color: #ff9800 !important; }
    .priority-low { border-left-color: #4caf50 !important; }

    .status-todo {
        border-left-color: #2196F3 !important;
    }
    .status-inprogress {
        border-left-color: #9C27B0 !important;
    }
    .status-pending {
        border-left-color: #FF9800 !important;
        border-left-style: double !important;
        border-left-width: 8px !important;
    }
    .status-completed {
        background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%) !important;
        border-left-color: #4CAF50 !important;
        box-shadow: -6px 6px 20px rgba(76, 175, 80, 0.3) !important;
    }

    /* Delete button styling */
    .stButton > button[title*="Delete"] {
        background-color: #dc3545 !important;
        color: white !important;
        border: 2px solid #dc3545 !important;
    }

    .stButton > button[title*="Delete"]:hover {
        background-color: #c82333 !important;
        border-color: #c82333 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3) !important;
    }

    /* Tabs styling */
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


async def render_kanban_board(dashboard_manager):
    """Render the Kanban board interface with archive functionality"""
    st.markdown("### 📋 Kanban Board")

    # Add toggle for current month vs all tasks
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        view_mode = st.radio(
            "View Mode:",
            ["Active Tasks", "Current Month", "All Tasks"],
            horizontal=True,
            help="Active Tasks shows non-archived tasks. Current Month shows only tasks created this month. All Tasks shows everything."
        )

    # Get tasks based on view mode
    with LoaderContext("Loading tasks...", "inline"):
        if view_mode == "Active Tasks":
            tasks = await dashboard_manager.get_user_tasks()
        elif view_mode == "Current Month":
            tasks = await dashboard_manager.get_current_month_user_tasks()
        else:
            tasks = await dashboard_manager.get_user_tasks()

        # Get notes counts for all tasks
        notes_counts = await dashboard_manager.get_task_notes_counts(tasks)

    # Add new task button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("ℹ️ Color Guide", help="Show color system information"):
            st.session_state.show_color_guide = not st.session_state.get(
                "show_color_guide", False)

    with col3:
        if st.button("➕ New Task", type="primary"):
            st.session_state.show_task_modal = True

    # Task creation modal
    if st.session_state.get("show_task_modal", False):
        @st.dialog("➕ Create New Task", width="large")
        def create_task_dialog():
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

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Create Task", type="primary"):
                        st.session_state['pending_task_creation'] = {
                            'title': title,
                            'description': description,
                            'status': 'todo',
                            'priority': priority,
                            'category': category,
                            'due_date': datetime.combine(due_date, datetime.min.time()) if due_date else None,
                            'created_by': RouteProtection.get_current_user().get('id') if RouteProtection.get_current_user() else None
                        }
                        st.session_state.show_task_modal = False
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.show_task_modal = False
                        st.rerun()

        create_task_dialog()

    # Handle pending task creation
    if 'pending_task_creation' in st.session_state:
        task_data = st.session_state['pending_task_creation']
        try:
            with LoaderContext("Creating task...", "inline"):
                await create_task(**task_data)
                st.success("Task created successfully!")
                del st.session_state['pending_task_creation']
                st.rerun()
        except Exception as e:
            st.error(f"Error creating task: {str(e)}")
            del st.session_state['pending_task_creation']

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
                # Get color information based on due date, status, and priority
                color_info = get_combined_task_color(
                    task.due_date, task.status, task.priority)

                # Check if task has notes
                notes_count = notes_counts.get(task.id, 0)
                notes_indicator = f" 📝({notes_count})" if notes_count > 0 else ""

                # Check if task is archived
                is_archived = getattr(task, 'is_archived', False)
                archive_indicator = " 📦" if is_archived else ""

                # Format dates for display
                created_date_str = format_date_display(task.created_at)

                description_preview = (task.description[:50] + "...") if task.description and len(
                    task.description) > 50 else (task.description or "No description")

                # Add archived class if task is archived
                archived_class = "archived" if is_archived else ""

                st.markdown(f"""
                <div class="task-card {color_info['all_classes']} {archived_class}">
                    <strong>{task.title}{notes_indicator}{archive_indicator}</strong><br>
                    <small>{description_preview}</small><br>
                    <div class="date-display created-date">📅 Created: {created_date_str}</div>
                    <small>🏷️ {task.category} | 🔥 {task.priority.title()} | 📊 {color_info['status_description']}</small>
                </div>
                """, unsafe_allow_html=True)

                # Task actions - All in one responsive row with archive functionality
                col_edit, col_notes, col_move, col_archive, col_delete = st.columns([1, 1, 2, 1, 1])
                with col_edit:
                    if st.button("✏️", key=f"edit_{task.id}", help="Edit task", use_container_width=True):
                        st.session_state[f"edit_modal_{task.id}"] = True
                with col_notes:
                    if st.button("📝", key=f"notes_{task.id}", help="Manage daily progress notes", use_container_width=True):
                        st.session_state[f"show_notes_{task.id}"] = True
                with col_move:
                    new_status = st.selectbox(
                        "Status:",
                        ["todo", "inprogress", "pending", "completed"],
                        index=["todo", "inprogress", "pending",
                               "completed"].index(task.status),
                        key=f"status_{task.id}",
                        label_visibility="collapsed"
                    )
                    if new_status != task.status:
                        with LoaderContext("Updating task...", "inline"):
                            try:
                                user = RouteProtection.get_current_user()
                                updated_task = await update_task(task.id, status=new_status, updated_by=user.get('id') if user else None)
                                st.success(f"✅ Task status updated to '{new_status}'!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating task: {str(e)}")
                with col_archive:
                    if is_archived:
                        if st.button("🔄", key=f"revive_{task.id}", help="Revive task from archive", use_container_width=True):
                            st.session_state[f"pending_revive_{task.id}"] = True
                    else:
                        if st.button("📦", key=f"archive_{task.id}", help="Archive this task", use_container_width=True):
                            st.session_state[f"pending_archive_{task.id}"] = True
                with col_delete:
                    if st.button("🗑️", key=f"delete_current_{task.id}", help="Delete this task permanently", type="secondary", use_container_width=True):
                        st.session_state[f"pending_delete_current_{task.id}"] = True

    # Handle archive/revive operations
    for task in tasks:
        # Handle archive operation
        if st.session_state.get(f"pending_archive_{task.id}", False):
            try:
                with LoaderContext("Archiving task...", "inline"):
                    user = RouteProtection.get_current_user()
                    await archive_task(task.id, archived_by=user.get('id') if user else None)
                    st.success(f"📦 Task '{task.title}' archived successfully!")
                    del st.session_state[f"pending_archive_{task.id}"]
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error archiving task: {str(e)}")
                del st.session_state[f"pending_archive_{task.id}"]

        # Handle revive operation
        if st.session_state.get(f"pending_revive_{task.id}", False):
            try:
                with LoaderContext("Reviving task...", "inline"):
                    user = RouteProtection.get_current_user()
                    await revive_task(task.id, revived_by=user.get('id') if user else None)
                    st.success(f"🔄 Task '{task.title}' revived successfully!")
                    del st.session_state[f"pending_revive_{task.id}"]
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error reviving task: {str(e)}")
                del st.session_state[f"pending_revive_{task.id}"]

        # Handle delete operation
        if st.session_state.get(f"pending_delete_current_{task.id}", False):
            try:
                with LoaderContext("Deleting task...", "inline"):
                    await delete_task(task.id)
                    st.success(f"✅ Task '{task.title}' deleted successfully!")
                    del st.session_state[f"pending_delete_current_{task.id}"]
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting task: {str(e)}")
                del st.session_state[f"pending_delete_current_{task.id}"]

    # Show task modals
    for task in tasks:
        if st.session_state.get(f"edit_modal_{task.id}", False):
            show_edit_task_modal(task)

        if st.session_state.get(f"show_notes_{task.id}", False):
            from app.core.interface.task_notes_interface import get_task_issue, get_task_resolution

            task_notes = await dashboard_manager.get_task_notes_for_modal(task.id)
            task_issue = await get_task_issue(task.id)
            task_resolution = await get_task_resolution(task.id)

            st.session_state[f'task_notes_{task.id}'] = task_notes
            st.session_state[f'task_issue_{task.id}'] = task_issue
            st.session_state[f'task_resolution_{task.id}'] = task_resolution

            await dashboard_manager.handle_notes_operations(task.id)

            from app.ui.components.task_notes_modal import show_task_notes_modal
            show_task_notes_modal(task)
            st.session_state[f"show_notes_{task.id}"] = False


async def render_archive_management():
    """Render archive management interface"""
    st.markdown("### 📦 Archive Management")
    
    dashboard_manager = DashboardManager()
    
    # Get archived tasks
    with LoaderContext("Loading archived tasks...", "inline"):
        archived_tasks = await dashboard_manager.get_archived_user_tasks()
    
    if not archived_tasks:
        st.info("📦 No archived tasks found.")
        return
    
    st.markdown(f"**Found {len(archived_tasks)} archived tasks**")
    
    # Display archived tasks
    for task in archived_tasks:
        with st.expander(f"📦 {task.title} (Archived: {format_date_display(getattr(task, 'archived_at', task.updated_at))})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Description:** {task.description or 'No description'}")
                st.markdown(f"**Status:** {task.status.title()}")
                st.markdown(f"**Priority:** {task.priority.title()}")
                st.markdown(f"**Category:** {task.category}")
                if task.due_date:
                    st.markdown(f"**Due Date:** {format_date_display(task.due_date)}")
            
            with col2:
                if st.button("🔄 Revive", key=f"revive_archive_{task.id}", help="Revive this task", use_container_width=True):
                    try:
                        user = RouteProtection.get_current_user()
                        await revive_task(task.id, revived_by=user.get('id') if user else None)
                        st.success(f"🔄 Task '{task.title}' revived successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error reviving task: {str(e)}")
                
                if st.button("🗑️ Delete", key=f"delete_archive_{task.id}", help="Delete permanently", type="secondary", use_container_width=True):
                    try:
                        await delete_task(task.id)
                        st.success(f"✅ Task '{task.title}' deleted permanently!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error deleting task: {str(e)}")


def dashboard(go_to_page):
    """Main dashboard function with archive functionality"""
    apply_custom_css()

    navbar(go_to_page, "dashboard")

    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">📊 AutoReportSystem Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Comprehensive project management with archive functionality
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize dashboard manager
    dashboard_manager = DashboardManager()

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📋 Kanban Board", "📦 Archive", "📊 Analytics", "🖥️ System Monitor", "📈 Task Analysis", "📦 Old Archive"])

    with tab1:
        asyncio.run(render_kanban_board(dashboard_manager))

    with tab2:
        asyncio.run(render_archive_management())

    # Other tabs would be implemented here...


if __name__ == "__main__":
    dashboard()