import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
from app.ui.navbar import navbar
from app.core.interface.task_interface import (
    get_tasks, create_task, update_task, delete_task, get_task_statistics,
    get_current_month_tasks, get_archived_tasks, archive_task, revive_task
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
        if "kanban_view_mode" not in st.session_state:
            st.session_state.kanban_view_mode = "active"  # "active" or "archived"

        # Initialize pending operations only if they don't exist (don't overwrite existing values)
        if "pending_task_deletion" not in st.session_state:
            st.session_state.pending_task_deletion = None
        if "pending_task_archive" not in st.session_state:
            st.session_state.pending_task_archive = None
        if "pending_task_revive" not in st.session_state:
            st.session_state.pending_task_revive = None

        # Initialize confirmation states only if they don't exist
        if "show_delete_confirmation" not in st.session_state:
            st.session_state.show_delete_confirmation = False
        if "task_to_delete" not in st.session_state:
            st.session_state.task_to_delete = None

    async def get_user_tasks(self):
        """Get tasks for current user"""
        user = RouteProtection.get_current_user()
        if user:
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
            return await get_archived_tasks(user_id=user.get('id'))
        return []

    async def get_task_notes_counts(self, tasks):
        """Get notes counts for a list of tasks (only progress notes, excluding issue and resolution)"""
        from app.core.interface.task_notes_interface import get_task_progress_notes
        notes_counts = {}
        for task in tasks:
            try:
                # Use get_task_progress_notes to exclude issue and resolution notes
                # This matches what's displayed in the timeline
                task_notes = await get_task_progress_notes(task.id)
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


def apply_custom_css():
    """Apply custom CSS for modern UI styling with enhanced soft teal color scheme"""
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
        padding: 1.3rem;
        border-radius: 18px;
        box-shadow: -6px 6px 25px rgba(0,0,0,0.12);
        border-left: 5px solid #667eea;
        margin-bottom: 1.2rem;
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        border: 1px solid rgba(0,0,0,0.06);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .task-card:hover {
        box-shadow: -10px 10px 35px rgba(0,0,0,0.18);
        transform: translateY(-4px) translateX(3px);
        border-left-width: 6px;
        background: rgba(255,255,255,0.98);
    }

    .task-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .task-card:hover::before {
        opacity: 1;
    }

    .task-content {
        flex-grow: 1;
        margin-bottom: 1rem;
    }

    .task-metadata {
        margin-top: auto;
    }

    .priority-high { border-left-color: #f44336 !important; }
    .priority-urgent { border-left-color: #d32f2f !important; }
    .priority-medium { border-left-color: #ff9800 !important; }
    .priority-low { border-left-color: #4caf50 !important; }

    /* Enhanced Color Scheme Implementation */
    
    /* COMPLETED TASKS - Enhanced green with better gradient */
    .status-completed {
        background: linear-gradient(135deg, #E8F5E8 0%, #A5D6A7 100%) !important;
        border-left-color: #4CAF50 !important;
        box-shadow: -6px 6px 25px rgba(76, 175, 80, 0.25) !important;
        border-left-width: 5px !important;
    }

    /* PENDING TASKS - Enhanced orange with better styling */
    .status-pending {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFD54F 100%) !important;
        border-left-color: #FF9800 !important;
        border-left-style: double !important;
        border-left-width: 8px !important;
        box-shadow: -6px 6px 25px rgba(255, 152, 0, 0.25) !important;
    }

    /* TODO TASKS - Combinations with Blue */
    /* No due date TODO: Soft Teal + Blue - Beautiful calming combination */
    .due-none.status-todo {
        background: linear-gradient(135deg, #B2DFDB 0%, #E3F2FD 100%) !important;
        border-left-color: #26A69A !important;
        box-shadow: -6px 6px 25px rgba(38, 166, 154, 0.3) !important;
        border-left-width: 5px !important;
    }
    
    /* Overdue TODO: Enhanced Red + Blue */
    .due-overdue.status-todo {
        background: linear-gradient(135deg, #FFCDD2 0%, #E1F5FE 100%) !important;
        border-left-color: #F44336 !important;
        box-shadow: -8px 8px 30px rgba(244, 67, 54, 0.35) !important;
        border-left-width: 6px !important;
    }
    
    /* Urgent TODO (today/tomorrow): Enhanced Orange + Blue */
    .due-urgent.status-todo {
        background: linear-gradient(135deg, #FFE0B2 0%, #E3F2FD 100%) !important;
        border-left-color: #FF9800 !important;
        box-shadow: -7px 7px 28px rgba(255, 152, 0, 0.3) !important;
        border-left-width: 5px !important;
    }
    
    /* Safe TODO (far away): Enhanced Green + Blue */
    .due-safe.status-todo {
        background: linear-gradient(135deg, #C8E6C9 0%, #E3F2FD 100%) !important;
        border-left-color: #4CAF50 !important;
        box-shadow: -6px 6px 25px rgba(76, 175, 80, 0.25) !important;
        border-left-width: 5px !important;
    }

    /* IN PROGRESS TASKS - Combinations with Purple */
    /* No due date IN PROGRESS: Soft Teal + Purple - Beautiful calming combination */
    .due-none.status-inprogress {
        background: linear-gradient(135deg, #B2DFDB 0%, #F3E5F5 100%) !important;
        border-left-color: #26A69A !important;
        box-shadow: -6px 6px 25px rgba(38, 166, 154, 0.3) !important;
        border-left-width: 5px !important;
    }
    
    /* Overdue IN PROGRESS: Enhanced Red + Purple */
    .due-overdue.status-inprogress {
        background: linear-gradient(135deg, #FFCDD2 0%, #F8E1FF 100%) !important;
        border-left-color: #F44336 !important;
        box-shadow: -8px 8px 30px rgba(244, 67, 54, 0.35) !important;
        border-left-width: 6px !important;
    }
    
    /* Urgent IN PROGRESS (today/tomorrow): Enhanced Orange + Purple */
    .due-urgent.status-inprogress {
        background: linear-gradient(135deg, #FFE0B2 0%, #F3E5F5 100%) !important;
        border-left-color: #FF9800 !important;
        box-shadow: -7px 7px 28px rgba(255, 152, 0, 0.3) !important;
        border-left-width: 5px !important;
    }
    
    /* Safe IN PROGRESS (far away): Enhanced Green + Purple */
    .due-safe.status-inprogress {
        background: linear-gradient(135deg, #C8E6C9 0%, #F3E5F5 100%) !important;
        border-left-color: #4CAF50 !important;
        box-shadow: -6px 6px 25px rgba(76, 175, 80, 0.25) !important;
        border-left-width: 5px !important;
    }

    /* Legacy support for old classes - fallback */
    .status-todo {
        border-left-color: #2196F3 !important;
    }
    .status-inprogress {
        border-left-color: #9C27B0 !important;
    }

    /* Enhanced Date display styling */
    .date-display {
        font-size: 0.9rem;
        color: #424242;
        margin: 0.3rem 0;
        font-weight: 500;
        text-shadow: 0 1px 1px rgba(255,255,255,0.6);
    }

    .due-date-urgent {
        color: #C62828 !important;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(255,255,255,0.8);
    }

    .due-date-warning {
        color: #E65100 !important;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(255,255,255,0.8);
    }

    .created-date {
        color: #424242;
        font-size: 0.85rem;
        font-weight: 600;
        text-shadow: 0 1px 1px rgba(255,255,255,0.6);
    }

    /* Enhanced text visibility for task cards */
    .task-card strong {
        color: #1a1a1a !important;
        font-weight: 700;
        text-shadow: 0 1px 3px rgba(255,255,255,0.9);
        font-size: 1.1rem;
    }

    .task-card small {
        color: #2c2c2c !important;
        font-weight: 500;
        text-shadow: 0 1px 2px rgba(255,255,255,0.7);
        line-height: 1.4;
    }

    .completion-date {
        color: #1B5E20 !important;
        font-weight: 700;
        font-size: 0.9rem;
        text-shadow: 0 1px 2px rgba(255,255,255,0.8);
    }

    .job-progress {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }

    /* Enhanced Tab styling */
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

    /* Enhanced Action button styling */
    .stButton > button[title="Delete task permanently"] {
        background-color: #ff4444 !important;
        color: white !important;
        border: 1px solid #ff4444 !important;
    }

    .stButton > button[title="Delete task permanently"]:hover {
        background-color: #cc0000 !important;
        border: 1px solid #cc0000 !important;
    }

    .stButton > button[title="Archive task"] {
        background-color: #666666 !important;
        color: white !important;
        border: 1px solid #666666 !important;
    }

    .stButton > button[title="Archive task"]:hover {
        background-color: #444444 !important;
        border: 1px solid #444444 !important;
    }

    .stButton > button[title="Revive task (move back to active)"] {
        background-color: #28a745 !important;
        color: white !important;
        border: 1px solid #28a745 !important;
    }

    .stButton > button[title="Revive task (move back to active)"]:hover {
        background-color: #1e7e34 !important;
        border: 1px solid #1e7e34 !important;
    }

    /* Enhanced Archived task card styling */
    .archived-task {
        opacity: 0.7 !important;
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%) !important;
        border-left-color: #999999 !important;
        box-shadow: -4px 4px 15px rgba(0,0,0,0.1) !important;
        position: relative;
    }

    .archived-task:hover {
        opacity: 0.85 !important;
        transform: translateY(-1px) translateX(1px) !important;
        box-shadow: -6px 6px 20px rgba(0,0,0,0.15) !important;
    }

    .archive-indicator {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: #666666;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: bold;
        text-shadow: none;
    }

    .archived-task strong {
        color: #666666 !important;
        text-shadow: 0 1px 2px rgba(255,255,255,0.8) !important;
    }

    .archived-task small {
        color: #777777 !important;
        text-shadow: 0 1px 1px rgba(255,255,255,0.7) !important;
    }

    .archive-date {
        color: #666666 !important;
        font-weight: 600;
        font-size: 0.85rem;
        text-shadow: 0 1px 1px rgba(255,255,255,0.6);
    }
    </style>
    """, unsafe_allow_html=True)


async def render_kanban_board(dashboard_manager):
    """Render the Kanban board interface"""
    st.markdown("### 📋 Kanban Board")

    # Add toggle for active vs archived tasks
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        task_view_mode = st.radio(
            "Task View:",
            ["Active Tasks", "Archived Tasks"],
            horizontal=True,
            help="Active Tasks shows current tasks. Archived Tasks shows previously archived tasks."
        )

    with col2:
        # Add secondary toggle for active tasks time filtering
        if task_view_mode == "Active Tasks":
            time_filter = st.radio(
                "Time Filter:",
                ["Current Month", "All Time"],
                horizontal=True,
                help="Current Month shows only tasks created this month. All Time shows all active tasks."
            )
        else:
            time_filter = "All Time"  # Archived tasks always show all time

    # Get tasks based on view mode
    with LoaderContext("Loading tasks...", "inline"):
        if task_view_mode == "Active Tasks":
            if time_filter == "Current Month":
                tasks = await dashboard_manager.get_current_month_user_tasks()
            else:
                tasks = await dashboard_manager.get_user_tasks()
        else:  # Archived Tasks
            tasks = await dashboard_manager.get_archived_user_tasks()

        # Get notes counts for all tasks
        notes_counts = await dashboard_manager.get_task_notes_counts(tasks)

    # Add action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("ℹ️ Color Guide", help="Show color system information"):
            st.session_state.show_color_guide = not st.session_state.get(
                "show_color_guide", False)

    with col3:
        # Only show "New Task" button for active tasks view
        if task_view_mode == "Active Tasks":
            if st.button("➕ New Task", type="primary"):
                st.session_state.show_task_modal = True
        else:
            st.write("")  # Empty space to maintain layout

    # Color system information panel
    if st.session_state.get("show_color_guide", False):
        @st.dialog("🎨 Enhanced Task Color System Guide", width="large")
        def color_guide_dialog():
            st.markdown("""
            ### ✨ Enhanced Color System with Soft Teal
            Each task card uses **beautiful gradient combinations** based on due date urgency and task status:

            **TODO Tasks (Blue combinations):**
            - 🟢🔵 **Soft Teal + Blue**: TODO tasks with no due date set (calm, flexible, no pressure)
            - 🔴+🔵 **Red + Blue**: Overdue TODO tasks (urgent attention needed)
            - 🟠+🔵 **Orange + Blue**: TODO tasks due today/tomorrow (moderate urgency)
            - 🟢+🔵 **Green + Blue**: TODO tasks due later (safe, well-planned)

            **IN PROGRESS Tasks (Purple combinations):**
            - 🟢🟣 **Soft Teal + Purple**: IN PROGRESS tasks with no due date set (calm, flexible workflow)
            - 🔴+🟣 **Red + Purple**: Overdue IN PROGRESS tasks (critical attention needed)
            - 🟠+🟣 **Orange + Purple**: IN PROGRESS tasks due today/tomorrow (focus required)
            - 🟢+🟣 **Green + Purple**: IN PROGRESS tasks due later (steady progress)

            **Special Status Rules:**
            - 🟠 **PENDING**: Always orange with double border (regardless of due date)
            - 🟢 **COMPLETED**: Always green (celebration of achievement)

            **✨ Visual Enhancements:**
            - **Soft teal** represents "no due date" with elegant, calming blend
            - Enhanced shadows and depth for better visual hierarchy
            - Smooth hover animations with subtle lighting effects
            - Improved gradient transitions for modern aesthetics
            - Better text contrast and readability
            """)

            # Enhanced Color examples
            st.markdown("#### 🎨 Color Examples:")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #B2DFDB 0%, #E3F2FD 100%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 5px solid #26A69A; 
                           box-shadow: -6px 6px 25px rgba(38, 166, 154, 0.3); margin: 0.5rem 0;">
                    <small><strong>No Due Date TODO</strong><br>🟢 Soft Teal + Blue</small>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #FFCDD2 0%, #E1F5FE 100%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 6px solid #F44336; 
                           box-shadow: -8px 8px 30px rgba(244, 67, 54, 0.35); margin: 0.5rem 0;">
                    <small><strong>Overdue TODO</strong><br>🔴 Red + Blue</small>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #FFE0B2 0%, #F3E5F5 100%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 5px solid #FF9800; 
                           box-shadow: -7px 7px 28px rgba(255, 152, 0, 0.3); margin: 0.5rem 0;">
                    <small><strong>Urgent IN PROGRESS</strong><br>🟠 Orange + Purple</small>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #FFF8E1 0%, #FFD54F 100%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 8px double #FF9800; 
                           box-shadow: -6px 6px 25px rgba(255, 152, 0, 0.25); margin: 0.5rem 0;">
                    <small><strong>PENDING</strong><br>🟠 Orange Double Border</small>
                </div>
                """, unsafe_allow_html=True)

            with col5:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #E8F5E8 0%, #A5D6A7 100%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 5px solid #4CAF50; 
                           box-shadow: -6px 6px 25px rgba(76, 175, 80, 0.25); margin: 0.5rem 0;">
                    <small><strong>COMPLETED</strong><br>🟢 Always Green</small>
                </div>
                """, unsafe_allow_html=True)

            if st.button("Close Guide"):
                st.session_state.show_color_guide = False
                st.rerun()

        color_guide_dialog()

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

                # Due date (optional - can be left empty)
                due_date = st.date_input(
                    "Due Date",
                    value=None,
                    help="Select the due date (leave empty if not needed)",
                )

                if not due_date:
                    due_date = None

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Create Task", type="primary"):
                        # Store task creation data for the parent async context to handle
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

        # Show the dialog
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

    # Delete confirmation dialog
    if st.session_state.get("show_delete_confirmation", False):
        task_to_delete = st.session_state.get("task_to_delete")
        if task_to_delete:
            @st.dialog("🗑️ Confirm Task Deletion", width="medium")
            def delete_confirmation_dialog():
                st.warning("⚠️ **This action cannot be undone!**")
                st.markdown(f"**Task:** {task_to_delete.title}")
                if task_to_delete.description:
                    st.markdown(
                        f"**Description:** {task_to_delete.description[:100]}{'...' if len(task_to_delete.description) > 100 else ''}")

                st.markdown("---")
                st.markdown(
                    "This will permanently delete the task and all its related data including:")
                st.markdown("- Task notes and progress history")
                st.markdown("- Status change history")
                st.markdown("- All associated records")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Delete Permanently", type="primary", use_container_width=True):
                        # Store deletion data for the parent async context to handle
                        st.session_state['pending_task_deletion'] = task_to_delete.id
                        st.session_state.show_delete_confirmation = False
                        st.session_state.task_to_delete = None
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.show_delete_confirmation = False
                        st.session_state.task_to_delete = None
                        st.rerun()

            delete_confirmation_dialog()

    # Handle pending task deletion
    if 'pending_task_deletion' in st.session_state and st.session_state['pending_task_deletion'] is not None:
        task_id = st.session_state['pending_task_deletion']
        st.info(f"Processing deletion for task {task_id}")  # Debug message
        try:
            with LoaderContext("Deleting task...", "inline"):
                success = await delete_task(task_id)
                if success:
                    st.success("✅ Task deleted successfully!")
                else:
                    st.error("❌ Failed to delete task - task may not exist")
                del st.session_state['pending_task_deletion']
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error deleting task: {str(e)}")
            del st.session_state['pending_task_deletion']

    # Handle pending task archive
    if 'pending_task_archive' in st.session_state and st.session_state['pending_task_archive'] is not None:
        archive_data = st.session_state['pending_task_archive']
        # Debug message
        st.info(f"Processing archive for task {archive_data['task_id']}")
        try:
            with LoaderContext("Archiving task...", "inline"):
                success = await archive_task(archive_data['task_id'], archive_data['archived_by'])
                if success:
                    st.success("✅ Task archived successfully!")
                else:
                    st.error(
                        "❌ Failed to archive task - task may not exist or already archived")
                del st.session_state['pending_task_archive']
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error archiving task: {str(e)}")
            del st.session_state['pending_task_archive']

    # Handle pending task revive
    if 'pending_task_revive' in st.session_state and st.session_state['pending_task_revive'] is not None:
        task_id = st.session_state['pending_task_revive']
        st.info(f"Processing revive for task {task_id}")  # Debug message
        try:
            with LoaderContext("Reviving task...", "inline"):
                success = await revive_task(task_id)
                if success:
                    st.success("✅ Task revived successfully!")
                else:
                    st.error(
                        "❌ Failed to revive task - task may not exist or not archived")
                del st.session_state['pending_task_revive']
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error reviving task: {str(e)}")
            del st.session_state['pending_task_revive']

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

                # Format dates for display
                created_date_str = format_date_display(task.created_at)

                # For completed tasks, show completion date instead of due date
                if task.status == "completed":
                    completion_date_str = get_completion_date_display(
                        task.status, task.updated_at)
                    due_date_display = completion_date_str
                    due_date_class = "completion-date"
                else:
                    # For non-completed tasks, show due date with context
                    due_date_str = format_date_display(
                        task.due_date) if task.due_date else "No due date"

                    # Get days until due for additional context
                    days_until_due = get_days_until_due(task.due_date)
                    due_context = ""
                    if days_until_due is not None:
                        if days_until_due < 0:
                            due_context = f" (Overdue by {abs(days_until_due)} day(s))"
                        elif days_until_due == 0:
                            due_context = " (Due today!)"
                        elif days_until_due == 1:
                            due_context = " (Due tomorrow)"
                        elif days_until_due <= 7:
                            due_context = f" (Due in {days_until_due} day(s))"

                    due_date_display = f"⏰ Due: {due_date_str}{due_context}"

                    # Determine due date text color
                    due_date_class = ""
                    if days_until_due is not None:
                        if days_until_due <= 0:
                            due_date_class = "due-date-urgent"
                        elif days_until_due <= 1:
                            due_date_class = "due-date-warning"

                description_preview = (task.description[:50] + "...") if task.description and len(
                    task.description) > 50 else (task.description or "No description")

                # Different styling for archived vs active tasks
                if task_view_mode == "Archived Tasks":
                    # Archived task card with muted styling and archive info
                    archived_date_str = format_date_display(
                        task.archived_at) if task.archived_at else "Unknown"
                    st.markdown(f"""
                    <div class="task-card archived-task {color_info['all_classes']}">
                        <div class="archive-indicator">📦 ARCHIVED</div>
                        <div class="task-content">
                            <strong>{task.title}{notes_indicator}</strong><br>
                            <small>{description_preview}</small>
                        </div>
                        <div class="task-metadata">
                            <div class="date-display created-date">📅 Created: {created_date_str}</div>
                            <div class="date-display archive-date">📦 Archived: {archived_date_str}</div>
                            <div class="date-display {due_date_class}">{due_date_display}</div>
                            <small>🏷️ {task.category} | 🔥 {task.priority.title()} | 📊 {color_info['status_description']}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Active task card with normal styling
                    st.markdown(f"""
                    <div class="task-card {color_info['all_classes']}">
                        <div class="task-content">
                            <strong>{task.title}{notes_indicator}</strong><br>
                            <small>{description_preview}</small>
                        </div>
                        <div class="task-metadata">
                            <div class="date-display created-date">📅 Created: {created_date_str}</div>
                            <div class="date-display {due_date_class}">{due_date_display}</div>
                            <small>🏷️ {task.category} | 🔥 {task.priority.title()} | 📊 {color_info['status_description']}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Task actions - different layouts for active vs archived tasks
                if task_view_mode == "Active Tasks":
                    # Active tasks: Edit, Notes, Status, Archive, Delete
                    col_edit, col_notes, col_move, col_archive, col_delete = st.columns(
                        5)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{task.id}", help="Edit task"):
                            st.session_state[f"edit_modal_{task.id}"] = True
                    with col_notes:
                        if st.button("📝", key=f"notes_{task.id}", help="Manage daily progress notes"):
                            st.session_state[f"show_notes_{task.id}"] = True
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
                                    user = RouteProtection.get_current_user()
                                    await update_task(task.id, status=new_status, updated_by=user.get('id') if user else None)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating task: {str(e)}")
                    with col_archive:
                        if st.button("📦", key=f"archive_{task.id}", help="Archive task"):
                            # Store archive data for the parent async context to handle
                            user = RouteProtection.get_current_user()
                            st.session_state['pending_task_archive'] = {
                                'task_id': task.id,
                                'archived_by': user.get('id') if user else None
                            }
                            # Debug message
                            st.success(
                                f"Archive button clicked for task {task.id}")
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{task.id}", help="Delete task permanently"):
                            st.session_state.show_delete_confirmation = True
                            st.session_state.task_to_delete = task
                            # Debug message
                            st.success(
                                f"Delete button clicked for task {task.id}")
                            st.rerun()
                else:
                    # Archived tasks: Edit, Notes, Revive, Delete (no status change)
                    col_edit, col_notes, col_revive, col_delete = st.columns(4)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{task.id}", help="Edit task"):
                            st.session_state[f"edit_modal_{task.id}"] = True
                    with col_notes:
                        if st.button("📝", key=f"notes_{task.id}", help="View progress notes"):
                            st.session_state[f"show_notes_{task.id}"] = True
                    with col_revive:
                        if st.button("🔄", key=f"revive_{task.id}", help="Revive task (move back to active)"):
                            # Store revive data for the parent async context to handle
                            st.session_state['pending_task_revive'] = task.id
                            # Debug message
                            st.success(
                                f"Revive button clicked for task {task.id}")
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{task.id}", help="Delete task permanently"):
                            st.session_state.show_delete_confirmation = True
                            st.session_state.task_to_delete = task
                            # Debug message
                            st.success(
                                f"Delete button clicked for task {task.id}")
                            st.rerun()

    # Handle pending task updates
    for task in tasks:
        if f'pending_task_update_{task.id}' in st.session_state:
            update_data = st.session_state[f'pending_task_update_{task.id}']
            try:
                with LoaderContext("Updating task...", "inline"):
                    await update_task(
                        update_data['task_id'],
                        title=update_data['title'],
                        description=update_data['description'],
                        status=update_data['status'],
                        priority=update_data['priority'],
                        category=update_data['category'],
                        due_date=update_data['due_date'],
                        updated_by=update_data.get('updated_by')
                    )
                    st.success("✅ Task updated successfully!")
                    del st.session_state[f'pending_task_update_{task.id}']
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating task: {str(e)}")
                del st.session_state[f'pending_task_update_{task.id}']

    # Show task modals for any tasks that have been clicked
    for task in tasks:
        if st.session_state.get(f"edit_modal_{task.id}", False):
            show_edit_task_modal(task)

        # Handle notes modal
        if st.session_state.get(f"show_notes_{task.id}", False):
            from app.ui.components.task_notes_modal import show_task_notes_modal
            show_task_notes_modal(task)
            # Don't automatically close the modal - let user close it manually


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
            <div class="task-content">
                <strong>System Details</strong>
            </div>
            <div class="task-metadata">
                <small>🔧 CPU Cores: {system_info['cpu_cores']}</small><br>
                <small>⚡ CPU Frequency: {system_info['cpu_frequency']}</small><br>
                <small>🧠 Total Memory: {system_info['total_memory']}</small><br>
                <small>💾 Total Disk: {system_info['total_disk']}</small><br>
                <small>⏱️ Uptime: {system_info['system_uptime']}</small><br>
                <small>🐍 Platform: {system_info['platform']}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)


async def render_archived_tasks(dashboard_manager):
    """Render the archived tasks interface"""
    st.markdown("### 📦 Archived Tasks")
    st.markdown(
        "View and manage tasks that have been archived. You can revive them back to active status or permanently delete them.")

    # Get archived tasks
    with LoaderContext("Loading archived tasks...", "inline"):
        archived_tasks = await dashboard_manager.get_archived_user_tasks()
        # Get notes counts for all archived tasks
        notes_counts = await dashboard_manager.get_task_notes_counts(archived_tasks)

    if not archived_tasks:
        st.info("📭 No archived tasks found. Tasks that are archived will appear here.")
        return

    st.markdown(f"**Found {len(archived_tasks)} archived tasks**")

    # Display archived tasks in a grid layout
    for i, task in enumerate(archived_tasks):
        # Create a container for each task
        with st.container():
            # Get color information (archived tasks will have muted colors)
            color_info = get_combined_task_color(
                task.due_date, task.status, task.priority)

            # Check if task has notes
            notes_count = notes_counts.get(task.id, 0)
            notes_indicator = f" 📝({notes_count})" if notes_count > 0 else ""

            # Format dates for display
            created_date_str = format_date_display(task.created_at)
            archived_date_str = format_date_display(
                task.archived_at) if task.archived_at else "Unknown"

            # Due date display
            if task.status == "completed":
                completion_date_str = get_completion_date_display(
                    task.status, task.updated_at)
                due_date_display = completion_date_str
                due_date_class = "completion-date"
            else:
                due_date_str = format_date_display(
                    task.due_date) if task.due_date else "No due date"
                days_until_due = get_days_until_due(task.due_date)
                due_context = ""
                if days_until_due is not None:
                    if days_until_due < 0:
                        due_context = f" (Was overdue by {abs(days_until_due)} day(s))"
                    elif days_until_due == 0:
                        due_context = " (Was due today)"
                    elif days_until_due == 1:
                        due_context = " (Was due tomorrow)"
                    elif days_until_due <= 7:
                        due_context = f" (Was due in {days_until_due} day(s))"

                due_date_display = f"⏰ Due: {due_date_str}{due_context}"
                due_date_class = ""

            description_preview = (task.description[:100] + "...") if task.description and len(
                task.description) > 100 else (task.description or "No description")

            # Archived task card with special styling
            st.markdown(f"""
            <div class="task-card archived-task {color_info['all_classes']}">
                <div class="archive-indicator">📦 ARCHIVED</div>
                <div class="task-content">
                    <strong>{task.title}{notes_indicator}</strong><br>
                    <small>{description_preview}</small>
                </div>
                <div class="task-metadata">
                    <div class="date-display created-date">📅 Created: {created_date_str}</div>
                    <div class="date-display archive-date">📦 Archived: {archived_date_str}</div>
                    <div class="date-display {due_date_class}">{due_date_display}</div>
                    <small>🏷️ {task.category} | 🔥 {task.priority.title()} | 📊 {color_info['status_description']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons for archived tasks
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if st.button("✏️", key=f"archived_edit_{task.id}", help="Edit task"):
                    st.session_state[f"edit_modal_{task.id}"] = True

            with col2:
                if st.button("📝", key=f"archived_notes_{task.id}", help="View progress notes"):
                    st.session_state[f"show_notes_{task.id}"] = True

            with col3:
                if st.button("🔄", key=f"archived_revive_{task.id}", help="Revive task (move back to active)"):
                    st.session_state['pending_task_revive'] = task.id
                    st.success(f"Revive button clicked for task {task.id}")
                    st.rerun()

            with col4:
                if st.button("🗑️", key=f"archived_delete_{task.id}", help="Delete task permanently"):
                    st.session_state.show_delete_confirmation = True
                    st.session_state.task_to_delete = task
                    st.success(f"Delete button clicked for task {task.id}")
                    st.rerun()

            with col5:
                # Show task status for reference
                status_colors = {
                    "todo": "🔵",
                    "inprogress": "🟣",
                    "pending": "🟠",
                    "completed": "🟢"
                }
                st.markdown(
                    f"{status_colors.get(task.status, '⚪')} {task.status.title()}")

            st.markdown("---")  # Separator between tasks

    # Handle task modals for archived tasks
    for task in archived_tasks:
        if st.session_state.get(f"edit_modal_{task.id}", False):
            show_edit_task_modal(task)

        # Handle notes modal for archived tasks
        if st.session_state.get(f"show_notes_{task.id}", False):
            from app.ui.components.task_notes_modal import show_task_notes_modal
            show_task_notes_modal(task)
            # Don't automatically close the modal - let user close it manually


def dashboard(go_to_page):
    """Main dashboard function"""
    apply_custom_css()

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📋 Kanban Board", "📊 Productivity Analytics", "🖥️ System Monitor", "📈 Task Analysis", "📦 Archive"])

    with tab1:
        asyncio.run(render_kanban_board(dashboard_manager))

    with tab2:
        asyncio.run(render_productivity_analytics(dashboard_manager))

    with tab3:
        asyncio.run(render_system_monitoring(dashboard_manager))

    with tab4:
        asyncio.run(render_task_analysis(dashboard_manager))

    with tab5:
        asyncio.run(render_archived_tasks(dashboard_manager))


if __name__ == "__main__":
    # For standalone testing
    dashboard()