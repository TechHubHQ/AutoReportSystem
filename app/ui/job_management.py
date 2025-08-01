import streamlit as st
import asyncio
from app.core.interface.job_interface import JobInterface
from app.core.jobs.discovery import initialize_jobs
from app.security.route_protection import RouteProtection
from app.ui.navbar import navbar


def job_management(go_to_page):
    """Job Management page for tracking active jobs"""

    if not RouteProtection.is_authenticated():
        go_to_page("login")
        return

    navbar(go_to_page)

    st.title("⚙️ Job Management")

    # Initialize jobs on page load
    if st.button("🔄 Refresh Jobs", type="primary"):
        with st.spinner("Discovering jobs..."):
            asyncio.run(initialize_jobs())
        st.success("Jobs refreshed successfully!")
        st.rerun()

    # Load jobs
    jobs = asyncio.run(JobInterface.get_all_jobs())

    if not jobs:
        st.info("No jobs found. Click 'Refresh Jobs' to discover available jobs.")
        return

    st.subheader("📋 Active Jobs")

    # Jobs table
    for job in jobs:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                status_icon = "✅" if job.is_active else "❌"
                st.write(f"{status_icon} **{job.name}**")
                if job.description:
                    st.caption(job.description)

            with col2:
                st.write(f"**Type:** {job.schedule_type}")
                st.write(f"**Function:** {job.function_name}")

            with col3:
                if job.last_run:
                    st.write(
                        f"**Last Run:** {job.last_run.strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.write("**Last Run:** Never")

                if job.next_run:
                    st.write(
                        f"**Next Run:** {job.next_run.strftime('%Y-%m-%d %H:%M')}")

            with col4:
                # Toggle job status
                new_status = st.toggle(
                    "Active",
                    value=job.is_active,
                    key=f"job_toggle_{job.id}"
                )

                if new_status != job.is_active:
                    asyncio.run(JobInterface.update_job_status(
                        job.id, new_status))
                    st.rerun()

            st.divider()

    # Job statistics
    st.subheader("📊 Job Statistics")
    active_jobs = sum(1 for job in jobs if job.is_active)
    inactive_jobs = len(jobs) - active_jobs

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Jobs", len(jobs))
    with col2:
        st.metric("Active Jobs", active_jobs)
    with col3:
        st.metric("Inactive Jobs", inactive_jobs)
