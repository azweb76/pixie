import { PixieRuntime } from './runtime';
import { PixieStep } from './steps';

export abstract class PixiePlugin {
  abstract init(runtime: PixieRuntime): void;
}

export class PixiePluginContext extends Map<string, any> {
  public steps: Record<string, PixieStep> = {};

  addStep(stepName: string, step: PixieStep): void {
    this.steps[stepName] = step;
  }
}