import os
from jinja2 import Environment, FileSystemLoader

def render_template(template_name: str, context: dict) -> str:
    """
    Renders an email template using Jinja2 with the provided context.

    This function loads a template from the `email_templates` directory 
    located relative to this script and renders it with the given context data.

    Args:
        template_name (str): The name of the Jinja2 template file (e.g., 'welcome_email.html').
        context (dict): A dictionary containing key-value pairs to populate the template.

    Returns:
        str: The rendered HTML content as a string.
    """
    # Set template directory relative to this file
    template_dir = os.path.join(os.path.dirname(__file__), 'email_templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    return template.render(context)
