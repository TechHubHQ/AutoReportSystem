import streamlit as st
import asyncio
import json
from app.core.interface.job_interface import JobInterface
from app.core.jobs.discovery import initialize_jobs
from app.security.route_protection import RouteProtection
from app.ui.navbar import navbar


def job_management(go_to_page):
    """Job Management page for tracking active jobs"""

    if not RouteProtection.is_authenticated():
        go_to_page("login")
        return

    navbar(go_to_page, "job_management")

    st.title("⚙️ Job Management")

    # Initialize session state
    if "selected_job" not in st.session_state:
        st.session_state.selected_job = None
    if "show_create_modal" not in st.session_state:
        st.session_state.show_create_modal = False

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("➕ Create Job", type="primary"):
            st.session_state.show_create_modal = True
            st.rerun()

    with col2:
        if st.button("🔄 Refresh Jobs"):
            with st.spinner("Discovering jobs..."):
                asyncio.run(initialize_jobs())
            st.success("Jobs refreshed successfully!")
            st.rerun()

    # Create Job Modal
    if st.session_state.show_create_modal:
        with st.expander("➕ Create New Job", expanded=True):
            with st.form("create_job_form"):
                col1, col2 = st.columns(2)
                with col1:
                    job_name = st.text_input("Job Name*")
                    function_name = st.text_input("Function Name*")
                with col2:
                    schedule_type = st.selectbox(
                        "Schedule Type*", ["daily", "weekly", "monthly", "custom"])

                # Schedule configuration based on type
                st.subheader("Schedule Configuration")
                schedule_config = {}

                if schedule_type in ["daily", "weekly", "monthly"]:
                    col_time, col_day = st.columns(2)
                    with col_time:
                        schedule_time = st.time_input(
                            "Execution Time", value=None)
                        if schedule_time:
                            schedule_config["hour"] = schedule_time.hour
                            schedule_config["minute"] = schedule_time.minute

                    if schedule_type == "weekly":
                        with col_day:
                            day_of_week = st.selectbox("Day of Week",
                                                       ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                            schedule_config["day_of_week"] = [
                                "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day_of_week)

                    elif schedule_type == "monthly":
                        with col_day:
                            day_of_month = st.number_input(
                                "Day of Month", min_value=1, max_value=31, value=1)
                            schedule_config["day_of_month"] = day_of_month

                elif schedule_type == "custom":
                    st.info("💡 Cron format: minute hour day month day_of_week")
                    cron_expression = st.text_input(
                        "Cron Expression", placeholder="0 9 * * 1 (Every Monday at 9 AM)")
                    if cron_expression:
                        schedule_config["cron"] = cron_expression

                    with st.expander("Cron Examples"):
                        st.code("""
0 9 * * *     # Daily at 9:00 AM
0 9 * * 1     # Every Monday at 9:00 AM
0 9 1 * *     # First day of every month at 9:00 AM
*/15 * * * *   # Every 15 minutes
0 */2 * * *   # Every 2 hours
                        """)

                description = st.text_area("Description")

                # Job code
                st.subheader("Job Code")
                code = st.text_area("Python Code*", height=200,
                                    value="async def your_job_function():\n    print('Job executed successfully!')\n    # Add your job logic here\n    pass")

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("Create Job", type="primary"):
                        if job_name and function_name and code:
                            try:
                                success = asyncio.run(JobInterface.create_job(
                                    name=job_name,
                                    description=description,
                                    function_name=function_name,
                                    code=code,
                                    schedule_type=schedule_type,
                                    schedule_config=json.dumps(
                                        schedule_config) if schedule_config else None
                                ))
                                if success:
                                    st.success("Job created successfully!")
                                    st.session_state.show_create_modal = False
                                    st.rerun()
                                else:
                                    st.error("Failed to create job")
                            except Exception as e:
                                st.error(f"Error creating job: {str(e)}")
                        else:
                            st.error("Please fill all required fields")

                with col2:
                    if st.form_submit_button("Test Code"):
                        if code:
                            result = asyncio.run(
                                JobInterface.test_job_code(code))
                            if result["success"]:
                                st.success(result["message"])
                            else:
                                st.error(
                                    f"Code test failed: {result['message']}")
                        else:
                            st.error("Please enter code to test")

                with col3:
                    if st.form_submit_button("Cancel"):
                        st.session_state.show_create_modal = False
                        st.rerun()

    # Load jobs
    jobs = asyncio.run(JobInterface.get_all_jobs())

    if not jobs:
        st.info(
            "No jobs found. Create a new job or click 'Refresh Jobs' to discover available jobs.")
        return

    st.subheader("📋 Job List")

    # Jobs table
    for job in jobs:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                status_icon = "✅" if job.is_active else "❌"
                custom_icon = "🔧" if getattr(job, 'is_custom', False) else "🤖"
                st.write(f"{status_icon} {custom_icon} **{job.name}**")
                if job.description:
                    st.caption(job.description)

            with col2:
                st.write(f"**Type:** {job.schedule_type}")

                # Display schedule details
                if hasattr(job, 'schedule_config') and job.schedule_config:
                    try:
                        config = json.loads(job.schedule_config)
                        schedule_details = _format_schedule_config(
                            job.schedule_type, config)
                        st.write(f"**Schedule:** {schedule_details}")
                    except:
                        pass

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
                # Action buttons
                col_toggle, col_edit, col_delete = st.columns(3)

                with col_toggle:
                    new_status = st.toggle(
                        "Active",
                        value=job.is_active,
                        key=f"job_toggle_{job.id}"
                    )

                    if new_status != job.is_active:
                        asyncio.run(JobInterface.update_job_status(
                            job.id, new_status))
                        st.rerun()

                with col_edit:
                    if st.button("✏️", key=f"edit_{job.id}", help="Edit job"):
                        st.session_state.selected_job = job
                        st.rerun()

                with col_delete:
                    if getattr(job, 'is_custom', False) and st.button("🗑️", key=f"delete_{job.id}", help="Delete job"):
                        if st.session_state.get(f"confirm_delete_{job.id}", False):
                            asyncio.run(JobInterface.delete_job(job.id))
                            st.success("Job deleted successfully!")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{job.id}"] = True
                            st.warning("Click again to confirm deletion")

            st.divider()

    # Edit Job Modal
    if st.session_state.selected_job:
        job = st.session_state.selected_job
        with st.expander(f"✏️ Edit Job: {job.name}", expanded=True):
            with st.form("edit_job_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Job Name", value=job.name)
                    new_function_name = st.text_input(
                        "Function Name", value=job.function_name)
                with col2:
                    new_schedule_type = st.selectbox("Schedule Type",
                                                     ["daily", "weekly",
                                                         "monthly", "custom"],
                                                     index=["daily", "weekly", "monthly", "custom"].index(job.schedule_type))

                # Load existing schedule config
                existing_config = {}
                if hasattr(job, 'schedule_config') and job.schedule_config:
                    try:
                        existing_config = json.loads(job.schedule_config)
                    except:
                        existing_config = {}

                # Schedule configuration for edit
                st.subheader("Schedule Configuration")
                new_schedule_config = {}

                if new_schedule_type in ["daily", "weekly", "monthly"]:
                    col_time, col_day = st.columns(2)
                    with col_time:
                        default_time = None
                        if "hour" in existing_config and "minute" in existing_config:
                            from datetime import time
                            default_time = time(
                                existing_config["hour"], existing_config["minute"])

                        new_schedule_time = st.time_input(
                            "Execution Time", value=default_time)
                        if new_schedule_time:
                            new_schedule_config["hour"] = new_schedule_time.hour
                            new_schedule_config["minute"] = new_schedule_time.minute

                    if new_schedule_type == "weekly":
                        with col_day:
                            days = ["Monday", "Tuesday", "Wednesday",
                                    "Thursday", "Friday", "Saturday", "Sunday"]
                            default_day = existing_config.get("day_of_week", 0)
                            new_day_of_week = st.selectbox(
                                "Day of Week", days, index=default_day)
                            new_schedule_config["day_of_week"] = days.index(
                                new_day_of_week)

                    elif new_schedule_type == "monthly":
                        with col_day:
                            default_day = existing_config.get(
                                "day_of_month", 1)
                            new_day_of_month = st.number_input(
                                "Day of Month", min_value=1, max_value=31, value=default_day)
                            new_schedule_config["day_of_month"] = new_day_of_month

                elif new_schedule_type == "custom":
                    st.info("💡 Cron format: minute hour day month day_of_week")
                    default_cron = existing_config.get("cron", "")
                    new_cron_expression = st.text_input(
                        "Cron Expression", value=default_cron, placeholder="0 9 * * 1 (Every Monday at 9 AM)")
                    if new_cron_expression:
                        new_schedule_config["cron"] = new_cron_expression

                new_description = st.text_area(
                    "Description", value=job.description or "")

                if hasattr(job, 'code') and job.code:
                    new_code = st.text_area(
                        "Python Code", value=job.code, height=200)
                else:
                    new_code = st.text_area("Python Code", height=200)

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("Update Job", type="primary"):
                        try:
                            success = asyncio.run(JobInterface.update_job(
                                job.id,
                                name=new_name,
                                description=new_description,
                                function_name=new_function_name,
                                schedule_type=new_schedule_type,
                                code=new_code,
                                schedule_config=json.dumps(
                                    new_schedule_config) if new_schedule_config else None
                            ))
                            if success:
                                st.success("Job updated successfully!")
                                st.session_state.selected_job = None
                                st.rerun()
                            else:
                                st.error("Failed to update job")
                        except Exception as e:
                            st.error(f"Error updating job: {str(e)}")

                with col2:
                    if st.form_submit_button("Test Code"):
                        if new_code:
                            result = asyncio.run(
                                JobInterface.test_job_code(new_code))
                            if result["success"]:
                                st.success(result["message"])
                            else:
                                st.error(
                                    f"Code test failed: {result['message']}")
                        else:
                            st.error("Please enter code to test")

                with col3:
                    if st.form_submit_button("Cancel"):
                        st.session_state.selected_job = None
                        st.rerun()

    # Job statistics
    st.subheader("📊 Job Statistics")
    active_jobs = sum(1 for job in jobs if job.is_active)
    inactive_jobs = len(jobs) - active_jobs
    custom_jobs = sum(1 for job in jobs if getattr(job, 'is_custom', False))
    auto_jobs = len(jobs) - custom_jobs

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jobs", len(jobs))
    with col2:
        st.metric("Active Jobs", active_jobs)
    with col3:
        st.metric("Custom Jobs", custom_jobs)
    with col4:
        st.metric("Auto-discovered", auto_jobs)


def _format_schedule_config(schedule_type: str, config: dict) -> str:
    """Format schedule configuration for display"""
    if schedule_type == "daily":
        if "hour" in config and "minute" in config:
            return f"Daily at {config['hour']:02d}:{config['minute']:02d}"
        return "Daily"

    elif schedule_type == "weekly":
        days = ["Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = days[config.get("day_of_week", 0)]
        if "hour" in config and "minute" in config:
            return f"Weekly on {day_name} at {config['hour']:02d}:{config['minute']:02d}"
        return f"Weekly on {day_name}"

    elif schedule_type == "monthly":
        day = config.get("day_of_month", 1)
        if "hour" in config and "minute" in config:
            return f"Monthly on day {day} at {config['hour']:02d}:{config['minute']:02d}"
        return f"Monthly on day {day}"

    elif schedule_type == "custom":
        cron = config.get("cron", "")
        return f"Custom: {cron}" if cron else "Custom"

    return schedule_type.title()
