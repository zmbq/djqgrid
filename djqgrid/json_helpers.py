import json

__author__ = 'zmbq'

escape = '@@'

def function(funcname):
    return escape + funcname + escape

def dumps(o, *args, **kwargs):
    s = json.dumps(o, *args, **kwargs)
    s = s.replace('"' + escape, '')
    s = s.replace(escape + '"', '')
    return s