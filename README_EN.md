# AI Unit Test Generation Tool

This tool uses artificial intelligence to automatically generate unit tests for Python code. It can detect code changes in a Git repository and generate corresponding test code for new or modified functions and methods.

## Features

- Automatically detect Python files changed between Git commits
- Parse functions and methods in Python files
- Generate high-quality unit tests using the OpenAI API
- Support test generation for class methods and standalone functions
- Automatically save generated tests to a specified directory

## Installation Requirements

- Python 3.8 or higher
- Git command-line tool

### Installing Dependencies

All dependencies are listed in the `requirements.txt` file. You can install all dependencies at once with the following command:

```bash
pip install -r requirements.txt
```

This will install the following main dependencies:

- requests: for API calls
- pytest: for running generated tests
- tk: for the GUI interface
- fastapi, uvicorn: for the Web version
- javalang: for Java code parsing
- pygithub: for GitHub integration

## Configuration

All configuration options are in the `config.py` file. You can modify these settings as needed.

### API Key Setup

Before using, you need to set up an OpenAI API key. There are two ways:

1. Set in the `config.py` file:

   ```python
   OPENAI_CONFIG = {
       "api_key": "YOUR_API_KEY",
       ...
   }
   ```

2. Set an environment variable:

   ```bash
   # Windows
   set OPENAI_API_KEY=YOUR_API_KEY

   # Linux/Mac
   export OPENAI_API_KEY=YOUR_API_KEY
   ```

### Other Configuration Options

The `config.py` file contains the following configuration sections:

1. **GENERATED_TESTS_DIR**: Directory where generated test files are saved
2. **OPENAI_CONFIG**: OpenAI API related settings
3. **GIT_CONFIG**: Git related settings
4. **TEST_CONFIG**: Test generation related settings
5. **PROMPT_TEMPLATE**: Prompt template used for test generation

## Usage

This tool provides two interfaces: a command-line interface and a graphical user interface.

## Graphical User Interface (GUI)

The GUI provides a more intuitive way to interact with the tool, suitable for users who are not familiar with the command line.

### Starting the GUI

```bash
python gui.py
```

### GUI Features

1. **Select Python File**: Choose a Python file to generate tests for using the "Browse" button
2. **Select AI Model**: Choose an AI model from the dropdown menu
3. **Select Save Directory**: Specify where to save the generated test files
4. **Select Code Snippet**: Choose a function or method from the loaded file
5. **Generate Test**: Click the "Generate Test" button to create a test using the selected AI model
6. **Save Test**: Save the generated test to the specified directory

### GUI Layout

The GUI is divided into two main areas:

- Left side displays the source code
- Right side displays the generated test code

The top area contains controls for selecting files, models, and save directories. The bottom has a status bar showing the current operation status.

## Command Line Interface (CLI)

The command line interface is suitable for automation scripts and CI/CD integration.

### Basic Usage

```bash
python initial.py
```

This will compare changes between the current commit (HEAD) and its parent (HEAD~1), and generate tests for all changed Python files.

### Specify AI Model

You can specify which AI model to use with the `--model` parameter:

```bash
python initial.py --model=<model_name>
```

Where `<model_name>` is a model name defined in the configuration file. The following models are supported:

- `openai_gpt35`: OpenAI ChatGPT (GPT-3.5)
- `openai_gpt4`: OpenAI GPT-4
- `azure_openai`: Azure OpenAI Service
- `anthropic_claude`: Anthropic Claude
- `google_gemini`: Google Gemini
- `xai_grok`: xAI Grok
- `deepseek`: DeepSeek

### Specify Commits

```bash
# Specify current commit
python initial.py [--model=<model_name>] <current_commit>

# Specify previous and current commits
python initial.py [--model=<model_name>] <previous_commit> <current_commit>
```

### Command Line Examples

```bash
# Compare current commit with its parent using the default model
python initial.py

# Use GPT-4 model
python initial.py --model=openai_gpt4

# Compare specific commit with its parent using Claude model
python initial.py --model=anthropic_claude abc123def456

# Compare two specific commits using Azure OpenAI
python initial.py --model=azure_openai abc123def456 ghi789jkl012
```

## Generated Tests

Generated tests will be saved in the `tests/generated` directory. Each test file is named as:

- For functions: `test_generated_<original_file_name>_<function_name>.py`
- For methods: `test_generated_<original_file_name>_<class_name>_<method_name>.py`

## Detailed Configuration Options

You can modify the following settings in the `config.py` file:

```python
# Directory where generated tests will be saved
GENERATED_TESTS_DIR = pathlib.Path("tests/generated")

# AI model configuration
AI_MODELS = {
    # Currently used model name
    "current_model": "openai_gpt35",

    # Available model configurations
    "models": {
        # OpenAI GPT-3.5 configuration
        "openai_gpt35": {
            "provider": "openai",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),  # Get API key from environment variable
            "api_base": "https://api.openai.com/v1",  # OpenAI API base URL
            "model": "gpt-3.5-turbo",  # AI model to use
            "temperature": 0.7,  # Randomness of generation (0.0-1.0)
            "max_tokens": 2000,  # Maximum tokens to generate
            "timeout": 30,  # API request timeout in seconds
        },

        # OpenAI GPT-4 configuration
        "openai_gpt4": {
            "provider": "openai",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "api_base": "https://api.openai.com/v1",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 60,
        },

        # Azure OpenAI configuration
        "azure_openai": {
            "provider": "azure_openai",
            "api_key": os.environ.get("AZURE_OPENAI_API_KEY", ""),
            "api_base": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            "deployment_name": os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            "api_version": "2023-05-15",
            "temperature": 0.7,
            "max_tokens": 2000,
            "timeout": 30,
        },

        # Anthropic Claude configuration
        "anthropic_claude": {
            "provider": "anthropic",
            "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "api_base": "https://api.anthropic.com/v1",
            "model": "claude-2",
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 60,
        }
    }
}

# Git configuration
GIT_CONFIG = {
    "default_current_commit": "HEAD",  # Default current commit
    "default_previous_commit": None,   # Default previous commit (None means use parent of current commit)
}

# Test generation configuration
TEST_CONFIG = {
    "test_file_prefix": "test_generated_",  # Prefix for generated test files
    "use_pytest": True,  # Use pytest framework
}
```

## Workflow

1. The script uses Git commands to get a list of Python files changed between two commits
2. For each changed file, it uses an AST parser to extract functions and methods
3. For each function or method, it builds a prompt and calls the selected AI model API to generate test code
4. It saves the generated test code to the `tests/generated` directory

## Notes

- Ensure your Git repository is up-to-date and the working directory is clean
- API calls may incur charges depending on the billing model of your chosen AI service provider
- Generated tests may need manual adjustments to fit specific project structures
- For complex functions, you may need to provide more context or write tests manually
- Different AI models may generate tests of varying quality, choose the appropriate model for your needs

## Troubleshooting

- If you encounter Git command errors, make sure you're running the script in a Git repository
- If API calls fail, check your API key and network connection
- If generated tests are incomplete, try increasing the `max_tokens` parameter
- If a particular AI model is unavailable, try switching to another model
- For GUI interface issues, ensure your Python environment supports Tkinter

## Contributing

Issue reports and improvement suggestions are welcome.

## License

[MIT License](LICENSE)
