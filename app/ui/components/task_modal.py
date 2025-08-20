import streamlit as st
import asyncio
from datetime import datetime
from app.core.interface.task_interface import update_task
from app.core.utils.task_color_utils import (
    get_combined_task_color, format_date_display, get_days_until_due, get_completion_date_display
)


def show_edit_task_modal(task):
    """Display edit task modal"""

    modal_key = f"edit_modal_{task.id}"

    if st.session_state.get(modal_key, False):
        @st.dialog(f"✏️ Edit Task: {task.title}", width="large")
        def edit_task_dialog():
            # Add close button at the top
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("❌ Close", key=f"close_edit_modal_{task.id}"):
                    st.session_state[modal_key] = False
                    st.rerun()
            # Get color information for the task
            color_info = get_combined_task_color(
                task.due_date, task.status, task.priority)

            # Display task information with colors
            created_date_str = format_date_display(task.created_at)

            # For completed tasks, show completion date instead of due date
            if task.status == "completed":
                completion_date_str = get_completion_date_display(
                    task.status, task.updated_at)
                due_date_display = completion_date_str if completion_date_str else "Completed"
            else:
                # For non-completed tasks, show due date with context
                due_date_str = format_date_display(
                    task.due_date) if task.due_date else "No due date"
                days_until_due = get_days_until_due(task.due_date)

                due_context = ""
                if days_until_due is not None:
                    if days_until_due < 0:
                        due_context = f" (Overdue by {abs(days_until_due)} day(s))"
                    elif days_until_due == 0:
                        due_context = " (Due today!)"
                    elif days_until_due == 1:
                        due_context = " (Due tomorrow)"

                due_date_display = f"Due: {due_date_str}{due_context}"

            st.markdown(f"""
            <div style="padding: 1rem; border-radius: 10px; margin-bottom: 1rem; 
                        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                        border-left: 4px solid #667eea;">
                <p style="margin: 0.5rem 0; color: #666;">📅 Created: {created_date_str}</p>
                <p style="margin: 0.5rem 0; color: #666;">⏰ {due_date_display}</p>
                <p style="margin: 0.5rem 0; color: #666;">🏷️ Category: {task.category} | 🔥 Priority: {task.priority.title()} | 📊 Status: {color_info['status_description']}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form(f"edit_task_form_{task.id}"):
                col1, col2 = st.columns(2)

                with col1:
                    new_title = st.text_input("Title", value=task.title)
                    new_priority = st.selectbox(
                        "Priority",
                        ["low", "medium", "high", "urgent"],
                        index=["low", "medium", "high",
                               "urgent"].index(task.priority)
                    )
                    new_status = st.selectbox(
                        "Status",
                        ["todo", "inprogress", "pending", "completed"],
                        index=["todo", "inprogress", "pending",
                               "completed"].index(task.status)
                    )

                with col2:
                    new_description = st.text_area(
                        "Description", value=task.description or "")
                    new_category = st.selectbox(
                        "Category",
                        ["in progress", "accomplishments"],
                        index=["in progress", "accomplishments"].index(
                            task.category)
                    )

                    # Handle due date with option to clear
                    current_due_date = None
                    if task.due_date:
                        if isinstance(task.due_date, str):
                            current_due_date = datetime.fromisoformat(
                                task.due_date.replace('Z', '+00:00')).date()
                        else:
                            current_due_date = task.due_date.date()

                    # Due date (optional - can be cleared)
                    new_due_date = st.date_input(
                        "Due Date",
                        value=current_due_date if current_due_date else None,
                        help="Select the due date (leave empty if not needed)",
                    )

                    # Convert empty to None
                    if not new_due_date:
                        new_due_date = None

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        # Store task update data for the parent async context to handle
                        st.session_state[f'pending_task_update_{task.id}'] = {
                            'task_id': task.id,
                            'title': new_title,
                            'description': new_description,
                            'status': new_status,
                            'priority': new_priority,
                            'category': new_category,
                            'due_date': datetime.combine(new_due_date, datetime.min.time()) if new_due_date else None
                        }
                        st.session_state[modal_key] = False
                        # Modal will close automatically when session state changes

                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state[modal_key] = False
                        # Modal will close automatically when session state changes

        # Show the dialog
        edit_task_dialog()
