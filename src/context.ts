import * as path from 'path';

export interface PixiePackage {
  path: string;
  [key: string]: any;
}

export class PixieContext extends Map<string, any> {
  public notes: string[] = [];
  public todos: string[] = [];

  constructor(data: Record<string, any> = {}) {
    super();
    
    // Initialize default values
    this.set('steps', {});
    this.set('colors', {
      PURPLE: '\x1b[35m',
      CYAN: '\x1b[36m',
      BLUE: '\x1b[34m',
      GREEN: '\x1b[32m',
      YELLOW: '\x1b[33m',
      RED: '\x1b[31m',
      BOLD: '\x1b[1m',
      UNDERLINE: '\x1b[4m',
      ITALIC: '\x1b[3m',
      END: '\x1b[0m',
    });

    // Set initial data
    for (const [key, value] of Object.entries(data)) {
      this.set(key, value);
    }
  }

  resolvePackagePath(filePath: string): string {
    const packageInfo = this.get('__package') as PixiePackage;
    if (!packageInfo || !packageInfo.path) {
      throw new Error('Package path not set in context');
    }
    return path.resolve(path.join(packageInfo.path, filePath));
  }

  resolveTargetPath(filePath: string): string {
    const targetDir = this.get('__target') as string;
    if (!targetDir) {
      throw new Error('Target directory not set in context');
    }
    return path.resolve(path.join(targetDir, filePath));
  }

  setStep(stepId: string, value: any): void {
    const steps = this.get('steps') as Record<string, any>;
    steps[stepId] = value;
  }

  // Helper methods to work with Map interface like a dictionary
  public [Symbol.iterator](): IterableIterator<[string, any]> {
    return super[Symbol.iterator]();
  }

  // Add compatibility methods for Python-like dict access
  public getItem(key: string): any {
    return this.get(key);
  }

  public setItem(key: string, value: any): void {
    this.set(key, value);
  }

  public hasItem(key: string): boolean {
    return this.has(key);
  }
}