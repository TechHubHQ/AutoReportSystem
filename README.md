# AutomateReportSystem

```
AutomateReportSystem
├─ .python-version
├─ .qodo
├─ app
│  ├─ config
│  │  ├─ config.py
│  │  └─ __init__.py
│  ├─ core
│  │  ├─ interface
│  │  │  ├─ task.py
│  │  │  ├─ template.py
│  │  │  ├─ user.py
│  │  │  └─ __init__.py
│  │  ├─ services
│  │  │  ├─ report_generator.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ database
│  │  ├─ db_connector.py
│  │  ├─ models.py
│  │  └─ __init__.py
│  ├─ Home.py
│  ├─ integrations
│  │  ├─ email
│  │  │  ├─ email_service.py
│  │  │  ├─ templates
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ pages
│  │  ├─ dashboard.py
│  │  ├─ login.py
│  │  ├─ signup.py
│  │  └─ __init__.py
│  ├─ security
│  │  └─ auth
│  │     ├─ auth_handler.py
│  │     └─ __init__.py
│  └─ __init__.py
├─ infra
│  └─ Dockerfile
├─ pyproject.toml
├─ README.md
└─ uv.lock

```
```
AutomateReportSystem
├─ .python-version
├─ .qodo
├─ .task_runner_status
├─ alembic
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     ├─ 8c8b218a72b0_init_db.py
│     ├─ add_job_fields.py
│     ├─ add_job_model.py
│     ├─ add_template_fields.py
│     └─ add_user_sessions_table.py
├─ alembic.ini
├─ app
│  ├─ config
│  │  ├─ config.py
│  │  └─ __init__.py
│  ├─ core
│  │  ├─ interface
│  │  │  ├─ analytics_interface.py
│  │  │  ├─ job_interface.py
│  │  │  ├─ metrics_interface.py
│  │  │  ├─ smtp_interface.py
│  │  │  ├─ task_interface.py
│  │  │  ├─ template_interface.py
│  │  │  ├─ user_interface.py
│  │  │  └─ __init__.py
│  │  ├─ jobs
│  │  │  ├─ discovery.py
│  │  │  ├─ registry.py
│  │  │  ├─ report_sender.py
│  │  │  ├─ scheduler.py
│  │  │  ├─ startup.py
│  │  │  ├─ task_runner.py
│  │  │  ├─ task_runner_manager.py
│  │  │  ├─ utils
│  │  │  │  ├─ content_loader.py
│  │  │  │  ├─ dateutils.py
│  │  │  │  ├─ template_loader.py
│  │  │  │  └─ __init__.py
│  │  │  └─ __init__.py
│  │  ├─ services
│  │  │  ├─ encryption_client.py
│  │  │  ├─ encryption_service.py
│  │  │  ├─ report_generator.py
│  │  │  └─ __init__.py
│  │  ├─ utils
│  │  │  ├─ datetime_utils.py
│  │  │  ├─ template_validator.py
│  │  │  ├─ timezone_utils.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ database
│  │  ├─ db_connector.py
│  │  ├─ models.py
│  │  └─ __init__.py
│  ├─ integrations
│  │  ├─ email
│  │  │  ├─ email_client.py
│  │  │  ├─ templates
│  │  │  │  ├─ monthly_update_template.html
│  │  │  │  └─ weekly_update_template.html
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ security
│  │  ├─ auth
│  │  │  ├─ auth_handler.py
│  │  │  └─ __init__.py
│  │  ├─ backend_session_manager.py
│  │  ├─ middleware.py
│  │  ├─ route_protection.py
│  │  ├─ session_manager.py
│  │  └─ session_validator.py
│  ├─ ui
│  │  ├─ components
│  │  │  ├─ cards.py
│  │  │  ├─ loader.py
│  │  │  ├─ session_status.py
│  │  │  ├─ task_modal.py
│  │  │  └─ __init__.py
│  │  ├─ dashboard.py
│  │  ├─ login.py
│  │  ├─ navbar.py
│  │  ├─ security_dashboard.py
│  │  ├─ signup.py
│  │  ├─ smtp_conf.py
│  │  ├─ template_designer.py
│  │  ├─ user_settings.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ infra
│  └─ Dockerfile
├─ main.py
├─ pyproject.toml
├─ README.md
└─ tests
   ├─ e2e
   │  └─ __init__.py
   ├─ integration
   │  └─ __init__.py
   ├─ unit
   │  ├─ test_models.py
   │  └─ __init__.py
   └─ __init__.py

```