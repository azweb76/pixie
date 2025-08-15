# Pixie SDK - TypeScript Version

TypeScript-based tool used to run pixie scripts. Pixie scripts are YAML files that contain one or more jobs with parameters and steps.

## TypeScript Conversion

This project has been successfully converted from Python to TypeScript while maintaining the same functionality and CLI interface.

### Key Features

- **Same CLI Interface**: All original commands (`run`, `discover`, `info`, `list`) are preserved
- **YAML Configuration**: Compatible with existing `.pixie.yaml` files
- **Template Rendering**: Uses Nunjucks (equivalent to Jinja2) for templating
- **Plugin System**: Modular plugin architecture with core plugins
- **Type Safety**: Full TypeScript implementation with strong typing

### Installation

```bash
# Install dependencies
npm install

# Build the TypeScript code
npm run build

# Run the CLI
node dist/cli.js --help
```

### Usage

The CLI interface remains the same as the Python version:

```bash
# Run a pixie job
node dist/cli.js run hello -c name=John

# Discover pixies in a package
node dist/cli.js discover .

# List discovered pixies
node dist/cli.js list

# Show job information
node dist/cli.js info hello
```

### Example Pixie File

```yaml
name: hello-world

jobs:
  hello:
    parameters:
      - name: name
        description: Your name
        default: World
    steps:
      - print: Hello ${{ name }}!
      - add_note: This is a test note
      - add_todo: Remember to test more features
```

### Available Commands

| Command | Description |
|---------|-------------|
| `run` | Execute a pixie job with optional parameters |
| `discover` | Discover pixies in a package |
| `list` | List all discovered pixies |
| `info` | Show information for a specific job |

### Core Plugins

The TypeScript version includes the following core plugins:

- **print**: Display messages to console
- **log**: Log messages  
- **add_note**: Add notes that are displayed at the end
- **add_todo**: Add todos that are displayed at the end
- **set_context**: Set context variables
- **prompt**: Interactive prompts (basic implementation)

### Development

```bash
# Install dependencies
npm install

# Build in watch mode
npm run dev

# Run tests
npm test

# Clean build artifacts
npm run clean
```

### Architecture

The TypeScript version maintains the same architecture as the Python version:

- **Context**: Manages variables and state during execution
- **Runtime**: Handles I/O operations and user interaction
- **Engine**: Core execution engine that processes jobs and steps
- **Plugins**: Modular system for extending functionality
- **Rendering**: Template rendering using Nunjucks
- **CLI**: Command-line interface using Commander.js

### Migration from Python

The TypeScript version is designed to be a drop-in replacement for the Python version:

1. **Same CLI commands and options**
2. **Compatible with existing `.pixie.yaml` files**
3. **Same template syntax using `${{ variable }}` placeholders**
4. **Equivalent plugin system**

### Testing

```bash
# Run all tests
npm test

# Test CLI functionality
node dist/cli.js run hello -c name=TypeScript
```

### TypeScript Dependencies

- **Commander.js**: CLI framework (replaces Click)
- **Nunjucks**: Template engine (replaces Jinja2)
- **Inquirer**: Interactive prompts (replaces inquirer Python package)
- **js-yaml**: YAML parsing (replaces ruamel.yaml)
- **Jest**: Testing framework (replaces pytest)

The TypeScript implementation provides the same powerful pixie scripting capabilities with modern JavaScript tooling and type safety.