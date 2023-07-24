from django import template

register = template.Library()

@register.inclusion_tag('form_start.html')
def form_start(form_name):
    return {'form_name': form_name}

@register.inclusion_tag('form_end.html')
def form_end(form_name):
    return {'form_name': form_name}