import asyncio
import streamlit as st
from datetime import date
from app.security.route_protection import RouteProtection
from app.core.interface.task_notes_handler import (
    create_progress_note_sync, update_progress_note_sync, delete_progress_note_sync,
    create_or_update_issue_sync, create_or_update_resolution_sync, get_task_notes_data_sync
)
import html
import re


def show_task_notes_modal(task):
    """Display task notes modal with timeline view and note management"""

    modal_key = f"notes_modal_{task.id}"

    @st.dialog(f"📝 Task Notes: {task.title}", width="large")
    def notes_modal():
        # Add comprehensive CSS for proper text handling
        st.markdown("""
        <style>
        /* Global text wrapping and container styles */
        .main-content-wrapper {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: hidden !important;
        }
        
        /* Timeline card styling */
        .timeline-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            border-left: 4px solid #007bff;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            overflow: hidden;
        }
        
        .timeline-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }
        
        /* Header styling */
        .card-header {
            padding: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            border-bottom: 2px solid #e9ecef;
        }
        
        .date-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #495057;
            margin: 0;
            flex: 1;
            min-width: 200px;
        }
        
        .entry-badge {
            background: #007bff;
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0,123,255,0.3);
            white-space: nowrap;
        }
        
        /* Content section styling */
        .content-section {
            background: white;
            border-top: 1px solid #e9ecef;
        }
        
        .section-header {
            padding: 1rem 1.5rem 0.5rem 1.5rem;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        
        .section-title {
            margin: 0;
            font-size: 0.9rem;
            font-weight: 600;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .word-count {
            background: #e9ecef;
            color: #6c757d;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        /* Text content styling - CRITICAL FOR WRAPPING */
        .note-text {
            padding: 1.5rem;
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            font-size: 0.95rem;
            line-height: 1.6;
            color: #2c3e50;
            
            /* Essential wrapping properties */
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            word-break: break-word !important;
            hyphens: auto;
            
            /* Container constraints */
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            overflow-x: hidden !important;
            box-sizing: border-box !important;
            
            /* Prevent code-like formatting issues */
            font-family: inherit !important;
        }
        
        /* Handle code blocks and technical content */
        .note-text code {
            background: #f1f3f4;
            padding: 0.1rem 0.3rem;
            border-radius: 3px;
            font-size: 0.9em;
            word-break: break-all;
        }
        
        /* Footer styling */
        .card-footer {
            padding: 1rem 1.5rem;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-top: 1px solid #e9ecef;
            font-size: 0.8rem;
            color: #6c757d;
            text-align: right;
        }
        
        /* Action buttons container */
        .action-buttons {
            padding: 0 1.5rem 1.5rem 1.5rem;
            background: white;
        }
        
        /* Statistics container */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 0.75rem;
            margin: 0.5rem 0;
        }
        
        .stat-item {
            background: rgba(255,255,255,0.8);
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            border: 1px solid rgba(144,202,249,0.3);
            font-size: 0.9rem;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .card-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }
            
            .date-title {
                min-width: auto;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """, unsafe_allow_html=True)

        # Close button
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

            # Load task notes data
            notes_data = get_task_notes_data_sync(task.id)

            if not notes_data['success']:
                st.error(f"Error loading task notes: {notes_data['message']}")
                return

            progress_notes = notes_data['progress_notes']
            task_issue = notes_data['issue']
            task_resolution = notes_data['resolution']

            # Task information header
            st.markdown(f"""
            <div style="
                background: linear-gradient(90deg, #007bff, #0056b3); 
                color: white; 
                padding: 1.5rem; 
                border-radius: 8px; 
                margin-bottom: 1.5rem;
            ">
                <h3 style="margin: 0; color: white; font-size: 1.3rem;">📋 {html.escape(task.title)}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.95rem;">
                    Status: {task.status.title()} | Priority: {task.priority.title()} | Category: {task.category.title()}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(
                ["🔍 Issue", "📝 Daily Progress", "✅ Resolution", "📚 Timeline"])

            with tab1:
                st.markdown("### 🔍 Task Issue Description")
                st.markdown(
                    "*Document the main issue or problem this task is meant to address*")

                existing_issue = task_issue

                with st.form(f"issue_form_{task.id}"):
                    issue_content = st.text_area(
                        "What is the main issue or problem?",
                        value=existing_issue.issue_description if existing_issue else "",
                        height=200,
                        placeholder="Describe the main issue, problem, or objective this task is addressing...",
                        help="Provide a clear description of the issue or objective for this task."
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Issue", type="primary"):
                            if not issue_content.strip():
                                st.error("❌ Issue description is required!")
                            else:
                                with st.spinner("Saving issue..."):
                                    result = create_or_update_issue_sync(
                                        task_id=task.id,
                                        issue_description=issue_content.strip(),
                                        created_by=user.get('id')
                                    )
                                if result['success']:
                                    st.success(result['message'])
                                else:
                                    st.error(result['message'])

                    with col2:
                        if st.form_submit_button("🗑️ Clear"):
                            st.rerun()

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
                        placeholder="What did you work on today? What progress was made? Any challenges encountered?...",
                        help="Document your detailed work, progress, analysis, and any insights gained."
                    )

                    submitted = st.form_submit_button(
                        "💾 Save Progress Note", type="primary")

                    if submitted:
                        if not analysis_content.strip():
                            st.error("❌ Progress content is required!")
                        else:
                            with st.spinner("Saving progress note..."):
                                result = create_progress_note_sync(
                                    task_id=task.id,
                                    note_date=note_date_input,
                                    analysis_content=analysis_content.strip(),
                                    created_by=user.get('id')
                                )
                            if result['success']:
                                st.success(result['message'])
                            else:
                                st.error(result['message'])

            with tab3:
                st.markdown("### ✅ Task Resolution Notes")
                st.markdown(
                    "*Document the final resolution when the task is completed*")

                existing_resolution = task_resolution

                with st.form(f"resolution_form_{task.id}"):
                    resolution_content = st.text_area(
                        "How was the issue resolved?",
                        value=existing_resolution.resolution_notes if existing_resolution else "",
                        height=200,
                        placeholder="Describe how the issue was resolved, what solution was implemented...",
                        help="Document the final resolution, solution, and important outcomes."
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Resolution", type="primary"):
                            if not resolution_content.strip():
                                st.error(
                                    "❌ Resolution description is required!")
                            else:
                                with st.spinner("Saving resolution..."):
                                    result = create_or_update_resolution_sync(
                                        task_id=task.id,
                                        resolution_notes=resolution_content.strip(),
                                        created_by=user.get('id')
                                    )
                                if result['success']:
                                    st.success(result['message'])
                                else:
                                    st.error(result['message'])

                    with col2:
                        if st.form_submit_button("🗑️ Clear"):
                            st.rerun()

                if existing_resolution:
                    st.markdown("---")
                    st.markdown("**✅ Current Resolution:**")
                    st.success(existing_resolution.resolution_notes)
                    if existing_resolution.updated_at:
                        st.caption(
                            f"Last updated: {existing_resolution.updated_at.strftime('%B %d, %Y at %I:%M %p')}")

            with tab4:
                st.markdown("### 📚 Notes Timeline")

                # Use custom wrapper for timeline content
                st.markdown('<div class="main-content-wrapper">',
                            unsafe_allow_html=True)

                try:
                    notes = progress_notes

                    if not notes:
                        st.info(
                            "📝 No notes have been added for this task yet. Use the 'Daily Progress' tab to create your first note.")
                    else:
                        st.markdown(f"**📊 Total Notes: {len(notes)}**")
                        st.markdown("---")

                        # Display notes with completely redesigned layout
                        for i, note in enumerate(notes):
                            note_number = len(notes) - i
                            word_count = len(note.analysis_content.split())
                            char_count = len(note.analysis_content)

                            # Clean and escape the content properly
                            escaped_content = html.escape(
                                note.analysis_content)

                            # Create the complete timeline card
                            st.markdown(f"""
                            <div class="timeline-card">
                                <!-- Card Header -->
                                <div class="card-header">
                                    <h4 class="date-title">📅 {note.note_date.strftime('%B %d, %Y')}</h4>
                                    <span class="entry-badge">Entry #{note_number}</span>
                                </div>
                                
                                <!-- Content Section -->
                                <div class="content-section">
                                    <div class="section-header">
                                        <h5 class="section-title">
                                            📊 Daily Progress & Analysis
                                            <span class="word-count">{word_count} words</span>
                                        </h5>
                                    </div>
                                    
                                    <div class="note-text">{escaped_content}</div>
                                </div>
                                
                                <!-- Card Footer -->
                                <div class="card-footer">
                                    🕰️ Created: {note.note_date.strftime('%A, %B %d, %Y')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Action buttons using Streamlit columns
                            st.markdown('<div class="action-buttons">',
                                        unsafe_allow_html=True)
                            col1, col2, col3, col4 = st.columns([1, 1, 2, 2])

                            with col1:
                                if st.button("✏️ Edit", key=f"edit_note_{note.id}", help="Edit this note", use_container_width=True):
                                    st.session_state[f"editing_note_{note.id}"] = True
                                    st.rerun()

                            with col2:
                                if st.button("🗑️ Delete", key=f"delete_note_{note.id}", help="Delete this note", use_container_width=True):
                                    with st.spinner("Deleting note..."):
                                        result = delete_progress_note_sync(
                                            note.id)
                                    if result['success']:
                                        st.success(result['message'])
                                    else:
                                        st.error(result['message'])

                            with col3:
                                st.caption(f"📊 {char_count} characters")

                            with col4:
                                from datetime import datetime
                                days_ago = (datetime.now().date() -
                                            note.note_date).days
                                if days_ago == 0:
                                    time_text = "Today"
                                elif days_ago == 1:
                                    time_text = "Yesterday"
                                else:
                                    time_text = f"{days_ago} days ago"
                                st.caption(f"🕰️ {time_text}")

                            st.markdown('</div>', unsafe_allow_html=True)

                            # Edit form
                            if st.session_state.get(f"editing_note_{note.id}", False):
                                with st.expander("✏️ Edit Progress Note", expanded=True):
                                    with st.form(f"edit_note_form_{note.id}"):
                                        edit_analysis = st.text_area(
                                            "Daily Progress & Analysis:",
                                            value=note.analysis_content,
                                            height=250,
                                            help="Update your progress note"
                                        )

                                        col_save, col_cancel, col_preview = st.columns([
                                                                                       1, 1, 2])
                                        with col_save:
                                            save_edit = st.form_submit_button(
                                                "💾 Save Changes", type="primary")
                                        with col_cancel:
                                            cancel_edit = st.form_submit_button(
                                                "❌ Cancel")
                                        with col_preview:
                                            if edit_analysis:
                                                st.caption(
                                                    f"Preview: {len(edit_analysis.split())} words")

                                        if save_edit:
                                            with st.spinner("Updating note..."):
                                                result = update_progress_note_sync(
                                                    note_id=note.id,
                                                    analysis_content=edit_analysis.strip()
                                                )
                                            if result['success']:
                                                st.success(result['message'])
                                                del st.session_state[f"editing_note_{note.id}"]
                                            else:
                                                st.error(result['message'])

                                        if cancel_edit:
                                            del st.session_state[f"editing_note_{note.id}"]
                                            st.rerun()

                        # Timeline Summary
                        total_words = sum(
                            len(note.analysis_content.split()) for note in notes)
                        avg_words = total_words // len(notes) if notes else 0

                        st.markdown("---")
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                            border: 1px solid #90caf9;
                            border-radius: 12px;
                            padding: 1.5rem;
                            margin: 1.5rem 0;
                        ">
                            <h4 style="margin: 0 0 1rem 0; color: #1565c0; font-size: 1.1rem;">📈 Timeline Summary</h4>
                            <div class="stats-grid">
                                <div class="stat-item"><strong>📝 Total Entries:</strong> {len(notes)}</div>
                                <div class="stat-item"><strong>📊 Total Words:</strong> {total_words:,}</div>
                                <div class="stat-item"><strong>📏 Avg Words/Entry:</strong> {avg_words}</div>
                                <div class="stat-item"><strong>📅 Date Range:</strong> {notes[-1].note_date.strftime('%b %d') if notes else 'N/A'} → {notes[0].note_date.strftime('%b %d, %Y') if notes else 'N/A'}</div>
                                <div class="stat-item"><strong>🕒 Latest Entry:</strong> {notes[0].note_date.strftime('%B %d, %Y') if notes else 'N/A'}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error loading notes: {e}")

                st.markdown('</div>', unsafe_allow_html=True)

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
                    # Display content properly wrapped
                    st.text_area(
                        "Note Content",
                        value=note.analysis_content[:200] + (
                            "..." if len(note.analysis_content) > 200 else ""),
                        height=100,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    if hasattr(note, 'resolution_notes') and note.resolution_notes:
                        st.markdown("**✅ Status:** Resolved")
                    else:
                        st.markdown("**⏳ Status:** In Progress")
        else:
            st.markdown("*No notes available*")

    except Exception as e:
        st.error(f"Error loading notes summary: {e}")
