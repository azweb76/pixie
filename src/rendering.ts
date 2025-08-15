import * as nunjucks from 'nunjucks';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import * as os from 'os';
import { PixieContext } from './context';
import * as yaml from 'js-yaml';

export class RenderUtils {
  private context: PixieContext;

  constructor(context: PixieContext) {
    this.context = context;
  }

  static readFile(filePath: string, parse: boolean = false): any {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      if (parse) {
        const ext = path.extname(filePath).toLowerCase();
        if (ext === '.json') {
          return JSON.parse(content);
        } else if (ext === '.yaml' || ext === '.yml') {
          return yaml.load(content);
        }
      }
      return content;
    } catch (error) {
      console.error(`Error reading file ${filePath}:`, error);
      return null;
    }
  }

  static readJson(filePath: string): any {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error(`Error reading JSON file ${filePath}:`, error);
      return null;
    }
  }

  static readYaml(filePath: string): any {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      return yaml.load(content);
    } catch (error) {
      console.error(`Error reading YAML file ${filePath}:`, error);
      return null;
    }
  }

  static randomString(length: number = 16, specialChars: string = ''): string {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789" + specialChars;
    const randomBytes = crypto.randomBytes(length);
    return Array.from(randomBytes, byte => chars[byte % chars.length]).join('');
  }

  checksum(filePath: string): string {
    try {
      const content = fs.readFileSync(filePath);
      return crypto.createHash('md5').update(content).digest('hex');
    } catch (error) {
      console.error(`Error calculating checksum for ${filePath}:`, error);
      return '';
    }
  }

  pathExists(filePath: string): boolean {
    return fs.existsSync(filePath);
  }

  joinArrays(...arrays: any[][]): any[] {
    return arrays.flat();
  }

  dirs(dirPath: string): string[] {
    try {
      return fs.readdirSync(dirPath).filter(item => {
        return fs.statSync(path.join(dirPath, item)).isDirectory();
      });
    } catch (error) {
      console.error(`Error reading directory ${dirPath}:`, error);
      return [];
    }
  }

  files(dirPath: string): string[] {
    try {
      return fs.readdirSync(dirPath).filter(item => {
        return fs.statSync(path.join(dirPath, item)).isFile();
      });
    } catch (error) {
      console.error(`Error reading directory ${dirPath}:`, error);
      return [];
    }
  }
}

export class GitUtils {
  remoteInfo(repoPath: string, remoteName: string): any {
    // Simplified git remote info - in a real implementation you'd use a git library
    console.debug(`Getting remote info for ${repoPath}/${remoteName}`);
    return {};
  }
}

export function formatList(value: any[], format: string = '{value}'): string {
  if (!Array.isArray(value)) {
    return String(value);
  }
  return value.map(item => format.replace('{value}', String(item))).join(', ');
}

export function yamlFormat(value: any): string {
  return yaml.dump(value);
}

export function jsonFormat(value: any): string {
  return JSON.stringify(value, null, 2);
}

export function joinPath(basePath: string, addedPath: string): string {
  return path.join(basePath, addedPath);
}

function getUtils(context: PixieContext) {
  return {
    utils: new RenderUtils(context),
    git: new GitUtils(),
    path: path,
    os: os
  };
}

function createEnvironment(variableStart = '${{', variableEnd = '}}', trimBlocks = true): nunjucks.Environment {
  const env = new nunjucks.Environment(null, {
    trimBlocks,
    lstripBlocks: true,
    tags: {
      variableStart,
      variableEnd
    }
  });

  // Add custom filters
  env.addFilter('formatlist', formatList);
  env.addFilter('yaml', yamlFormat);
  env.addFilter('json', jsonFormat);
  env.addFilter('join_path', joinPath);

  return env;
}

export function renderValue(text: any, context: PixieContext): any {
  if (text === null || text === undefined) {
    return text;
  }

  if (typeof text !== 'string') {
    return text;
  }

  if (text.includes('\n')) {
    return renderText(text, context);
  }

  const env = createEnvironment();
  const utils = getUtils(context);
  
  // Convert context Map to object for template rendering
  const contextObj: Record<string, any> = {};
  for (const [key, value] of context.entries()) {
    contextObj[key] = value;
  }

  try {
    const template = nunjucks.compile(text, env);
    return template.render({ context: contextObj, ...utils, ...contextObj });
  } catch (error) {
    console.error('Error rendering value:', error);
    return text;
  }
}

export function renderText(text: string | null, context: PixieContext): string | null {
  if (text === null || text === undefined) {
    return text;
  }

  const env = createEnvironment();
  const utils = getUtils(context);
  
  // Convert context Map to object for template rendering
  const contextObj: Record<string, any> = {};
  for (const [key, value] of context.entries()) {
    contextObj[key] = value;
  }

  try {
    const template = nunjucks.compile(text, env);
    return template.render({ context: contextObj, ...utils, ...contextObj });
  } catch (error) {
    console.error('Error rendering text:', error);
    return text;
  }
}

function _renderValue(value: any, context: PixieContext, excludeKeys: string[] = []): any {
  if (typeof value === 'string') {
    return renderValue(value, context);
  } else if (Array.isArray(value)) {
    return value.map(item => _renderValue(item, context, []));
  } else if (typeof value === 'object' && value !== null) {
    const result: Record<string, any> = {};
    for (const [key, val] of Object.entries(value)) {
      if (excludeKeys.includes(key)) {
        result[key] = val;
      } else {
        result[key] = _renderValue(val, context, []);
      }
    }
    return result;
  }
  return value;
}

export function renderOptions(options: Record<string, any>, context: PixieContext, excludeKeys: string[] = []): Record<string, any> {
  return _renderValue(options, context, excludeKeys);
}

export function renderTokenFile(filePath: string, tokens: Record<string, string>): string {
  const content = fs.readFileSync(filePath, 'utf8');
  return renderTokens(content, tokens);
}

export function renderTokens(content: string, tokens: Record<string, string>): string {
  let result = content;
  for (const [token, replacement] of Object.entries(tokens)) {
    result = result.replace(new RegExp(token, 'g'), replacement);
  }
  return result;
}