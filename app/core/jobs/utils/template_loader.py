import re
from jinja2 import Environment, BaseLoader, select_autoescape, FileSystemLoader
from app.core.jobs.utils.content_loader import process_dynamic_content
from app.core.interface.template_interface import get_template, get_templates
import asyncio


class StringTemplateLoader(BaseLoader):
    """Custom Jinja2 loader for string templates"""

    def __init__(self, template_string):
        self.template_string = template_string

    def get_source(self, environment, template):
        return self.template_string, None, lambda: True


async def load_template_from_string(template_content: str, subject: str, user_id: int = None):
    """Load template from string content with data processing"""
    # Process placeholders in both subject and content
    subject_context = await process_dynamic_content(subject, user_id)
    content_context = await process_dynamic_content(template_content, user_id)

    # Merge contexts
    context = {**subject_context, **content_context}

    # Replace [placeholder] syntax with {{placeholder}} for Jinja2
    processed_subject = re.sub(r'\[([^\]]+)\]', r'{{\1}}', subject)
    processed_content = re.sub(r'\[([^\]]+)\]', r'{{\1}}', template_content)

    # Create Jinja2 environment
    env = Environment(
        loader=StringTemplateLoader(processed_content),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Render subject
    subject_template = env.from_string(processed_subject)
    rendered_subject = subject_template.render(**context)

    # Render content
    content_template = env.get_template('')
    rendered_content = content_template.render(**context)

    return {
        'subject': rendered_subject,
        'content': rendered_content
    }


async def load_template_by_id(template_id: int, context: dict = None, user_id: int = None):
    """Load template by ID and render with context"""
    try:
        template = await get_template(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        return await load_template_from_string(
            template.html_content,
            template.subject,
            user_id
        )
    except Exception as e:
        print(f"Error loading template by ID {template_id}: {e}")
        raise e


async def load_template_by_name(template_name: str, context: dict = None, user_id: int = None):
    """Load template by name and render with context"""
    try:
        templates = await get_templates(user_id)
        template = next((t for t in templates if t.name.lower()
                        == template_name.lower()), None)

        if not template:
            raise ValueError(f"Template with name '{template_name}' not found")

        return await load_template_from_string(
            template.html_content,
            template.subject,
            user_id
        )
    except Exception as e:
        print(f"Error loading template by name '{template_name}': {e}")
        raise e


async def get_available_templates(user_id: int = None):
    """Get list of available templates for job configuration"""
    try:
        templates = await get_templates(user_id)
        return [{
            'id': template.id,
            'name': template.name,
            'description': getattr(template, 'description', ''),
            'category': getattr(template, 'category', 'General')
        } for template in templates if template.is_active]
    except Exception as e:
        print(f"Error getting available templates: {e}")
        return []


async def load_template(content, template):
    """Legacy function for backward compatibility"""
    # Check if template is a file path (legacy) or template name/ID
    if template.endswith('.html'):
        # Legacy file-based loading
        env = Environment(
            loader=FileSystemLoader('app/integrations/email/templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template_obj = env.get_template(template)
        context = content
        return template_obj.render(**context)
    else:
        # New template loading by name
        try:
            result = await load_template_by_name(template, content)
            return result['content']
        except Exception as e:
            print(
                f"Failed to load template '{template}' dynamically, falling back to legacy: {e}")
            # Fallback to legacy if loading fails
            env = Environment(
                loader=FileSystemLoader('app/integrations/email/templates'),
                autoescape=select_autoescape(['html', 'xml'])
            )
            template_obj = env.get_template(f"{template}.html")
            context = content
            return template_obj.render(**context)
