# Pixie SDK
Python-based CLI tool for running "pixie scripts" - YAML-based automation and templating system with plugin support.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Install Dependencies
- Install Poetry (Python package manager): `pip install poetry`
- Install all project dependencies: `poetry install`
  - **NEVER CANCEL**: Takes 2 seconds (cached) to 10 minutes (fresh install with 50+ packages including boto3, GitPython, etc.). Set timeout to 15+ minutes.
  - Dependencies include AWS SDK, GitHub API, Git tools, YAML processing, templating engines
- Verify installation: `poetry run pixie --help`

### Build Process
- Build the project: `poetry build`
  - Takes ~1 second
  - Creates wheel and sdist packages in `dist/` directory
- Clean build: `rm -rf dist/ && poetry build`

### Testing
- **KNOWN ISSUE**: Tests currently fail due to pytest 5.4.3 compatibility with Python 3.12
- Test command: `poetry run pytest` -- **FAILS with TypeError: required field "lineno" missing from alias**
- Manual testing via CLI: `poetry run pixie run [job] -c param=value`
- **Validation Scenarios**: Always test CLI functionality manually:
  - Run `poetry run pixie --help` to verify CLI works
  - Test with examples: `cd examples && poetry run pixie run hello -c fname=TestUser`
  - Create and run a simple pixie script to validate end-to-end functionality

### Code Quality and Formatting
- Format code: `poetry run autopep8 --in-place --recursive pixie/`
- **NOTE**: Black is in dev dependencies but not working in current environment - use autopep8

## CLI Usage and Examples

### Core Commands
- `poetry run pixie --help` - Show all available commands
- `poetry run pixie run [job]` - Run a pixie job
- `poetry run pixie info [job]` - Show job information
- `poetry run pixie discover` - Discover pixies in current directory
- `poetry run pixie list` - List all discovered pixies

### Running Pixie Scripts
```bash
# Run with context variables
poetry run pixie run hello -c fname=John -c lname=Doe

# Run with script file
poetry run pixie run greet -s /path/to/custom.pixie.yaml

# Run with context file
poetry run pixie run deploy --context-from config.yaml

# Run with target directory
poetry run pixie run generate -t ./output
```

### Example Pixie Script
```yaml
name: example
jobs:
  greet:
    parameters:
      - name: username
        description: Your name
        default: World
    steps:
      - print: Hello, ${{ username }}! Welcome to Pixie.
```

## Project Structure and Key Locations

### Important Files
- `pixie/engine.py` - Core execution engine for pixie scripts
- `pixie/cli.py` - Command-line interface implementation
- `pixie/context.py` - Context management and templating
- `pixie/plugins/` - Built-in plugin system (AWS, GitHub, config, etc.)
- `examples/` - Sample pixie scripts for testing
- `pyproject.toml` - Poetry configuration and dependencies
- `Makefile` - Alternative build commands

### Plugin System
Built-in plugins located in `pixie/plugins/`:
- `aws.py` - AWS capabilities (SSM parameters, etc.)
- `config.py` - Configuration file reading/writing
- `core.py` - Core steps (print, log)
- `fetch.py` - File and resource fetching
- `github.py` - GitHub API integration
- `shell.py` - Shell command execution

### Key Directories
```
pixie/                  # Main package
├── engine.py          # Core execution engine
├── cli.py             # CLI interface
├── context.py         # Context and templating
├── plugins/           # Plugin system
└── ...
examples/              # Sample scripts
tests/                 # Test suite (currently broken)
docs/plugins/          # Plugin documentation
```

## Validation Scenarios

### End-to-End Testing
After making any changes, run these complete scenarios:

1. **Basic CLI Test**:
   ```bash
   poetry run pixie --help
   # Should show usage and command list
   ```

2. **Example Script Execution**:
   ```bash
   cd examples
   poetry run pixie discover
   # Should show: 📦 Package: . (/path/to/examples/)
   
   poetry run pixie run hello -c fname=TestUser
   # Should exit cleanly (code 0), may not show output
   ```

3. **Custom Script Creation and Execution**:
   ```bash
   # Create test script
   cat > test.pixie.yaml << EOF
   name: test
   jobs:
     hello:
       parameters:
         - name: user
           default: World
       steps:
         - print: Hello \${{ user }}!
   EOF
   
   # Run it
   poetry run pixie run hello -s test.pixie.yaml -c user=Developer
   # Should execute without errors
   ```

4. **Debug Mode Verification**:
   ```bash
   poetry run pixie --log-level debug run hello -c fname=TestUser
   # Should show debug output including config file reading and execution steps
   ```

## Common Issues

### Making Changes
1. **Always run bootstrap first**: `poetry install` (NEVER CANCEL - wait up to 15 minutes)
2. **Test CLI works**: `poetry run pixie --help`
3. **Make your changes** to the relevant files in `pixie/`
4. **Format code**: `poetry run autopep8 --in-place --recursive pixie/`
5. **Build**: `poetry build` (~1 second)
6. **Manual validation**: Test with working examples

### Common Issues
Always validate changes with these steps:
1. **CLI Help**: `poetry run pixie --help` should work and show command list
2. **Example Run**: `cd examples && poetry run pixie run hello -c fname=TestUser` - should exit cleanly (code 0)
3. **Custom Script**: Create a simple test pixie script and run it - should execute without errors
4. **Build Success**: `poetry build` should complete and create files in `dist/`
5. **Debug Mode**: Use `poetry run pixie --log-level debug run [job]` to see detailed execution

**Note**: Pixie commands often complete silently with exit code 0. Use debug logging or check exit codes to verify success.

## Development Workflow
- **Tests Broken**: Don't try to fix pytest issues - use manual CLI testing
- **Poetry Warnings**: Ignore "poetry.dev-dependencies is deprecated" warnings
- **Plugin Errors**: Some plugins may need credentials (GitHub token, AWS credentials)
- **CLI Bugs**: Some CLI commands have bugs (e.g., `info` command has TypeError)

## Timing Expectations
- **Poetry Install**: 2 seconds (cached) to 10 minutes (fresh) - NEVER CANCEL
- **Poetry Build**: ~1 second
- **CLI Commands**: Near-instant for most operations
- **Plugin Operations**: Variable depending on external API calls

## Quick Reference

### Common Output Locations
```bash
ls -la
# .
# ..
# README.md
# Makefile
# pyproject.toml
# poetry.lock
# pixie/
# examples/
# tests/
# docs/
```

### Dependencies Overview
Core dependencies: Click (CLI), Jinja2 (templating), PyYAML (YAML processing), GitPython (Git operations), boto3 (AWS), PyGithub (GitHub API), requests (HTTP), inquirer (interactive prompts).

### Makefile Commands (Alternative)
- `make install` - Equivalent to `poetry install`
- `make build` - Equivalent to `poetry build`
- `make publish` - Publish to PyPI (requires authentication)

## Final Notes
- **ALWAYS** run `poetry install` first before any development work
- **NEVER CANCEL** long-running Poetry operations - they will complete
- Use manual CLI testing instead of pytest for validation
- Focus on the core engine (`engine.py`) and CLI (`cli.py`) for most changes
- The plugin system is well-structured - add new plugins in `pixie/plugins/`