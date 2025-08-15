import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { PixieContext } from './context';
import { PixieRuntime, convert } from './runtime';
import { PixiePluginContext } from './plugin';
import { PixieStepExecution } from './steps';
import { renderOptions, renderText, renderValue } from './rendering';
import { loadPlugins } from './plugins';

export interface PixiePackageInfo {
  path: string;
  options: any;
}

export interface PixieOptions {
  package: string;
  script?: string;
  job?: string;
  context?: Record<string, any>;
  steps?: any[];
  [key: string]: any;
}

export function readParameter(prompt: any, context: PixieContext, runtime: PixieRuntime): Promise<any> {
  const defaultValue = prompt.default || null;

  if (prompt.if !== undefined) {
    const enabled = prompt.if;
    if (!enabled) {
      return Promise.resolve(defaultValue);
    }
  }

  return runtime.ask(prompt);
}

export function locateScaffoldFile(basePath: string, name: string): string | null {
  const basePaths = [basePath];
  const extensions = ['.yaml', '.yml', '.json', ''];
  const names = [name, `.${name}`, path.join(name, '.pixie')];

  for (const baseDir of basePaths) {
    for (const ext of extensions) {
      for (const n of names) {
        const fullPath = path.join(baseDir, n + ext);
        console.debug(`Locating pixie script using ${fullPath}`);
        if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
          return fullPath;
        }
      }
    }
  }
  return null;
}

export async function processParameters(
  parameters: any[] | undefined,
  context: PixieContext,
  runtime: PixieRuntime
): Promise<void> {
  if (!parameters) return;

  for (const parameter of parameters) {
    const parameterOverrides = runtime.config.get('parameterOverrides');
    if (parameterOverrides) {
      const pName = parameter.name;
      for (const pOverride of parameterOverrides) {
        if (pOverride.names && pOverride.names.includes(pName)) {
          Object.assign(parameter, pOverride.overrides || {});
          break;
        }
      }
    }

    const parameterName = parameter.name;
    const contextSource = parameter.context_source || parameterName;
    const contextTarget = parameter.context_target || parameterName;

    if (context.has(contextSource)) {
      context.set(contextTarget, convert(context.get(contextSource), parameter.type || 'str'));
    } else {
      const parameterOptions = renderOptions(parameter, context);
      const value = await readParameter(parameterOptions, context, runtime);
      context.set(contextTarget, value);
    }
  }
}

export async function executeScaffold(
  context: PixieContext,
  options: PixieOptions,
  runtime: PixieRuntime
): Promise<void> {
  const packageName = options.package;
  const script = options.script || '.pixie.yaml';

  let pkgDir: string;
  if (context.has('__package')) {
    pkgDir = context.resolvePackagePath(packageName);
  } else {
    pkgDir = packageName;
  }

  if (!fs.existsSync(pkgDir)) {
    throw new Error(`Package directory not found: ${pkgDir}`);
  }

  console.debug(`Using local package '${pkgDir}'`);

  const scaffoldFile = locateScaffoldFile(pkgDir, script);
  console.debug(`Using pixie file: ${scaffoldFile}`);

  if (scaffoldFile) {
    pkgDir = path.dirname(scaffoldFile);
  }

  const jobName = options.job || 'default';
  let config: any;

  if (scaffoldFile) {
    const content = fs.readFileSync(scaffoldFile, 'utf8');
    config = yaml.load(content);
  } else if (jobName === 'scaffold') {
    config = {
      jobs: {
        [jobName]: {
          steps: options.steps || [{
            action: 'fetch',
            with: {
              source: '${{ source | default(".") }}'
            }
          }]
        }
      }
    };
  } else {
    config = { jobs: {} };
  }

  // Add todos and notes from config
  if (config.todos) {
    context.todos.push(...config.todos);
  }
  if (config.notes) {
    context.notes.push(...config.notes);
  }

  const pluginContext = new PixiePluginContext();
  
  // Load and initialize plugins
  const plugins = loadPlugins();
  for (const plugin of plugins) {
    plugin.init(pluginContext);
  }
  
  const stepExecution = new PixieStepExecution(pluginContext);

  // Process context
  const contextOptions = renderOptions(config.context || {}, context);
  for (const [key, value] of Object.entries(contextOptions)) {
    context.set(key, value);
  }

  const optionsContext = renderOptions(options.context || {}, context);
  for (const [key, value] of Object.entries(optionsContext)) {
    context.set(key, value);
  }

  await processParameters(config.parameters, context, runtime);

  context.set('__package', {
    path: pkgDir,
    options
  });

  const stepsContext = {};
  context.set('steps', stepsContext);

  const job = config.jobs?.[jobName] || {};

  // Process job context
  const jobContextOptions = renderOptions(job.context || {}, context);
  for (const [key, value] of Object.entries(jobContextOptions)) {
    context.set(key, value);
  }

  await processParameters(job.parameters, context, runtime);

  if (!context.has('__target')) {
    context.set('__target', process.cwd());
  }

  const steps = job.steps || [];
  await stepExecution.execute(context, runtime, stepsContext, steps);
}

export async function run(context: PixieContext, options: PixieOptions, runtime: PixieRuntime): Promise<PixieContext> {
  await executeScaffold(context, options, runtime);

  runtime.printTodos(context);
  runtime.printNotes(context);

  return context;
}