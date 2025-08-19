import asyncio
import streamlit as st
from datetime import date
from app.security.route_protection import RouteProtection
from app.core.interface.task_notes_handler import (
    create_progress_note_sync, update_progress_note_sync, delete_progress_note_sync,
    create_or_update_issue_sync, create_or_update_resolution_sync, get_task_notes_data_sync
)


def show_task_notes_modal(task):
    """Display task notes modal with timeline view and note management"""

    modal_key = f"notes_modal_{task.id}"

    @st.dialog(f"📝 Task Notes: {task.title}", width="large")
    def notes_modal():
        try:
            # Get current user
            user = RouteProtection.get_current_user()
            if not user:
                st.error("Please log in to manage task notes.")
                return

            # Load task notes data directly (no session state dependency)
            notes_data = get_task_notes_data_sync(task.id)
            
            if not notes_data['success']:
                st.error(f"Error loading task notes: {notes_data['message']}")
                return
                
            progress_notes = notes_data['progress_notes']
            task_issue = notes_data['issue']
            task_resolution = notes_data['resolution']

            # Task information header
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #007bff, #0056b3); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <h3 style="margin: 0; color: white;">📋 {task.title}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Status: {task.status.title()} | Priority: {task.priority.title()} | Category: {task.category.title()}</p>
            </div>
            """, unsafe_allow_html=True)

            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(
                ["🔍 Issue", "📝 Daily Progress", "✅ Resolution", "📚 Timeline"])

            with tab1:
                st.markdown("### 🔍 Task Issue Description")
                st.markdown(
                    "*Document the main issue or problem this task is meant to address*")

                # Use the loaded issue data
                existing_issue = task_issue

                with st.form(f"issue_form_{task.id}"):
                    issue_content = st.text_area(
                        "What is the main issue or problem?",
                        value=existing_issue.issue_description if existing_issue else "",
                        height=200,
                        placeholder="Describe the main issue, problem, or objective this task is addressing. What needs to be solved or accomplished?",
                        help="Provide a clear description of the issue or objective for this task."
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Issue", type="primary"):
                            if not issue_content.strip():
                                st.error("❌ Issue description is required!")
                            else:
                                # Save issue directly to database
                                with st.spinner("Saving issue..."):
                                    result = create_or_update_issue_sync(
                                        task_id=task.id,
                                        issue_description=issue_content.strip(),
                                        created_by=user.get('id')
                                    )
                                
                                if result['success']:
                                    st.success(result['message'])
                                    st.rerun()  # Refresh to show updated data
                                else:
                                    st.error(result['message'])

                    with col2:
                        if st.form_submit_button("🗑️ Clear"):
                            st.rerun()

                # Show existing issue info
                if existing_issue:
                    st.markdown("---")
                    st.markdown("**📅 Current Issue:**")
                    st.info(existing_issue.issue_description)
                    if existing_issue.updated_at:
                        st.caption(
                            f"Last updated: {existing_issue.updated_at.strftime('%B %d, %Y at %I:%M %p')}")

            with tab2:
                st.markdown("### ➕ Add Daily Progress Note")

                with st.form(f"add_note_form_{task.id}"):
                    note_date_input = st.date_input(
                        "📅 Note Date",
                        value=date.today(),
                        help="Select the date for this progress entry"
                    )

                    st.markdown("#### 📊 Daily Progress & Analysis")
                    analysis_content = st.text_area(
                        "Document your daily progress, work done, challenges, and findings:",
                        height=200,
                        placeholder="What did you work on today? What progress was made? Any challenges encountered? Key findings or insights...",
                        help="Document your detailed work, progress, analysis, and any insights gained during the day."
                    )

                    submitted = st.form_submit_button(
                        "💾 Save Progress Note", type="primary")

                    if submitted:
                        if not analysis_content.strip():
                            st.error("❌ Progress content is required!")
                        else:
                            # Save progress note directly to database
                            with st.spinner("Saving progress note..."):
                                result = create_progress_note_sync(
                                    task_id=task.id,
                                    note_date=note_date_input,
                                    analysis_content=analysis_content.strip(),
                                    created_by=user.get('id')
                                )
                            
                            if result['success']:
                                st.success(result['message'])
                                st.rerun()  # Refresh to show updated data
                            else:
                                st.error(result['message'])

            with tab3:
                st.markdown("### ✅ Task Resolution Notes")
                st.markdown(
                    "*Document the final resolution when the task is completed*")

                # Use the loaded resolution data
                existing_resolution = task_resolution

                with st.form(f"resolution_form_{task.id}"):
                    resolution_content = st.text_area(
                        "How was the issue resolved?",
                        value=existing_resolution.resolution_notes if existing_resolution else "",
                        height=200,
                        placeholder="Describe how the issue was resolved, what solution was implemented, lessons learned, and final outcomes...",
                        help="Document the final resolution, solution, and any important outcomes or lessons learned."
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Resolution", type="primary"):
                            if not resolution_content.strip():
                                st.error(
                                    "❌ Resolution description is required!")
                            else:
                                # Save resolution directly to database
                                with st.spinner("Saving resolution..."):
                                    result = create_or_update_resolution_sync(
                                        task_id=task.id,
                                        resolution_notes=resolution_content.strip(),
                                        created_by=user.get('id')
                                    )
                                
                                if result['success']:
                                    st.success(result['message'])
                                    st.rerun()  # Refresh to show updated data
                                else:
                                    st.error(result['message'])

                    with col2:
                        if st.form_submit_button("🗑️ Clear"):
                            st.rerun()

                # Show existing resolution info
                if existing_resolution:
                    st.markdown("---")
                    st.markdown("**✅ Current Resolution:**")
                    st.success(existing_resolution.resolution_notes)
                    if existing_resolution.updated_at:
                        st.caption(
                            f"Last updated: {existing_resolution.updated_at.strftime('%B %d, %Y at %I:%M %p')}")

            with tab4:
                st.markdown("### 📚 Notes Timeline")

                try:
                    # Use the loaded progress notes data
                    notes = progress_notes

                    if not notes:
                        st.info(
                            "📝 No notes have been added for this task yet. Use the 'Add New Note' tab to create your first note.")
                    else:
                        st.markdown(f"**📊 Total Notes: {len(notes)}**")

                        # Display notes in timeline format
                        for i, note in enumerate(notes):
                            with st.container():
                                st.markdown(
                                    f"### 📅 {note.note_date.strftime('%B %d, %Y')} (Entry #{len(notes) - i})")

                                # Progress section
                                st.markdown("**📊 Daily Progress:**")
                                st.markdown(f"> {note.analysis_content}")

                                # Action buttons
                                col1, col2, col3 = st.columns([1, 1, 4])
                                with col1:
                                    if st.button(f"✏️ Edit", key=f"edit_note_{note.id}"):
                                        st.session_state[f"editing_note_{note.id}"] = True
                                        st.rerun()

                                with col2:
                                    if st.button(f"🗑️ Delete", key=f"delete_note_{note.id}"):
                                        # Delete note directly from database
                                        with st.spinner("Deleting note..."):
                                            result = delete_progress_note_sync(note.id)
                                        
                                        if result['success']:
                                            st.success(result['message'])
                                            st.rerun()  # Refresh to show updated data
                                        else:
                                            st.error(result['message'])

                                # Edit form (if editing)
                                if st.session_state.get(f"editing_note_{note.id}", False):
                                    with st.expander("✏️ Edit Progress Note", expanded=True):
                                        with st.form(f"edit_note_form_{note.id}"):
                                            edit_analysis = st.text_area(
                                                "Daily Progress & Analysis:", value=note.analysis_content, height=200)

                                            col_save, col_cancel = st.columns(
                                                2)
                                            with col_save:
                                                save_edit = st.form_submit_button(
                                                    "💾 Save Changes", type="primary")
                                            with col_cancel:
                                                cancel_edit = st.form_submit_button(
                                                    "❌ Cancel")

                                            if save_edit:
                                                # Update note directly in database
                                                with st.spinner("Updating note..."):
                                                    result = update_progress_note_sync(
                                                        note_id=note.id,
                                                        analysis_content=edit_analysis.strip()
                                                    )
                                                
                                                if result['success']:
                                                    st.success(result['message'])
                                                    del st.session_state[f"editing_note_{note.id}"]
                                                    st.rerun()  # Refresh to show updated data
                                                else:
                                                    st.error(result['message'])

                                            if cancel_edit:
                                                del st.session_state[f"editing_note_{note.id}"]
                                                st.rerun()

                                st.markdown("---")

                        # Summary statistics
                        st.markdown(f"""
                        **📈 Summary:**
                        - Total Progress Entries: {len(notes)}
                        - Date Range: {notes[-1].note_date.strftime('%B %d, %Y') if notes else 'N/A'} to {notes[0].note_date.strftime('%B %d, %Y') if notes else 'N/A'}
                        - Latest Entry: {notes[0].note_date.strftime('%B %d, %Y') if notes else 'N/A'}
                        """)

                except Exception as e:
                    st.error(f"Error loading notes: {e}")

        except Exception as e:
            st.error(f"Error in notes modal: {e}")

    # Show the modal
    notes_modal()


def show_task_notes_summary(task, max_notes: int = 3):
    """Show a compact summary of recent task notes"""
    try:
        from app.core.interface.task_notes_interface import get_recent_notes

        notes = asyncio.run(get_recent_notes(task.id, limit=max_notes))

        if notes:
            st.markdown("**📝 Recent Notes:**")
            for note in notes:
                with st.expander(f"📅 {note.note_date.strftime('%m/%d/%Y')}", expanded=False):
                    st.markdown(
                        f"**🔍 Issue:** {note.issue_description[:100]}{'...' if len(note.issue_description) > 100 else ''}")
                    if note.resolution_notes:
                        st.markdown(f"**✅ Status:** Resolved")
                    else:
                        st.markdown(f"**⏳ Status:** In Progress")
        else:
            st.markdown("*No notes available*")

    except Exception as e:
        st.error(f"Error loading notes summary: {e}")
