import os
import sys
import click
import logging

from termcolor import colored

from . import __version__
from . import engine, utils
from .config import PixieConfig
from .context import PixieContext
from .runtime import PixieConsoleRuntime


_log = logging.getLogger(__name__)


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
@click.argument('package', default='.', type=click.Path(), shell_complete=complete_library_packages)
@click.option('-s', '--save', is_flag=True, help='Path to the pixie script.')
def discover_cli(package, save):
    config = PixieConfig.from_user()
    library = config.get('library', {})

    runtime = PixieConsoleRuntime(config)
    package_info = engine.discover(runtime, {}, package)
    aliases = package_info['aliases']
    library[package] = aliases
    config['library'] = library

    click.echo('📦 Package: ' + colored(package, 'green') + ' ' + colored('(' + package_info['package_path'] + ')', 'grey') + '\n')
    for alias_name in aliases:
        alias = aliases[alias_name]
        click.echo('  ➜ ' + colored(alias_name, "green") + f': {alias["description"]}')
    
    if save:
        config.save_user()
        click.echo('\n' + colored('Saved to ' + config.file, "grey"))


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


@click.command("info", help="Show information for a job.")
@click.argument('job', shell_complete=complete_library_aliases)
@click.option('-p', '--package', default='.', type=click.Path(), help='Pixie package name.', shell_complete=complete_library_packages)
@click.option('-s', '--script', default='.pixie.yaml', type=click.Path(), help='Path to the pixie script.')
def info_cli(job, package, script):
    config = PixieConfig.from_user()
    library = config.get('library', {})

    for package_name in library:
        lib_pkg = library[package_name]
        if job in lib_pkg:
            job_alias = lib_pkg[job]
            script = job_alias['script']
            package = job_alias['package']
            job = job_alias['job']
            break
    
    runtime = PixieConsoleRuntime(config)
    actual_job = engine.get_job(dict(
        package=package,
        job=job,
        script=script
    ), runtime)

    click.echo('Job: ' + colored(job, 'green') + ' ' + colored('(' + package + ')', 'grey'))
    if 'description' in actual_job:
        click.echo(colored(actual_job['description'], 'grey'))

    if '__script_url' in actual_job:
        click.echo('\nScript: ' + colored(actual_job.get('__script_url', '<auto generated>'), 'green'))
    else:
        click.echo('\nScript: <auto generated>')

    parameters = actual_job.get('parameters', [])

    if parameters:
        click.echo('\nParameters:')

        for p in actual_job.get('parameters', []):
            click.echo(f'  {p["name"]}: {colored(p.get("description"), "green")}')
    else:
        click.echo('\nParameters: None')


@click.command("completion", help="Return shell completion script.")
@click.argument('shell')
def completion_cli(shell: str):
    shell = shell.lower()
    os.system(f'_PIXIE_COMPLETE={shell}_source pixie')


@click.command("run", help="Used to run a pixie job.")
@click.argument('job', shell_complete=complete_library_aliases)
@click.option('-p', '--package', default='.', type=click.Path(), help='Package to run.', shell_complete=complete_library_packages)
@click.option('-s', '--script', default='.pixie.yaml', type=click.Path(), help='Path to the pixie script.')
@click.option('-c', '--context', multiple=True, help='Context values to set.')
@click.option('--context-from', type=click.Path(), help='File used to set context')
@click.option('-t', '--target', default='.', type=click.Path(), help='Directory to use when generating files')
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
@click.option('--log-level', default='info', help='The log level to output (debug, info, warning, error)')
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
cli.add_command(info_cli)
cli.add_command(completion_cli)


if __name__ == '__main__':
    cli()
