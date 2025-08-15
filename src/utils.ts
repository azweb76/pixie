import * as yaml from 'js-yaml';
import * as fs from 'fs';
import * as path from 'path';

export function readConfig(filePath: string, defaultValue: any = null): any {
  if (filePath && fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath).toLowerCase();
    if (ext === '.json') {
      return readJson(filePath, defaultValue);
    } else if (ext === '.yaml' || ext === '.yml') {
      return readYaml(filePath, defaultValue);
    }
  }
  return defaultValue;
}

export function readJson(filePath: string, defaultValue: any = null): any {
  if (filePath && fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error(`Error reading JSON file ${filePath}:`, error);
    }
  }
  return defaultValue;
}

export function readYaml(filePath: string, defaultValue: any = null): any {
  if (filePath && fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const value = yaml.load(content);
      if (value) {
        return value;
      }
    } catch (error) {
      console.error(`Error reading YAML file ${filePath}:`, error);
    }
  }
  return defaultValue;
}

export function saveYaml(data: any, filePath: string): void {
  try {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    const yamlContent = yaml.dump(data);
    fs.writeFileSync(filePath, yamlContent, 'utf8');
  } catch (error) {
    console.error(`Error saving YAML file ${filePath}:`, error);
    throw error;
  }
}

export function merge(source: Record<string, any>, destination: Record<string, any>): Record<string, any> {
  for (const [key, value] of Object.entries(source)) {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      // Get node or create one
      const node = destination[key] || {};
      destination[key] = node;
      merge(value, node);
    } else {
      destination[key] = value;
    }
  }
  return destination;
}