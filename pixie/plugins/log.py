from charset_normalizer import logging
from pixie.context import PixieContext
from ..runtime import PixieRuntime
from ..steps import PixieStep
from ..plugin import PixiePluginContext
from ..rendering import render_text


_log = logging.getLogger(__name__)


def init(context: PixiePluginContext):
    context.add_step('log', LogStep())
    context.add_step('debug', DebugStep())
    context.add_step('print', PrintStep())


class LogStep(PixieStep):
    # def resolve_fn(self, obj_name, fn_name, context):
    #     return getattr(_log, fn_name), False

    def run(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        message = render_text(step['message'], context)
        _log.info(message)


class DebugStep(PixieStep):
    def run(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        message = render_text(step['message'], context)
        _log.debug(message)


class PrintStep(PixieStep):
    def run(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        message = render_text(step['message'], context)
        print(message)
