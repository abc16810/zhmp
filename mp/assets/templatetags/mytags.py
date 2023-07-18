# -*- coding: utf-8 -*
from django import template
from mp.assets.models import Assets
from mp.links.models import Links
import json

register = template.Library()


@register.filter(name="get_assets_type_display")
def get_assets_type_display():
    res = dict(Assets.assets_type_choices)
    return json.dumps(res)


@register.filter
def pagination_range(total_page, current_num=1, display=5):
    try:
        current_num = int(current_num)
    except ValueError:
        current_num = 1

    half_display = int(display / 2)
    start = current_num - half_display if current_num > half_display else 1
    if start + display <= total_page:
        end = start + display
    else:
        end = total_page + 1
        start = end - display if end > display else 1
    return range(start, end)


@register.filter
def paginator_num(total_page, current_page):
    DOT = '.'
    ON_EACH_SIDE = 2
    ON_ENDS = 2
    if total_page <= 10:
        page_range = range(1, total_page + 1)
    else:
        page_range = []
        if current_page > (ON_EACH_SIDE + ON_ENDS + 1):
            page_range.extend(range(1, ON_ENDS + 1))
            page_range.append(DOT)
            page_range.extend(range(current_page - ON_EACH_SIDE, current_page + 1))
        else:
            page_range.extend(range(1, current_page + 1))
        if current_page < (total_page - ON_EACH_SIDE - ON_ENDS):
            page_range.extend(range(current_page + 1, current_page + ON_EACH_SIDE + 1))
            page_range.extend(DOT)
            page_range.extend(range(total_page - ON_ENDS + 1, total_page + 1))
        else:
            page_range.extend(range(current_page + 1, total_page + 1))
    return page_range

@register.filter()
def get_name_display(value):
    return dict(Links.links_type_choices).get(value)