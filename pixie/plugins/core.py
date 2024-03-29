from collections import abc
import importlib
import importlib
from importlib import util
import subprocess
import sys
import os

from ..utils import merge
from pixie.context import PixieContext
from pixie.runtime import PixieRuntime
from ..steps import PixieStep
from ..plugin import PixiePluginContext
from ..rendering import render_options, render_text, render_value


def init(context: PixiePluginContext):
    context.add_step("set_context", SetStep())
    context.add_step("add_note", AddNoteStep())
    context.add_step("add_todo", AddTodoStep())
    context.add_step("module", ModuleStep())
    context.add_step("file", FileStep())
    context.add_step("prompt", PromptStep())


class PromptStep(PixieStep):
    def run(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        options = render_options(step, context)
        value = runtime.ask(options)
        output_to_context = step.get('name')
        if output_to_context:
            context[output_to_context] = value


class SetStep(PixieStep):   
    def run(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        context_names = step
        for context_name in context_names:
            if isinstance(context_names[context_name], abc.Mapping):
                new_options = render_options(context_names[context_name], context)
                if context_name in context:
                    merge(new_options, context[context_name])
                else:
                    context[context_name] = new_options
            else:
                context[context_name] = render_value(
                    context_names[context_name], context)


class AddNoteStep(PixieStep):
    def run(self, context: PixieContext, step: str, runtime: PixieRuntime):
        message = render_text(step, context)
        context.notes.append(message)


class AddTodoStep(PixieStep):
    def run(self, context: PixieContext, step: str, runtime: PixieRuntime):
        message = render_text(step, context)
        context.todos.append(message)


class ModuleStep(PixieStep):
    def run(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        options = render_options(step, context)

        install_dependencies(options.get('dependencies', []))

        file = context.resolve_package_path(options['path'])
        spec = util.spec_from_file_location("module.name", file)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        main_fn = getattr(foo, 'main')

        module_context = PixieContext(
            **render_options(options.get('context', {}), context),
            __target=context.get('__target', os.getcwd())
        )

        return main_fn(module_context, options, runtime)


class FileStep(PixieStep):
    def write(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        options = render_options(step, context)

        path = context.resolve_target_path(options['path'])
        content = str(options.get('content'))

        with open(path, 'w') as fhd:
            fhd.write(content)
    
    def read(self, context: PixieContext, step: dict, runtime: PixieRuntime):
        options = render_options(step, context)

        path = context.resolve_target_path(options['path'])

        with open(path, 'r') as fhd:
            return fhd.read()


def install_dependencies(dependencies):
    for dep in dependencies:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
