from jinja2 import Environment, FileSystemLoader

# Set up Jinja2 environment
template_loader = FileSystemLoader(searchpath="./app/templates")
template_env = Environment(loader=template_loader)
