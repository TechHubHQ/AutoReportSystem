import math
import pandas as pd
import streamlit as st
from app.ui.components.loader import LoaderContext


def apply_modern_task_analysis_css():
    """Apply modern CSS styling for the task analysis dashboard"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .main-container {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
        padding: 0;
    }
    
    /* Modern Header */
    .analysis-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 0 0 30px 30px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .analysis-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        animation: float 20s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    .header-content {
        position: relative;
        z-index: 1;
    }
    
    .analysis-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .analysis-subtitle {
        font-size: 1.2rem;
        font-weight: 300;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Stats Cards */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
        padding: 0 1rem;
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15);
    }
    
    .stat-card:hover::before {
        transform: scaleX(1);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #6B7280;
        font-weight: 500;
        margin: 0.5rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Modern Task Cards */
    .task-timeline-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    .task-card-modern {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .task-card-modern:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
    }
    
    .task-header-modern {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 2rem;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        position: relative;
    }
    
    .task-title-modern {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0 0 0.5rem 0;
        line-height: 1.2;
    }
    
    .task-meta-modern {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: center;
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .task-id-badge {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Timeline Section */
    .timeline-section {
        padding: 0;
        position: relative;
    }
    
    .timeline-header {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 1.5rem 2rem;
        border-bottom: 2px solid #f59e0b;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .timeline-icon {
        width: 40px;
        height: 40px;
        background: #f59e0b;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
    }
    
    .timeline-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #92400e;
        margin: 0;
    }
    
    .timeline-content {
        padding: 2rem;
        line-height: 1.8;
        color: #374151;
        font-size: 1rem;
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        white-space: pre-wrap;
        word-wrap: break-word;
        border-left: 4px solid #f59e0b;
        margin: 0;
        min-height: 100px;
        position: relative;
    }
    
    .timeline-content::before {
        content: '"';
        position: absolute;
        top: 1rem;
        left: 1rem;
        font-size: 4rem;
        color: #f59e0b;
        opacity: 0.2;
        font-family: Georgia, serif;
    }
    
    /* Analysis Section */
    .analysis-section {
        padding: 0;
        position: relative;
    }
    
    .analysis-header {
        background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%);
        padding: 1.5rem 2rem;
        border-bottom: 2px solid #8b5cf6;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .analysis-icon {
        width: 40px;
        height: 40px;
        background: #8b5cf6;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
    }
    
    .analysis-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #5b21b6;
        margin: 0;
    }
    
    .analysis-content {
        padding: 2rem;
        line-height: 1.8;
        color: #374151;
        font-size: 1rem;
        background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
        white-space: pre-wrap;
        word-wrap: break-word;
        border-left: 4px solid #8b5cf6;
        margin: 0;
        min-height: 100px;
        position: relative;
    }
    
    .analysis-content::before {
        content: '💡';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 2rem;
        opacity: 0.3;
    }
    
    /* Issue/Resolution Sections */
    .issue-section {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
        padding: 1.5rem 2rem;
        margin: 0;
        position: relative;
    }
    
    .issue-section::before {
        content: '⚠️';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
    }
    
    .resolution-section {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border-left: 4px solid #22c55e;
        padding: 1.5rem 2rem;
        margin: 0;
        position: relative;
    }
    
    .resolution-section::before {
        content: '✅';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
    }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .section-content {
        line-height: 1.8;
        color: #374151;
        font-size: 0.95rem;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    /* Empty States */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: #9ca3af;
        font-style: italic;
        background: rgba(0, 0, 0, 0.02);
        border-radius: 12px;
        margin: 1rem;
    }
    
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    /* Progress Notes Timeline */
    .notes-timeline {
        position: relative;
        margin: 2rem 0;
    }
    
    .note-item {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #3b82f6;
        position: relative;
        transition: all 0.3s ease;
    }
    
    .note-item:hover {
        transform: translateX(8px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    
    .note-date {
        font-size: 0.9rem;
        font-weight: 600;
        color: #3b82f6;
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .note-date::before {
        content: '📅';
        font-size: 1rem;
    }
    
    /* Filters and Controls */
    .controls-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .controls-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0 0 1.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .controls-title::before {
        content: '🎛️';
        font-size: 1.2rem;
    }
    
    /* Search and Pagination */
    .search-container {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
        margin: 1rem 0;
    }
    
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin: 2rem 0;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 16px;
        backdrop-filter: blur(10px);
    }
    
    .page-info {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .analysis-title {
            font-size: 2rem;
        }
        
        .task-header-modern {
            padding: 1.5rem;
        }
        
        .task-title-modern {
            font-size: 1.5rem;
        }
        
        .timeline-content,
        .analysis-content {
            padding: 1.5rem;
        }
        
        .stats-container {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }
    }
    
    /* Loading Animation */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem;
        gap: 1rem;
    }
    
    .loading-spinner {
        width: 60px;
        height: 60px;
        border: 4px solid #f3f4f6;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-text {
        color: #6b7280;
        font-weight: 500;
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)


async def render_task_analysis(dashboard_manager):
    """Render task analysis as an Excel-like table with merged cells (rowspan), grouping timeline by date."""
    apply_modern_task_analysis_css()

    # Extra CSS for table view (sticky header, palette, merged-cell visuals)
    st.markdown("""
    <style>
    /* Table wrapper with rounded outer corners */
    .table-wrapper {
        width: 100%;
        overflow: auto;
        border-radius: 14px;                 /* outer rounded container */
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
        background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(250,250,255,0.98));
        padding: 1rem;
        margin-top: 1rem;
    }

    /* Use separate border model + spacing so cells become rounded "tiles" */
    table.analysis-table {
        border-collapse: separate;           /* important for rounded cells */
        border-spacing: 10px;                /* gap between rounded cells */
        width: 100%;
        min-width: 1100px;
        font-family: Inter, Arial, sans-serif;
        font-size: 14px;
    }

    /* Sticky header remains but each header cell is rounded */
    table.analysis-table thead th {
        position: sticky;
        top: 0;
        z-index: 5;
        padding: 12px 12px;
        text-align: left;
        color: white;
        font-weight: 700;
        letter-spacing: 0.4px;
        border-radius: 10px;                 /* rounded header cells */
        box-shadow: 0 6px 18px rgba(15,23,42,0.06);
    }

    /* Header gradients follow the palette (kept) */
    th.col-task { background: linear-gradient(90deg,#667eea,#764ba2); }
    th.col-issue { background: linear-gradient(90deg,#f97316,#fb923c); }
    th.col-analysis { background: linear-gradient(90deg,#8b5cf6,#c4b5fd); }
    th.col-timeline { background: linear-gradient(90deg,#f59e0b,#fde68a); color: #222; }
    th.col-res { background: linear-gradient(90deg,#10b981,#34d399); color: #fff; }

    /* Body cells styled as rounded tiles */
    table.analysis-table td {
        background: rgba(255,255,255,0.95);
        padding: 12px;
        vertical-align: top;
        border: none;                        /* remove hard borders—we rely on spacing */
        border-radius: 10px;                 /* rounded tile look */
        box-shadow: 0 6px 18px rgba(15,23,42,0.03);
        min-width: 180px;
    }

    /* Subtle hover to lift the tile */
    table.analysis-table tbody tr:hover td {
        transform: translateY(-3px);
        transition: transform 0.18s ease;
        box-shadow: 0 12px 30px rgba(15,23,42,0.06);
    }

    /* Column accent backgrounds (subtle, still rounded) */
    td.task-cell {
        background: linear-gradient(135deg, rgba(102,126,234,0.06), rgba(118,75,162,0.03));
        min-width: 220px;
        font-weight: 600;
    }
    td.issue-cell {
        background: linear-gradient(135deg, rgba(254,202,202,0.05), rgba(254,165,165,0.02));
        min-width: 260px;
    }
    td.analysis-cell {
        background: linear-gradient(135deg, rgba(237,233,254,0.05), rgba(220,213,255,0.02));
        min-width: 340px;
    }
    td.timeline-cell {
        background: linear-gradient(135deg, rgba(255,249,235,0.05), rgba(255,244,199,0.02));
        min-width: 260px;
    }
    td.res-cell {
        background: linear-gradient(135deg, rgba(220,252,231,0.05), rgba(187,247,208,0.02));
        min-width: 260px;
    }

    /* Reduce scrollbar visual noise on mac/windows */
    .table-wrapper::-webkit-scrollbar { height: 8px; }
    .table-wrapper::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 8px; }

    /* cell content and badge style unchanged */
    .task-meta { font-size: 12px; color: #6b7280; margin-top: 6px; font-weight: 500; }
    .cell-content {
        max-height: 220px;              /* give more vertical room */
        overflow-y: auto;               /* only vertical scroll */
        overflow-x: hidden;
        white-space: normal;            /* normal wrapping, no big gaps */
        word-break: break-word;         /* break long words gracefully */
        line-height: 1.5;               /* improve readability */
        padding-right: 6px;             /* so scrollbar doesn’t overlap text */
    }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; color: white; margin-right: 6px; }
    .badge-status { background: linear-gradient(90deg,#4fc3f7,#667eea); }
    .badge-priority { background: linear-gradient(90deg,#ffb86b,#ff6b6b); color: #111; }

    /* Grouped date header inside timeline cell */
    .timeline-date-group { margin-bottom: 8px; }
    .timeline-date-title { font-weight: 700; color: #92400e; margin-bottom: 6px; }
    .timeline-entry { margin-left: 8px; margin-bottom: 6px; }
    .analysis-entry { margin-left: 8px; margin-bottom: 6px; }

    @media (max-width: 900px) {
        table.analysis-table { min-width: 900px; font-size: 13px; border-spacing: 8px; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Controls bar (compact)
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
    with col1:
        view_scope = st.selectbox(
            "Scope", ["All Tasks", "Current Month", "Archived Only"], index=0)
    with col2:
        status_filter = st.multiselect("Status", ["todo", "inprogress", "pending", "completed"],
                                       default=["todo", "inprogress", "pending", "completed"])
    with col3:
        priority_filter = st.multiselect("Priority", ["low", "medium", "high", "urgent"],
                                         default=["low", "medium", "high", "urgent"])
    with col4:
        items_per_page = st.selectbox(
            "Rows/page", [10, 20, 50, "All"], index=1)
    with col5:
        search_query = st.text_input(
            "Search", help="Search across title, issue, analysis, timeline, resolution")

    # Load data (same as previous logic)
    with LoaderContext("Loading tasks for table view...", "inline"):
        if view_scope == "Current Month":
            tasks = await dashboard_manager.get_current_month_user_tasks()
        elif view_scope == "Archived Only":
            tasks = await dashboard_manager.get_archived_user_tasks()
        else:
            current_tasks = await dashboard_manager.get_user_tasks()
            archived_tasks = await dashboard_manager.get_archived_user_tasks()
            tasks = current_tasks + archived_tasks

        from app.core.interface.task_notes_interface import (
            get_task_issue, get_task_resolution, get_task_progress_notes
        )

        enhanced_tasks = []
        for task in tasks:
            task_issue = await get_task_issue(task.id)
            task_resolution = await get_task_resolution(task.id)
            progress_notes = await get_task_progress_notes(task.id) or []
            enhanced_tasks.append({
                "task": task,
                "issue": task_issue,
                "resolution": task_resolution,
                "progress_notes": progress_notes,
                "notes_count": len(progress_notes)
            })

    # Check if any tasks have meaningful analysis content (moved here to avoid UnboundLocalError)
    has_any_analysis = False
    for e in enhanced_tasks:
        notes = e['progress_notes'] or []
        for note in notes:
            a = getattr(note, 'analysis_content', '') or ''
            if a.strip() and a.strip() != "Progress note - analysis pending":
                has_any_analysis = True
                break
        if has_any_analysis:
            break
    
    # Apply filters and search
    def _matches_search(e_task):
        if not search_query:
            return True
        s = search_query.lower()
        t = e_task['task']
        fields = [
            t.title or "",
            t.description or "",
            (e_task['issue'].issue_description if e_task['issue'] else "") or "",
            (e_task['resolution'].resolution_notes if e_task['resolution'] else "") or ""
        ]
        for note in e_task['progress_notes']:
            fields.append((note.timeline_content or "") +
                          " " + (note.analysis_content or ""))
        combined = " ".join(fields).lower()
        return s in combined

    filtered = [
        e for e in enhanced_tasks
        if e['task'].status in status_filter and e['task'].priority in priority_filter and _matches_search(e)
    ]

    if not filtered:
        st.info("No tasks found for the current filters/search.")
        return

    # Pagination
    if items_per_page != "All":
        per_page = items_per_page
        total_pages = math.ceil(len(filtered) / per_page)
        if 'analysis_table_page' not in st.session_state:
            st.session_state.analysis_table_page = 1

        colp1, colp2, colp3 = st.columns([1, 2, 1])
        with colp1:
            if st.button("◀ Prev", disabled=st.session_state.analysis_table_page <= 1):
                st.session_state.analysis_table_page -= 1
                st.rerun()
        with colp2:
            st.markdown(
                f"<div style='text-align:center; padding:6px;'>Page {st.session_state.analysis_table_page} / {total_pages}</div>", unsafe_allow_html=True)
        with colp3:
            if st.button("Next ▶", disabled=st.session_state.analysis_table_page >= total_pages):
                st.session_state.analysis_table_page += 1
                st.rerun()

        start = (st.session_state.analysis_table_page - 1) * per_page
        display_set = filtered[start:start + per_page]
    else:
        display_set = filtered

    # Build flat DataFrame for export
    export_rows = []
    for e in display_set:
        t = e['task']
        if e['progress_notes']:
            for note in e['progress_notes']:
                # Get analysis content, but exclude default placeholder
                analysis_content = getattr(note, "analysis_content", "") or ""
                if analysis_content.strip() == "Progress note - analysis pending":
                    analysis_content = ""
                
                row_data = {
                    "task_id": t.id,
                    "task_title": t.title,
                    "task_status": t.status,
                    "task_priority": t.priority,
                    "issue": getattr(e['issue'], "issue_description", "") if e['issue'] else "",
                    "timeline": getattr(note, "timeline_content", "") or "",
                    "note_date": getattr(note, "note_date", "").strftime("%Y-%m-%d") if getattr(note, "note_date", None) else "",
                    "resolution": getattr(e['resolution'], "resolution_notes", "") if e['resolution'] else ""
                }
                
                # Only include analysis column if there's meaningful analysis content in the dataset
                if has_any_analysis:
                    row_data["analysis"] = analysis_content
                
                export_rows.append(row_data)
        else:
            row_data = {
                "task_id": t.id,
                "task_title": t.title,
                "task_status": t.status,
                "task_priority": t.priority,
                "issue": getattr(e['issue'], "issue_description", "") if e['issue'] else "",
                "timeline": "",
                "note_date": "",
                "resolution": getattr(e['resolution'], "resolution_notes", "") if e['resolution'] else ""
            }
            
            # Only include analysis column if there's meaningful analysis content in the dataset
            if has_any_analysis:
                row_data["analysis"] = ""
            
            export_rows.append(row_data)

    df_export = pd.DataFrame(export_rows)
    csv_bytes = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Export CSV", csv_bytes,
                       file_name="task_analysis_export.csv", mime="text/csv")

    # has_any_analysis is now calculated earlier in the function
    
    # Build HTML table with rowspan for merged task cells — now grouping progress notes by date
    table_html = [
        '<div class="table-wrapper"><table class="analysis-table"><thead>']
    table_html.append('<tr>')
    table_html.append('<th class="col-task">Task Name</th>')
    table_html.append('<th class="col-issue">Issue</th>')
    
    # Only show analysis column if there's meaningful analysis content
    if has_any_analysis:
        table_html.append('<th class="col-analysis">Analysis</th>')
    
    table_html.append('<th class="col-timeline">Timeline</th>')
    table_html.append('<th class="col-res">Resolution</th>')
    table_html.append('</tr></thead><tbody>')

    # Helper to escape content
    from html import escape as _esc

    for e in display_set:
        t = e['task']
        notes = e['progress_notes'] or []

        # Group notes by date (multiple notes on same date will be combined into one timeline row)
        groups = {}
        for note in notes:
            note_date = getattr(note, 'note_date', None)
            key = note_date.strftime('%Y-%m-%d') if note_date else 'undated'
            groups.setdefault(key, []).append(note)

        # Sort groups by date descending (latest first)
        sorted_keys = sorted(groups.keys(), reverse=True)
        # If there were no notes, ensure we still show one row
        if not sorted_keys:
            sorted_keys = ['']

        n = max(1, len(sorted_keys))

        # prepare escaped task-level fields
        task_title = _esc(t.title or "")
        task_meta = f"ID: {_esc(str(t.id))} &nbsp; <span class='badge badge-status'>{_esc(t.status)}</span> <span class='badge badge-priority'>{_esc(t.priority)}</span>"
        issue_text = _esc(getattr(e['issue'], "issue_description", "") or "")
        resolution_text = _esc(
            getattr(e['resolution'], "resolution_notes", "") or "")

        if notes:
            for idx, key in enumerate(sorted_keys):
                group_notes = groups[key]
                # Prepare combined analysis (join per-note analysis) - only show if not empty
                analysis_parts = []
                for gn in group_notes:
                    a = getattr(gn, 'analysis_content', '') or ''
                    # Skip default placeholder text and empty content
                    if a.strip() and a.strip() != "Progress note - analysis pending":
                        analysis_parts.append(
                            f"<div class='analysis-entry'>{_esc(a).replace('\n', '<br>')}</div>")
                analysis_html = ''.join(
                    analysis_parts) if analysis_parts else '<small style="color:#9aa2af;">—</small>'

                # Prepare combined timeline entries for the date group
                timeline_parts = []
                for gn in group_notes:
                    tl = getattr(gn, 'timeline_content', '') or ''
                    if tl.strip():
                        # Keep user's formatting newlines but escape
                        timeline_parts.append(
                            f"<div class='timeline-entry'>• {_esc(tl).replace('\n', '<br>')}</div>")
                timeline_html = ''.join(
                    timeline_parts) if timeline_parts else '<small style="color:#9aa2af;">—</small>'

                # Human-readable date label
                if key and key != 'undated':
                    from datetime import datetime
                    try:
                        dt = datetime.strptime(key, '%Y-%m-%d')
                        date_label = dt.strftime('%A, %b %d, %Y')
                    except Exception:
                        date_label = key
                else:
                    date_label = 'Undated'

                # Check if we have any meaningful analysis content for this date group
                has_analysis_content = any(analysis_parts)
                
                # First row: include task cell + issue + analysis (if column exists) + timeline + resolution
                if idx == 0:
                    row = "<tr>"
                    row += f"<td class='task-cell' rowspan='{n}'><div>{task_title}</div><div class='task-meta'>{task_meta}</div></td>"
                    row += f"<td class='issue-cell' rowspan='{n}'><div class='cell-content'>{issue_text or '<small style=\"color:#9aa2af;\">—</small>'}</div></td>"
                    
                    # Only include analysis column if the table has analysis column
                    if has_any_analysis:
                        if has_analysis_content:
                            row += f"<td class='analysis-cell'><div class='cell-content'><div class='timeline-date-group'><div class='timeline-date-title'>{_esc(date_label)}</div>{analysis_html}</div></div></td>"
                        else:
                            row += f"<td class='analysis-cell'><div class='cell-content'><div class='timeline-date-group'><div class='timeline-date-title'>{_esc(date_label)}</div><small style=\"color:#9aa2af;\">—</small></div></div></td>"
                    
                    row += f"<td class='timeline-cell'><div class='cell-content'><div class='timeline-date-group'><div class='timeline-date-title'>{_esc(date_label)}</div>{timeline_html}</div></div></td>"
                    row += f"<td class='res-cell' rowspan='{n}'><div class='cell-content'>{resolution_text or '<small style=\"color:#9aa2af;\">—</small>'}</div></td>"
                    row += "</tr>"
                    table_html.append(row)
                else:
                    # subsequent date-group rows: only analysis (if column exists) + timeline
                    row = "<tr>"
                    
                    # Only include analysis column if the table has analysis column
                    if has_any_analysis:
                        if has_analysis_content:
                            row += f"<td class='analysis-cell'><div class='cell-content'><div class='timeline-date-group'><div class='timeline-date-title'>{_esc(date_label)}</div>{analysis_html}</div></div></td>"
                        else:
                            row += f"<td class='analysis-cell'><div class='cell-content'><div class='timeline-date-group'><div class='timeline-date-title'>{_esc(date_label)}</div><small style=\"color:#9aa2af;\">—</small></div></div></td>"
                    
                    row += f"<td class='timeline-cell'><div class='cell-content'><div class='timeline-date-group'><div class='timeline-date-title'>{_esc(date_label)}</div>{timeline_html}</div></div></td>"
                    row += "</tr>"
                    table_html.append(row)
        else:
            # No notes: single row with empty analysis/timeline
            row = "<tr>"
            row += f"<td class='task-cell'><div>{task_title}</div><div class='task-meta'>{task_meta}</div></td>"
            row += f"<td class='issue-cell'><div class='cell-content'>{issue_text or '<small style=\"color:#9aa2af;\">—</small>'}</div></td>"
            
            # Only include analysis column if the table has analysis column
            if has_any_analysis:
                row += f"<td class='analysis-cell'><div class='cell-content'><small style=\"color:#9aa2af;\">No analysis</small></div></td>"
            
            row += f"<td class='timeline-cell'><div class='cell-content'><small style=\"color:#9aa2af;\">No timeline</small></div></td>"
            row += f"<td class='res-cell'><div class='cell-content'>{resolution_text or '<small style=\"color:#9aa2af;\">—</small>'}</div></td>"
            row += "</tr>"
            table_html.append(row)

    table_html.append("</tbody></table></div>")
    table_final = "".join(table_html)
    st.markdown(table_final, unsafe_allow_html=True)

    # Small legend / tips
    analysis_note = " The Analysis column is hidden when no meaningful analysis content exists." if not has_any_analysis else ""
    st.markdown(f"""
    <div style="margin-top:0.5rem; font-size:13px; color:#6b7280;">
        <strong>Tips:</strong> The task name, issue and resolution are merged vertically and the Timeline column is grouped by date — multiple notes from the same date are displayed under a single date header.{analysis_note}
        Use the Export button to download the flattened CSV for editing in Excel.
    </div>
    """, unsafe_allow_html=True)
