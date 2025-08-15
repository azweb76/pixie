import { PixieStep } from '../steps';
import { PixieContext } from '../context';
import { PixieRuntime, PixieConsoleRuntime } from '../runtime';
import { PixiePluginContext } from '../plugin';
import { renderOptions, renderText, renderValue } from '../rendering';
import { merge } from '../utils';

export function init(context: PixiePluginContext): void {
  context.addStep('set_context', new SetStep());
  context.addStep('add_note', new AddNoteStep());
  context.addStep('add_todo', new AddTodoStep());
  context.addStep('prompt', new PromptStep());
  context.addStep('print', new PrintStep());
  context.addStep('log', new LogStep());
}

export class SetStep extends PixieStep {
  run(context: PixieContext, step: Record<string, any>, runtime: PixieRuntime): any {
    for (const [contextName, value] of Object.entries(step)) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        const newOptions = renderOptions(value, context);
        if (context.has(contextName)) {
          const existing = context.get(contextName) || {};
          merge(newOptions, existing);
          context.set(contextName, existing);
        } else {
          context.set(contextName, newOptions);
        }
      } else {
        context.set(contextName, renderValue(value, context));
      }
    }
  }
}

export class AddNoteStep extends PixieStep {
  run(context: PixieContext, step: Record<string, any>, runtime: PixieRuntime): void {
    const message = renderText(step.message || step, context);
    if (message) {
      context.notes.push(message);
    }
  }
}

export class AddTodoStep extends PixieStep {
  run(context: PixieContext, step: Record<string, any>, runtime: PixieRuntime): void {
    const message = renderText(step.message || step, context);
    if (message) {
      context.todos.push(message);
    }
  }
}

export class PromptStep extends PixieStep {
  async run(context: PixieContext, step: Record<string, any>, runtime: PixieRuntime): Promise<any> {
    const options = renderOptions(step, context);
    const value = await runtime.ask(options);
    const outputToContext = step.name;
    if (outputToContext) {
      context.set(outputToContext, value);
    }
    return value;
  }
}

export class PrintStep extends PixieStep {
  run(context: PixieContext, step: Record<string, any>, runtime: PixieRuntime): void {
    const message = renderText(step.message || step, context);
    if (message) {
      runtime.write(message + '\n');
    }
  }
}

export class LogStep extends PixieStep {
  run(context: PixieContext, step: Record<string, any>, runtime: PixieRuntime): void {
    const message = renderText(step.message || step, context);
    if (message && runtime instanceof PixieConsoleRuntime) {
      (runtime as PixieConsoleRuntime).log(message);
    }
  }
}