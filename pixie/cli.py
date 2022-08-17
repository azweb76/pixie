import os
import sys
import click
import logging

from termcolor import colored
from click.shell_completion import CompletionItem

from pixie import __version__
from pixie import engine, utils
from pixie.config import PixieConfig
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


def get_aliases():
    config = PixieConfig.from_user()

    library = config.get('library', {})

    aliases = []
    for package_name in library:
        package = library[package_name]
        for alias_name in package:
            aliases.append(alias_name)
    return aliases


def get_library_packages():
    config = PixieConfig.from_user()
    library = config.get('library', {})

    package_names = []
    for package_name in library:
        package_names.append(package_name)
    return package_names


def complete_library_packages(ctx, param, incomplete):
    package_names = list(get_library_packages())
    return [
        name for name in package_names if name.startswith(incomplete)
    ]


def complete_library_aliases(ctx, param, incomplete):
    aliases = list(get_aliases())
    return [
        name for name in aliases if name.startswith(incomplete)
    ]


@click.command("discover", help="Discover pixies in a package.")
@click.option('-p', '--package', default='.', help='Package to run.', shell_complete=complete_library_packages)
def discover_cli(package):
    config = PixieConfig.from_user()
    library = config.get('library', {})

    runtime = PixieConsoleRuntime()
    aliases = engine.discover(runtime, {}, package)
    library[package] = aliases
    config['library'] = library

    config.save_user()

    for alias_name in aliases:
        alias = aliases[alias_name]
        click.echo(f'discovered {colored(alias_name, "green")}: {alias["description"]}')


@click.command("list", help="List all discovered pixies.")
def list_cli():
    config = PixieConfig.from_user()
    library = config.get('library', {})

    for package_name in library:
        package = library[package_name]
        click.echo(colored(package_name + ':', 'grey'))
        for alias_name in package:
            alias = package[alias_name]
            click.echo('  ' + colored(alias_name, 'green') + ': ' + alias["description"])


@click.command("run", help="Used to run a pixie job.")
@click.argument('job', shell_complete=complete_library_aliases)
@click.option('-p', '--package', default='.', help='Package to run.')
@click.option('-s', '--script', default='.pixie.yaml', help='Path to the pixie script.')
@click.option('-c', '--context', multiple=True, help='Context values to set.')
@click.option('--context-from', help='File used to set context')
@click.option('-t', '--target', default='.', help='Directory to use when generating files')
def run_cli(job, package, script, context, context_from, target):
    config = PixieConfig.from_user()

    library = config.get('library', {})

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
        }, PixieConsoleRuntime(config))
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
cli.add_command(list_cli)


if __name__ == '__main__':
    cli()
