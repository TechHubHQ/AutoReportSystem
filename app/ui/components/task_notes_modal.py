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
        # Add custom CSS for enhanced timeline styling
        st.markdown("""
        <style>
        .timeline-note-card {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .timeline-note-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }
        .note-content {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .note-header {
            background: linear-gradient(90deg, #007bff, #0056b3);
        }
        .word-count-badge {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 15px;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            color: #6c757d;
        }
        /* Ensure text wrapping in all containers */
        .stMarkdown, .stText {
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Add close button at the top
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("❌ Close", key=f"close_notes_modal_{task.id}"):
                st.session_state[f"show_notes_{task.id}"] = False
                st.rerun()
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
                                    # Don't close modal - just show success message
                                else:
                                    st.error(result['message'])

                    with col2:
                        if st.form_submit_button("🗑️ Clear"):
                            # Clear the form by rerunning without closing modal
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
                                # Don't close modal - just show success message
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
                                    # Don't close modal - just show success message
                                else:
                                    st.error(result['message'])

                    with col2:
                        if st.form_submit_button("🗑️ Clear"):
                            # Clear the form by rerunning without closing modal
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
                        st.markdown("---")

                        # Display notes in enhanced timeline format
                        for i, note in enumerate(notes):
                            # Create a card-like container for each note
                            note_number = len(notes) - i
                            
                            # Enhanced card styling with better text handling and hover effects
                            # Escape HTML characters in the content to prevent XSS
                            import html
                            escaped_content = html.escape(note.analysis_content)
                            
                            st.markdown(f"""
                            <div class="timeline-note-card" style="
                                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                border: 1px solid #dee2e6;
                                border-left: 4px solid #007bff;
                                border-radius: 12px;
                                padding: 1.5rem;
                                margin: 1rem 0;
                                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                                position: relative;
                                cursor: default;
                            ">
                                <!-- Date Header -->
                                <div style="
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    margin-bottom: 1rem;
                                    padding-bottom: 0.5rem;
                                    border-bottom: 2px solid #e9ecef;
                                ">
                                    <h4 style="
                                        margin: 0;
                                        color: #495057;
                                        font-size: 1.1rem;
                                        font-weight: 600;
                                    ">
                                        📅 {note.note_date.strftime('%B %d, %Y')}
                                    </h4>
                                    <span style="
                                        background: #007bff;
                                        color: white;
                                        padding: 0.25rem 0.75rem;
                                        border-radius: 20px;
                                        font-size: 0.8rem;
                                        font-weight: 500;
                                        box-shadow: 0 2px 4px rgba(0,123,255,0.3);
                                    ">
                                        Entry #{note_number}
                                    </span>
                                </div>
                                
                                <!-- Content Section -->
                                <div style="
                                    background: white;
                                    border-radius: 8px;
                                    padding: 1.25rem;
                                    border: 1px solid #e9ecef;
                                    box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
                                ">
                                    <h5 style="
                                        margin: 0 0 0.75rem 0;
                                        color: #6c757d;
                                        font-size: 0.9rem;
                                        font-weight: 600;
                                        text-transform: uppercase;
                                        letter-spacing: 0.5px;
                                        display: flex;
                                        align-items: center;
                                        gap: 0.5rem;
                                    ">
                                        📊 Daily Progress & Analysis
                                        <span class="word-count-badge">{len(note.analysis_content.split())} words</span>
                                    </h5>
                                    <div class="note-content" style="
                                        color: #212529;
                                        line-height: 1.7;
                                        font-size: 0.95rem;
                                        white-space: pre-wrap;
                                        word-wrap: break-word;
                                        max-width: 100%;
                                        overflow-wrap: break-word;
                                        hyphens: auto;
                                        text-align: justify;
                                    ">
                                        {escaped_content}
                                    </div>
                                </div>
                                
                                <!-- Timestamp footer -->
                                <div style="
                                    margin-top: 1rem;
                                    padding-top: 0.5rem;
                                    border-top: 1px solid #e9ecef;
                                    font-size: 0.8rem;
                                    color: #6c757d;
                                    text-align: right;
                                ">
                                    🕰️ Created: {note.note_date.strftime('%A, %B %d, %Y')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Action buttons with better spacing
                            col1, col2, col3, col4 = st.columns([1, 1, 2, 2])
                            with col1:
                                if st.button(f"✏️ Edit", key=f"edit_note_{note.id}", help="Edit this note", use_container_width=True):
                                    st.session_state[f"editing_note_{note.id}"] = True
                                    st.rerun()  # Refresh to show edit form

                            with col2:
                                if st.button(f"🗑️ Delete", key=f"delete_note_{note.id}", help="Delete this note", use_container_width=True):
                                    # Delete note directly from database
                                    with st.spinner("Deleting note..."):
                                        result = delete_progress_note_sync(note.id)
                                    
                                    if result['success']:
                                        st.success(result['message'])
                                        # Don't close modal - just show success message
                                    else:
                                        st.error(result['message'])
                            
                            with col3:
                                # Show note statistics
                                word_count = len(note.analysis_content.split())
                                char_count = len(note.analysis_content)
                                st.caption(f"📊 {char_count} characters")
                            
                            with col4:
                                # Show relative time
                                from datetime import datetime
                                days_ago = (datetime.now().date() - note.note_date).days
                                if days_ago == 0:
                                    time_text = "Today"
                                elif days_ago == 1:
                                    time_text = "Yesterday"
                                else:
                                    time_text = f"{days_ago} days ago"
                                st.caption(f"🕰️ {time_text}")

                            # Edit form (if editing)
                            if st.session_state.get(f"editing_note_{note.id}", False):
                                st.markdown("")
                                with st.expander("✏️ Edit Progress Note", expanded=True):
                                    with st.form(f"edit_note_form_{note.id}"):
                                        st.markdown("**Edit your progress note:**")
                                        edit_analysis = st.text_area(
                                            "Daily Progress & Analysis:", 
                                            value=note.analysis_content, 
                                            height=250,
                                            help="Update your progress note with new information"
                                        )

                                        col_save, col_cancel, col_preview = st.columns([1, 1, 2])
                                        with col_save:
                                            save_edit = st.form_submit_button(
                                                "💾 Save Changes", type="primary")
                                        with col_cancel:
                                            cancel_edit = st.form_submit_button(
                                                "❌ Cancel")
                                        with col_preview:
                                            if edit_analysis:
                                                st.caption(f"Preview: {len(edit_analysis.split())} words")

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
                                                # Don't close modal - just show success message
                                            else:
                                                st.error(result['message'])

                                        if cancel_edit:
                                            del st.session_state[f"editing_note_{note.id}"]
                                            st.rerun()  # Refresh to exit edit mode

                            # Add some spacing between notes
                            st.markdown("<br>", unsafe_allow_html=True)

                        # Enhanced Summary statistics with card styling
                        total_words = sum(len(note.analysis_content.split()) for note in notes)
                        avg_words = total_words // len(notes) if notes else 0
                        
                        st.markdown("---")
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                            border: 1px solid #90caf9;
                            border-radius: 10px;
                            padding: 1rem;
                            margin: 1rem 0;
                        ">
                            <h4 style="margin: 0 0 0.75rem 0; color: #1565c0;">📈 Timeline Summary</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem;">
                                <div><strong>📝 Total Entries:</strong> {len(notes)}</div>
                                <div><strong>📊 Total Words:</strong> {total_words:,}</div>
                                <div><strong>📏 Avg Words/Entry:</strong> {avg_words}</div>
                                <div><strong>📅 Date Range:</strong> {notes[-1].note_date.strftime('%b %d') if notes else 'N/A'} → {notes[0].note_date.strftime('%b %d, %Y') if notes else 'N/A'}</div>
                                <div><strong>🕒 Latest Entry:</strong> {notes[0].note_date.strftime('%B %d, %Y') if notes else 'N/A'}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

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