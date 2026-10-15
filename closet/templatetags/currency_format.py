from django import template

register = template.Library()


@register.filter
def rupiah(value):
    if value is None:
        return "-"
    return "Rp " + f"{int(value):,}".replace(",", ".")