import streamlit as st
import asyncio
import json
from app.core.interface.job_interface import JobInterface
from app.core.jobs.discovery import initialize_jobs
from app.security.route_protection import RouteProtection
from app.ui.navbar import navbar
from app.core.jobs.utils.template_loader import get_available_templates
from app.security.backend_session_manager import BackendSessionManager
from app.core.jobs.task_runner_manager import (
    start_task_runner, stop_task_runner, restart_task_runner,
    get_task_runner_status, is_task_runner_running, get_task_runner_health
)
from app.core.utils.timezone_utils import (
    now_ist, format_ist_time_display, format_schedule_display,
    get_timezone_info, utc_to_ist
)


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

    with col3:
        # Task Runner Status
        runner_status = get_task_runner_status()
        is_running = runner_status.get('running', False)

        if is_running:
            st.success("🟢 Task Runner: Active")
        else:
            st.error("🔴 Task Runner: Stopped")

    # Create Job Modal
    if st.session_state.show_create_modal:
        with st.expander("➕ Create New Job", expanded=True):
            with st.form("create_job_form"):
                # Basic Job Information
                st.subheader("📋 Basic Information")
                col1, col2 = st.columns(2)
                with col1:
                    job_name = st.text_input(
                        "Job Name*", placeholder="e.g., Weekly Sales Report")
                    job_type = st.selectbox(
                        "Job Type*",
                        ["Email Report", "Data Export", "Notification", "Custom"],
                        help="Select the type of job to create"
                    )
                with col2:
                    schedule_type = st.selectbox(
                        "Schedule Type*", ["daily", "weekly", "monthly", "custom"])
                    description = st.text_area(
                        "Description", placeholder="Brief description of what this job does")

                # Schedule Configuration
                st.subheader("⏰ Schedule Configuration")

                # Show timezone info
                timezone_info = get_timezone_info()
                st.info(
                    f"🌍 All times are in {timezone_info['full_name']} ({timezone_info['offset']})")
                st.caption(f"Current IST time: {timezone_info['current_ist']}")

                schedule_config = {}

                if schedule_type in ["daily", "weekly", "monthly"]:
                    col_time, col_day = st.columns(2)
                    with col_time:
                        schedule_time = st.time_input(
                            "Execution Time (IST)", value=None, help="When should this job run in Indian Standard Time?")
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
                    st.info(
                        "💡 Cron format: minute hour day month day_of_week (IST timezone)")
                    cron_expression = st.text_input(
                        "Cron Expression (IST)", placeholder="0 9 * * 1 (Every Monday at 9 AM IST)")
                    if cron_expression:
                        schedule_config["cron"] = cron_expression

                    with st.expander("Cron Examples"):
                        st.code("""
0 9 * * *     # Daily at 9:00 AM IST
0 9 * * 1     # Every Monday at 9:00 AM IST
0 9 1 * *     # First day of every month at 9:00 AM IST
*/15 * * * *   # Every 15 minutes
0 */2 * * *   # Every 2 hours
                        """)

                # Template Configuration
                st.subheader("📄 Template & Content Configuration")

                # Get current user
                current_user = BackendSessionManager.get_current_user()
                user_id = current_user.get('id') if current_user else None

                # Load available templates
                available_templates = asyncio.run(
                    get_available_templates(user_id))

                if not available_templates:
                    st.warning(
                        "⚠️ No templates available. Please create a template first in the Template Designer.")
                    st.info(
                        "💡 Go to Template Designer → Create New to create your first template.")
                    template_id = None
                    content_type = "all"
                    recipients = []
                else:
                    # Template selection
                    template_options = [
                        "None (No template)"] + [f"{t['name']} ({t['category']})" for t in available_templates]
                    selected_template_option = st.selectbox(
                        "Select Template*",
                        options=template_options,
                        help="Choose which template to use for this job"
                    )

                    if selected_template_option == "None (No template)":
                        template_id = None
                        st.info(
                            "💡 This job will run without sending emails. You can add custom logic later.")
                    else:
                        # Find selected template
                        template_name = selected_template_option.split(" (")[0]
                        template_id = next(
                            t['id'] for t in available_templates if t['name'] == template_name)

                        # Show template details
                        selected_template = next(
                            t for t in available_templates if t['id'] == template_id)
                        st.success(f"✅ Selected: {selected_template['name']}")
                        if selected_template['description']:
                            st.caption(f"📝 {selected_template['description']}")

                        # Content type selection
                        col_content, col_recipients = st.columns(2)
                        with col_content:
                            content_type = st.selectbox(
                                "Content Type",
                                options=["all", "weekly", "monthly",
                                         "accomplishments", "in_progress", "stats"],
                                help="What type of content to include in the report"
                            )

                        with col_recipients:
                            # Recipients
                            recipients_text = st.text_area(
                                "Recipients (one email per line)*",
                                placeholder="user@example.com\\nmanager@example.com",
                                help="Enter email addresses, one per line"
                            )
                            recipients = [email.strip() for email in recipients_text.split(
                                '\\n') if email.strip()] if recipients_text else []

                            if recipients:
                                st.success(
                                    f"📧 {len(recipients)} recipient(s) configured")
                            else:
                                st.warning(
                                    "⚠️ Please add at least one recipient")

                # Job Configuration Summary
                if template_id:
                    st.subheader("📊 Job Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Template", selected_template['name'])
                    with col2:
                        st.metric("Content Type", content_type.title())
                    with col3:
                        st.metric("Recipients", len(recipients)
                                  if recipients else 0)
                    with col4:
                        if schedule_config:
                            schedule_display = format_schedule_display(
                                schedule_type, schedule_config)
                            st.metric("Schedule", schedule_display)

                # Form submission
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("🚀 Create Job", type="primary"):
                        if job_name and schedule_type:
                            # Validate required fields
                            if template_id and not recipients:
                                st.error(
                                    "❌ Please add at least one recipient for email jobs")
                            else:
                                try:
                                    # Generate function name
                                    function_name = f"job_{job_name.lower().replace(' ', '_').replace('-', '_')}"

                                    # Generate appropriate code based on job type
                                    if template_id:
                                        code = f'''async def {function_name}():
    """Auto-generated job: {job_name}"""
    from app.core.jobs.dynamic_report_sender import send_report
    
    # Job configuration
    template_id = {template_id}
    content_type = "{content_type}"
    recipients = {recipients}
    user_id = {user_id or 1}
    
    try:
        # Send report using template
        await send_report(
            template_id=template_id,
            content_type=content_type,
            user_id=user_id,
            recipients=recipients
        )
        print(f"✅ {job_name} completed successfully - Report sent to {{len(recipients)}} recipients")
    except Exception as e:
        print(f"❌ {job_name} failed: {{str(e)}}")
        raise e'''
                                    else:
                                        code = f'''async def {function_name}():
    """Auto-generated job: {job_name}"""
    print("🚀 Job '{job_name}' executed successfully!")
    
    # Add your custom job logic here
    # This job currently doesn't send emails
    # You can modify this code to add your specific functionality
    
    pass'''

                                    # Prepare job configuration
                                    job_config = {
                                        'job_type': job_type,
                                        'template_id': template_id,
                                        'content_type': content_type if template_id else None,
                                        'recipients': recipients if template_id else [],
                                        'user_id': user_id
                                    }

                                    success = asyncio.run(JobInterface.create_job(
                                        name=job_name,
                                        description=description,
                                        function_name=function_name,
                                        code=code,
                                        schedule_type=schedule_type,
                                        schedule_config=json.dumps(
                                            schedule_config) if schedule_config else None,
                                        job_config=json.dumps(job_config)
                                    ))

                                    if success:
                                        st.success(
                                            "✅ Job created successfully!")
                                        st.session_state.show_create_modal = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to create job")
                                except Exception as e:
                                    st.error(f"❌ Error creating job: {str(e)}")
                        else:
                            st.error("❌ Please fill in all required fields")

                with col2:
                    if st.form_submit_button("👁️ Preview Code"):
                        if job_name:
                            function_name = f"job_{job_name.lower().replace(' ', '_').replace('-', '_')}"
                            if template_id:
                                preview_code = f'''async def {function_name}():
    """Auto-generated job: {job_name}"""
    from app.core.jobs.dynamic_report_sender import send_report
    
    # Job configuration
    template_id = {template_id}
    content_type = "{content_type}"
    recipients = {recipients}
    user_id = {user_id or 1}
    
    try:
        await send_report(
            template_id=template_id,
            content_type=content_type,
            user_id=user_id,
            recipients=recipients
        )
        print(f"✅ {job_name} completed successfully")
    except Exception as e:
        print(f"❌ {job_name} failed: {{str(e)}}")
        raise e'''
                            else:
                                preview_code = f'''async def {function_name}():
    """Auto-generated job: {job_name}"""
    print("🚀 Job '{job_name}' executed successfully!")
    # Add your custom logic here
    pass'''

                            st.code(preview_code, language='python')
                        else:
                            st.error("❌ Please enter a job name first")

                with col3:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.show_create_modal = False
                        st.rerun()

    # Load jobs
    jobs = asyncio.run(JobInterface.get_all_jobs())

    if not jobs:
        st.info(
            "📋 No jobs found. Create a new job or click 'Refresh Jobs' to discover available jobs.")
        return

    st.subheader("📋 Job List")

    # Jobs table with enhanced display
    for job in jobs:
        with st.container():
            # Create expandable job card
            with st.expander(f"{'✅' if job.is_active else '❌'} {job.name}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write("**📋 Job Details**")
                    st.write(f"**Name:** {job.name}")
                    st.write(f"**Type:** {job.schedule_type}")
                    st.write(f"**Function:** {job.function_name}")
                    if job.description:
                        st.write(f"**Description:** {job.description}")

                    # Display job configuration if available
                    if hasattr(job, 'schedule_config') and job.schedule_config:
                        try:
                            config = json.loads(job.schedule_config)
                            job_config = config.get('job', {})
                            if job_config.get('template_id'):
                                st.write(
                                    f"**📄 Template ID:** {job_config['template_id']}")
                                st.write(
                                    f"**📊 Content Type:** {job_config.get('content_type', 'all')}")
                                recipients = job_config.get('recipients', [])
                                st.write(
                                    f"**📧 Recipients:** {len(recipients)} email(s)")
                        except:
                            pass

                with col2:
                    st.write("**⏰ Schedule Information**")

                    # Display schedule details
                    if hasattr(job, 'schedule_config') and job.schedule_config:
                        try:
                            config = json.loads(job.schedule_config)
                            schedule_details = format_schedule_display(
                                job.schedule_type, config)
                            st.write(f"**Schedule:** {schedule_details}")
                        except:
                            st.write(
                                f"**Schedule:** {job.schedule_type.title()} (IST)")
                    else:
                        st.write(
                            f"**Schedule:** {job.schedule_type.title()} (IST)")

                    if job.last_run:
                        last_run_ist = utc_to_ist(job.last_run)
                        st.write(
                            f"**Last Run:** {format_ist_time_display(last_run_ist)}")
                    else:
                        st.write("**Last Run:** Never")

                    if job.next_run:
                        next_run_ist = utc_to_ist(job.next_run)
                        st.write(
                            f"**Next Run:** {format_ist_time_display(next_run_ist)}")

                with col3:
                    st.write("**🔧 Actions**")

                    # Toggle active status
                    new_status = st.toggle(
                        "Active",
                        value=job.is_active,
                        key=f"job_toggle_{job.id}"
                    )

                    if new_status != job.is_active:
                        asyncio.run(JobInterface.update_job_status(
                            job.id, new_status))
                        st.rerun()

                    # Edit button
                    if st.button("✏️ Edit", key=f"edit_{job.id}", use_container_width=True):
                        st.session_state.selected_job = job
                        st.rerun()

                    # Delete button (only for custom jobs)
                    if getattr(job, 'is_custom', False):
                        if st.button("🗑️ Delete", key=f"delete_{job.id}", use_container_width=True, type="secondary"):
                            if st.session_state.get(f"confirm_delete_{job.id}", False):
                                asyncio.run(JobInterface.delete_job(job.id))
                                st.success("✅ Job deleted successfully!")
                                st.rerun()
                            else:
                                st.session_state[f"confirm_delete_{job.id}"] = True
                                st.warning(
                                    "⚠️ Click again to confirm deletion")

    # Edit Job Modal
    if st.session_state.selected_job:
        job = st.session_state.selected_job
        with st.expander(f"✏️ Edit Job: {job.name}", expanded=True):
            with st.form("edit_job_form"):
                st.subheader("📋 Basic Information")
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Job Name", value=job.name)
                    new_description = st.text_area(
                        "Description", value=job.description or "")
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
                st.subheader("⏰ Schedule Configuration")

                # Show timezone info
                timezone_info = get_timezone_info()
                st.info(
                    f"🌍 All times are in {timezone_info['full_name']} ({timezone_info['offset']})")

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
                            "Execution Time (IST)", value=default_time)
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
                        "Cron Expression (IST)", value=default_cron, placeholder="0 9 * * 1 (Every Monday at 9 AM IST)")
                    if new_cron_expression:
                        new_schedule_config["cron"] = new_cron_expression

                # Template Configuration for Edit
                st.subheader("📄 Template Configuration")

                # Get existing job config
                existing_job_config = {}
                if hasattr(job, 'schedule_config') and job.schedule_config:
                    try:
                        config = json.loads(job.schedule_config)
                        existing_job_config = config.get('job', {})
                    except:
                        existing_job_config = {}

                # Get current user
                current_user = BackendSessionManager.get_current_user()
                user_id = current_user.get('id') if current_user else None

                # Load available templates
                available_templates = asyncio.run(
                    get_available_templates(user_id))

                if available_templates:
                    template_options = [
                        "None (No template)"] + [f"{t['name']} ({t['category']})" for t in available_templates]

                    # Find current selection
                    current_template_id = existing_job_config.get(
                        'template_id')
                    current_selection = 0
                    if current_template_id:
                        for i, template in enumerate(available_templates):
                            if template['id'] == current_template_id:
                                current_selection = i + 1  # +1 because of "None" option
                                break

                    selected_template_option = st.selectbox(
                        "Select Template",
                        options=template_options,
                        index=current_selection,
                        key=f"edit_template_select_{job.id}"
                    )

                    if selected_template_option != "None (No template)":
                        template_name = selected_template_option.split(" (")[0]
                        edit_template_id = next(
                            t['id'] for t in available_templates if t['name'] == template_name)

                        # Content type and recipients
                        col_content, col_recipients = st.columns(2)
                        with col_content:
                            content_options = [
                                "all", "weekly", "monthly", "accomplishments", "in_progress", "stats"]
                            current_content = existing_job_config.get(
                                'content_type', 'all')
                            content_index = content_options.index(
                                current_content) if current_content in content_options else 0
                            edit_content_type = st.selectbox(
                                "Content Type", options=content_options, index=content_index)

                        with col_recipients:
                            current_recipients = existing_job_config.get(
                                'recipients', [])
                            recipients_text = st.text_area(
                                "Recipients (one email per line)",
                                value='\\n'.join(
                                    current_recipients) if current_recipients else '',
                                key=f"edit_recipients_{job.id}"
                            )
                            edit_recipients = [email.strip() for email in recipients_text.split(
                                '\\n') if email.strip()] if recipients_text else []
                    else:
                        edit_template_id = None
                        edit_content_type = "all"
                        edit_recipients = []

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("💾 Update Job", type="primary"):
                        try:
                            # Generate new function name if name changed
                            new_function_name = f"job_{new_name.lower().replace(' ', '_').replace('-', '_')}"

                            # Generate updated code
                            if edit_template_id:
                                new_code = f'''async def {new_function_name}():
    """Auto-generated job: {new_name}"""
    from app.core.jobs.dynamic_report_sender import send_report
    
    # Job configuration
    template_id = {edit_template_id}
    content_type = "{edit_content_type}"
    recipients = {edit_recipients}
    user_id = {user_id or 1}
    
    try:
        await send_report(
            template_id=template_id,
            content_type=content_type,
            user_id=user_id,
            recipients=recipients
        )
        print(f"✅ {new_name} completed successfully")
    except Exception as e:
        print(f"❌ {new_name} failed: {{str(e)}}")
        raise e'''
                            else:
                                new_code = f'''async def {new_function_name}():
    """Auto-generated job: {new_name}"""
    print("🚀 Job '{new_name}' executed successfully!")
    # Add your custom logic here
    pass'''

                            # Prepare updated job configuration
                            updated_job_config = {
                                'template_id': edit_template_id,
                                'content_type': edit_content_type if edit_template_id else None,
                                'recipients': edit_recipients if edit_template_id else [],
                                'user_id': user_id
                            }

                            success = asyncio.run(JobInterface.update_job(
                                job.id,
                                name=new_name,
                                description=new_description,
                                function_name=new_function_name,
                                schedule_type=new_schedule_type,
                                code=new_code,
                                schedule_config=json.dumps(
                                    new_schedule_config) if new_schedule_config else None,
                                job_config=json.dumps(updated_job_config)
                            ))

                            if success:
                                st.success("✅ Job updated successfully!")
                                st.session_state.selected_job = None
                                st.rerun()
                            else:
                                st.error("❌ Failed to update job")
                        except Exception as e:
                            st.error(f"❌ Error updating job: {str(e)}")

                with col2:
                    if st.form_submit_button("👁️ Preview Code"):
                        new_function_name = f"job_{new_name.lower().replace(' ', '_').replace('-', '_')}"
                        if edit_template_id:
                            preview_code = f'''async def {new_function_name}():
    """Auto-generated job: {new_name}"""
    from app.core.jobs.dynamic_report_sender import send_report
    
    template_id = {edit_template_id}
    content_type = "{edit_content_type}"
    recipients = {edit_recipients}
    user_id = {user_id or 1}
    
    await send_report(
        template_id=template_id,
        content_type=content_type,
        user_id=user_id,
        recipients=recipients
    )'''
                        else:
                            preview_code = f'''async def {new_function_name}():
    """Auto-generated job: {new_name}"""
    print("🚀 Job '{new_name}' executed successfully!")
    pass'''

                        st.code(preview_code, language='python')

                with col3:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.selected_job = None
                        st.rerun()

    # Task Runner Management
    st.subheader("🎛️ Task Runner Management")

    # Get task runner status
    runner_status = get_task_runner_status()
    health_status = get_task_runner_health()
    is_running = runner_status.get('running', False)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if is_running:
            st.success("✅ Status: Running")
        else:
            st.error("❌ Status: Stopped")

    with col2:
        scheduled_jobs = runner_status.get('scheduled_jobs', 0)
        st.metric("Scheduled Jobs", scheduled_jobs)

    with col3:
        if st.button("🚀 Start Runner", disabled=is_running):
            with st.spinner("Starting task runner..."):
                if start_task_runner():
                    st.success("✅ Task runner started successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to start task runner")

    with col4:
        if st.button("🛑 Stop Runner", disabled=not is_running):
            with st.spinner("Stopping task runner..."):
                if stop_task_runner():
                    st.success("✅ Task runner stopped successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to stop task runner")

    # Additional controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Restart Runner"):
            with st.spinner("Restarting task runner..."):
                if restart_task_runner():
                    st.success("✅ Task runner restarted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to restart task runner")

    with col2:
        if st.button("📊 Show Status Details"):
            st.session_state.show_runner_details = not st.session_state.get(
                'show_runner_details', False)
            st.rerun()

    # Show detailed status if requested
    if st.session_state.get('show_runner_details', False):
        with st.expander("🔍 Task Runner Details", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Runner Status")
                st.json(runner_status)

            with col2:
                st.subheader("Health Check")
                st.json(health_status)

    st.divider()

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
    """Format schedule configuration for display (deprecated - use timezone_utils.format_schedule_display)"""
    return format_schedule_display(schedule_type, config)
