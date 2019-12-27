from django import template
from django.utils.html import format_html_join

from hooks import hook

register = template.Library()


@register.simple_tag(name="hook", takes_context=True)
def hook_tag(context, name, *args, **kwargs):
    return format_html_join(
        sep="\n",
        format_string="{}",
        args_generator=(
            (response,)
            for response in hook(name, context, *args, **kwargs)
        )
    )
