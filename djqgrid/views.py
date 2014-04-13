import json
from django.http import HttpResponse
from grid_registrar import get_grid_class

__author__ = 'zmbq'

class JsonResponse(HttpResponse):
    def __init__(self, content, mimetype='application/json', status=None, content_type='application/json'):
        super(JsonResponse, self).__init__(
            content=json.dumps(content),
            mimetype=mimetype,
            status=status,
            content_type=content_type)


def query(request, grid_id):
    cls = get_grid_class(grid_id)
    grid = cls()
    data = grid.get_json_data(request.GET)
    return JsonResponse(data)
