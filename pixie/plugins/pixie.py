from re import T
from pixie.context import PixieContext
from pixie.runtime import PixieRuntime
from pixie.steps import PixieStep
from ..plugin import PixiePluginContext
from ..engine import execute_scaffold
from ..rendering import render_options


def init(context: PixiePluginContext):
    context.add_step('pixie', PixieStep())

class PixieStep(PixieStep):
    def run(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        options = render_options(step, context)
        orig_package = context['__package']

        has_private_context = True
        actual_context = PixieContext(options.get('context', {}))
        actual_context['__package'] = orig_package
        actual_context['__target'] = context['__target']
        actual_context['env'] = context['env']

        execute_scaffold(actual_context, options, runtime)
        if has_private_context:
            context.todos.extend(actual_context.todos)
            context.notes.extend(actual_context.notes)
        context['__package'] = orig_package
