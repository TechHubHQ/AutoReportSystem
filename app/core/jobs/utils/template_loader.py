from jinja2 import Environment, FileSystemLoader, select_autoescape


async def load_template(content, template):

    env = Environment(
        loader=FileSystemLoader('app/integrations/email/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template(template)

    context = content

    return template.render(**context)
