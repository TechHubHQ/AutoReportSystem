import streamlit as st
import pandas as pd
from datetime import datetime
import asyncio
from app.security.route_protection import RouteProtection
from app.ui.navbar import navbar
from app.core.interface.template_interface import TemplateInterface, get_templates, update_template, delete_template
from app.core.utils.template_validator import TemplateValidator
from app.integrations.git.auto_commit import GitAutoCommit
from app.integrations.git.config import is_auto_commit_enabled, is_auto_push_enabled


def apply_custom_css():
    """Apply custom CSS for modern UI styling"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }

    .template-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e1e5e9;
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .template-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }

    .template-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #eee;
    }

    .template-meta {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        color: #666;
    }

    .category-badge {
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .code-editor {
        background: #f8f9fa;
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    }

    .preview-container {
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        height: 500px;
        overflow: auto;
        background: white;
    }

    .template-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 0 1.5rem;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e1e5e9;
        text-align: center;
    }

    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)


def render_template_preview(html_content: str):
    """Render HTML template preview"""
    if html_content.strip():
        # Clean and prepare HTML for preview
        try:
            # For security, we'll show the HTML in an iframe-like container
            # In production, you might want to sanitize the HTML more thoroughly
            st.components.v1.html(html_content, height=500, scrolling=True)
        except Exception as e:
            st.error(f"Error rendering preview: {str(e)}")
    else:
        st.info("No content to preview")


def render_git_status():
    """Render Git status information"""
    try:
        git_client = GitAutoCommit()
        
        # Check if Git is available and auto-commit is enabled
        is_git_repo = git_client.is_git_repository()
        auto_commit_enabled = is_auto_commit_enabled()
        auto_push_enabled = is_auto_push_enabled()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if is_git_repo:
                st.success("🔗 Git Repository")
            else:
                st.warning("⚠️ Not a Git Repository")
        
        with col2:
            if auto_commit_enabled:
                st.success("✅ Auto-Commit Enabled")
            else:
                st.info("ℹ️ Auto-Commit Disabled")
        
        with col3:
            if auto_push_enabled:
                st.success("🚀 Auto-Push Enabled")
            else:
                st.info("📝 Auto-Push Disabled")
        
        # Show Git status if it's a repository
        if is_git_repo:
            status = git_client.get_git_status()
            if status['success'] and status['has_changes']:
                st.warning(f"⚠️ Uncommitted changes: {len(status['modified_files'])} modified, {len(status['new_files'])} new, {len(status['deleted_files'])} deleted")
            elif status['success']:
                st.success("✅ Working directory clean")
    
    except Exception as e:
        st.error(f"❌ Error checking Git status: {str(e)}")


def render_template_list():
    """Render the list of existing templates"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📄 Existing Templates")
    with col2:
        if st.button("🔄 Sync Files", help="Sync template files with database"):
            try:
                asyncio.run(TemplateInterface.sync_templates_from_files())
                st.success("✅ Templates synced successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error syncing templates: {str(e)}")
    
    # Show Git status
    with st.expander("🔗 Git Integration Status", expanded=False):
        render_git_status()

    try:
        templates = asyncio.run(get_templates())

        if not templates:
            st.info("No templates found. Create your first template!")
            return

        # Template statistics
        st.markdown('<div class="stats-container">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number" style="color: #667eea;">{len(templates)}</div>
                <div class="stat-label">Total Templates</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            active_templates = len([t for t in templates if t.is_active])
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number" style="color: #6bcf7f;">{active_templates}</div>
                <div class="stat-label">Active Templates</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            categories = len(set(getattr(t, 'category', 'General')
                             for t in templates))
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number" style="color: #4fc3f7;">{categories}</div>
                <div class="stat-label">Categories</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            recent_templates = len([t for t in templates if (
                datetime.now() - t.created_at).days <= 7])
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number" style="color: #ffd93d;">{recent_templates}</div>
                <div class="stat-label">Created This Week</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Templates list
        for template in templates:
            with st.container():
                st.markdown(f"""
                <div class="template-card">
                    <div class="template-header">
                        <div>
                            <h3 style="margin: 0; color: #333;">{template.name}</h3>
                            <p style="margin: 0.5rem 0 0 0; color: #666;">{getattr(template, 'description', '')}</p>
                        </div>
                        <div class="category-badge">{getattr(template, 'category', 'General')}</div>
                    </div>
                    <div class="template-meta">
                        <span>📅 Created: {template.created_at.strftime('%Y-%m-%d')}</span>
                        <span>🔄 Updated: {template.updated_at.strftime('%Y-%m-%d')}</span>
                        <span>📊 Status: {'Active' if template.is_active else 'Inactive'}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Template actions
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("👁️ Preview", key=f"preview_{template.id}"):
                        st.session_state.preview_template = template

                with col2:
                    if st.button("✏️ Edit", key=f"edit_{template.id}"):
                        st.session_state.edit_template = template

                with col3:
                    if st.button("📋 Code", key=f"code_{template.id}"):
                        st.session_state.show_code = template

                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{template.id}", type="secondary"):
                        if st.session_state.get(f"confirm_delete_{template.id}", False):
                            try:
                                asyncio.run(delete_template(template.id))
                                st.success(
                                    f"✅ Template '{template.name}' deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(
                                    f"❌ Error deleting template: {str(e)}")
                        else:
                            st.session_state[f"confirm_delete_{template.id}"] = True
                            st.warning("⚠️ Click delete again to confirm")

        # Preview modal
        if st.session_state.get("preview_template"):
            template = st.session_state.preview_template
            with st.expander(f"🔍 Preview: {template.name}", expanded=True):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("**HTML Code:**")
                    st.code(template.html_content, language='html')

                with col2:
                    st.markdown("**Preview:**")
                    render_template_preview(template.html_content)

                if st.button("Close Preview"):
                    st.session_state.preview_template = None
                    st.rerun()

        # Show code modal
        if st.session_state.get("show_code"):
            template = st.session_state.show_code
            with st.expander(f"📋 HTML Code: {template.name}", expanded=True):
                st.code(template.html_content, language='html')

                if st.download_button(
                    label="📥 Download HTML",
                    data=template.html_content,
                    file_name=f"{template.name.replace(' ', '_').lower()}.html",
                    mime="text/html"
                ):
                    st.success("✅ Template downloaded!")

                if st.button("Close Code View"):
                    st.session_state.show_code = None
                    st.rerun()

        # Edit template modal
        if st.session_state.get("edit_template"):
            template = st.session_state.edit_template
            with st.expander(f"✏️ Edit Template: {template.name}", expanded=True):
                with st.form("edit_template_form"):
                    new_name = st.text_input(
                        "Template Name", value=template.name)
                    new_description = st.text_area(
                        "Description", value=getattr(template, 'description', ''))
                    new_category = st.text_input(
                        "Category", value=getattr(template, 'category', 'General'))

                    st.markdown("**HTML Content:**")
                    new_html_content = st.text_area(
                        "HTML Code",
                        value=template.html_content,
                        height=300,
                        help="Enter your HTML template code here"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.form_submit_button("💾 Update Template", type="primary"):
                            try:
                                asyncio.run(update_template(
                                    template.id,
                                    name=new_name.strip(),
                                    subject=new_name.strip(),
                                    html_content=new_html_content.strip()
                                ))
                                st.session_state.edit_template = None
                                st.success("✅ Template updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(
                                    f"❌ Error updating template: {str(e)}")

                    with col2:
                        if st.form_submit_button("👁️ Preview"):
                            if new_html_content.strip():
                                st.markdown("**Preview:**")
                                render_template_preview(new_html_content)

                    with col3:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.edit_template = None
                            st.rerun()

    except Exception as e:
        st.error(f"❌ Error loading templates: {str(e)}")


def render_create_template():
    """Render the create new template interface"""
    st.markdown("### ➕ Create New Template")

    with st.form("create_template_form"):
        # Template basic info
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Template Name *", placeholder="e.g., Monthly Report Template")

        with col2:
            category = st.text_input(
                "Category", placeholder="e.g., Reports, Status, Analytics")

        description = st.text_area(
            "Description", placeholder="Brief description of what this template is used for")

        # HTML content with tabs for code and preview
        st.markdown("**HTML Content:**")

        # Predefined templates dropdown
        template_presets = {
            "Blank Template": "",
            "Basic Report": """<!DOCTYPE html>
<html>
<head>
    <title>{{title}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{report_title}}</h1>
        <p>{{date}}</p>
    </div>
    <div class="content">
        <p>{{content}}</p>
    </div>
</body>
</html>""",
            "Dashboard Template": """<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{dashboard_title}}</h1>
            <p>{{period}}</p>
        </div>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{{metric1_value}}</div>
                <div>{{metric1_label}}</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{metric2_value}}</div>
                <div>{{metric2_label}}</div>
            </div>
        </div>
    </div>
</body>
</html>""",
            "Email Template": """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{subject}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .email-container { max-width: 600px; margin: 0 auto; background: white; }
        .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px; }
        .footer { background: #ecf0f1; padding: 20px; text-align: center; font-size: 0.9em; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{{header_title}}</h1>
        </div>
        <div class="content">
            <h2>{{content_title}}</h2>
            <p>{{message_body}}</p>
            <p><a href="{{action_link}}" class="button">{{action_text}}</a></p>
        </div>
        <div class="footer">
            <p>{{footer_text}}</p>
        </div>
    </div>
</body>
</html>"""
        }

        preset_choice = st.selectbox(
            "Start with a preset:", list(template_presets.keys()))

        html_content = st.text_area(
            "HTML Code",
            value=template_presets[preset_choice],
            height=400,
            help="Enter your HTML template code. Use {{variable_name}} for content placeholders."
        )

        # Form buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            submit_button = st.form_submit_button(
                "🚀 Create Template", type="primary")

        with col2:
            preview_button = st.form_submit_button("👁️ Preview")
            validate_button = st.form_submit_button("✅ Validate")

        with col3:
            clear_button = st.form_submit_button("🗑️ Clear Form")

        if submit_button:
            if name.strip() and html_content.strip():
                # Validate template before creating
                validation_result = TemplateValidator.validate_template(
                    html_content.strip())

                if not validation_result['is_valid']:
                    st.error("❌ Cannot create template with validation errors:")
                    for error in validation_result['errors']:
                        st.error(f"- {error}")
                else:
                    try:
                        user = RouteProtection.get_current_user()
                        user_id = user.get('id') if user else None

                        new_template = asyncio.run(TemplateInterface.create_template(
                            name=name.strip(),
                            html_content=html_content.strip(),
                            description=description.strip(),
                            category=category.strip() or "General",
                            user_id=user_id
                        ))

                        st.success("✅ Template created successfully!")
                        st.balloons()

                        # Clear form
                        st.session_state.clear_form = True
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error creating template: {str(e)}")
            else:
                st.error(
                    "❌ Please provide at least a template name and HTML content")

        if preview_button and html_content.strip():
            st.markdown("---")
            st.markdown("### 🔍 Template Preview")
            render_template_preview(html_content)

        if validate_button and html_content.strip():
            st.markdown("---")
            st.markdown("### ✅ Template Validation")
            validation_result = TemplateValidator.validate_template(
                html_content)

            if validation_result['is_valid']:
                st.success("✅ Template is valid and ready to use!")
            else:
                st.error("❌ Template has the following errors:")
                for error in validation_result['errors']:
                    st.error(f"- {error}")

            if validation_result['warnings']:
                st.warning("⚠️ Warnings:")
                for warning in validation_result['warnings']:
                    st.warning(f"- {warning}")

            # Show template statistics
            stats = validation_result['stats']
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Characters", stats['character_count'])
            with col2:
                st.metric("Lines", stats['line_count'])
            with col3:
                st.metric("Variables", stats['variable_count'])
            with col4:
                st.metric("Unique Variables", stats['unique_variables'])

            # Show variables found
            if validation_result['variables']:
                st.markdown("**Template Variables:**")
                variables_df = pd.DataFrame({
                    'Variable': [f"{{{{{var}}}}}" for var in set(validation_result['variables'])],
                    'Usage Count': [validation_result['variables'].count(var) for var in set(validation_result['variables'])]
                })
                st.dataframe(
                    variables_df, use_container_width=True, hide_index=True)

        if clear_button:
            st.rerun()


def render_template_help():
    """Render help and documentation for template creation"""
    st.markdown("### 📚 Template Help & Documentation")

    # Help sections
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🎯 Getting Started", "🔧 Variables", "🎨 Styling Tips", "📖 Examples"])

    with tab1:
        st.markdown("""
        #### Getting Started with Templates

        Templates are HTML documents with placeholder variables that get replaced with actual data when generating reports.

        **Basic Structure:**
        - Use standard HTML5 structure
        - Include CSS styles in the `<head>` section
        - Use `{{variable_name}}` for content
        - Test your template with the preview function

        **Best Practices:**
        - Keep templates responsive for different screen sizes
        - Use semantic HTML elements
        - Include fallback fonts
        - Optimize for both screen and print media
        """)

        with tab2:
            st.markdown("""
            #### Variables

            You can use double curly braces `{{ }}` to insert variables into your HTML templates. These variables will be replaced with actual data during report generation.

            **Examples:**
            - `{{report_title}}`
            - `{{date}}`
            - `{{total_sales}}`
            - `{{user_name}}`

            **Loops and Conditionals (for template engines that support them):**
            - Use `{{#items}} ... {{/items}}` for looping over a list
            - Use `{{^items}}` for checking if a list is empty (inverted section)

            **Tips:**
            - Ensure variable names match exactly with your data keys
            - Avoid using special characters or spaces in variable names
            """)

    with tab3:
        st.markdown("""
        #### Styling Tips

        Good styling enhances readability and professionalism. Use the `<style>` tag in your `<head>` section for custom CSS.

        **Suggestions:**
        - Use web-safe fonts (`Arial`, `Segoe UI`, `Verdana`)
        - Stick to a consistent color scheme
        - Use `padding` and `margin` to space out elements
        - Apply box-shadow and border-radius for modern card designs
        - Use CSS grid or flexbox for layout management

        **Responsive Design:**
        - Use percentage-based widths or `max-width` for containers
        - Add `@media` queries for small screens
        """)

    with tab4:
        st.markdown("""
        #### Template Examples

        **Sales Report Template:**
        ```html
        <div class="metric-card">
            <h3>Total Revenue</h3>
            <p>${{total_revenue}}</p>
        </div>
        ```

        **Task List Template:**
        ```html
        {{#tasks}}
        <li>{{task_name}} - {{status}}</li>
        {{/tasks}}
        ```

        **Project Status Template:**
        ```html
        <div>
            <h2>Status: {{project_status}}</h2>
            <p>{{status_description}}</p>
        </div>
        ```

        **Tip:**
        Combine variables with loops to create advanced, data-driven layouts!
        """)


def render_template_variables():
    """Show available template variables and their usage"""
    st.markdown("### 🔢 Template Variables Reference")

    # Common variables
    variables_data = {
        "Basic Variables": [
            {"Variable": "{{title}}", "Description": "Document title",
                "Example": "Monthly Report"},
            {"Variable": "{{date}}", "Description": "Current date",
                "Example": "2024-01-15"},
            {"Variable": "{{user_name}}",
                "Description": "Current user name", "Example": "John Doe"},
            {"Variable": "{{company_name}}",
                "Description": "Company name", "Example": "Acme Corp"},
        ],
        "Report Variables": [
            {"Variable": "{{report_title}}", "Description": "Report title",
                "Example": "Sales Analysis"},
            {"Variable": "{{period}}",
                "Description": "Report period", "Example": "Q1 2024"},
            {"Variable": "{{total_revenue}}",
                "Description": "Total revenue amount", "Example": "$125,000"},
            {"Variable": "{{growth_rate}}",
                "Description": "Growth percentage", "Example": "15.5"},
        ],
        "Task Variables": [
            {"Variable": "{{task_name}}", "Description": "Task name",
                "Example": "Complete project"},
            {"Variable": "{{task_status}}",
                "Description": "Task status", "Example": "In Progress"},
            {"Variable": "{{due_date}}", "Description": "Task due date",
                "Example": "2024-02-01"},
            {"Variable": "{{priority}}",
                "Description": "Task priority", "Example": "High"},
        ]
    }

    for category, variables in variables_data.items():
        st.markdown(f"#### {category}")
        df = pd.DataFrame(variables)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("---")


def template_designer(go_to_page=None):
    """Main entry point for the Template Designer UI, rendering all sections."""
    from app.ui.navbar import navbar

    # Add navbar
    if go_to_page:
        navbar(go_to_page, "template_designer")

    apply_custom_css()
    st.markdown('<div class="main-header"><h1>🖌️ Template Designer</h1><p>Create, edit, and manage your report templates</p></div>', unsafe_allow_html=True)
    tabs = st.tabs(["Templates", "Create New", "Help & Docs"])
    with tabs[0]:
        render_template_list()
    with tabs[1]:
        render_create_template()
    with tabs[2]:
        render_template_help()
        render_template_variables()
