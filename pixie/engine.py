#!/usr/bin/env python
# coding: utf-8

import collections
import glob
import logging
import os
import pathlib
import re
import sys
import tempfile

from ruamel.yaml import YAML

from pixie.steps import PixieStepExecution

from .context import PixieContext
from .plugin import PixiePluginContext
from .plugins import load_plugins
from .rendering import render_options, render_text, render_value
from .runtime import PixieRuntime
from . import utils


_log = logging.getLogger(__name__)


def str2bool(v):
    if v is None:
        return False
    return v.lower() in ("yes", "true", "t", "1", "y")


known_types = {
    'int': int,
    'bool': str2bool,
    'str': str,
    'float': float
}


def convert(v, type):
    if type in known_types:
        return known_types[type](v)
    return str(v)


def read_parameter(prompt, context, runtime: PixieRuntime):
    default = prompt.get('default', None)

    if 'if' in prompt:
        enabled = prompt['if']
        if not enabled:
            return default
    
    d = runtime.ask(prompt)

    return convert(d, prompt.get('type', 'str'))


def config_cli(args):
    options = {}
    scaffold_file = os.path.expanduser('~/.pixie')

    yaml = YAML()
    if os.path.exists(scaffold_file):
        with open(scaffold_file, 'r') as fhd:
            options = yaml.load(fhd)

    if args.action == 'save':
        options['url'] = args.url

        with open(scaffold_file, 'w') as fhd:
            yaml.dump(options, fhd, default_flow_style=False)
    elif args.action == 'view':
        sys.stdout.write('url: %s' % options.get('url', 'not defined'))


def rm_rf(d):
    for path in (os.path.join(d, f) for f in os.listdir(d)):
        if os.path.isdir(path):
            rm_rf(path)
        else:
            os.unlink(path)
    os.rmdir(d)


def locate_scaffold_file(path, name):
    base_paths = [
        path
    ]

    extensions = [
        '.yaml',
        '.yml',
        '.json',
        ''
    ]

    names = [
        f'{name}',
        f'.{name}',
        os.path.join(name, '.pixie')
    ]
    for base_path in base_paths:
        for ext in extensions:
            for n in names:
                full_path = os.path.join(base_path, n + ext)
                _log.debug(f'locating pixie script using {full_path}')
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    return full_path
    return None


def process_parameters(parameters, context: PixieContext, runtime: PixieRuntime):
    for parameter in (parameters or []):
        parameter_options = render_options(parameter, context)
        parameter_name = parameter_options['name']
        context_source = parameter_options.get('context_source', parameter_name)
        context_target = parameter_options.get('context_target', parameter_name)
        if context_source in context:
            context[context_target] = convert(context[context_source], parameter.get('type', 'str'))
        else:
            context[context_target] = read_parameter(parameter_options, context, runtime)


def run(context: PixieContext, options, runtime: PixieRuntime):
    execute_scaffold(context, options, runtime)

    runtime.print_todos(context)
    runtime.print_notes(context)

    return context


def execute_scaffold(context: PixieContext, options, runtime: PixieRuntime):
    package = options['package']

    yaml = YAML()

    script = options.get('script', '.pixie.yaml')

    if '__package' in context:
        package_path = context.resolve_package_path(package)
    else:
        package_path = package
    if os.path.exists(package_path):
        _log.debug('using local package \'%s\'', package_path)
        pkg_dir = package_path
    else:
        pkg_dir = fetch_package(runtime, options, package)
    
    scaffold_file = locate_scaffold_file(pkg_dir, script)
    _log.debug('using pixie file: %s', scaffold_file)

    if scaffold_file:
        pkg_dir = os.path.dirname(scaffold_file)
    sys.path.append(pkg_dir)

    job_name = options.get('job', 'default')
    if scaffold_file is not None:
        with open(scaffold_file, 'r') as fhd:
            config = yaml.load(fhd)
    elif job_name == 'scaffold':
        config = {
            'jobs': {
                job_name: {
                    'steps': options.get('steps', [{
                        'action': 'fetch',
                        'with': {
                            'source': '${{ source | default(".") }}'
                        }
                    }])
                }
            }
        }
    else:
        config = {
            'jobs': {}
        }

    context.todos.extend(config.get('todos', []))
    context.notes.extend(config.get('notes', []))

    plugin_context = PixiePluginContext(
        config.get('plugins', {})
    )

    step_execution = PixieStepExecution(plugin_context)

    plugins: list = load_plugins()
    for plugin in plugins:
        plugin.init(plugin_context)

    context_options = render_options(config.get('context', {}), context)
    context.update(context_options)
    context.update(render_options(options.get('context', {}), context))

    process_parameters(config.get('parameters', []), context, runtime)

    context['__package'] = {
        'path': pkg_dir,
        'options': options
    }

    steps_context = context['steps'] = {}
    job = config.get('jobs', {}).get(job_name, {})

    context_options = render_options(job.get('context', {}), context)
    context.update(context_options)
    process_parameters(job.get('parameters', []), context, runtime)

    if context.get('__target') is None:
        context['__target'] = '.'
    
    _log.debug('%s', context)

    steps: list = job.get('steps', [])

    step_execution.execute(context, runtime, steps_context, steps)

    return context


def discover(runtime, options, package):
    result = {}
    pkg_dir = pathlib.Path(fetch_package(runtime, options, package))
    for f in pkg_dir.glob('**/.pixie.yaml'):
        pixie_config = utils.read_yaml(str(f), {})
        if 'name' in pixie_config:
            pkg_name = pixie_config['name']
            jobs = pixie_config.get('jobs')
            for job_name in jobs:
                job = jobs[job_name]
                alias_name = f'{pkg_name}/{job_name}'
                result[alias_name] = dict(
                    package=package,
                    job=job_name,
                    description=job.get('description', ''),
                    script=str(f.relative_to(pkg_dir))
                )
    return result


def fetch_package(runtime, options, package):

    packages_dir = os.path.realpath(os.path.expanduser('~/.pixie/packages'))
    tempdir = options.get('temp', packages_dir)

    package_parts = package.split('@')
    if len(package_parts) == 1:
        package_name = package_parts[0]
        package_version = 'main'
    else:
        package_name = package_parts[0]
        package_version = package_parts[1]
    package_name_parts = package_name.split('/')
    if len(package_name_parts) <= 2:
        package_name_parts = ['github.com'] + package_name_parts
        package_name = '/'.join(package_name_parts)
    pkg_dir = os.path.join(tempdir, f'{package_name}@{package_version}')
    _log.debug('using package dir: %s', pkg_dir)

    rc = 9999
    if os.path.exists(pkg_dir):
        _log.debug('[git] updating %s package', package)
        rc = os.system(
                """(cd {pkg_dir} && git pull >/dev/null 2>&1)""".format(pkg_dir=pkg_dir))
        if rc != 0:
            _log.error('package %s is having issues, repairing', package)
            rm_rf(pkg_dir)

    if rc != 0:
        _log.debug('[git] pulling %s package', package_name)
        rc = os.system(f"""
        git clone https://{package_name} {pkg_dir} >/dev/null 2>&1
        """)
    if rc != 0:
        raise Exception(
                'Failed to pull scaffold package %s' % package)

    rc = os.system(f"""(cd {pkg_dir} && git checkout -f {package_version} >/dev/null 2>&1)""")
    if rc != 0:
        raise Exception('Failed to load version %s' % package_version)
    return pkg_dir
