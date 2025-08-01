import re
from jinja2 import Environment, BaseLoader, select_autoescape, FileSystemLoader
from app.core.jobs.utils.content_loader import process_dynamic_content


class StringTemplateLoader(BaseLoader):
    """Custom Jinja2 loader for string templates"""

    def __init__(self, template_string):
        self.template_string = template_string

    def get_source(self, environment, template):
        return self.template_string, None, lambda: True


async def load_template_from_string(template_content: str, subject: str, user_id: int = None):
    """Load template from string content with dynamic data processing"""
    # Process dynamic placeholders in both subject and content
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


async def load_template(content, template):
    """Legacy function for backward compatibility"""
    env = Environment(
        loader=FileSystemLoader('app/integrations/email/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template(template)
    context = content
    return template.render(**context)
