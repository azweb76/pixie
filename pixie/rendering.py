import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import re
from tabnanny import check
import requests
import tempfile
import logging
import boto3
from typing import List
from git import Repo
from giturlparse import parse

from jinja2 import Environment, ChainableUndefined
from jinja2 import FileSystemLoader
from jinja2.nativetypes import NativeEnvironment
from ruamel.yaml import YAML
from termcolor import colored

from pixie.context import PixieContext


_log = logging.getLogger(name=__name__)


class AwsUtils(object):
    def get_parameter(self, name, profile_name=None):
        try:
            session = boto3.Session(
                profile_name=profile_name
            )

            ssm_client = session.client('ssm')
            param = ssm_client.get_parameter(Name=name)
            return param['Parameter']['Value']
        except Exception as ex:
            _log.debug(ex)
        return ''


class GitUtils(object):
    def remote_info(self, path, remote_name):
        try:
            repo = Repo(path)
            remote = repo.remote(remote_name)
            return parse(remote.url, check_domain=False)
        except Exception as ex:
            _log.debug(ex)
        return {}
    
    def owner_repo(self, path, remote_name):
        try:
            repo = Repo(path)
            remote = repo.remote(remote_name)
            u = parse(remote.url, check_domain=False)
            return u.owner + '/' + u.repo
        except Exception as ex:
            _log.debug(ex)
        return ''


class RenderUtils(object):  # pylint: disable=R0903
    """Template utilities."""

    def __init__(self, context) -> None:
        super().__init__()

        self.context = context
        self.colored = colored

    @classmethod
    def read_file(cls, path, parse=False):
        """Used to read a file and return its contents."""

        with open(path, 'r') as file_handle:
            if parse:
                parser = get_parser(path)
                return parser.load(file_handle)
            else:
                return file_handle.read()

    @classmethod
    def read_json(cls, path):
        """Used to read a JSON file and return its contents."""

        with open(path, 'r') as file_handle:
            return json.load(file_handle)

    @classmethod
    def read_yaml(cls, path):
        """Used to read a YAML file and return its contents."""
        yaml = YAML()
        with open(path, 'r') as file_handle:
            return yaml.load(file_handle)
    
    @classmethod
    def random_string(cls, length=16, special_chars=''):
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789" + special_chars
        from os import urandom

        return "".join(chars[c % len(chars)] for c in urandom(length))

    def checksum(cls, file):
        with open(file, 'rb') as fhd:
            return hashlib.md5(fhd.read()).hexdigest()

    def download_file(cls, url, checksum):
        file = tempfile.mktemp()
        resp = requests.get(url)
        if resp.status_code == 200:
            with open(file, 'w') as fhd:
                fhd.write(resp.text)
            actual_checksum = cls.checksum(file)
            if checksum != actual_checksum:
                raise RuntimeError('checksum mismatch for %s (actual=%s, expected=%s)',
                    file, actual_checksum, checksum)
        else:
            raise RuntimeError('failed to download file (code=%s)' % resp.status_code)
        return file

    def path_exists(cls, path):
        return os.path.exists(os.path.expanduser(path))
    
    def join_arrays(cls, *arrays):
        output_array = []
        for array in arrays:
            output_array.extend(array)
        return output_array
    
    def dirs(cls, path):
        return [x.name for x in Path(path).iterdir() if x.is_dir]

    def files(cls, path):
        return [x.name for x in Path(path).iterdir() if x.is_file]
    
    def glob(cls, path):
        return Path(path).glob(path)


def format_list(value, format='{value}'):
    for idx, x in enumerate(value):
        value[idx] = format.format(value=value[idx], index=idx)
    return value


def yaml_format(value, **kw):
    if value is None:
        return 'null'
    yaml = YAML()
    stream = StringIO()
    yaml.dump(value, stream, **kw)
    return stream.getvalue().rstrip()


def json_format(value):
    if value is None:
        return 'null'
    return json.dumps(value)


def join_path(value, added_path):
    if value is None:
        return 'null'
    return os.path.join(value, added_path)


def get_parser(path):
    ext = os.path.splitext(path)[1]
    if ext == '.yaml' or ext == '.yml':
        yaml = YAML()
        return yaml
    elif ext == '.json':
        return json
    else:
        exit('Parser format not supported: %s' % ext)


def get_utils(context):
    return dict(
        utils=RenderUtils(context),
        aws=AwsUtils(),
        git=GitUtils(),
        path=os.path,
        tempfile=tempfile
    )


def render(template_name, context, template_dir):
    """Used to render a Jinja template."""

    env = Environment(loader=FileSystemLoader(template_dir), variable_start_string='${{', variable_end_string='}}', keep_trailing_newline=True, undefined=ChainableUndefined)
    add_filters(env)
    utils = get_utils(context)

    template = env.get_template(template_name)

    return template.render(context=context, **utils, **context)


def add_filters(env):
    env.filters['formatlist'] = format_list
    env.filters['yaml'] = yaml_format
    env.filters['json'] = json_format
    env.filters['join_path'] = join_path


def render_value(text, context: PixieContext):
    """Used to render a Jinja template."""

    if text is None:
        return None

    if not isinstance(text, str):
        return text

    if '\n' in text:
        return render_text(text, context)

    env = NativeEnvironment(variable_start_string='${{', variable_end_string='}}', undefined=ChainableUndefined)
    add_filters(env)

    utils = get_utils(context)

    template = env.from_string(text)

    return template.render(context=context, **utils, **context)


def render_text(text, context: PixieContext):
    """Used to render a Jinja template."""

    if text is None:
        return None

    env = Environment(variable_start_string='${{', variable_end_string='}}', keep_trailing_newline=True, undefined=ChainableUndefined)
    add_filters(env)
    utils = get_utils(context)

    template = env.from_string(text)

    return template.render(context=context, **utils, **context)


def _render_value(value, context: PixieContext, exclude_keys: List[str]):
    if isinstance(value, str):
        return render_value(value, context)
    elif isinstance(value, list):
        v_list: list[str] = []
        for x in value:
            v_list.append(_render_value(x, context, []))
        return v_list
    elif isinstance(value, dict):
        opts = value.copy()
        for k, v in opts.items():
            if k in exclude_keys:
                opts[k] = v
            else:
                opts[k] = _render_value(v, context, [])
        return opts
    else:
        return value

def render_options(options: dict, context: PixieContext, exclude_keys=[]):
    return _render_value(options, context, exclude_keys)

def render_token_file(path: str, tokens: dict):
    """Used to render a Token File."""

    with open(path, 'r') as file_handle:
        content = file_handle.read()

    return render_tokens(content, tokens)

def render_tokens(content: str, tokens: dict):
    """Used to render a Token File."""

    for token in tokens:
        content = content.replace(token, tokens[token])
    return content
