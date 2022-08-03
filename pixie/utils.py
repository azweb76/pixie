import json
import os


def read_json(path, default_value):
    if path and os.path.exists(path) and os.path.isfile(path):
        with open(path, 'r') as fhd:
            return json.load(fhd)
    return default_value


def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination
