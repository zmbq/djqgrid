# coding=utf-8
import json
from django import template
from djqgrid import json_helpers

register = template.Library()

@register.simple_tag(takes_context=True)
def jqgrid(context, grid, prefix='', pager=True, urlquery=None, **kwargs):
    if prefix and prefix[-1]!='-':
        prefix += '-'  # Append a - to the prefix

    gridId = prefix + "grid"
    pagerId = prefix + "pager"
    options = grid.get_options(kwargs)
    # Add the query dict to the url
    if not '?' in options['url']:
        options['url'] += '?'
    if urlquery:
        options['url'] += urlquery
    options['url'] += context['request'].GET.urlencode()
    if pager:
        options['pager'] = '#' + pagerId
    else:
        options['rows'] = 99999
    options = json_helpers.dumps(options, indent=4)

    html = """
    <table id="%s"><tr><td></td></tr></table>
    <div id="%s"></div>
    <script type="text/javascript">
        $(function() {
            $('#%s').jqGrid(%s);
        });
    </script>""" % (gridId, pagerId, gridId, options);

    return html
