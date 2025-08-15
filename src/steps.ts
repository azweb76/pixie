import { PixieContext } from './context';
import { PixieRuntime } from './runtime';
import { renderOptions, renderText, renderValue } from './rendering';

export interface StepOptions {
  [key: string]: any;
}

export interface Step {
  id?: string;
  action?: string;
  with?: StepOptions;
  if?: any;
  group?: Step[];
  foreach?: {
    items: any[];
    item_name?: string;
    steps: Step[];
  };
  description?: string;
  output_to_context?: string;
  on_error?: 'warn' | 'ignore';
  [key: string]: any;
}

export abstract class PixieStep {
  resolveFn(objName: string, fnName: string, context: PixieContext): any {
    // Override in subclasses
    return null;
  }

  abstract run(context: PixieContext, step: StepOptions, runtime: PixieRuntime): any;
}

export interface PluginContext {
  steps: Record<string, PixieStep>;
}

export class PixieStepExecution {
  private pluginContext: PluginContext;

  constructor(pluginContext: PluginContext) {
    this.pluginContext = pluginContext;
  }

  getExecutor(step: Step, stepName: string, context: PixieContext): [any, boolean] {
    const nameParts = stepName.split(':');
    const objName = nameParts[0];
    const fnName = nameParts.length > 1 ? nameParts.slice(1).join(':') : 'run';

    if (objName in this.pluginContext.steps) {
      console.debug(`Locating ${stepName} in plugin`);
      const stepPlugin = this.pluginContext.steps[objName];
      
      if (typeof (stepPlugin as any)[fnName] === 'function') {
        return [(stepPlugin as any)[fnName].bind(stepPlugin), true];
      } else if (typeof stepPlugin.resolveFn === 'function') {
        return [stepPlugin.resolveFn(objName, fnName, context), true];
      }
      
      console.warn(`${fnName} executor not found in context`);
    } else if (context.has(objName)) {
      console.debug(`Locating ${objName} in context`);
      const ctx = context.get(objName);
      
      if (ctx && typeof ctx[fnName] === 'function') {
        return [ctx[fnName].bind(ctx), false];
      }
      
      console.warn(`${fnName} executor not found in ${objName} context`);
    }
    
    return [null, false];
  }

  normalizeStep(step: Step): Step {
    if ('run' in step) {
      return {
        action: 'shell',
        with: {
          command: step.run
        },
        ...step
      };
    } else if ('log' in step) {
      return {
        action: 'log',
        with: {
          message: step.log
        },
        ...step
      };
    } else if ('print' in step) {
      return {
        action: 'print',
        with: {
          message: step.print
        },
        ...step
      };
    } else if ('prompt' in step) {
      return {
        action: 'prompt',
        with: step.prompt,
        ...step
      };
    } else if ('dump' in step) {
      return {
        action: 'dump',
        with: {
          message: step.dump
        },
        ...step
      };
    } else if ('set_context' in step) {
      return {
        action: 'set_context',
        with: step.set_context,
        ...step
      };
    } else if ('pixie' in step) {
      return {
        action: 'pixie',
        with: step.pixie,
        ...step
      };
    }
    
    return step;
  }

  private async _execute(step: Step, context: PixieContext, runtime: PixieRuntime, stepsContext: any): Promise<void> {
    if (step.if !== undefined) {
      const enabled = renderValue(step.if, context);
      if (enabled === false) {
        return;
      }
    }

    if (step.group) {
      await this.execute(context, runtime, stepsContext, step.group);
    } else if (step.foreach) {
      const foreachSteps = step.foreach;
      const items = renderValue(foreachSteps.items || [], context);
      const contextName = foreachSteps.item_name;
      const stepId = step.id || 'foreach';
      
      for (const item of items) {
        context.setStep(stepId, item);
        if (contextName) {
          context.set(contextName, item);
        }
        await this.execute(context, runtime, stepsContext, foreachSteps.steps || []);
      }
    } else {
      const actionName = step.action;
      if (!actionName) {
        throw new Error('Step must have an action');
      }

      const [executor, isPlugin] = this.getExecutor(step, actionName, context);
      console.debug(step);

      if (executor) {
        let stepOptions = step.with || {};
        const stepId = step.id || actionName;
        const description = renderText(step.description || null, context);
        
        if (description) {
          console.info(`[${stepId}] ${description}`);
        }
        
        console.debug(`[${stepId}] running`);
        
        let result: any;
        if (isPlugin) {
          if (typeof stepOptions === 'object' && stepOptions !== null) {
            (stepOptions as any).__id = stepId;
          }
          console.debug(`${stepId}:`, stepOptions);
          result = await executor(context, stepOptions, runtime);
        } else {
          if (typeof stepOptions === 'object' && stepOptions !== null && !Array.isArray(stepOptions)) {
            stepOptions = renderOptions(stepOptions, context);
            const args = (stepOptions as any).args || [stepOptions];
            const kwargs = (stepOptions as any).kwargs || {};
            
            if ('args' in stepOptions && !('kwargs' in stepOptions)) {
              result = await executor(...args);
            } else if (!('args' in stepOptions) && 'kwargs' in stepOptions) {
              result = await executor(kwargs);
            } else {
              result = await executor(...args, kwargs);
            }
          } else {
            result = await executor(renderValue(stepOptions, context));
          }
        }

        if (step.output_to_context) {
          const outputToContext = renderText(step.output_to_context, context);
          if (outputToContext) {
            context.set(outputToContext, result);
          }
        }
        
        context.setStep(stepId, result);
      }
    }
  }

  async execute(context: PixieContext, runtime: PixieRuntime, stepsContext: any, steps: Step[]): Promise<void> {
    for (const stepRaw of steps) {
      const step = this.normalizeStep(stepRaw);
      const onError = step.on_error;
      
      try {
        await this._execute(step, context, runtime, stepsContext);
      } catch (error) {
        if (onError === 'warn') {
          console.warn(error);
        } else if (onError === 'ignore') {
          console.debug(error);
        } else {
          throw error;
        }
      }
    }
  }
}