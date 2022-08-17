from collections.abc import Mapping
import logging

from pixie.rendering import render_options, render_text, render_value
from .context import PixieContext
from .runtime import PixieRuntime


_log = logging.getLogger(__name__)

class PixieStep:
    def resolve_fn(self, obj_name: str, fn_name: str, context: PixieContext):
        pass
    def run(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        pass


class PixieStepExecution():
    def __init__(self, plugin_context) -> None:
        self.plugin_context = plugin_context
    
    def get_executor(self, step, step_name: str, context):
        name_parts = step_name.split(':')
        obj_name = name_parts[0]
        fn_name = name_parts[1] if len(name_parts) > 1 else 'run'

        if obj_name in self.plugin_context.steps:
            _log.debug('locating %s in plugin', step_name)
            step_plugin = self.plugin_context.steps[obj_name]
            if hasattr(step_plugin, fn_name):
                return getattr(step_plugin, fn_name), True
            else:
                if hasattr(step_plugin, 'resolve_fn'):
                    return step_plugin.resolve_fn(obj_name, fn_name, context, step)
            _log.warning('%s executor not found in context', fn_name)

        elif obj_name in context:
            _log.debug('locating %s in context', obj_name)
            ctx = context[obj_name]
            if hasattr(ctx, fn_name):
                return getattr(ctx, fn_name), False
            _log.warning('%s executor not found in context', fn_name)
        return None, False
    
    def normalize_step(self, step):
        if 'run' in step:
            return dict({
                'action': 'shell',
                'with': {
                    'command': step['run']
                }
            }, **step)
        elif 'log' in step:
            return dict({
                'action': 'log',
                'with': {
                    'message': step['log']
                }
            }, **step)
        elif 'print' in step:
            return dict({
                'action': 'print',
                'with': {
                    'message': step['print']
                }
            }, **step)
        elif 'set_context' in step:
            return dict({
                'action': 'set_context',
                'with': step['set_context']
            }, **step)
        elif 'pixie' in step:
            return dict({
                'action': 'pixie',
                'with': step['pixie']
            }, **step)
        return step

    def execute(self, context: PixieContext, runtime, steps_context, steps):
        step: dict
        for step in steps:
            step = self.normalize_step(step)
            if 'if' in step:
                enabled = render_value(step['if'], context)
                if enabled == False:
                    continue
            if 'group' in step:
                group_steps = step['group']
                self.execute(context, runtime, steps_context, group_steps)
            elif 'foreach' in step:
                foreach_steps = step['foreach']
                items = render_value(foreach_steps.get('items', []), context)
                context_name = foreach_steps.get('item_name', None)
                step_id = step.get('id', 'foreach')
                for item in items:
                    context.set_step(step_id, item)
                    if context_name is not None:
                        context[context_name] = item
                    self.execute(context, runtime, steps_context, foreach_steps.get('steps', []))
            else:
                executor = None
                executor_step_name = None
                is_plugin = False
                action_name = step.get('action', None)
                executor, is_plugin = self.get_executor(step, action_name, context)
                _log.debug(step)
                if executor:
                    step_options = step.get('with', {})

                    step_id = step.get('id', action_name)
                    description = render_text(step.get('description', None), context)
                    if description:
                        _log.info(f'[{step_id}] {description}')
                    
                    _log.debug(f'[{step_id}] running')
                    if is_plugin:
                        if isinstance(executor_step_name, Mapping):
                            step_options['__id'] = step_id
                        _log.debug('%s: %s', step_id, step_options);
                        result = executor(context, step_options, runtime)
                    else:
                        if isinstance(step_options, Mapping):
                            step_options = render_options(step_options, context)
                            args = step_options.get('args', [step_options])
                            kwargs = step_options.get('kwargs', {})
                            result = executor(*args, **kwargs)
                        else:
                            result = executor(render_value(step_options, context))
                    if 'output_to_context' in step:
                        context[step['output_to_context']] = result
                    context.set_step(step_id, result)
