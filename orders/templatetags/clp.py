from django import template

register = template.Library()


@register.filter
def clp(value):
    amount = int(value)
    return f'${amount:,}'.replace(',', '.')