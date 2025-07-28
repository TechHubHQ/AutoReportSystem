"""
Kanban Board Component for Task Management

This module provides a comprehensive Kanban-style task management interface
with drag-and-drop functionality, task creation, editing, and status management.
"""

import streamlit as st
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from app.core.interface.task_interface import (
    get_tasks_by_status, create_task, update_task, delete_task, get_task_statistics
)
from app.core.utils.datetime_utils import (
    get_due_date_status, format_datetime_for_display, get_current_utc_datetime
)
from app.security.route_protection import RouteProtection


def kanban_board():
    """Main Kanban board component"""

    # Custom CSS for Kanban board
    st.markdown("""
    <style>
    .kanban-container {
        display: flex;
        gap: 1rem;
        padding: 1rem 0;
        min-height: 600px;
    }

    .kanban-column {
        flex: 1;
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        min-height: 500px;
        border: 2px solid #e9ecef;
    }

    .kanban-column.todo {
        border-color: #6c757d;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }

    .kanban-column.inprogress {
        border-color: #ffc107;
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    }

    .kanban-column.completed {
        border-color: #28a745;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    }

    .kanban-column.pending {
        border-color: #dc3545;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    }

    .kanban-header {
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        border-radius: 8px;
        color: white;
    }

    .kanban-header.todo {
        background: #6c757d;
    }

    .kanban-header.inprogress {
        background: #ffc107;
        color: #212529;
    }

    .kanban-header.completed {
        background: #28a745;
    }

    .kanban-header.pending {
        background: #dc3545;
    }

    .task-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #dee2e6;
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .task-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }

    .task-card.priority-low {
        border-left-color: #28a745;
    }

    .task-card.priority-medium {
        border-left-color: #ffc107;
    }

    .task-card.priority-high {
        border-left-color: #fd7e14;
    }

    .task-card.priority-urgent {
        border-left-color: #dc3545;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        50% { box-shadow: 0 4px 12px rgba(220,53,69,0.3); }
        100% { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    }

    .task-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #212529;
    }

    .task-description {
        color: #6c757d;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .task-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.8rem;
        color: #6c757d;
    }

    .priority-badge {
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
        text-transform: uppercase;
    }

    .priority-low {
        background: #d4edda;
        color: #155724;
    }

    .priority-medium {
        background: #fff3cd;
        color: #856404;
    }

    .priority-high {
        background: #ffeaa7;
        color: #d63031;
    }

    .priority-urgent {
        background: #f8d7da;
        color: #721c24;
    }

    .due-date {
        font-size: 0.7rem;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        background: #e9ecef;
        color: #495057;
    }

    .due-date.overdue {
        background: #f8d7da;
        color: #721c24;
    }

    .due-date.due-soon {
        background: #fff3cd;
        color: #856404;
    }

    .stats-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }

    .stat-card {
        flex: 1;
        min-width: 200px;
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }

    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #495057;
    }

    .stat-label {
        color: #6c757d;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Get current user
    user = RouteProtection.get_current_user()
    if not user:
        st.error("🔒 Authentication required")
        return

    user_id = user.get('id')

    # Header with statistics
    st.markdown("### 📋 Task Management - Kanban Board")

    # Load and display statistics
    try:
        stats = asyncio.run(get_task_statistics(user_id))

        # Statistics cards
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("📊 Total Tasks", stats['total'])
        with col2:
            st.metric("📝 To Do", stats['todo'])
        with col3:
            st.metric("🔄 In Progress", stats['inprogress'])
        with col4:
            st.metric("✅ Completed", stats['completed'])
        with col5:
            st.metric("⏳ Pending", stats['pending'])

        # Additional stats
        if stats['overdue'] > 0 or stats['urgent'] > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                if stats['overdue'] > 0:
                    st.metric(
                        "🚨 Overdue", stats['overdue'], delta=f"-{stats['overdue']}")
            with col2:
                if stats['urgent'] > 0:
                    st.metric("🔥 Urgent", stats['urgent'],
                              delta=f"+{stats['urgent']}")
            with col3:
                if stats['high_priority'] > 0:
                    st.metric("⚡ High Priority", stats['high_priority'])

    except Exception as e:
        st.error(f"Error loading statistics: {e}")
        stats = {'total': 0, 'todo': 0, 'inprogress': 0,
                 'completed': 0, 'pending': 0}

    st.markdown("---")

    # Task creation section
    with st.expander("➕ Create New Task", expanded=False):
        create_task_form(user_id)

    st.markdown("---")

    # Kanban columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kanban_column("todo", "📝 To Do", "#6c757d", user_id)

    with col2:
        render_kanban_column("inprogress", "🔄 In Progress", "#ffc107", user_id)

    with col3:
        render_kanban_column("completed", "✅ Completed", "#28a745", user_id)

    with col4:
        render_kanban_column("pending", "⏳ Pending", "#dc3545", user_id)


def create_task_form(user_id: int):
    """Form for creating new tasks"""

    with st.form("create_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input(
                "📝 Task Title*", placeholder="Enter task title...")
            priority = st.selectbox("⚡ Priority",
                                    options=["low", "medium",
                                             "high", "urgent"],
                                    index=1)
            category = st.selectbox("🏷️ Category",
                                   options=["in progress", "accomplishments"],
                                   index=0)

        with col2:
            description = st.text_area("📄 Description",
                                       placeholder="Describe the task...")
            status = st.selectbox("📊 Initial Status",
                                  options=["todo", "inprogress", "pending"],
                                  index=0)
            due_date = st.date_input("📅 Due Date (Optional)", value=None)

        submitted = st.form_submit_button(
            "🚀 Create Task", type="primary", use_container_width=True)

        if submitted:
            if title.strip():
                try:
                    # Convert due_date to datetime if provided
                    due_datetime = None
                    if due_date:
                        due_datetime = datetime.combine(
                            due_date, datetime.min.time()).replace(tzinfo=timezone.utc)

                    # Create the task
                    new_task = asyncio.run(create_task(
                        title=title.strip(),
                        description=description.strip(),
                        status=status,
                        priority=priority,
                        category=category.strip(),
                        due_date=due_datetime,
                        created_by=user_id
                    ))

                    st.success(f"✅ Task '{title}' created successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error creating task: {e}")
            else:
                st.error("⚠️ Task title is required!")


def render_kanban_column(status: str, title: str, color: str, user_id: int):
    """Render a single Kanban column"""

    # Column header
    st.markdown(f"""
    <div class="kanban-header {status}">
        {title}
    </div>
    """, unsafe_allow_html=True)

    try:
        # Load tasks for this status
        tasks = asyncio.run(get_tasks_by_status(status, user_id))

        if not tasks:
            st.markdown(f"""
            <div style="text-align: center; color: #6c757d; padding: 2rem; font-style: italic;">
                No tasks in {title.lower()}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Render each task
            for task in tasks:
                render_task_card(task, status)

    except Exception as e:
        st.error(f"Error loading {title.lower()}: {e}")


def render_task_card(task, current_status: str):
    """Render a single task card"""

    # Calculate due date status using utility function
    due_status = get_due_date_status(task.due_date, task.status)

    # Format due date
    due_date_str = ""
    if task.due_date:
        try:
            due_date_str = format_datetime_for_display(task.due_date, "%m/%d")
        except Exception:
            # Fallback if formatting fails
            due_date_str = "Invalid date"

    # Create unique key for this task
    task_key = f"task_{task.id}_{current_status}"

    # Task card container
    with st.container():
        # Task card HTML
        st.markdown(f"""
        <div class="task-card priority-{task.priority}">
            <div class="task-title">{task.title}</div>
            {f'<div class="task-description">{task.description}</div>' if task.description else ''}
            <div class="task-meta">
                <span class="priority-badge priority-{task.priority}">{task.priority}</span>
                {f'<span class="due-date {due_status}">📅 {due_date_str}</span>' if due_date_str else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Task actions
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✏️", key=f"edit_{task_key}", help="Edit task"):
                st.session_state[f"editing_task_{task.id}"] = True
                st.rerun()

        with col2:
            if st.button("🔄", key=f"status_{task_key}", help="Change status"):
                st.session_state[f"changing_status_{task.id}"] = True
                st.rerun()

        with col3:
            if st.button("📋", key=f"details_{task_key}", help="View details"):
                st.session_state[f"viewing_task_{task.id}"] = True
                st.rerun()

        with col4:
            if st.button("🗑️", key=f"delete_{task_key}", help="Delete task"):
                st.session_state[f"deleting_task_{task.id}"] = True
                st.rerun()

        # Handle task actions
        handle_task_actions(task)


def handle_task_actions(task):
    """Handle task action modals and forms"""

    # Edit task modal
    if st.session_state.get(f"editing_task_{task.id}", False):
        edit_task_modal(task)

    # Change status modal
    if st.session_state.get(f"changing_status_{task.id}", False):
        change_status_modal(task)

    # View details modal
    if st.session_state.get(f"viewing_task_{task.id}", False):
        view_task_details_modal(task)

    # Delete confirmation modal
    if st.session_state.get(f"deleting_task_{task.id}", False):
        delete_task_modal(task)


def edit_task_modal(task):
    """Modal for editing task details"""

    with st.expander(f"✏️ Edit Task: {task.title}", expanded=True):
        with st.form(f"edit_task_form_{task.id}"):
            col1, col2 = st.columns(2)

            with col1:
                new_title = st.text_input("📝 Title", value=task.title)
                new_priority = st.selectbox("⚡ Priority",
                                            options=["low", "medium",
                                                     "high", "urgent"],
                                            index=["low", "medium", "high", "urgent"].index(task.priority))
                new_category = st.selectbox(
                    "🏷️ Category", 
                    options=["in progress", "accomplishments"],
                    index=0 if task.category == "in progress" else 1)

            with col2:
                new_description = st.text_area(
                    "📄 Description", value=task.description or "")
                new_status = st.selectbox("📊 Status",
                                          options=["todo", "inprogress",
                                                   "completed", "pending"],
                                          index=["todo", "inprogress", "completed", "pending"].index(task.status))

                # Handle due date
                current_due_date = task.due_date.date() if task.due_date else None
                new_due_date = st.date_input(
                    "📅 Due Date", value=current_due_date)

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                    try:
                        # Convert due_date to datetime if provided
                        due_datetime = None
                        if new_due_date:
                            due_datetime = datetime.combine(
                                new_due_date, datetime.min.time()).replace(tzinfo=timezone.utc)

                        # Update the task
                        asyncio.run(update_task(
                            task_id=task.id,
                            title=new_title.strip(),
                            description=new_description.strip(),
                            status=new_status,
                            priority=new_priority,
                            category=new_category.strip(),
                            due_date=due_datetime
                        ))

                        st.success("✅ Task updated successfully!")
                        st.session_state[f"editing_task_{task.id}"] = False
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error updating task: {e}")

            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state[f"editing_task_{task.id}"] = False
                    st.rerun()


def change_status_modal(task):
    """Modal for quickly changing task status"""

    with st.expander(f"🔄 Change Status: {task.title}", expanded=True):
        st.write(f"**Current Status:** {task.status.title()}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📝 To Do", use_container_width=True,
                         disabled=(task.status == "todo")):
                update_task_status(task.id, "todo")

        with col2:
            if st.button("🔄 In Progress", use_container_width=True,
                         disabled=(task.status == "inprogress")):
                update_task_status(task.id, "inprogress")

        with col3:
            if st.button("✅ Completed", use_container_width=True,
                         disabled=(task.status == "completed")):
                update_task_status(task.id, "completed")

        with col4:
            if st.button("⏳ Pending", use_container_width=True,
                         disabled=(task.status == "pending")):
                update_task_status(task.id, "pending")

        if st.button("❌ Cancel", use_container_width=True):
            st.session_state[f"changing_status_{task.id}"] = False
            st.rerun()


def view_task_details_modal(task):
    """Modal for viewing detailed task information"""

    with st.expander(f"📋 Task Details: {task.title}", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**📝 Title:** {task.title}")
            st.markdown(f"**📊 Status:** {task.status.title()}")
            st.markdown(f"**⚡ Priority:** {task.priority.title()}")
            st.markdown(f"**🏷️ Category:** {task.category}")

        with col2:
            st.markdown(
                f"**📅 Created:** {format_datetime_for_display(task.created_at, '%Y-%m-%d %H:%M')}")
            st.markdown(
                f"**🔄 Updated:** {format_datetime_for_display(task.updated_at, '%Y-%m-%d %H:%M')}")
            st.markdown(
                f"**⏰ Due Date:** {format_datetime_for_display(task.due_date, '%Y-%m-%d')}")
            
            # Show due date status if applicable
            due_status = get_due_date_status(task.due_date, task.status)
            if due_status == "overdue":
                st.error("🚨 This task is overdue!")
            elif due_status == "due-soon":
                st.warning("⚠️ This task is due soon!")

        if task.description:
            st.markdown("**📄 Description:**")
            st.markdown(task.description)

        if st.button("❌ Close", use_container_width=True):
            st.session_state[f"viewing_task_{task.id}"] = False
            st.rerun()


def delete_task_modal(task):
    """Modal for confirming task deletion"""

    with st.expander(f"🗑️ Delete Task: {task.title}", expanded=True):
        st.warning(
            f"⚠️ Are you sure you want to delete the task **'{task.title}'**?")
        st.markdown("This action cannot be undone.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
                try:
                    asyncio.run(delete_task(task.id))
                    st.success("✅ Task deleted successfully!")
                    st.session_state[f"deleting_task_{task.id}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error deleting task: {e}")

        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state[f"deleting_task_{task.id}"] = False
                st.rerun()


def update_task_status(task_id: int, new_status: str):
    """Update task status and refresh the page"""
    try:
        asyncio.run(update_task(task_id=task_id, status=new_status))
        st.success(f"✅ Task status updated to {new_status.title()}!")

        # Clear the status change modal
        st.session_state[f"changing_status_{task_id}"] = False
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error updating task status: {e}")


# Quick action functions for better UX
def quick_create_task(title: str, status: str = "todo", user_id: int = None):
    """Quick task creation function"""
    try:
        asyncio.run(create_task(
            title=title,
            status=status,
            created_by=user_id
        ))
        return True
    except Exception:
        return False
