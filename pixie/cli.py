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


def apply_cli(job, script, package, context, context_from, target):
    file_context = utils.read_json(context_from, {})

    user_context_file = os.path.realpath(os.path.expanduser('~/.pixie/context.json'))
    user_context = utils.read_json(user_context_file, {})
    file_context = utils.read_json(context_from, {})
    p_context = PixieContext(
        env=os.environ,
        __target=target
    )

    c: str
    for c in context:
        eq_idx = c.index('=')
        parameter_name = c[0:eq_idx]
        parameter_value = c[eq_idx+1:]
        p_context[parameter_name] = parameter_value
    engine.run(p_context, {
        'script': script,
        'job': job,
        'package': package,
        'context': utils.merge(file_context, user_context)
    }, PixieConsoleRuntime())

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
#@click.group()
@click.argument('job')
@click.argument('package')
@click.version_option(__version__)
@click.option('-s', '--script', default='.pixie.yaml', help='Path to the pixie script.')
@click.option('-c', '--context', multiple=True, help='Context values to set.')
@click.option('--context-from', help='File used to set context')
@click.option('--target', default='.', help='Directory to use when generating files')
@click.option('--log-level', default='info', help='The log level to output')
def cli(job, script, package, context, context_from, target, log_level):
    stdout_hdlr = logging.StreamHandler(stream=sys.stdout)
    stdout_hdlr.setFormatter(AddColorFormatter())

    logging.root.handlers.clear()

    loglevel_str = log_level.upper()
    loglevel = getattr(logging, loglevel_str)

    stdout_hdlr.setLevel(loglevel)
    logging.root.setLevel(loglevel)
    logging.root.addHandler(stdout_hdlr)
    
    apply_cli(job, script, package, context, context_from, target)

#cli.add_command(apply_cli)

if __name__ == '__main__':
    cli()
