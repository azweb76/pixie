#!/usr/bin/env node

import { Command } from 'commander';
import * as path from 'path';
import * as fs from 'fs';
import { __version__ } from './index';
import { PixieConfig } from './config';
import { PixieContext } from './context';
import { PixieConsoleRuntime } from './runtime';
import { run } from './engine';
import { readJson, readYaml, merge } from './utils';
import * as colors from 'colors';

function expanduser(filePath: string): string {
  if (filePath.startsWith('~/')) {
    return path.join(require('os').homedir(), filePath.slice(2));
  }
  return filePath;
}

interface CliContext {
  [key: string]: any;
}

function parseContextOption(value: string, previous: CliContext): CliContext {
  const eqIdx = value.indexOf('=');
  if (eqIdx === -1) {
    throw new Error(`Invalid context format: ${value}. Expected format: key=value`);
  }
  
  const parameterName = value.substring(0, eqIdx);
  const parameterValue = value.substring(eqIdx + 1);
  previous[parameterName] = parameterValue;
  return previous;
}

async function runCommand(
  job: string,
  options: {
    package?: string;
    script?: string;
    context?: CliContext;
    contextFrom?: string;
    target?: string;
  }
): Promise<void> {
  const config = PixieConfig.fromUser();
  const library = config.get('library') || {};

  // Read context from various sources
  const fileContext = readJson(options.contextFrom || '', {});
  
  const userContextFile = path.resolve(expanduser('~/.pixie/context.yaml'));
  const userContext = readYaml(userContextFile, {});
  
  const cwdContextFile = path.resolve('./.pixierc.yaml');
  const cwdContext = readYaml(cwdContextFile, {});

  const pContext = options.context || {};

  try {
    // Merge contexts with priority: file < user < cwd < command line
    let ctx = merge(fileContext, userContext);
    ctx = merge(cwdContext, ctx);
    ctx = merge(pContext, ctx);

    const context = new PixieContext({
      env: process.env,
      __target: options.target || process.cwd()
    });

    // Check if job is an alias
    let actualJob = job;
    let actualPackage = options.package || '.';
    let actualScript = options.script || '.pixie.yaml';

    for (const packageName of Object.keys(library)) {
      const libPkg = library[packageName];
      if (job in libPkg) {
        const jobAlias = libPkg[job];
        actualScript = jobAlias.script;
        actualPackage = jobAlias.package;
        actualJob = jobAlias.job;
        break;
      }
    }

    await run(context, {
      script: actualScript,
      job: actualJob,
      package: actualPackage,
      context: ctx
    }, new PixieConsoleRuntime(config));

  } catch (error) {
    if (error instanceof Error && error.message === 'User cancelled prompt') {
      // Handle Ctrl+C gracefully
      console.log('\nOperation cancelled.');
      process.exit(0);
    }
    throw error;
  }
}

async function discoverCommand(
  packagePath: string = '.',
  options: { save?: boolean }
): Promise<void> {
  console.log(`🔍 Discovering pixies in package: ${colors.green(packagePath)}`);
  console.log('📦 Discovery functionality not yet implemented in TypeScript version');
  
  if (options.save) {
    console.log(colors.grey('Note: Save functionality not yet implemented'));
  }
}

async function listCommand(): Promise<void> {
  const config = PixieConfig.fromUser();
  const library = config.get('library') || {};

  console.log('📝 Discovered pixies:');
  
  for (const packageName of Object.keys(library)) {
    const pkg = library[packageName];
    console.log(colors.grey(`${packageName}:`));
    for (const aliasName of Object.keys(pkg)) {
      const alias = pkg[aliasName];
      console.log(`  ${colors.green(aliasName)}: ${alias.description || 'No description'}`);
    }
  }
}

async function infoCommand(
  job: string,
  options: {
    package?: string;
    script?: string;
  }
): Promise<void> {
  console.log(`ℹ️  Job info: ${colors.green(job)}`);
  console.log(colors.grey('Info functionality not yet implemented in TypeScript version'));
  
  if (options.package) {
    console.log(`Package: ${colors.grey(options.package)}`);
  }
  if (options.script) {
    console.log(`Script: ${colors.grey(options.script)}`);
  }
}



const program = new Command();

program
  .name('pixie')
  .description('TypeScript-based tool used to run pixie scripts')
  .version(__version__);

program
  .command('run <job>')
  .description('Used to run a pixie job')
  .option('-p, --package <package>', 'Package to run', '.')
  .option('-s, --script <script>', 'Path to the pixie script', '.pixie.yaml')
  .option('-c, --context <context>', 'Context values to set (key=value)', parseContextOption, {})
  .option('--context-from <file>', 'File used to set context')
  .option('-t, --target <target>', 'Directory to use when generating files', '.')
  .action(runCommand);

program
  .command('discover [package]')
  .description('Discover pixies in a package')
  .option('-s, --save', 'Save discovered pixies to library')
  .action(discoverCommand);

program
  .command('list')
  .description('List all discovered pixies')
  .action(listCommand);

program
  .command('info <job>')
  .description('Show information for a job')
  .option('-p, --package <package>', 'Pixie package name', '.')
  .option('-s, --script <script>', 'Path to the pixie script', '.pixie.yaml')
  .action(infoCommand);

// Handle uncaught exceptions and unhandled rejections
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

export { program };

// If this file is run directly, parse the command line arguments
if (require.main === module) {
  program.parse();
}