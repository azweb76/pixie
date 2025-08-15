import * as fs from 'fs';
import * as path from 'path';

export interface PluginModule {
  init: (context: any) => void;
}

export function loadPlugins(): PluginModule[] {
  const pluginsPath = getPathToPlugins();
  const modules: PluginModule[] = [];
  
  try {
    if (fs.existsSync(pluginsPath)) {
      const files = fs.readdirSync(pluginsPath);
      
      for (const file of files) {
        if (file.endsWith('.js') && !file.startsWith('index.')) {
          try {
            const modulePath = path.join(pluginsPath, file);
            const module = require(modulePath);
            if (module.init && typeof module.init === 'function') {
              modules.push(module);
            }
          } catch (error) {
            console.error(`Error loading plugin ${file}:`, error);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error loading plugins:', error);
  }
  
  return modules;
}

export function getPathToPlugins(): string {
  return path.join(__dirname, 'plugins');
}