import streamlit as st
from app.ui.navbar import navbar


def template_designer(go_to_page):
    """Template designer page with navbar"""
    navbar(go_to_page, "template_designer")

    st.markdown("# 🎨 Template Designer")
    st.markdown(
        "Create and customize report templates for your automated reports.")

    st.divider()

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
