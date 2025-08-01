import streamlit as st
import asyncio
from datetime import datetime
from app.core.interface.task_interface import update_task


def show_edit_task_modal(task):
    """Display edit task modal"""

    modal_key = f"edit_modal_{task.id}"

    if st.session_state.get(modal_key, False):
        with st.container():
            st.markdown("### ✏️ Edit Task")

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

                    # Handle due date
                    current_due_date = None
                    if task.due_date:
                        if isinstance(task.due_date, str):
                            current_due_date = datetime.fromisoformat(
                                task.due_date.replace('Z', '+00:00')).date()
                        else:
                            current_due_date = task.due_date.date()

                    new_due_date = st.date_input(
                        "Due Date", value=current_due_date)

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        try:
                            asyncio.run(update_task(
                                task.id,
                                title=new_title,
                                description=new_description,
                                status=new_status,
                                priority=new_priority,
                                category=new_category,
                                due_date=datetime.combine(
                                    new_due_date, datetime.min.time()) if new_due_date else None
                            ))
                            st.success("✅ Task updated successfully!")
                            st.session_state[modal_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error updating task: {str(e)}")

                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state[modal_key] = False
                        st.rerun()
