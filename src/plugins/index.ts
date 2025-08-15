import * as fs from 'fs';
import * as path from 'path';

export interface PluginModule {
  init: (context: any) => void;
}

export function loadPlugins(): PluginModule[] {
  // For now, manually load the core plugin since we're in development
  // In a production environment, this would scan the plugins directory
  const corePlugin = require('./core');
  return [corePlugin];
}

export function getPathToPlugins(): string {
  return path.join(__dirname, 'plugins');
}