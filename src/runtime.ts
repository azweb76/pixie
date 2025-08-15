import * as url from 'url';
import inquirer from 'inquirer';
import { PixieContext } from './context';
import { PixieConfig } from './config';
import { renderText } from './rendering';

export const CLI_COLORS = {
  PURPLE: '\x1b[35m',
  CYAN: '\x1b[36m',
  BLUE: '\x1b[34m',
  GREY: '\x1b[90m',
  GREEN: '\x1b[32m',
  YELLOW: '\x1b[33m',
  RED: '\x1b[31m',
  BOLD: '\x1b[1m',
  UNDERLINE: '\x1b[4m',
  ITALIC: '\x1b[3m',
  END: '\x1b[0m',
};

export function str2bool(v: any): boolean {
  if (v === null || v === undefined) {
    return false;
  }
  const str = String(v).toLowerCase();
  return ['yes', 'true', 't', '1', 'y'].includes(str);
}

export function str2url(value: string): url.UrlWithStringQuery {
  return url.parse(String(value));
}

export function str2giturl(value: string): any {
  // For simplicity, we'll use a basic git URL parser
  // In a real implementation, you'd want to use a proper git URL parsing library
  const gitUrlRegex = /^(https?:\/\/|git@)([^\/]+)[\/:]([^\/]+)\/(.+?)(?:\.git)?$/;
  const match = String(value).match(gitUrlRegex);
  
  if (match) {
    return {
      protocol: match[1].includes('@') ? 'ssh' : 'https',
      host: match[2],
      owner: match[3],
      name: match[4]
    };
  }
  
  return { protocol: '', host: '', owner: '', name: value };
}

export const knownTypes: Record<string, (v: any) => any> = {
  int: (v: any) => parseInt(String(v), 10),
  bool: str2bool,
  str: (v: any) => String(v),
  float: (v: any) => parseFloat(String(v)),
  checklist: (v: any) => Array.isArray(v) ? v : [v],
  confirm: str2bool,
  url: str2url,
  giturl: str2giturl,
};

export function convert(v: any, type?: string): any {
  if (type && type in knownTypes) {
    return knownTypes[type](v);
  }
  return String(v);
}

export interface PromptOptions {
  name?: string;
  description?: string;
  default?: any;
  validate?: string;
  type?: string;
  choices?: string[];
  secure?: boolean;
}

export abstract class PixieRuntime {
  public config: PixieConfig;

  constructor(config: PixieConfig) {
    this.config = config;
  }

  abstract write(message: string, format?: boolean): void;
  abstract ask(prompt: PromptOptions): Promise<any>;
  abstract printTodos(context: PixieContext): void;
  abstract printNotes(context: PixieContext): void;
}

export class PixieConsoleRuntime extends PixieRuntime {
  log(message: string): void {
    this.write(message + '\n');
  }

  async ask(prompt: PromptOptions): Promise<any> {
    const name = prompt.name || 'value';
    const defaultValue = prompt.default;
    const validate = prompt.validate;
    const description = prompt.description || name;
    const promptType = prompt.type;
    
    let validateFn: ((input: string) => boolean | string) | undefined;
    
    if (validate) {
      validateFn = (input: string) => {
        const regex = new RegExp(validate);
        return regex.test(input) || `Input must match pattern: ${validate}`;
      };
    } else if (defaultValue === undefined) {
      validateFn = (input: string) => {
        return input.length > 0 || 'Input is required';
      };
    }

    try {
      let result: any;
      
      if (promptType === 'checklist') {
        result = await inquirer.prompt([{
          type: 'checkbox',
          name: 'value',
          message: description,
          default: defaultValue,
          choices: prompt.choices || []
        }]);
        return result.value;
      } else if (prompt.choices && prompt.choices.length > 0) {
        result = await inquirer.prompt([{
          type: 'list',
          name: 'value',
          message: description,
          choices: prompt.choices,
          default: defaultValue,
          validate: validateFn
        }]);
        return convert(result.value, promptType);
      } else if (promptType === 'confirm') {
        result = await inquirer.prompt([{
          type: 'confirm',
          name: 'value',
          message: description,
          default: defaultValue
        }]);
        return result.value;
      } else if (prompt.secure) {
        result = await inquirer.prompt([{
          type: 'password',
          name: 'value',
          message: description,
          default: defaultValue,
          validate: validateFn
        }]);
        return convert(result.value, promptType);
      } else {
        result = await inquirer.prompt([{
          type: 'input',
          name: 'value',
          message: description,
          default: defaultValue,
          validate: validateFn
        }]);
        return convert(result.value, promptType);
      }
    } catch (error) {
      throw new Error('User cancelled prompt');
    }
  }

  write(message: string, format: boolean = false): void {
    if (format) {
      // Replace color placeholders with actual ANSI codes
      let formattedMessage = message;
      for (const [key, value] of Object.entries(CLI_COLORS)) {
        formattedMessage = formattedMessage.replace(new RegExp(`{${key}}`, 'g'), value);
      }
      process.stdout.write(formattedMessage);
    } else {
      process.stdout.write(message);
    }
  }

  printTodos(context: PixieContext): void {
    if (context.todos.length > 0) {
      this.write(`\n{GREEN}{BOLD}TODO:{END}\n`, true);
      for (const todo of context.todos) {
        const todoStr = renderText(todo, context);
        this.write(` [ ] ${todoStr}\n`);
      }
    }
  }

  printNotes(context: PixieContext): void {
    if (context.notes.length > 0) {
      this.write(`\n{BLUE}{BOLD}NOTES:{END}\n`, true);
      for (const note of context.notes) {
        const noteStr = renderText(note, context);
        this.write(`${noteStr}\n`);
      }
    }
  }
}