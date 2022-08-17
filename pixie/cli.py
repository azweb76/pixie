import os
import sys
import click
import logging

from click.decorators import help_option

from pixie import __version__
from pixie import engine, utils
from pixie.context import PixieContext
from pixie.runtime import PixieConsoleRuntime


class AddColorFormatter(logging.Formatter):
    def format(self, record):
        msg = super(AddColorFormatter, self).format(record)
        # Green/Cyan/Yellow/Red/Redder based on log level:
        color = (
            "\033[1;"
            + ("32m", "36m", "33m", "31m", "41m")[
                min(4, int(4 * record.levelno / logging.FATAL))
            ]
        )
        return color + record.levelname + "\033[1;0m: " + msg

@click.command("discover", help="Discover pixies in a package.")
@click.option('-p', '--package', default='.', help='Package to run.')
def discover_cli(package):
    user_config_file = os.path.realpath(os.path.expanduser('~/.pixie/config.yaml'))
    user_config = utils.read_yaml(user_config_file, {})
    library = user_config.get('library', {})

    runtime = PixieConsoleRuntime()
    aliases = engine.discover(runtime, {}, package)
    library[package] = aliases
    user_config['library'] = library

    utils.save_yaml(user_config, user_config_file)

    for alias_name in aliases:
        alias = aliases[alias_name]
        click.echo(f'discovered {alias_name}: {alias["description"]}')


@click.command("run", help="Used to run a pixie job.")
@click.argument('job')
@click.option('-p', '--package', default='.', help='Package to run.')
@click.option('-s', '--script', default='.pixie.yaml', help='Path to the pixie script.')
@click.option('-c', '--context', multiple=True, help='Context values to set.')
@click.option('--context-from', help='File used to set context')
@click.option('-t', '--target', default='.', help='Directory to use when generating files')
def run_cli(job, package, script, context, context_from, target):
    user_config_file = os.path.realpath(os.path.expanduser('~/.pixie/config.yaml'))
    user_config = utils.read_yaml(user_config_file, {})
    library = user_config.get('library', {})

    file_context = utils.read_json(context_from, {})

    user_context_file = os.path.realpath(os.path.expanduser('~/.pixie/context.yaml'))
    user_context = utils.read_yaml(user_context_file, {})

    cwd_context_file = os.path.realpath(os.path.expanduser('./.pixierc.yaml'))
    cwd_context = utils.read_yaml(cwd_context_file, {})

    file_context = utils.read_json(context_from, {})    

    p_context = {}
    c: str
    for c in context:
        eq_idx = c.index('=')
        parameter_name = c[0:eq_idx]
        parameter_value = c[eq_idx+1:]
        p_context[parameter_name] = parameter_value
    
    try:
        ctx = utils.merge(file_context, user_context)
        ctx = utils.merge(cwd_context, ctx)
        ctx = utils.merge(p_context, ctx)

        context2 = PixieContext(
            env=os.environ,
            __target=target
        )

        for package_name in library:
            lib_pkg = library[package_name]
            if job in lib_pkg:
                job_alias = lib_pkg[job]
                script = job_alias['script']
                package = job_alias['package']
                job = job_alias['job']
                break

        engine.run(context2, {
            'script': script,
            'job': job,
            'package': package,
            'context': ctx
        }, PixieConsoleRuntime())
    except KeyboardInterrupt:
        pass

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(__version__)
@click.option('--log-level', default='info', help='The log level to output')
def cli(log_level):
    stdout_hdlr = logging.StreamHandler(stream=sys.stdout)
    stdout_hdlr.setFormatter(AddColorFormatter())

    logging.root.handlers.clear()

    loglevel_str = log_level.upper()
    loglevel = getattr(logging, loglevel_str)

    stdout_hdlr.setLevel(loglevel)
    logging.root.setLevel(loglevel)
    logging.root.addHandler(stdout_hdlr)

cli.add_command(run_cli)
cli.add_command(discover_cli)


if __name__ == '__main__':
    cli()
