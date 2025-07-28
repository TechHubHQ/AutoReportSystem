import streamlit as st
from app.ui.navbar import navbar


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
    .template-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    navbar(go_to_page, "template_designer")

    st.markdown("""
    <div class="template-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🎨 Template Designer</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Create and customize report templates for your automated reports</p>
    </div>
    """, unsafe_allow_html=True)

    # Template selection
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Templates")
        templates = ["Monthly Report", "Weekly Summary",
                     "Daily Analytics", "Custom Template"]
        selected_template = st.selectbox("Select Template", templates)

        if st.button("➕ New Template", use_container_width=True):
            st.info("New template creation feature coming soon!")

        if st.button("📥 Import Template", use_container_width=True):
            st.info("Template import feature coming soon!")

    with col2:
        st.subheader("✏️ Template Editor")

        # Template name
        template_name = st.text_input("Template Name", value=selected_template)

        # Template content
        template_content = st.text_area(
            "Template Content",
            height=300,
            value=f"""# {selected_template}

## Summary
This is a sample template for {selected_template.lower()}.

## Key Metrics
- Metric 1: {{metric_1}}
- Metric 2: {{metric_2}}
- Metric 3: {{metric_3}}

## Analysis
{{analysis_content}}

## Recommendations
{{recommendations}}

---
Generated on: {{date}}
"""
        )

        # Template settings
        st.subheader("🔧 Template Settings")
        col3, col4 = st.columns(2)
        with col3:
            st.selectbox("Output Format", ["HTML", "PDF", "Markdown"])
            st.checkbox("Include Charts", value=True)
        with col4:
            st.selectbox("Color Theme", [
                         "Default", "Blue", "Green", "Corporate"])
            st.checkbox("Auto-generate summary", value=False)

        # Action buttons
        col5, col6, col7 = st.columns(3)
        with col5:
            if st.button("💾 Save Template", type="primary", use_container_width=True):
                st.success(f"Template '{template_name}' saved successfully!")
        with col6:
            if st.button("👁️ Preview", use_container_width=True):
                st.info("Preview feature coming soon!")
        with col7:
            if st.button("🗑️ Delete", use_container_width=True):
                st.warning("Delete confirmation required!")
