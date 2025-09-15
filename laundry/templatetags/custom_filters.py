from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def sum_qty(items):
    try:
        return sum(int(i['qty']) for i in items)
    except:
        return 0

@register.filter
def render_ironing_desc(items):
    try:
        return ", ".join(f"{i['article']} × {i['qty']}" for i in items)
    except:
        return ""

@register.filter(name='zip')
def zip_lists(a, b):
    return zip(a, b)

@register.filter(name='sum_list')
def sum_list(values):
    try:
        return sum(float(v) for v in values)
    except:
        return 0

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''
@register.filter
def is_positive(value):
    try:
        return float(value) > 0
    except:
        return False
@register.filter
def floatval(value):
    try:
        return float(value)
    except:
        return 0.0