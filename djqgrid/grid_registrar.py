from zlib import crc32

__author__ = 'zmbq'

_grids = {}

def register_grid(gridcls):
    _grids[gridcls.get_grid_id()] = gridcls

def get_grid_class(id):
    return _grids[id]