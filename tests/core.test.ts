import { PixieContext } from '../src/context';
import { PixieConfig } from '../src/config';

describe('Pixie Core Functionality', () => {
  let config: PixieConfig;
  let context: PixieContext;

  beforeEach(() => {
    config = new PixieConfig();
    context = new PixieContext();
  });

  test('should create context with default values', () => {
    expect(context.get('colors')).toBeDefined();
    expect(context.notes).toEqual([]);
    expect(context.todos).toEqual([]);
  });

  test('should set and get context values', () => {
    context.set('test', 'value');
    expect(context.get('test')).toBe('value');
  });

  test('should add notes and todos', () => {
    context.notes.push('Test note');
    context.todos.push('Test todo');
    
    expect(context.notes).toContain('Test note');
    expect(context.todos).toContain('Test todo');
  });

  test('should resolve paths when package and target are set', () => {
    context.set('__package', { path: '/test/package' });
    context.set('__target', '/test/target');
    
    const packagePath = context.resolvePackagePath('file.txt');
    const targetPath = context.resolveTargetPath('output.txt');
    
    expect(packagePath).toContain('file.txt');
    expect(targetPath).toContain('output.txt');
  });

  test('should create config from data', () => {
    const config = new PixieConfig({ key: 'value' });
    expect(config.get('key')).toBe('value');
  });
});