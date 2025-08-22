import streamlit as st
import pandas as pd
from app.ui.components.loader import LoaderContext


async def render_task_analysis(dashboard_manager):
    """Render comprehensive task analysis with enhanced UI for better readability"""
    st.markdown("### 📈 Comprehensive Task Analysis")
    st.markdown(
        "*Enhanced view with expandable sections for better note readability*")

    # Add custom CSS for better styling
    st.markdown("""
    <style>
    .task-analysis-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .task-analysis-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    .task-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e0e6ed;
    }
    
    .task-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #2c3e50;
        margin: 0;
    }
    
    .task-id {
        background: #667eea;
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    .note-section {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 3px solid #4fc3f7;
    }
    
    .note-header {
        font-weight: bold;
        color: #34495e;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .note-content {
        color: #555;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .issue-section {
        border-left-color: #ff9800;
    }
    
    .resolution-section {
        border-left-color: #6bcf7f;
    }
    
    .no-content {
        color: #999;
        font-style: italic;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .view-toggle {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        view_scope = st.selectbox(
            "View Scope:",
            ["All Tasks", "Current Month", "Archived Only"],
            help="Select which tasks to include in the analysis"
        )

    with col2:
        status_filter = st.multiselect(
            "Filter by Status:",
            ["todo", "inprogress", "pending", "completed"],
            default=["todo", "inprogress", "pending", "completed"],
            help="Select task statuses to include"
        )

    with col3:
        priority_filter = st.multiselect(
            "Filter by Priority:",
            ["low", "medium", "high", "urgent"],
            default=["low", "medium", "high", "urgent"],
            help="Select task priorities to include"
        )

    # Load tasks based on scope
    with LoaderContext("Loading task analysis data...", "inline"):
        if view_scope == "Current Month":
            tasks = await dashboard_manager.get_current_month_user_tasks()
        elif view_scope == "Archived Only":
            tasks = await dashboard_manager.get_archived_user_tasks()
        else:  # All Tasks
            current_tasks = await dashboard_manager.get_user_tasks()
            archived_tasks = await dashboard_manager.get_archived_user_tasks()
            tasks = current_tasks + archived_tasks

        # Apply filters
        filtered_tasks = [
            task for task in tasks
            if task.status in status_filter and task.priority in priority_filter
        ]

        if not filtered_tasks:
            st.info("📋 No tasks match the selected filters.")
            return

        # Load detailed analysis data for all filtered tasks
        from app.core.interface.task_notes_interface import (
            get_task_issue, get_task_resolution, get_task_progress_notes
        )

        analysis_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, task in enumerate(filtered_tasks):
            status_text.text(
                f"Loading analysis for task {i+1}/{len(filtered_tasks)}: {task.title}")
            progress_bar.progress((i + 1) / len(filtered_tasks))

            # Get issue, resolution, and progress notes
            task_issue = await get_task_issue(task.id)
            task_resolution = await get_task_resolution(task.id)
            progress_notes = await get_task_progress_notes(task.id)

            # Create a record for each progress note
            for note in progress_notes:
                analysis_data.append({
                    'ID': task.id,
                    'Created At': task.created_at.strftime('%Y-%m-%d') if task.created_at else 'N/A',
                    'Title': task.title,
                    'Issue': task_issue.issue_description if task_issue else 'No issue documented',
                    'Notes Date': note.note_date.strftime('%Y-%m-%d'),
                    'Timeline': note.timeline_content if note.timeline_content else 'No timeline content',
                    'Analysis': note.analysis_content if note.analysis_content else 'No analysis content',
                    'Resolution Notes': task_resolution.resolution_notes if task_resolution else 'No resolution documented'
                })
            else:
                # If no progress notes, still show the task with empty analysis
                analysis_data.append({
                    'ID': task.id,
                    'Created At': task.created_at.strftime('%Y-%m-%d') if task.created_at else 'N/A',
                    'Title': task.title,
                    'Issue': task_issue.issue_description if task_issue else 'No issue documented',
                    'Notes Date': 'No notes',
                    'Timeline': 'No timeline content',
                    'Analysis': 'No analysis content',
                    'Resolution Notes': task_resolution.resolution_notes if task_resolution else 'No resolution documented'
                })

        progress_bar.empty()
        status_text.empty()

    # Display summary statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        unique_tasks = len(set(item['ID'] for item in analysis_data))
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">📋 {unique_tasks}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Unique Tasks</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        total_notes = len(
            [item for item in analysis_data if item['Notes Date'] != 'No notes'])
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4fc3f7; margin: 0;">📝 {total_notes}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Progress Notes</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        tasks_with_issues = len(set(
            item['ID'] for item in analysis_data if item['Issue'] != 'No issue documented'))
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #ff9800; margin: 0;">🔍 {tasks_with_issues}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">With Issues</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        tasks_resolved = len(set(
            item['ID'] for item in analysis_data if item['Resolution Notes'] != 'No resolution documented'))
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #6bcf7f; margin: 0;">✅ {tasks_resolved}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Resolved</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Display options
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        view_mode = st.radio(
            "📋 Display Mode:",
            ["Card View", "Table View"],
            help="Choose how to display the task analysis data"
        )
    with col2:
        if view_mode == "Card View":
            group_by_task = st.checkbox(
                "📑 Group by Task",
                value=True,
                help="Group all notes under each task for better organization"
            )
        else:
            show_full_content = st.checkbox(
                "📄 Show full content",
                help="Show complete text instead of truncated versions"
            )
    with col3:
        items_per_page = st.selectbox(
            "📄 Items per page:",
            [5, 10, 20, 50, "All"],
            index=1,
            help="Number of items to display per page"
        )

    # Sort data by ID and Notes Date for better grouping
    analysis_data.sort(key=lambda x: (
        x['ID'], x['Notes Date'] if x['Notes Date'] != 'No notes' else '9999-12-31'))

    # Pagination setup
    if items_per_page != "All":
        total_items = len(analysis_data) if view_mode == "Table View" else len(
            set(item['ID'] for item in analysis_data))
        total_pages = (total_items - 1) // items_per_page + \
            1 if total_items > 0 else 1

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Previous", disabled=st.session_state.current_page <= 1):
                st.session_state.current_page -= 1
                st.rerun()
        with col2:
            st.markdown(
                f"<div style='text-align: center; padding: 8px;'><strong>Page {st.session_state.current_page} of {total_pages}</strong></div>", unsafe_allow_html=True)
        with col3:
            if st.button("Next ➡️", disabled=st.session_state.current_page >= total_pages):
                st.session_state.current_page += 1
                st.rerun()

    # Display based on selected mode
    if view_mode == "Card View":
        st.markdown("#### 📋 Task Analysis Cards")
        st.markdown("*Click on expandable sections to view detailed content*")

        if group_by_task:
            # Group data by task ID
            tasks_dict = {}
            for item in analysis_data:
                task_id = item['ID']
                if task_id not in tasks_dict:
                    tasks_dict[task_id] = {
                        'task_info': item,
                        'notes': []
                    }
                if item['Notes Date'] != 'No notes':
                    tasks_dict[task_id]['notes'].append(item)

            # Apply pagination for tasks
            task_ids = list(tasks_dict.keys())
            if items_per_page != "All":
                start_idx = (st.session_state.current_page - 1) * \
                    items_per_page
                end_idx = start_idx + items_per_page
                task_ids = task_ids[start_idx:end_idx]

            # Display each task as a card
            for task_id in task_ids:
                task_data = tasks_dict[task_id]
                task_info = task_data['task_info']
                notes = task_data['notes']

                # Task card container
                st.markdown(f"""
                <div class="task-analysis-card">
                    <div class="task-header">
                        <h3 class="task-title">📋 {task_info['Title']}</h3>
                        <span class="task-id">ID: {task_id}</span>
                    </div>
                    <p><strong>📅 Created:</strong> {task_info['Created At']}</p>
                </div>
                """, unsafe_allow_html=True)

                # Issue section
                with st.expander(f"🔍 Issue Description ({task_id})", expanded=False):
                    if task_info['Issue'] != 'No issue documented':
                        st.markdown(f"""
                        <div class="note-section issue-section">
                            <div class="note-content">{task_info['Issue']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div class='no-content'>No issue documented for this task</div>", unsafe_allow_html=True)

                # Progress notes section
                with st.expander(f"📝 Progress Notes ({len(notes)} notes)", expanded=True):
                    if notes:
                        for i, note in enumerate(notes):
                            st.markdown(f"""
                            <div class="note-section">
                                <div class="note-header">
                                    📅 {note['Notes Date']} - Note #{i+1}
                                </div>
                                <div class="note-content">
                                    <strong>📅 Timeline:</strong><br>
                                    {note['Timeline'] if note['Timeline'] != 'No timeline content' else '<em>No timeline content</em>'}<br><br>
                                    <strong>📊 Analysis:</strong><br>
                                    {note['Analysis'] if note['Analysis'] != 'No analysis content' else '<em>No analysis content</em>'}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div class='no-content'>No progress notes available for this task</div>", unsafe_allow_html=True)

                # Resolution section
                with st.expander(f"✅ Resolution Notes ({task_id})", expanded=False):
                    if task_info['Resolution Notes'] != 'No resolution documented':
                        st.markdown(f"""
                        <div class="note-section resolution-section">
                            <div class="note-content">{task_info['Resolution Notes']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div class='no-content'>No resolution documented for this task</div>", unsafe_allow_html=True)

                st.markdown("---")
        else:
            # Display individual notes as separate cards
            if items_per_page != "All":
                start_idx = (st.session_state.current_page - 1) * \
                    items_per_page
                end_idx = start_idx + items_per_page
                display_items = analysis_data[start_idx:end_idx]
            else:
                display_items = analysis_data

            for item in display_items:
                st.markdown(f"""
                <div class="task-analysis-card">
                    <div class="task-header">
                        <h4 class="task-title">📋 {item['Title']}</h4>
                        <span class="task-id">ID: {item['ID']}</span>
                    </div>
                    <p><strong>📅 Created:</strong> {item['Created At']} | <strong>📝 Note Date:</strong> {item['Notes Date']}</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)

                with col1:
                    with st.expander("🔍 Issue", expanded=False):
                        if item['Issue'] != 'No issue documented':
                            st.markdown(
                                f"<div class='note-content'>{item['Issue']}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(
                                "<div class='no-content'>No issue documented</div>", unsafe_allow_html=True)

                with col2:
                    with st.expander("📅 Timeline", expanded=False):
                        if item['Timeline'] != 'No timeline content':
                            st.markdown(
                                f"<div class='note-content'>{item['Timeline']}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(
                                "<div class='no-content'>No timeline content</div>", unsafe_allow_html=True)

                with col3:
                    with st.expander("📊 Analysis", expanded=True):
                        if item['Analysis'] != 'No analysis content':
                            st.markdown(
                                f"<div class='note-content'>{item['Analysis']}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(
                                "<div class='no-content'>No analysis content</div>", unsafe_allow_html=True)

                # Add resolution in a separate row
                with st.expander("✅ Resolution", expanded=False):
                    if item['Resolution Notes'] != 'No resolution documented':
                        st.markdown(
                            f"<div class='note-content'>{item['Resolution Notes']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div class='no-content'>No resolution documented</div>", unsafe_allow_html=True)

                st.markdown("---")

    else:  # Table View
        st.markdown("#### 📊 Task Analysis Table")
        st.markdown("*Traditional table view with sortable columns*")

        # Prepare data for display
        display_data = []
        for item in analysis_data:
            display_item = {
                'ID': item['ID'],
                'Created At': item['Created At'],
                'Title': item['Title'],
                'Issue': item['Issue'] if show_full_content else (item['Issue'][:100] + '...' if len(item['Issue']) > 100 else item['Issue']),
                'Notes Date': item['Notes Date'],
                'Timeline': item['Timeline'] if show_full_content else (item['Timeline'][:100] + '...' if len(item['Timeline']) > 100 else item['Timeline']),
                'Analysis': item['Analysis'] if show_full_content else (item['Analysis'][:100] + '...' if len(item['Analysis']) > 100 else item['Analysis']),
                'Resolution Notes': item['Resolution Notes'] if show_full_content else (item['Resolution Notes'][:100] + '...' if len(item['Resolution Notes']) > 100 else item['Resolution Notes'])
            }
            display_data.append(display_item)

        # Apply pagination
        if items_per_page != "All":
            start_idx = (st.session_state.current_page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            display_data = display_data[start_idx:end_idx]

        # Create DataFrame and display
        df = pd.DataFrame(display_data)

        # Display the table
        st.dataframe(
            df,
            use_container_width=True,
            height=600
        )

    # Export options
    st.markdown("---")
    st.markdown("#### 📥 Export Options")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Export to CSV"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"task_notes_analysis_{view_scope.lower().replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("📄 Export Full Report"):
            # Create detailed report with full content
            full_data = []
            for item in analysis_data:
                full_data.append({
                    'Task ID': item['ID'],
                    'Created At': item['Created At'],
                    'Task Title': item['Title'],
                    'Issue Description': item['Issue'],
                    'Notes Date': item['Notes Date'],
                    'Timeline Content': item['Timeline'],
                    'Analysis Content': item['Analysis'],
                    'Resolution Notes': item['Resolution Notes']
                })

            full_df = pd.DataFrame(full_data)
            csv_data = full_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Full Report",
                data=csv_data,
                file_name=f"detailed_task_notes_analysis_{view_scope.lower().replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with col3:
        if st.button("📈 Generate Summary"):
            st.markdown("#### 📈 Analysis Summary")

            # Task distribution
            st.markdown("**Task Analysis:**")
            st.markdown(f"- Total unique tasks: {unique_tasks}")
            st.markdown(f"- Total progress notes: {total_notes}")
            st.markdown(
                f"- Average notes per task: {total_notes/unique_tasks:.1f}" if unique_tasks > 0 else "- Average notes per task: 0")

            # Documentation completeness
            st.markdown("**Documentation Completeness:**")
            st.markdown(
                f"- Tasks with issues: {tasks_with_issues}/{unique_tasks} ({(tasks_with_issues/unique_tasks*100):.1f}%)" if unique_tasks > 0 else "- Tasks with issues: 0%")
            st.markdown(
                f"- Tasks with resolutions: {tasks_resolved}/{unique_tasks} ({(tasks_resolved/unique_tasks*100):.1f}%)" if unique_tasks > 0 else "- Tasks with resolutions: 0%")

    # Quick actions
    st.markdown("---")
    st.markdown("#### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Show Tasks Without Issues"):
            tasks_without_issues = list(set(
                item['ID'] for item in analysis_data if item['Issue'] == 'No issue documented'))
            if tasks_without_issues:
                st.markdown(
                    f"**Found {len(tasks_without_issues)} tasks without issue documentation:**")
                for task_id in tasks_without_issues:
                    task_title = next(
                        item['Title'] for item in analysis_data if item['ID'] == task_id)
                    st.markdown(f"- **{task_title}** (ID: {task_id})")
            else:
                st.success("✅ All tasks have issue documentation!")

    with col2:
        if st.button("📝 Show Tasks Without Progress"):
            tasks_without_progress = list(set(
                item['ID'] for item in analysis_data if item['Analysis'] == 'No analysis content' and item['Timeline'] == 'No timeline content'))
            if tasks_without_progress:
                st.markdown(
                    f"**Found {len(tasks_without_progress)} tasks without progress notes:**")
                for task_id in tasks_without_progress:
                    task_title = next(
                        item['Title'] for item in analysis_data if item['ID'] == task_id)
                    st.markdown(f"- **{task_title}** (ID: {task_id})")
            else:
                st.success("✅ All tasks have progress documentation!")

    with col3:
        if st.button("✅ Show Unresolved Tasks"):
            unresolved_tasks = list(set(
                item['ID'] for item in analysis_data if item['Resolution Notes'] == 'No resolution documented'))
            if unresolved_tasks:
                st.markdown(
                    f"**Found {len(unresolved_tasks)} tasks without resolution:**")
                for task_id in unresolved_tasks:
                    task_title = next(
                        item['Title'] for item in analysis_data if item['ID'] == task_id)
                    st.markdown(f"- **{task_title}** (ID: {task_id})")
            else:
                st.success("✅ All tasks have been resolved!")
