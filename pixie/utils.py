from ruamel.yaml import YAML

import json
import os


def read_config(path, default_value):
    if path and os.path.exists(path) and os.path.isfile(path):
        parts = os.path.splitext(path)
        if parts[1] == 'json':
            return read_json(path, default_value=default_value)
        elif parts[1] == 'yaml':
            return read_yaml(path, default_value=default_value)
    return default_value


def read_json(path, default_value):
    if path and os.path.exists(path) and os.path.isfile(path):
        with open(path, 'r') as fhd:
            return json.load(fhd)
    return default_value


def read_yaml(path, default_value):
    if path and os.path.exists(path) and os.path.isfile(path):
        yaml = YAML()
        with open(path, 'r') as fhd:
            return yaml.load(fhd)
    return default_value


def save_yaml(data, path):
    yaml = YAML()
    with open(path, 'w') as fhd:
        return yaml.dump(data, fhd)


def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination
