import streamlit as st
import pandas as pd
from app.ui.components.loader import LoaderContext


async def render_task_analysis(dashboard_manager):
    """Render comprehensive task analysis in tabular format with individual note records"""
    st.markdown("### 📈 Comprehensive Task Analysis")
    st.markdown(
        "*Detailed view showing each progress note as a separate record*")

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
            if progress_notes:
                for note in progress_notes:
                    analysis_data.append({
                        'ID': task.id,
                        'Created At': task.created_at.strftime('%Y-%m-%d') if task.created_at else 'N/A',
                        'Title': task.title,
                        'Issue': task_issue.issue_description if task_issue else 'No issue documented',
                        'Notes Date': note.note_date.strftime('%Y-%m-%d'),
                        'Analysis': note.analysis_content,
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
                    'Analysis': 'No progress notes',
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
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("#### 📈 Detailed Task Analysis Table")
        st.markdown("*Each row represents a progress note entry*")
    with col2:
        show_full_content = st.checkbox(
            "Show full content", help="Show complete text instead of truncated versions")

    # Prepare data for display
    display_data = []
    for item in analysis_data:
        display_item = {
            'ID': item['ID'],
            'Created At': item['Created At'],
            'Title': item['Title'],
            'Issue': item['Issue'] if show_full_content else (item['Issue'][:100] + '...' if len(item['Issue']) > 100 else item['Issue']),
            'Notes Date': item['Notes Date'],
            'Analysis': item['Analysis'] if show_full_content else (item['Analysis'][:100] + '...' if len(item['Analysis']) > 100 else item['Analysis']),
            'Resolution Notes': item['Resolution Notes'] if show_full_content else (item['Resolution Notes'][:100] + '...' if len(item['Resolution Notes']) > 100 else item['Resolution Notes'])
        }
        display_data.append(display_item)

    # Create DataFrame and display
    df = pd.DataFrame(display_data)

    # Sort by ID and Notes Date for better grouping
    df = df.sort_values(['ID', 'Notes Date'])

    # Display the table
    st.dataframe(
        df,
        use_container_width=True,
        height=600
    )

    # Export options
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
                item['ID'] for item in analysis_data if item['Analysis'] == 'No progress notes'))
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
