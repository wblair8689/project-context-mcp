# Project Context MCP Server

A Model Context Protocol (MCP) server that provides unified project context and monitoring capabilities for development projects.

## Features

- **Project Status Monitoring**: Get comprehensive project health and readiness metrics
- **Build Diagnostics**: Track build errors, warnings, and solutions (when Xcode monitoring enabled)
- **Git Integration**: Monitor repository status, branches, and commits
- **Infrastructure Checking**: Validate project structure and dependencies
- **Conversation Context**: Initialize development sessions with full project context
- **Configurable Monitoring**: Enable/disable specific monitoring features per project

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd project-context-mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Standalone Server
```bash
python run_modular_server.py --project-root /path/to/your/project --transport stdio
```

### As MCP Server
Add to your Claude configuration:
```json
{
  "mcpServers": {
    "project-context": {
      "command": "python",
      "args": ["/path/to/project-context-mcp/run_modular_server.py", "--project-root", "/path/to/your/project"],
      "cwd": "/path/to/project-context-mcp"
    }
  }
}
```

## Configuration

The server creates a `config/project_config.json` file in your project directory with settings:

- `project_name`: Display name for your project
- `current_phase`: Development phase description
- `xcode_monitoring.enabled`: Enable/disable Xcode-specific features
- `feature_groups`: Project components to monitor

## Available Tools

- `get_project_status()`: Get unified project status and health metrics
- `get_diagnostics()`: Get build errors and warnings with solutions
- `build()`: Trigger build and get immediate feedback
- `fix_error(error_message, solution)`: Apply fix and record solution

## License

MIT License
