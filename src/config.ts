import * as os from 'os';
import * as path from 'path';
import { saveYaml, readYaml } from './utils';

export class PixieConfig extends Map<string, any> {
  public file?: string;

  constructor(data: Record<string, any> = {}) {
    super();
    for (const [key, value] of Object.entries(data)) {
      this.set(key, value);
    }
  }

  static fromUser(): PixieConfig {
    const configFile = path.resolve(path.join(os.homedir(), '.pixie', 'config.yaml'));
    const config = PixieConfig.fromFile(configFile);
    config.file = configFile;
    return config;
  }

  saveUser(): void {
    if (!this.file) {
      throw new Error('Config file path not set');
    }
    const data: Record<string, any> = {};
    for (const [key, value] of this.entries()) {
      data[key] = value;
    }
    saveYaml(data, this.file);
  }

  static fromFile(filePath: string): PixieConfig {
    console.debug(`Reading config file ${filePath}`);
    const data = readYaml(filePath, {});
    return new PixieConfig(data);
  }
}