import html
import asyncio
import streamlit as st
import re
from datetime import date
from app.security.route_protection import RouteProtection
from app.core.interface.task_notes_handler import (
    create_progress_note_sync, update_progress_note_sync, delete_progress_note_sync,
    create_or_update_issue_sync, create_or_update_resolution_sync, get_task_notes_data_sync
)


def show_formatting_help():
    """Display formatting help for users"""
    with st.expander("📝 Text Formatting Guide", expanded=False):
        st.markdown("""
        **Available Formatting Options:**

        • **Bold text**: `**bold text**` → **bold text**
        • *Italic text*: `*italic text*` → *italic text*
        • <u>Underlined text</u>: `<u>underlined text</u>` → <u>underlined text</u>
        • ~~Strikethrough~~: `~~strikethrough~~` → ~~strikethrough~~
        • `Code text`: `` `code text` `` → `code text`
        • [Links](url): `[Link Text](https://example.com)` → [Link Text](https://example.com)

        **Lists:**
        • Bullet points: Start lines with `•` or `-`
        • Numbered lists: Start lines with `1.`, `2.`, etc.

        **Special:**
        • Line breaks: Use double space at end of line or empty line
        • Horizontal rule: `---` on its own line

        **Examples:**
        ```
        **Important:** This is a *critical* update.

        <u>Key findings:</u>
        • ~~Old approach~~ didn't work
        • New `solution()` implemented
        • [Documentation](https://docs.example.com) updated
        ```
        """, unsafe_allow_html=True)


def apply_text_formatting(text):
    """Apply markdown-like formatting to text for HTML display"""
    if not text:
        return ""

    # Escape HTML first to prevent XSS
    formatted_text = html.escape(text)

    # Apply formatting patterns
    # Bold: **text** -> <strong>text</strong>
    formatted_text = re.sub(
        r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_text)

    # Italic: *text* -> <em>text</em>
    formatted_text = re.sub(
        r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', formatted_text)

    # Underline: <u>text</u> (already HTML, just preserve)
    formatted_text = re.sub(r'&lt;u&gt;(.*?)&lt;/u&gt;',
                            r'<u>\1</u>', formatted_text)

    # Strikethrough: ~~text~~ -> <del>text</del>
    formatted_text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', formatted_text)

    # Code: `text` -> <code>text</code>
    formatted_text = re.sub(
        r'`([^`]+?)`', r'<code style="background-color: #f1f3f4; padding: 2px 4px; border-radius: 3px; font-family: monospace;">\1</code>', formatted_text)

    # Links: [text](url) -> <a href="url">text</a>
    formatted_text = re.sub(r'\[([^\]]+?)\]\(([^\)]+?)\)',
                            r'<a href="\2" target="_blank" style="color: #007bff; text-decoration: none;">\1</a>', formatted_text)

    # Line breaks
    formatted_text = formatted_text.replace('\n', '<br>')

    # Horizontal rules
    formatted_text = re.sub(
        r'<br>---<br>', '<hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">', formatted_text)

    return formatted_text


def show_formatting_toolbar(text_area_key, content_type="text"):
    """Show formatting toolbar with quick insert buttons"""
    st.markdown(f"**🎨 Formatting Toolbar for {content_type.title()}:**")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        if st.button("**B**", help="Bold text", key=f"bold_{text_area_key}"):
            st.session_state[f"format_insert_{text_area_key}"] = "**bold text**"

    with col2:
        if st.button("*I*", help="Italic text", key=f"italic_{text_area_key}"):
            st.session_state[f"format_insert_{text_area_key}"] = "*italic text*"

    with col3:
        if st.button("<u>U</u>", help="Underline text", key=f"underline_{text_area_key}"):
            st.session_state[f"format_insert_{text_area_key}"] = "<u>underlined text</u>"

    with col4:
        if st.button("~~S~~", help="Strikethrough", key=f"strike_{text_area_key}"):
            st.session_state[f"format_insert_{text_area_key}"] = "~~strikethrough~~"

    with col5:
        if st.button("`C`", help="Code text", key=f"code_{text_area_key}"):
            st.session_state[f"format_insert_{text_area_key}"] = "`code text`"

    with col6:
        if st.button("🔗", help="Insert link", key=f"link_{text_area_key}"):
            st.session_state[f"format_insert_{text_area_key}"] = "[Link Text](https://example.com)"

    # Show insert message if formatting was clicked
    if f"format_insert_{text_area_key}" in st.session_state:
        st.info(
            f"💡 Copy this formatting: `{st.session_state[f'format_insert_{text_area_key}']}`")
        # Clear the message after showing
        del st.session_state[f"format_insert_{text_area_key}"]


def render_formatted_content(content, content_type="Timeline"):
    """Render content with formatting applied"""
    if not content or not content.strip():
        return ""

    formatted_content = apply_text_formatting(content)
    return f"<div><strong>📅 {content_type}:</strong><br>{formatted_content}</div>"


def show_task_notes_modal(task):
    """Display task notes modal with timeline view and note management"""

    modal_key = f"notes_modal_{task.id}"

    @st.dialog(f"📝 Task Notes: {task.title}", width="large")
    def notes_modal():
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

            # Task information header (cleaner, rounded)
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #1f6feb, #0b4ea2); color: white; padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem; box-shadow: 0 6px 18px rgba(12,38,70,0.12);">
                <h3 style="margin: 0; color: white;">📋 {task.title}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.95;">Status: {task.status.title()} | Priority: {task.priority.title()} | Category: {task.category.title()}</p>
            </div>
            """, unsafe_allow_html=True)

            # Tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["🔍 Issue", "📝 Daily Progress", "✅ Resolution", "📚 Timeline", "📊 Analysis"])

            with tab1:
                st.markdown("### 🔍 Task Issue Description")
                st.markdown(
                    "*Document the main issue or problem this task is meant to address*")

                # Show formatting help
                show_formatting_help()

                # Formatting toolbar for issue (outside form)
                show_formatting_toolbar(
                    f"issue_{task.id}", "Issue Description")

                # Use the loaded issue data
                existing_issue = task_issue

                with st.form(f"issue_form_{task.id}"):
                    issue_content = st.text_area(
                        "What is the main issue or problem?",
                        value=existing_issue.issue_description if existing_issue else "",
                        height=200,
                        placeholder="**Problem:** Describe the main issue\n\n**Impact:** What are the consequences?\n\n**Requirements:** What needs to be accomplished?",
                        help="Provide a clear description of the issue or objective for this task. Use formatting options above!"
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
                    formatted_issue = apply_text_formatting(
                        existing_issue.issue_description)
                    st.markdown(
                        f'<div style="padding: 1rem; background-color: #e7f3ff; border-left: 4px solid #007bff; border-radius: 6px;">{formatted_issue}</div>', unsafe_allow_html=True)
                    if existing_issue.updated_at:
                        st.caption(
                            f"Last updated: {existing_issue.updated_at.strftime('%B %d, %Y at %I:%M %p')}")

            with tab2:
                st.markdown("### ➕ Add Daily Progress Note")

                # Show formatting help
                show_formatting_help()

                # Formatting toolbars for timeline and analysis (outside form)
                st.markdown("#### 📅 Daily Timeline")
                show_formatting_toolbar(f"timeline_add_{task.id}", "Timeline")

                st.markdown("#### 📊 Detailed Analysis")
                show_formatting_toolbar(f"analysis_add_{task.id}", "Analysis")

                with st.form(f"add_note_form_{task.id}"):
                    note_date_input = st.date_input(
                        "📅 Note Date",
                        value=date.today(),
                        help="Select the date for this progress entry"
                    )

                    st.markdown("**Timeline Content:**")
                    timeline_content = st.text_area(
                        "What actions did you take today?",
                        height=150,
                        placeholder="• **9:00 AM** - Started working on *feature X*\n• **10:30 AM** - Met with team to discuss requirements\n• **2:00 PM** - Implemented `solution Y`\n• **4:00 PM** - Tested and debugged...",
                        help="Document the specific actions, meetings, and activities you performed during the day. Use formatting options above!",
                        key=f"timeline_content_add_{task.id}"
                    )

                    st.markdown("**Analysis Content:**")
                    analysis_content = st.text_area(
                        "Provide detailed analysis of your work:",
                        height=150,
                        placeholder="**Key Findings:**\n• ~~Old approach~~ didn't work due to *performance issues*\n• New `solution()` implemented with <u>significant improvements</u>\n• [Documentation](https://docs.example.com) updated\n\n**Next Steps:**\n• Test in production environment\n• Monitor performance metrics",
                        help="Document your detailed analysis, insights, challenges, and findings from today's work. Use formatting options above!",
                        key=f"analysis_content_add_{task.id}"
                    )

                    submitted = st.form_submit_button(
                        "💾 Save Progress Note", type="primary")

                    if submitted:
                        if not timeline_content.strip() and not analysis_content.strip():
                            st.error(
                                "❌ At least one of Timeline or Analysis content is required!")
                        else:
                            # Save progress note directly to database
                            with st.spinner("Saving progress note..."):
                                result = create_progress_note_sync(
                                    task_id=task.id,
                                    note_date=note_date_input,
                                    timeline_content=timeline_content.strip() if timeline_content.strip() else None,
                                    analysis_content=analysis_content.strip() if analysis_content.strip() else None,
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

                # Show formatting help
                show_formatting_help()

                # Formatting toolbar for resolution (outside form)
                show_formatting_toolbar(f"resolution_{task.id}", "Resolution")

                # Use the loaded resolution data
                existing_resolution = task_resolution

                with st.form(f"resolution_form_{task.id}"):
                    resolution_content = st.text_area(
                        "How was the issue resolved?",
                        value=existing_resolution.resolution_notes if existing_resolution else "",
                        height=200,
                        placeholder="**Solution:** Describe the implemented solution\n\n**Results:** What were the outcomes?\n\n**Lessons Learned:** Key insights and takeaways\n\n**Follow-up:** Any remaining tasks or monitoring needed",
                        help="Document the final resolution, solution, and any important outcomes or lessons learned. Use formatting options above!"
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
                    formatted_resolution = apply_text_formatting(
                        existing_resolution.resolution_notes)
                    st.markdown(
                        f'<div style="padding: 1rem; background-color: #d4edda; border-left: 4px solid #28a745; border-radius: 6px;">{formatted_resolution}</div>', unsafe_allow_html=True)
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
                            "📝 No notes have been added for this task yet. Start documenting your progress using the 'Daily Progress' tab."
                        )
                    else:
                        st.markdown(f"**📊 Total Entries: {len(notes)}**")
                        st.markdown("---")

                        # Enhanced CSS for collapsible note content (refined colors and spacing)
                        st.markdown(
                            """
                            <style>
                            .note-card {
                                border: 1px solid #e9ecef;
                                border-radius: 12px;
                                padding: 16px;
                                margin-bottom: 16px;
                                background: #ffffff;
                                box-shadow: 0 6px 18px rgba(12,38,70,0.04);
                                transition: all 0.18s ease;
                            }
                            .note-card:hover {
                                box-shadow: 0 10px 24px rgba(12,38,70,0.08);
                                transform: translateY(-2px);
                            }
                            .note-header {
                                display: flex;
                                justify-content: space-between;
                                align-items: flex-start;
                                margin-bottom: 8px;
                            }
                            .note-date {
                                margin: 0;
                                color: #222222; /* neutral/darker */
                                font-size: 1.05em;
                                font-weight: 700;
                            }
                            .note-meta {
                                font-size: 0.85em;
                                color: #6c757d;
                                margin: 4px 0 12px 0;
                            }
                            .note-content {
                                font-size: 1em;
                                line-height: 1.6;
                                color: #222;
                                white-space: normal;
                                overflow: hidden;
                                max-height: 9.6em; /* 6 lines approx */
                                margin-bottom: 12px;
                                transition: max-height 0.28s ease;
                            }
                            .note-content.expanded {
                                max-height: none;
                            }
                            .read-more {
                                color: #0b5ed7;
                                cursor: pointer;
                                font-weight: 600;
                                font-size: 0.95em;
                                user-select: none;
                            }
                            .read-more:hover {
                                text-decoration: underline;
                            }
                            .action-btn {
                                font-size: 0.9em;
                                padding: 6px 10px;
                                border-radius: 6px;
                            }
                            .summary-box {
                                margin-top: 2rem;
                                padding: 1rem;
                                background-color: #f8f9fa;
                                border-radius: 10px;
                                font-size: 0.95em;
                                color: #495463;
                                line-height: 1.6;
                            }
                            </style>
                            """,
                            unsafe_allow_html=True
                        )

                        for i, note in enumerate(notes):
                            note_id = f"note_{note.id}"
                            is_expanded_key = f"expanded_{note.id}"

                            # Initialize session state for expand/collapse (timeline)
                            if is_expanded_key not in st.session_state:
                                st.session_state[is_expanded_key] = False

                            note_date_str = note.note_date.strftime(
                                '%A, %B %d, %Y')
                            time_ago = "Today" if note.note_date == date.today(
                            ) else f"{(date.today() - note.note_date).days} day(s) ago"

                            # Prepare timeline content for display with formatting
                            timeline_display = ""
                            if note.timeline_content and note.timeline_content.strip():
                                if st.session_state[is_expanded_key]:
                                    # Show full content with formatting
                                    timeline_display = render_formatted_content(
                                        note.timeline_content, "Timeline")
                                else:
                                    # Show truncated content with formatting
                                    timeline_lines = note.timeline_content.strip().split('\n')
                                    truncated_timeline = '\n'.join(
                                        timeline_lines[:3])
                                    timeline_display = render_formatted_content(
                                        truncated_timeline, "Timeline")
                                timeline_display = f"<div style='margin-bottom: 10px;'>{timeline_display}</div>"

                            # NOTE: Timeline tab now intentionally shows ONLY timeline content (no analysis)

                            # Render note card (timeline only)
                            st.markdown(
                                f"""
                                <div class="note-card" id="{note_id}_card">
                                    <div class="note-header">
                                        <h4 class="note-date">📅 {note_date_str}</h4>
                                        <span style="
                                            background-color: #495057;
                                            color: white;
                                            padding: 4px 8px;
                                            border-radius: 8px;
                                            font-size: 0.8em;
                                            font-weight: 600;
                                        ">#{len(notes) - i}</span>
                                    </div>
                                    <p class="note-meta"><i>📝 {time_ago}</i></p>
                                    <div class="note-content {'expanded' if st.session_state[is_expanded_key] else ''}">
                                        {timeline_display}
                                    </div>
                                    <div class="read-more-container" style="margin-top: 0.5rem;">
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Render the "View More"/"View Less" button for timeline
                            view_more_button = st.button(
                                "🔽 View Less" if st.session_state[is_expanded_key] else "🔺 View More",
                                key=f"btn_toggle_{note.id}",
                                use_container_width=False,
                                type="secondary",
                                help="Expand or collapse note content",
                                on_click=lambda nk=is_expanded_key: st.session_state.update(
                                    {nk: not st.session_state[nk]})
                            )

                            if view_more_button:
                                st.rerun()

                            # Action buttons (Edit, Delete)
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                if st.button(f"✏️ Edit", key=f"edit_note_{note.id}"):
                                    st.session_state[f"editing_note_{note.id}"] = True
                                    st.rerun()

                            with col2:
                                if st.button(f"🗑️ Delete", key=f"delete_note_{note.id}"):
                                    with st.spinner("Deleting note..."):
                                        result = delete_progress_note_sync(
                                            note.id)
                                    if result['success']:
                                        st.success(result['message'])
                                        st.rerun()
                                    else:
                                        st.error(result['message'])

                            # Edit mode (only if in edit state)
                            if st.session_state.get(f"editing_note_{note.id}", False):
                                with st.expander("✏️ Edit Note", expanded=True):
                                    # Show formatting help for editing
                                    show_formatting_help()

                                    # Formatting toolbars for editing (outside form)
                                    st.markdown("#### 📅 Timeline Content")
                                    show_formatting_toolbar(
                                        f"timeline_edit_{note.id}", "Timeline")

                                    st.markdown("#### 📊 Analysis Content")
                                    show_formatting_toolbar(
                                        f"analysis_edit_{note.id}", "Analysis")

                                    with st.form(f"edit_note_form_{note.id}"):
                                        st.markdown("**Timeline:**")
                                        updated_timeline = st.text_area(
                                            "Edit timeline content:",
                                            value=note.timeline_content or "",
                                            height=150,
                                            key=f"edit_timeline_{note.id}",
                                            placeholder="Daily actions and activities with formatting..."
                                        )

                                        st.markdown("**Analysis:**")
                                        updated_analysis = st.text_area(
                                            "Edit analysis content:",
                                            value=note.analysis_content or "",
                                            height=150,
                                            key=f"edit_analysis_{note.id}",
                                            placeholder="Detailed analysis and insights with formatting..."
                                        )

                                        col_save, col_cancel = st.columns(2)
                                        with col_save:
                                            save_clicked = st.form_submit_button(
                                                "💾 Save", type="primary")
                                        with col_cancel:
                                            cancel_clicked = st.form_submit_button(
                                                "❌ Cancel")

                                        if save_clicked:
                                            if not updated_timeline.strip() and not updated_analysis.strip():
                                                st.error(
                                                    "❌ At least one of Timeline or Analysis content is required!")
                                            else:
                                                with st.spinner("Updating..."):
                                                    result = update_progress_note_sync(
                                                        note_id=note.id,
                                                        timeline_content=updated_timeline.strip() if updated_timeline.strip() else None,
                                                        analysis_content=updated_analysis.strip() if updated_analysis.strip() else None
                                                    )
                                                if result['success']:
                                                    st.success(
                                                        "✅ Note updated successfully!")
                                                    del st.session_state[f"editing_note_{note.id}"]
                                                    st.rerun()
                                                else:
                                                    st.error(result['message'])

                                        if cancel_clicked:
                                            del st.session_state[f"editing_note_{note.id}"]
                                            st.rerun()

                            st.markdown("---")

                        # Summary Box
                        st.markdown(
                            f"""
                            <div class="summary-box">
                                <strong>📈 Activity Summary</strong><br>
                                • 📝 <strong>{len(notes)}</strong> total progress entries<br>
                                • 🗓️ <strong>Date Range:</strong> {notes[-1].note_date.strftime('%b %d')} – {notes[0].note_date.strftime('%b %d, %Y')}<br>
                                • 🔁 <strong>Latest:</strong> {time_ago}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                except Exception as e:
                    st.error(f"❌ Failed to load timeline: {str(e)}")

            with tab5:
                st.markdown("### 📊 Analysis View")

                try:
                    # Use the loaded progress notes data
                    notes = progress_notes

                    if not notes:
                        st.info(
                            "📊 No analysis entries have been added for this task yet. Start documenting your analysis using the 'Daily Progress' tab."
                        )
                    else:
                        st.markdown(
                            f"**📊 Total Analysis Entries: {len(notes)}**")
                        st.markdown("---")

                        # Filter notes that have analysis content
                        analysis_notes = [
                            note for note in notes if note.analysis_content and note.analysis_content.strip()]

                        if not analysis_notes:
                            st.info(
                                "📊 No detailed analysis content found. Add analysis content in the 'Daily Progress' tab.")
                        else:
                            for i, note in enumerate(analysis_notes):
                                note_date_str = note.note_date.strftime(
                                    '%A, %B %d, %Y')
                                time_ago = "Today" if note.note_date == date.today(
                                ) else f"{(date.today() - note.note_date).days} day(s) ago"

                                # Use a per-analysis expanded key so users can independently expand analysis cards
                                analysis_expanded_key = f"analysis_expanded_{note.id}"
                                if analysis_expanded_key not in st.session_state:
                                    st.session_state[analysis_expanded_key] = False

                                # Prepare analysis display (truncated or full)
                                if st.session_state[analysis_expanded_key]:
                                    formatted_analysis = apply_text_formatting(
                                        note.analysis_content)
                                    analysis_display_html = f"<div class=\"note-content expanded\"><strong>📊 Detailed Analysis:</strong><br>{formatted_analysis}</div>"
                                else:
                                    analysis_lines = note.analysis_content.strip().split('\n')
                                    truncated_analysis = '\n'.join(
                                        analysis_lines[:4])
                                    formatted_truncated = apply_text_formatting(
                                        truncated_analysis)
                                    analysis_display_html = f"<div class=\"note-content\"><strong>📊 Detailed Analysis:</strong><br>{formatted_truncated}</div>"

                                # Render analysis card
                                st.markdown(
                                    f"""
                                    <div class="note-card" style="border-left: 4px solid #28a745;">
                                        <div class="note-header">
                                            <h4 class="note-date">📊 {note_date_str}</h4>
                                            <span style="
                                                background-color: #28a745;
                                                color: white;
                                                padding: 4px 8px;
                                                border-radius: 8px;
                                                font-size: 0.8em;
                                                font-weight: 600;
                                            ">Analysis #{len(analysis_notes) - i}</span>
                                        </div>
                                        <p class="note-meta"><i>📊 {time_ago}</i></p>
                                        {analysis_display_html}
                                    </div>
                                    """, unsafe_allow_html=True
                                )

                                # Add view more / view less button for analysis card
                                analysis_toggle = st.button(
                                    "🔽 View Less" if st.session_state[analysis_expanded_key] else "🔺 View More",
                                    key=f"analysis_btn_toggle_{note.id}",
                                    help="Expand or collapse analysis content",
                                    on_click=lambda k=analysis_expanded_key: st.session_state.update(
                                        {k: not st.session_state[k]})
                                )
                                if analysis_toggle:
                                    st.rerun()

                                # Quick edit button for analysis
                                if st.button(f"✏️ Edit Analysis", key=f"edit_analysis_btn_{note.id}"):
                                    st.session_state[f"editing_analysis_{note.id}"] = True
                                    st.rerun()

                                # Edit mode for analysis only
                                if st.session_state.get(f"editing_analysis_{note.id}", False):
                                    with st.expander("✏️ Edit Analysis", expanded=True):
                                        # Show formatting help for analysis editing
                                        show_formatting_help()

                                        # Formatting toolbar for analysis editing (outside form)
                                        show_formatting_toolbar(
                                            f"analysis_only_edit_{note.id}", "Analysis")

                                        with st.form(f"edit_analysis_form_{note.id}"):
                                            updated_analysis = st.text_area(
                                                "Edit analysis content:",
                                                value=note.analysis_content or "",
                                                height=200,
                                                key=f"edit_analysis_textarea_{note.id}",
                                                placeholder="Detailed analysis and insights with formatting..."
                                            )

                                            col_save, col_cancel = st.columns(
                                                2)
                                            with col_save:
                                                save_clicked = st.form_submit_button(
                                                    "💾 Save Analysis", type="primary")
                                            with col_cancel:
                                                cancel_clicked = st.form_submit_button(
                                                    "❌ Cancel")

                                            if save_clicked:
                                                if not updated_analysis.strip():
                                                    st.error(
                                                        "❌ Analysis content cannot be empty!")
                                                else:
                                                    with st.spinner("Updating analysis..."):
                                                        result = update_progress_note_sync(
                                                            note_id=note.id,
                                                            timeline_content=note.timeline_content,  # Keep existing timeline
                                                            analysis_content=updated_analysis.strip()
                                                        )
                                                    if result['success']:
                                                        st.success(
                                                            "✅ Analysis updated successfully!")
                                                        del st.session_state[f"editing_analysis_{note.id}"]
                                                        st.rerun()
                                                    else:
                                                        st.error(
                                                            result['message'])

                                            if cancel_clicked:
                                                del st.session_state[f"editing_analysis_{note.id}"]
                                                st.rerun()

                                st.markdown("---")

                        # Summary Box for Analysis
                        st.markdown(
                            f"""
                            <div class="summary-box" style="border-left: 4px solid #28a745;">
                                <strong>📊 Analysis Summary</strong><br>
                                • 📊 <strong>{len(analysis_notes)}</strong> detailed analysis entries<br>
                                • 🗓️ <strong>Date Range:</strong> {analysis_notes[-1].note_date.strftime('%b %d')} – {analysis_notes[0].note_date.strftime('%b %d, %Y')}<br>
                                • 🔍 <strong>Latest Analysis:</strong> {time_ago}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                except Exception as e:
                    st.error(f"❌ Failed to load analysis: {str(e)}")
        except Exception as e:
            st.error(f"Error loading notes: {e}")

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
