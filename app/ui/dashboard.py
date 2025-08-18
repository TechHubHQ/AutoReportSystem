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

    .priority-high { border-left-color: #f44336 !important; }
    .priority-urgent { border-left-color: #d32f2f !important; }
    .priority-medium { border-left-color: #ff9800 !important; }
    .priority-low { border-left-color: #4caf50 !important; }

    /* Status-based background colors - will be combined with due date colors diagonally */
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

    /* Due date-based colors (override status when urgent) - Enhanced with brighter colors */
    /* Overdue + Status combinations */
    .due-overdue.status-todo {
        background: linear-gradient(135deg, #FFCDD2 50%, #E3F2FD 50%) !important;
        border-left-color: #F44336 !important;
        box-shadow: -8px 8px 25px rgba(244, 67, 54, 0.4) !important;
    }
    .due-overdue.status-inprogress {
        background: linear-gradient(135deg, #FFCDD2 50%, #F3E5F5 50%) !important;
        border-left-color: #F44336 !important;
        box-shadow: -8px 8px 25px rgba(244, 67, 54, 0.4) !important;
    }
    .due-overdue.status-pending {
        background: linear-gradient(135deg, #FFCDD2 50%, #FFF3E0 50%) !important;
        border-left-color: #F44336 !important;
        box-shadow: -8px 8px 25px rgba(244, 67, 54, 0.4) !important;
    }
    /* Due today + Status combinations */
    .due-today.status-todo {
        background: linear-gradient(135deg, #FFAB91 50%, #E3F2FD 50%) !important;
        border-left-color: #FF5722 !important;
        box-shadow: -8px 8px 25px rgba(255, 87, 34, 0.35) !important;
    }
    .due-today.status-inprogress {
        background: linear-gradient(135deg, #FFAB91 50%, #F3E5F5 50%) !important;
        border-left-color: #FF5722 !important;
        box-shadow: -8px 8px 25px rgba(255, 87, 34, 0.35) !important;
    }
    .due-today.status-pending {
        background: linear-gradient(135deg, #FFAB91 50%, #FFF3E0 50%) !important;
        border-left-color: #FF5722 !important;
        box-shadow: -8px 8px 25px rgba(255, 87, 34, 0.35) !important;
    }
    /* Due tomorrow + Status combinations */
    .due-tomorrow.status-todo {
        background: linear-gradient(135deg, #FFCC80 50%, #E3F2FD 50%) !important;
        border-left-color: #FF9800 !important;
        box-shadow: -8px 8px 25px rgba(255, 152, 0, 0.3) !important;
    }
    .due-tomorrow.status-inprogress {
        background: linear-gradient(135deg, #FFCC80 50%, #F3E5F5 50%) !important;
        border-left-color: #FF9800 !important;
        box-shadow: -8px 8px 25px rgba(255, 152, 0, 0.3) !important;
    }
    .due-tomorrow.status-pending {
        background: linear-gradient(135deg, #FFCC80 50%, #FFF3E0 50%) !important;
        border-left-color: #FF9800 !important;
        box-shadow: -8px 8px 25px rgba(255, 152, 0, 0.3) !important;
    }
    /* Due soon/later + Status combinations */
    .due-soon.status-todo, .due-later.status-todo {
        # Load detailed analysis data for all filtered tasks
        from app.core.interface.task_notes_interface import (
            get_task_issue, get_task_resolution, get_task_progress_notes
        )
        
        analysis_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, task in enumerate(filtered_tasks):
            status_text.text(f"Loading analysis for task {i+1}/{len(filtered_tasks)}: {task.title}")
            progress_bar.progress((i + 1) / len(filtered_tasks))
            
            # Get issue, resolution, and progress notes
            task_issue = await get_task_issue(task.id)
            task_resolution = await get_task_resolution(task.id)
            progress_notes = await get_task_progress_notes(task.id)
            
            # Create a record for each progress note
            if progress_notes:
                for note in progress_notes:
                    analysis_data.append({
                        'ID': task.id,
                        'Created At': task.created_at.strftime('%Y-%m-%d') if task.created_at else 'N/A',
                        'Title': task.title,
                        'Issue': task_issue.issue_description if task_issue else 'No issue documented',
                        'Notes Date': note.note_date.strftime('%Y-%m-%d'),
                        'Analysis': note.analysis_content,
                        'Resolution Notes': task_resolution.resolution_notes if task_resolution else 'No resolution documented',
                        'Task Object': task  # Keep for reference
                    })
            else:
                # If no progress notes, still show the task with empty analysis
                analysis_data.append({
                    'ID': task.id,
                    'Created At': task.created_at.strftime('%Y-%m-%d') if task.created_at else 'N/A',
                    'Title': task.title,
                    'Issue': task_issue.issue_description if task_issue else 'No issue documented',
                    'Notes Date': 'No notes',
                    'Analysis': 'No progress notes',
                    'Resolution Notes': task_resolution.resolution_notes if task_resolution else 'No resolution documented',
                    'Task Object': task  # Keep for reference
                })
        background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%) !important;
        border-left-color: #4CAF50 !important;
        box-shadow: -6px 6px 20px rgba(76, 175, 80, 0.3) !important;
    }

    /* Date display styling */
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

    /* Delete button styling */
    .stButton > button[title="Delete task"],
    .stButton > button[title="Delete archived task"] {
        background-color: #ff4444 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button[title="Delete task"]:hover,
    .stButton > button[title="Delete archived task"]:hover {
        background-color: #cc0000 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(255, 68, 68, 0.3) !important;
    }

    /* Confirmation dialog styling */
    .stDialog {
        border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)


async def render_kanban_board(dashboard_manager):
    """Render the Kanban board interface"""
    st.markdown("### 📋 Kanban Board")

    # Add toggle for current month vs all tasks
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        view_mode = st.radio(
            "View Mode:",
            ["Current Month", "All Tasks"],
            horizontal=True,
            help="Current Month shows only tasks created this month. All Tasks shows everything."
        )

    # Get tasks based on view mode
    with LoaderContext("Loading tasks...", "inline"):
        if view_mode == "Current Month":
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

    # Color system information panel
    if st.session_state.get("show_color_guide", False):
        @st.dialog("🎨 Task Color System Guide", width="large")
        def color_guide_dialog():
            st.markdown("""
            ### Diagonal Split Color System
            Each task card uses a **diagonal split** showing two types of information:

            **Left Side = Due Date Urgency:**
            - 🔴 **Light Red**: Overdue tasks (need immediate attention)
            - 🟠 **Light Orange**: Due today (urgent)
            - 🟡 **Light Amber**: Due tomorrow (prepare for action)
            - 🟢 **Light Green**: Due in future (on track)

            **Right Side = Task Status:**
            - 🔵 **Light Blue**: To Do (ready to start)
            - 🟣 **Light Purple**: In Progress (actively working)
            - 🟠 **Light Orange**: On Hold (blocked/waiting) - *dashed border*
            - 🟢 **Light Green**: Completed (finished) - *always full green*

            **Special Cases:**
            - **No Due Date**: Shows only status color (full background)
            - **Completed Tasks**: Always light green regardless of due date
            - **Enhanced Shadows**: Urgent tasks have stronger shadows

            **Example:** A task due tomorrow that's in progress shows amber→purple diagonal split.
            """)

            # Color examples
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #ffcdd2 50%, #e3f2fd 50%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 4px solid #e57373; 
                           box-shadow: 0 4px 8px rgba(244, 67, 54, 0.2); margin: 0.5rem 0;">
                    <small><strong>Overdue + To Do</strong><br>Red → Blue</small>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #ffcc80 50%, #f3e5f5 50%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 4px solid #ffb74d; 
                           box-shadow: 0 4px 8px rgba(255, 152, 0, 0.15); margin: 0.5rem 0;">
                    <small><strong>Due Tomorrow + In Progress</strong><br>Amber → Purple</small>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #c8e6c9 50%, #fff3e0 50%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 4px dashed #ffa726; 
                           box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin: 0.5rem 0;">
                    <small><strong>Future + On Hold</strong><br>Green → Orange (dashed)</small>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); 
                           padding: 0.5rem; border-radius: 8px; border-left: 4px solid #66bb6a; 
                           box-shadow: 0 4px 8px rgba(76, 175, 80, 0.15); margin: 0.5rem 0;">
                    <small><strong>Completed</strong><br>Always Light Green</small>
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
                due_date = st.date_input("Due Date")

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

                st.markdown(f"""
                <div class="task-card {color_info['all_classes']}">
                    <strong>{task.title}{notes_indicator}</strong><br>
                    <small>{description_preview}</small><br>
                    <div class="date-display created-date">📅 Created: {created_date_str}</div>
                    <div class="date-display {due_date_class}">{due_date_display}</div>
                    <small>🏷️ {task.category} | 🔥 {task.priority.title()} | 📊 {color_info['status_description']}</small>
                </div>
                """, unsafe_allow_html=True)

                # Task actions
                col_edit, col_notes, col_move, col_delete = st.columns(4)
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
                                old_status = task.status
                                old_category = task.category

                                # Update the task
                                updated_task = await update_task(task.id, status=new_status, updated_by=user.get('id') if user else None)

                                # Check if category was automatically changed
                                if updated_task and updated_task.category != old_category:
                                    st.success(
                                        f"✅ Task status updated to '{new_status}' and category automatically changed from '{old_category}' to '{updated_task.category}'!")
                                else:
                                    st.success(
                                        f"✅ Task status updated to '{new_status}'!")

                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating task: {str(e)}")
                with col_delete:
                    if st.button("🗑️", key=f"delete_current_{task.id}", help="Delete task"):
                        st.session_state[f"pending_delete_current_{task.id}"] = True

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
                        due_date=update_data['due_date']
                    )
                    st.success("✅ Task updated successfully!")
                    del st.session_state[f'pending_task_update_{task.id}']
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating task: {str(e)}")
                del st.session_state[f'pending_task_update_{task.id}']

    # Removed confirmation dialog - tasks are deleted immediately when delete button is clicked

    # Handle pending task deletions
    for task in tasks:
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

    # Show task modals for any tasks that have been clicked
    for task in tasks:
        if st.session_state.get(f"edit_modal_{task.id}", False):
            show_edit_task_modal(task)

        # Handle notes modal
        if st.session_state.get(f"show_notes_{task.id}", False):
            # Load notes, issue, and resolution for this task
            from app.core.interface.task_notes_interface import get_task_issue, get_task_resolution

            task_notes = await dashboard_manager.get_task_notes_for_modal(task.id)
            task_issue = await get_task_issue(task.id)
            task_resolution = await get_task_resolution(task.id)

            st.session_state[f'task_notes_{task.id}'] = task_notes
            st.session_state[f'task_issue_{task.id}'] = task_issue
            st.session_state[f'task_resolution_{task.id}'] = task_resolution

            # Handle pending operations
            await dashboard_manager.handle_notes_operations(task.id)

            from app.ui.components.task_notes_modal import show_task_notes_modal
            show_task_notes_modal(task)
            st.session_state[f"show_notes_{task.id}"] = False


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


async def render_archived_tasks(dashboard_manager):
    """Render archived tasks (older than current month)"""
    st.markdown("### 📦 Archived Tasks")
    st.markdown("*Tasks created before the current month*")

    # Get archived tasks with loader
    with LoaderContext("Loading archived tasks...", "inline"):
        archived_tasks = await dashboard_manager.get_archived_user_tasks()

        # Get notes counts for all archived tasks
        archived_notes_counts = await dashboard_manager.get_task_notes_counts(archived_tasks)

    if not archived_tasks:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 2rem; 
                   background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                   border-radius: 20px; margin: 2rem 0; border: 2px dashed #dee2e6;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📦</div>
            <h3 style="color: #666; margin-bottom: 1rem;">No Archived Tasks</h3>
            <p style="color: #888; margin-bottom: 2rem; font-size: 1.1rem;">
                Tasks created before this month will appear here.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Show archived task statistics
    col1, col2, col3, col4 = st.columns(4)

    archived_stats = {
        'total': len(archived_tasks),
        'completed': len([t for t in archived_tasks if t.status == 'completed']),
        'inprogress': len([t for t in archived_tasks if t.status == 'inprogress']),
        'pending': len([t for t in archived_tasks if t.status == 'pending'])
    }

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">📋 {archived_stats['total']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Total Archived</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #6bcf7f; margin: 0;">✅ {archived_stats['completed']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Completed</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4fc3f7; margin: 0;">🔄 {archived_stats['inprogress']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">In Progress</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #ff9800; margin: 0;">⏳ {archived_stats['pending']}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Pending</p>
        </div>
        """, unsafe_allow_html=True)

    # Archived Kanban columns
    st.markdown("#### 📋 Archived Kanban Board")
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
            status_tasks = [
                task for task in archived_tasks if task.status == status]

            for task in status_tasks:
                # Get color information based on due date, status, and priority
                color_info = get_combined_task_color(
                    task.due_date, task.status, task.priority)

                # Check if task has notes
                notes_count = archived_notes_counts.get(task.id, 0)
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

                st.markdown(f"""
                <div class="task-card {color_info['all_classes']}" style="opacity: 0.8;">
                    <strong>{task.title}{notes_indicator}</strong><br>
                    <small>{description_preview}</small><br>
                    <div class="date-display created-date">📅 Created: {created_date_str}</div>
                    <div class="date-display {due_date_class}">{due_date_display}</div>
                    <small>🏷️ {task.category} | 🔥 {task.priority.title()} | 📊 {color_info['status_description']}</small>
                </div>
                """, unsafe_allow_html=True)

                # Actions for archived tasks
                col_edit, col_notes, col_delete = st.columns(3)
                with col_edit:
                    if st.button("✏️ Edit", key=f"edit_archived_{task.id}", help="Edit archived task"):
                        st.session_state[f"edit_modal_{task.id}"] = True
                with col_notes:
                    if st.button("📝 Notes", key=f"notes_archived_{task.id}", help="View progress notes"):
                        st.session_state[f"show_notes_{task.id}"] = True
                with col_delete:
                    if st.button("🗑️ Delete", key=f"delete_archived_{task.id}", help="Delete archived task"):
                        st.session_state[f"pending_delete_archived_{task.id}"] = True

    # Handle pending task updates for archived tasks
    for task in archived_tasks:
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
                        due_date=update_data['due_date']
                    )
                    st.success("✅ Task updated successfully!")
                    del st.session_state[f'pending_task_update_{task.id}']
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating task: {str(e)}")
                del st.session_state[f'pending_task_update_{task.id}']

    # Removed confirmation dialog - archived tasks are deleted immediately when delete button is clicked

    # Handle pending archived task deletions
    for task in archived_tasks:
        if st.session_state.get(f"pending_delete_archived_{task.id}", False):
            try:
                with LoaderContext("Deleting archived task...", "inline"):
                    await delete_task(task.id)
                    st.success(
                        f"✅ Archived task '{task.title}' deleted successfully!")
                    del st.session_state[f"pending_delete_archived_{task.id}"]
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting archived task: {str(e)}")
                del st.session_state[f"pending_delete_archived_{task.id}"]

    # Show task modals for any archived tasks that have been clicked
    for task in archived_tasks:
        if st.session_state.get(f"edit_modal_{task.id}", False):
            show_edit_task_modal(task)

        # Handle notes modal for archived tasks
        if st.session_state.get(f"show_notes_{task.id}", False):
            # Load notes, issue, and resolution for this task
            from app.core.interface.task_notes_interface import get_task_issue, get_task_resolution

            task_notes = await dashboard_manager.get_task_notes_for_modal(task.id)
            task_issue = await get_task_issue(task.id)
            task_resolution = await get_task_resolution(task.id)

            st.session_state[f'task_notes_{task.id}'] = task_notes
            st.session_state[f'task_issue_{task.id}'] = task_issue
            st.session_state[f'task_resolution_{task.id}'] = task_resolution

            # Handle pending operations
            await dashboard_manager.handle_notes_operations(task.id)

            from app.ui.components.task_notes_modal import show_task_notes_modal
            show_task_notes_modal(task)
            st.session_state[f"show_notes_{task.id}"] = False


# Removed corrupted function - now imported from dashboard_task_analysis.py


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
