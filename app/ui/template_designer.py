import streamlit as st
import asyncio
from app.ui.navbar import navbar
from app.ui.components.loader import LoaderContext
from app.core.interface.template_interface import create_template, get_templates, get_template, update_template, delete_template
from app.core.jobs.utils.template_loader import load_template_from_string


def template_designer(go_to_page):
    """Template designer page with navbar"""
    st.markdown("""
    <style>
    .template-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .dynamic-help {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    navbar(go_to_page, "template_designer")

    st.markdown("""
    <div class="template-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🎨 Email Template Designer</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Create HTML email templates with dynamic data loading</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'templates' not in st.session_state:
        st.session_state.templates = []
    if 'selected_template_id' not in st.session_state:
        st.session_state.selected_template_id = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

    # Load templates
    try:
        templates = asyncio.run(get_templates())
        st.session_state.templates = templates
    except Exception as e:
        st.error(f"Error loading templates: {e}")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Templates")
        
        # Template list
        if st.session_state.templates:
            template_options = {f"{t.name} (ID: {t.id})": t.id for t in st.session_state.templates}
            selected_option = st.selectbox("Select Template", list(template_options.keys()))
            if selected_option:
                st.session_state.selected_template_id = template_options[selected_option]
        else:
            st.info("No templates found. Create your first template!")

        if st.button("➕ New Template", use_container_width=True):
            st.session_state.edit_mode = False
            st.session_state.selected_template_id = None

        if st.button("✏️ Edit Selected", use_container_width=True, disabled=not st.session_state.selected_template_id):
            st.session_state.edit_mode = True

    with col2:
        st.subheader("✏️ Template Editor")
        
        # Load template data if editing
        template_data = None
        if st.session_state.edit_mode and st.session_state.selected_template_id:
            try:
                template_data = asyncio.run(get_template(st.session_state.selected_template_id))
            except Exception as e:
                st.error(f"Error loading template: {e}")

        # Template form
        template_name = st.text_input(
            "Template Name", 
            value=template_data.name if template_data else ""
        )
        
        template_subject = st.text_input(
            "Email Subject",
            value=template_data.subject if template_data else "Weekly Report - [current_week]",
            help="Use [placeholder] syntax for dynamic content"
        )

        # Dynamic content help
        with st.expander("📖 Dynamic Content Guide"):
            st.markdown("""
            <div class="dynamic-help">
            <strong>Available Dynamic Placeholders:</strong><br>
            • <code>[weekly_tasks]</code> - Current week's tasks<br>
            • <code>[monthly_tasks]</code> - Current month's tasks<br>
            • <code>[accomplishments]</code> - Completed tasks<br>
            • <code>[in_progress]</code> - Tasks in progress<br>
            • <code>[task_stats]</code> - Task statistics<br>
            • <code>[current_date]</code> - Current date<br>
            • <code>[current_week]</code> - Current week<br>
            • <code>[current_month]</code> - Current month
            </div>
            """, unsafe_allow_html=True)

        # HTML template content
        default_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>[current_week] Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .header { color: #2196F3; border-bottom: 2px solid #2196F3; padding-bottom: 10px; }
        .section { margin: 20px 0; }
        .task-list { list-style: none; padding: 0; }
        .task-item { background: #f8f9fa; margin: 5px 0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">Weekly Report - [current_week]</h1>
        
        <div class="section">
            <h2>📊 Task Summary</h2>
            <p>Total Tasks: [task_stats.total]</p>
            <p>Completed: [task_stats.completed]</p>
            <p>In Progress: [task_stats.inprogress]</p>
        </div>
        
        <div class="section">
            <h2>✅ Accomplishments</h2>
            <ul class="task-list">
                {% for task in accomplishments %}
                <li class="task-item">{{ task }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="section">
            <h2>🔄 In Progress</h2>
            <ul class="task-list">
                {% for task in in_progress %}
                <li class="task-item">{{ task }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <p><em>Generated on [current_date]</em></p>
    </div>
</body>
</html>"""
        
        template_content = st.text_area(
            "HTML Template Content",
            height=400,
            value=template_data.html_content if template_data else default_html,
            help="Write HTML with [placeholder] for dynamic content and {{variable}} for Jinja2 loops"
        )

        # Action buttons
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if st.button("💾 Save Template", type="primary", use_container_width=True):
                if template_name and template_subject and template_content:
                    try:
                        user_id = st.session_state.get('user_id', 1)  # Default user for demo
                        if st.session_state.edit_mode and template_data:
                            asyncio.run(update_template(
                                template_data.id, template_name, template_subject, template_content
                            ))
                            st.success(f"Template '{template_name}' updated successfully!")
                        else:
                            asyncio.run(create_template(
                                template_name, template_subject, template_content, user_id
                            ))
                            st.success(f"Template '{template_name}' created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving template: {e}")
                else:
                    st.error("Please fill in all fields")
        
        with col4:
            if st.button("👁️ Preview", use_container_width=True):
                if template_content and template_subject:
                    try:
                        user_id = st.session_state.get('user_id', 1)
                        preview = asyncio.run(load_template_from_string(
                            template_content, template_subject, user_id
                        ))
                        st.subheader("📧 Email Preview")
                        st.write(f"**Subject:** {preview['subject']}")
                        st.components.v1.html(preview['content'], height=400, scrolling=True)
                    except Exception as e:
                        st.error(f"Preview error: {e}")
                else:
                    st.error("Please enter template content")
        
        with col5:
            if st.button("🗑️ Delete", use_container_width=True, disabled=not st.session_state.selected_template_id):
                if st.session_state.selected_template_id:
                    try:
                        asyncio.run(delete_template(st.session_state.selected_template_id))
                        st.success("Template deleted successfully!")
                        st.session_state.selected_template_id = None
                        st.session_state.edit_mode = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting template: {e}")
