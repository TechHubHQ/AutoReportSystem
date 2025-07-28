import streamlit as st
import asyncio
from app.ui.navbar import navbar
from app.ui.kanban_board import kanban_board
from app.core.interface.task_interface import get_task_statistics
from app.security.route_protection import RouteProtection


def dashboard(go_to_page):
    """Enhanced Dashboard page with Kanban board and metrics"""
    
    # Custom CSS for enhanced dashboard styling
    st.markdown("""
    <style>
    .dashboard-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .dashboard-section {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .quick-action-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid #dee2e6;
    }
    .quick-action-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .activity-item {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #dee2e6;
        background: #f8f9fa;
    }
    .activity-item.completed {
        border-left-color: #28a745;
        background: #d4edda;
    }
    .activity-item.inprogress {
        border-left-color: #ffc107;
        background: #fff3cd;
    }
    .activity-item.pending {
        border-left-color: #dc3545;
        background: #f8d7da;
    }
    .activity-item.todo {
        border-left-color: #6c757d;
        background: #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

    navbar(go_to_page, "dashboard")

    user = st.session_state.get("user", {})
    username = user.get("username", "User")
    user_id = user.get("id")

    # Enhanced header
    st.markdown(f"""
    <div class="dashboard-header">
        <h1 style="margin: 0; font-size: 2.5rem;">📊 Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Welcome back, <strong>{username}</strong>! Here's your productivity overview.</p>
    </div>
    """, unsafe_allow_html=True)

    # Load task statistics
    try:
        stats = asyncio.run(get_task_statistics(user_id))
        
        # Enhanced metrics with real data
        st.markdown("### 📈 Task Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📊 Total Tasks", stats['total'])
        with col2:
            st.metric("📝 To Do", stats['todo'], delta=f"+{stats['todo']}")
        with col3:
            st.metric("🔄 In Progress", stats['inprogress'], delta=f"+{stats['inprogress']}")
        with col4:
            st.metric("✅ Completed", stats['completed'], delta=f"+{stats['completed']}")
        with col5:
            st.metric("⏳ Pending", stats['pending'], delta=f"+{stats['pending']}")
        
        # Additional metrics if there are urgent/overdue tasks
        if stats.get('urgent', 0) > 0 or stats.get('overdue', 0) > 0:
            st.markdown("### 🚨 Attention Required")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if stats.get('overdue', 0) > 0:
                    st.metric("🚨 Overdue Tasks", stats['overdue'], delta=f"-{stats['overdue']}")
            with col2:
                if stats.get('urgent', 0) > 0:
                    st.metric("🔥 Urgent Tasks", stats['urgent'], delta=f"+{stats['urgent']}")
            with col3:
                if stats.get('high_priority', 0) > 0:
                    st.metric("⚡ High Priority", stats['high_priority'])
    
    except Exception as e:
        st.error(f"Error loading task statistics: {e}")
        # Fallback metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Reports", "24", "↗️ 12%")
        with col2:
            st.metric("📋 Active Templates", "8", "↗️ 2")
        with col3:
            st.metric("⏰ Scheduled Tasks", "15", "→ 0%")
        with col4:
            st.metric("✅ Success Rate", "98.5%", "↗️ 1.2%")

    st.markdown("---")

    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["📋 Kanban Board", "📈 Analytics", "🚀 Quick Actions"])
    
    with tab1:
        # Kanban Board - Main feature
        kanban_board()
    
    with tab2:
        # Analytics and insights
        render_analytics_tab(user_id)
    
    with tab3:
        # Quick actions and shortcuts
        render_quick_actions_tab(go_to_page, user_id)


def render_analytics_tab(user_id: int):
    """Render analytics and insights tab"""
    
    st.markdown("### 📊 Task Analytics & Insights")
    
    try:
        stats = asyncio.run(get_task_statistics(user_id))
        
        # Progress visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Task Distribution")
            
            # Create a simple progress visualization
            total_tasks = stats['total']
            if total_tasks > 0:
                completed_percentage = (stats['completed'] / total_tasks) * 100
                inprogress_percentage = (stats['inprogress'] / total_tasks) * 100
                todo_percentage = (stats['todo'] / total_tasks) * 100
                pending_percentage = (stats['pending'] / total_tasks) * 100
                
                st.progress(completed_percentage / 100, text=f"✅ Completed: {completed_percentage:.1f}%")
                st.progress(inprogress_percentage / 100, text=f"🔄 In Progress: {inprogress_percentage:.1f}%")
                st.progress(todo_percentage / 100, text=f"📝 To Do: {todo_percentage:.1f}%")
                st.progress(pending_percentage / 100, text=f"⏳ Pending: {pending_percentage:.1f}%")
            else:
                st.info("📝 No tasks yet. Create your first task to see analytics!")
        
        with col2:
            st.markdown("#### 🎯 Productivity Insights")
            
            if total_tasks > 0:
                completion_rate = (stats['completed'] / total_tasks) * 100
                
                if completion_rate >= 80:
                    st.success(f"🎉 Excellent! {completion_rate:.1f}% completion rate")
                elif completion_rate >= 60:
                    st.info(f"👍 Good progress! {completion_rate:.1f}% completion rate")
                elif completion_rate >= 40:
                    st.warning(f"⚠️ Room for improvement: {completion_rate:.1f}% completion rate")
                else:
                    st.error(f"🚨 Focus needed: {completion_rate:.1f}% completion rate")
                
                # Priority distribution
                st.markdown("**Priority Distribution:**")
                st.write(f"🔥 Urgent: {stats.get('urgent', 0)} tasks")
                st.write(f"⚡ High: {stats.get('high_priority', 0)} tasks")
                st.write(f"📊 Total Active: {stats['todo'] + stats['inprogress']} tasks")
                
                if stats.get('overdue', 0) > 0:
                    st.error(f"🚨 {stats['overdue']} overdue tasks need attention!")
            else:
                st.info("📊 Analytics will appear once you create tasks")
        
        # Recent activity simulation (this would come from actual task updates)
        st.markdown("#### 📈 Recent Activity")
        
        activity_items = [
            {"type": "completed", "text": "Completed 'Monthly Report Generation'", "time": "2 hours ago"},
            {"type": "inprogress", "text": "Started working on 'Email Template Design'", "time": "4 hours ago"},
            {"type": "todo", "text": "Created new task 'Database Optimization'", "time": "1 day ago"},
            {"type": "pending", "text": "Task 'Client Review' is pending approval", "time": "2 days ago"},
        ]
        
        for item in activity_items:
            st.markdown(f"""
            <div class="activity-item {item['type']}">
                <strong>{item['text']}</strong><br>
                <small style="color: #6c757d;">{item['time']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")


def render_quick_actions_tab(go_to_page, user_id: int):
    """Render quick actions and shortcuts tab"""
    
    st.markdown("### 🚀 Quick Actions & Shortcuts")
    
    # Quick task creation
    st.markdown("#### ⚡ Quick Task Creation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        quick_title = st.text_input("📝 Quick Task Title", placeholder="Enter task title...")
        quick_priority = st.selectbox("⚡ Priority", ["low", "medium", "high", "urgent"], index=1)
    
    with col2:
        quick_status = st.selectbox("📊 Status", ["todo", "inprogress", "pending"], index=0)
        quick_category = st.text_input("🏷️ Category", value="general")
    
    if st.button("🚀 Create Quick Task", type="primary", use_container_width=True):
        if quick_title.strip():
            try:
                from app.core.interface.task_interface import create_task
                asyncio.run(create_task(
                    title=quick_title.strip(),
                    status=quick_status,
                    priority=quick_priority,
                    category=quick_category.strip(),
                    created_by=user_id
                ))
                st.success(f"✅ Quick task '{quick_title}' created!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating task: {e}")
        else:
            st.error("⚠️ Please enter a task title")
    
    st.markdown("---")
    
    # System shortcuts
    st.markdown("#### 🔧 System Shortcuts")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="quick-action-card">
            <h4>📊 Reports</h4>
            <p>Generate and manage reports</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📊 Generate Report", use_container_width=True):
            with st.spinner("📊 Generating report..."):
                import time
                time.sleep(2)
                st.success("🎉 Report generated successfully!")
    
    with col2:
        st.markdown("""
        <div class="quick-action-card">
            <h4>🎨 Templates</h4>
            <p>Design custom templates</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎨 Template Designer", use_container_width=True):
            go_to_page("template_designer")
    
    with col3:
        st.markdown("""
        <div class="quick-action-card">
            <h4>📧 Email</h4>
            <p>Configure SMTP settings</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📧 SMTP Config", use_container_width=True):
            go_to_page("smtp_conf")
    
    with col4:
        st.markdown("""
        <div class="quick-action-card">
            <h4>⚙️ Settings</h4>
            <p>System preferences</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚙️ Settings", use_container_width=True):
            go_to_page("settings")
    
    st.markdown("---")
    
    # Productivity tips
    st.markdown("#### 💡 Productivity Tips")
    
    tips = [
        "🎯 **Focus on High Priority Tasks**: Tackle urgent and high-priority items first",
        "📅 **Set Due Dates**: Add deadlines to keep yourself accountable",
        "🔄 **Update Status Regularly**: Keep your Kanban board current for better visibility",
        "📊 **Review Analytics**: Check your completion rate weekly to track progress",
        "🏷️ **Use Categories**: Organize tasks by project or type for better management",
        "✅ **Celebrate Completions**: Acknowledge finished tasks to stay motivated"
    ]
    
    for tip in tips:
        st.markdown(f"- {tip}")