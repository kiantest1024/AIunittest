import subprocess
import ast
import os
import pathlib
import sys
import json
import requests
from typing import List, Dict, Optional, Any

# 导入配置
try:
    from config import (
        GENERATED_TESTS_DIR,
        AI_MODELS,
        GIT_CONFIG,
        TEST_CONFIG,
        PROMPT_TEMPLATE
    )
except ImportError:
    # 如果找不到配置文件，使用默认配置
    print("警告: 未找到配置文件 'config.py'，使用默认配置。", file=sys.stderr)

    # 定义生成的测试文件保存目录
    GENERATED_TESTS_DIR = pathlib.Path("tests/generated")

    # AI 模型配置
    AI_MODELS = {
        # 当前使用的模型名称
        "current_model": "openai_gpt35",

        # 可用模型配置
        "models": {
            # OpenAI GPT-3.5 配置
            "openai_gpt35": {
                "provider": "openai",
                "api_key": os.environ.get("OPENAI_API_KEY", ""),  # 优先从环境变量获取API密钥
                "api_base": "https://api.openai.com/v1",  # OpenAI API 基础 URL
                "model": "gpt-3.5-turbo",  # 使用的 AI 模型
                "temperature": 0.7,  # 生成的随机性 (0.0-1.0)
                "max_tokens": 2000,  # 生成的最大令牌数
                "timeout": 30,  # API 请求超时时间（秒）
            }
        }
    }

    # Git配置
    GIT_CONFIG = {
        "default_current_commit": "HEAD",  # 默认当前提交
        "default_previous_commit": None,   # 默认前一个提交（None表示使用当前提交的父提交）
    }

    # 测试生成配置
    TEST_CONFIG = {
        "test_file_prefix": "test_generated_",  # 生成的测试文件前缀
        "use_pytest": True,  # 使用pytest框架
    }

    # 提示模板配置
    PROMPT_TEMPLATE = """
请为以下 Python {code_type} 生成单元测试代码:

```python
{code}
```

请生成完整的测试代码，包括必要的导入语句、测试函数和断言。
测试应该全面覆盖代码的功能，包括正常情况和边缘情况。
使用 pytest 框架，并遵循以下指南:

1. 测试函数名应以 'test_' 开头
2. 使用描述性的测试函数名称
3. 为每个测试用例添加清晰的注释
4. 包含必要的 mock 对象或测试夹具
5. 使用有意义的断言消息
6. 考虑边缘情况和异常处理

假设可以使用以下导入语句: {import_statement}

请仅返回测试代码，不要包含任何解释或额外的文本。
"""

def get_changed_python_files(previous_commit: str = None, current_commit: str = 'HEAD') -> List[str]:
    """
    使用 git diff 获取两个提交之间更改的 Python 文件列表。
    如果未提供 previous_commit，则将当前提交与其父提交进行比较。

    参数:
        previous_commit: 前一个提交的 SHA。默认为 current_commit 的父提交。
        current_commit: 当前提交的 SHA。默认为 HEAD。

    返回:
        更改的 Python 文件（.py）路径列表。
    """
    try:
        if previous_commit:
            # 比较两个特定的提交
            diff_command = ["git", "diff", "--name-only", previous_commit, current_commit]
        else:
            # 将当前提交与其父提交进行比较（适用于单次提交触发的场景）
            diff_command = ["git", "diff", "--name-only", f"{current_commit}~1", current_commit]

        # 执行 git 命令
        result = subprocess.run(diff_command, capture_output=True, text=True, check=True)
        changed_files = result.stdout.strip().splitlines()

        # 过滤 Python 文件并确保它们存在（例如，排除已删除的文件）
        python_files = [
            file_path for file_path in changed_files
            if file_path.endswith(".py") and os.path.exists(file_path)
        ]
        return python_files

    except subprocess.CalledProcessError as e:
        print(f"执行 git 命令时出错: {e}", file=sys.stderr)
        print(f"命令: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"错误输出: {e.stderr}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("错误: 未找到 'git' 命令。请确保 Git 已安装并在您的 PATH 中。", file=sys.stderr)
        return []

def parse_python_file(file_path: str) -> List[Dict[str, Any]]:
    """
    解析 Python 文件以提取函数和方法的代码片段。

    参数:
        file_path: Python 文件的路径。

    返回:
        字典列表，每个字典包含:
        - 'name': 函数或方法的名称。
        - 'type': 'function' 或 'method'。
        - 'code': 函数或方法的源代码。
        - 'class_name': 父类的名称（如果类型是 'method'），否则为 None。
    """
    code_snippets = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        # 辅助函数，用于获取 AST 节点的源代码
        def get_source_segment(source: str, node: ast.AST) -> str:
            # ast.get_source_segment 在 Python 3.8+ 中可用
            # 对于较旧的版本，您可能需要不同的方法或库
            # 此实现是简化的，假设使用 Python 3.8+
            try:
                # 获取节点的精确源代码段
                lines = source.splitlines(True)  # True 参数保留行尾换行符
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno is not None else start_line + 1
                start_col = node.col_offset
                end_col = node.end_col_offset if hasattr(node, 'end_col_offset') and node.end_col_offset is not None else None

                # 处理多行节点
                if start_line == end_line - 1:
                    return lines[start_line][start_col:end_col]
                else:
                    code_lines = lines[start_line:end_line]
                    code_lines[0] = code_lines[0][start_col:]
                    if end_col is not None:
                        code_lines[-1] = code_lines[-1][:end_col]
                    return "".join(code_lines)

            except Exception as e:
                print(f"警告: 无法获取节点 {node} 的源代码段: {e}", file=sys.stderr)
                # 回退: 返回整个文件内容（不太理想）或空字符串
                return ""


        # 使用 NodeVisitor 正确识别类中的方法
        class CodeExtractor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # 访问函数和方法
                # 检查是否在类定义内部（是否为方法）
                in_class = False
                class_name = None

                # 获取父节点的上下文
                for parent_ctx in reversed(self.context):
                    if isinstance(parent_ctx, ast.ClassDef):
                        in_class = True
                        class_name = parent_ctx.name
                        break

                source_segment = get_source_segment(source_code, node)
                if source_segment:
                    code_snippets.append({
                        'name': node.name,
                        'type': 'method' if in_class else 'function',
                        'code': source_segment,
                        'class_name': class_name
                    })
                self.generic_visit(node)  # 继续访问子节点

            def visit_ClassDef(self, node):
                # 访问类定义
                self.generic_visit(node)  # 访问类的子节点

        # 创建访问器并添加上下文跟踪
        visitor = CodeExtractor()
        visitor.context = []

        # 添加上下文跟踪方法
        original_generic_visit = visitor.generic_visit

        def generic_visit_with_context(node):
            visitor.context.append(node)
            original_generic_visit(node)
            visitor.context.pop()

        visitor.generic_visit = generic_visit_with_context
        visitor.visit(tree)


    except FileNotFoundError:
        print(f"错误: 在 {file_path} 找不到文件", file=sys.stderr)
        return []
    except Exception as e:
        print(f"解析文件 {file_path} 时出错: {e}", file=sys.stderr)
        return []

    # 过滤掉由于访问者模式逻辑导致的重复项
    unique_snippets = {}
    for snippet in code_snippets:
        # 使用 (name, type, class_name) 元组作为唯一键
        key = (snippet['name'], snippet['type'], snippet['class_name'])
        unique_snippets[key] = snippet  # 这将保留给定键的最后一个遇到的片段

    return list(unique_snippets.values())


def generate_tests_with_ai(code_snippet: Dict[str, Any], model_name: str = None) -> Optional[str]:
    """
    与 AI 模型交互生成单元测试代码。

    参数:
        code_snippet: 包含 'name', 'type', 'code', 'class_name' 的字典。
        model_name: 要使用的AI模型名称，如果为None则使用配置中的当前模型。

    返回:
        包含生成的测试代码的字符串，如果生成失败则返回 None。
    """
    # 获取要使用的模型配置
    if model_name is None:
        model_name = AI_MODELS["current_model"]

    if model_name not in AI_MODELS["models"]:
        print(f"错误: 未找到名为 '{model_name}' 的模型配置。", file=sys.stderr)
        return None

    model_config = AI_MODELS["models"][model_name]
    provider = model_config["provider"]

    print(f"--- 为{code_snippet['type']} '{code_snippet['name']}' 调用 AI ({provider}/{model_name}) 生成测试 ...")

    # 检查 API 密钥是否已设置
    if not model_config["api_key"]:
        print(f"错误: 未设置 {provider} API 密钥。请在配置文件中设置 'api_key' 或设置相应的环境变量。", file=sys.stderr)
        return None

    # 构建提示
    module_name = os.path.basename(os.path.dirname(os.path.abspath(".")))

    # 确定代码类型和导入语句
    if code_snippet['type'] == 'function':
        import_statement = f"from {module_name} import {code_snippet['name']}"
        code_type = "函数"
    else:  # method
        import_statement = f"from {module_name} import {code_snippet['class_name']}"
        code_type = f"类 {code_snippet['class_name']} 的方法"

    # 使用配置中的提示模板
    prompt = PROMPT_TEMPLATE.format(
        code_type=code_type,
        code=code_snippet['code'],
        import_statement=import_statement
    )

    # 根据不同的提供商调用不同的API
    try:
        if provider == "openai":
            return _call_openai_api(prompt, model_config)
        elif provider == "azure_openai":
            return _call_azure_openai_api(prompt, model_config)
        elif provider == "anthropic":
            return _call_anthropic_api(prompt, model_config)
        elif provider == "google":
            return _call_google_api(prompt, model_config)
        elif provider == "grok":
            return _call_grok_api(prompt, model_config)
        elif provider == "deepseek":
            return _call_deepseek_api(prompt, model_config)
        else:
            print(f"错误: 不支持的AI提供商 '{provider}'", file=sys.stderr)
            return None
    except Exception as e:
        print(f"调用 AI API 时出错: {e}", file=sys.stderr)
        return None


def _call_openai_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """调用 OpenAI API 生成测试代码"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }

        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }

        response = requests.post(
            f"{config['api_base']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=config["timeout"]
        )

        if response.status_code != 200:
            print(f"API 调用失败，状态码: {response.status_code}", file=sys.stderr)
            print(f"响应: {response.text}", file=sys.stderr)
            return None

        # 解析响应
        response_data = response.json()
        test_code = response_data["choices"][0]["message"]["content"].strip()

        # 如果响应包含 ```python 和 ``` 标记，则提取其中的代码
        if "```python" in test_code and "```" in test_code:
            start_idx = test_code.find("```python") + len("```python")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()
        elif "```" in test_code:
            start_idx = test_code.find("```") + len("```")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()

        print(f"--- 成功生成测试代码 ({len(test_code)} 字符)")
        return test_code

    except requests.RequestException as e:
        print(f"OpenAI API 请求异常: {e}", file=sys.stderr)
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"处理 OpenAI API 响应时出错: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"OpenAI API 调用时发生未知错误: {e}", file=sys.stderr)
        return None


def _call_azure_openai_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """调用 Azure OpenAI API 生成测试代码"""
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": config["api_key"]
        }

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }

        response = requests.post(
            f"{config['api_base']}/openai/deployments/{config['deployment_name']}/chat/completions?api-version={config['api_version']}",
            headers=headers,
            json=payload,
            timeout=config["timeout"]
        )

        if response.status_code != 200:
            print(f"Azure OpenAI API 调用失败，状态码: {response.status_code}", file=sys.stderr)
            print(f"响应: {response.text}", file=sys.stderr)
            return None

        # 解析响应
        response_data = response.json()
        test_code = response_data["choices"][0]["message"]["content"].strip()

        # 如果响应包含 ```python 和 ``` 标记，则提取其中的代码
        if "```python" in test_code and "```" in test_code:
            start_idx = test_code.find("```python") + len("```python")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()
        elif "```" in test_code:
            start_idx = test_code.find("```") + len("```")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()

        print(f"--- 成功生成测试代码 ({len(test_code)} 字符)")
        return test_code

    except requests.RequestException as e:
        print(f"Azure OpenAI API 请求异常: {e}", file=sys.stderr)
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"处理 Azure OpenAI API 响应时出错: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Azure OpenAI API 调用时发生未知错误: {e}", file=sys.stderr)
        return None


def _call_anthropic_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """调用 Anthropic API 生成测试代码"""
    try:
        # 检查是否使用新版Claude API (Claude 3)
        if "claude-3" in config["model"]:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": config["api_key"],
                "anthropic-version": "2023-06-01"
            }

            payload = {
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"]
            }

            response = requests.post(
                f"{config['api_base']}/messages",
                headers=headers,
                json=payload,
                timeout=config["timeout"]
            )

            if response.status_code != 200:
                print(f"Anthropic API 调用失败，状态码: {response.status_code}", file=sys.stderr)
                print(f"响应: {response.text}", file=sys.stderr)
                return None

            # 解析响应
            response_data = response.json()
            test_code = response_data["content"][0]["text"].strip()
        else:
            # 旧版Claude API
            headers = {
                "Content-Type": "application/json",
                "x-api-key": config["api_key"],
                "anthropic-version": "2023-06-01"
            }

            payload = {
                "model": config["model"],
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "temperature": config["temperature"],
                "max_tokens_to_sample": config["max_tokens"]
            }

            response = requests.post(
                f"{config['api_base']}/complete",
                headers=headers,
                json=payload,
                timeout=config["timeout"]
            )

            if response.status_code != 200:
                print(f"Anthropic API 调用失败，状态码: {response.status_code}", file=sys.stderr)
                print(f"响应: {response.text}", file=sys.stderr)
                return None

            # 解析响应
            response_data = response.json()
            test_code = response_data["completion"].strip()

        # 如果响应包含 ```python 和 ``` 标记，则提取其中的代码
        if "```python" in test_code and "```" in test_code:
            start_idx = test_code.find("```python") + len("```python")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()
        elif "```" in test_code:
            start_idx = test_code.find("```") + len("```")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()

        print(f"--- 成功生成测试代码 ({len(test_code)} 字符)")
        return test_code

    except requests.RequestException as e:
        print(f"Anthropic API 请求异常: {e}", file=sys.stderr)
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"处理 Anthropic API 响应时出错: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Anthropic API 调用时发生未知错误: {e}", file=sys.stderr)
        return None


def _call_google_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """调用 Google Gemini API 生成测试代码"""
    try:
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": config["temperature"],
                "maxOutputTokens": config["max_tokens"],
                "topP": 0.95,
                "topK": 40
            }
        }

        response = requests.post(
            f"{config['api_base']}/models/{config['model']}:generateContent?key={config['api_key']}",
            headers=headers,
            json=payload,
            timeout=config["timeout"]
        )

        if response.status_code != 200:
            print(f"Google Gemini API 调用失败，状态码: {response.status_code}", file=sys.stderr)
            print(f"响应: {response.text}", file=sys.stderr)
            return None

        # 解析响应
        response_data = response.json()
        test_code = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # 如果响应包含 ```python 和 ``` 标记，则提取其中的代码
        if "```python" in test_code and "```" in test_code:
            start_idx = test_code.find("```python") + len("```python")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()
        elif "```" in test_code:
            start_idx = test_code.find("```") + len("```")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()

        print(f"--- 成功生成测试代码 ({len(test_code)} 字符)")
        return test_code

    except requests.RequestException as e:
        print(f"Google Gemini API 请求异常: {e}", file=sys.stderr)
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"处理 Google Gemini API 响应时出错: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Google Gemini API 调用时发生未知错误: {e}", file=sys.stderr)
        return None


def _call_grok_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """调用 xAI Grok API 生成测试代码"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }

        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }

        response = requests.post(
            f"{config['api_base']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=config["timeout"]
        )

        if response.status_code != 200:
            print(f"Grok API 调用失败，状态码: {response.status_code}", file=sys.stderr)
            print(f"响应: {response.text}", file=sys.stderr)
            return None

        # 解析响应
        response_data = response.json()
        test_code = response_data["choices"][0]["message"]["content"].strip()

        # 如果响应包含 ```python 和 ``` 标记，则提取其中的代码
        if "```python" in test_code and "```" in test_code:
            start_idx = test_code.find("```python") + len("```python")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()
        elif "```" in test_code:
            start_idx = test_code.find("```") + len("```")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()

        print(f"--- 成功生成测试代码 ({len(test_code)} 字符)")
        return test_code

    except requests.RequestException as e:
        print(f"Grok API 请求异常: {e}", file=sys.stderr)
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"处理 Grok API 响应时出错: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Grok API 调用时发生未知错误: {e}", file=sys.stderr)
        return None


def _call_deepseek_api(prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """调用 DeepSeek API 生成测试代码"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }

        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }

        response = requests.post(
            f"{config['api_base']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=config["timeout"]
        )

        if response.status_code != 200:
            print(f"DeepSeek API 调用失败，状态码: {response.status_code}", file=sys.stderr)
            print(f"响应: {response.text}", file=sys.stderr)
            return None

        # 解析响应
        response_data = response.json()
        test_code = response_data["choices"][0]["message"]["content"].strip()

        # 如果响应包含 ```python 和 ``` 标记，则提取其中的代码
        if "```python" in test_code and "```" in test_code:
            start_idx = test_code.find("```python") + len("```python")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()
        elif "```" in test_code:
            start_idx = test_code.find("```") + len("```")
            end_idx = test_code.rfind("```")
            test_code = test_code[start_idx:end_idx].strip()

        print(f"--- 成功生成测试代码 ({len(test_code)} 字符)")
        return test_code

    except requests.RequestException as e:
        print(f"DeepSeek API 请求异常: {e}", file=sys.stderr)
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"处理 DeepSeek API 响应时出错: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"DeepSeek API 调用时发生未知错误: {e}", file=sys.stderr)
        return None

def save_generated_test(original_file_path: str, snippet_info: Dict[str, Any], test_code: str) -> None:
    """
    将生成的测试代码保存到指定目录。

    参数:
        original_file_path: 原始 Python 文件的路径。
        snippet_info: 包含代码片段详细信息的字典 ('name', 'type', 'class_name')。
        test_code: 生成的测试代码字符串。
    """
    if not test_code:
        print(f"未为 {snippet_info['name']} 生成测试代码。跳过保存。", file=sys.stderr)
        return

    # 如果生成的测试目录不存在，则创建它
    GENERATED_TESTS_DIR.mkdir(parents=True, exist_ok=True)

    # 根据原始文件和代码片段名称生成文件名
    original_file_name = pathlib.Path(original_file_path).stem
    snippet_name = snippet_info['name']
    class_name = snippet_info['class_name']
    test_file_name = f"{TEST_CONFIG['test_file_prefix']}{original_file_name}_{class_name or ''}{'_' if class_name else ''}{snippet_name}.py"
    test_file_path = GENERATED_TESTS_DIR / test_file_name

    try:
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)
        print(f"成功将生成的测试保存到 {test_file_path}")
    except IOError as e:
        print(f"将生成的测试保存到 {test_file_path} 时出错: {e}", file=sys.stderr)


if __name__ == "__main__":
    # 在 CI/CD 环境中，通常会从环境变量获取提交 SHA。
    # 对于本地测试，您可以通过命令行参数传递它们或硬编码进行测试。
    # 使用环境变量的示例（常见于 GitHub Actions、GitLab CI 等）：
    # PREVIOUS_COMMIT = os.environ.get('CI_PREVIOUS_COMMIT_SHA')  # 替换为实际的环境变量名
    # CURRENT_COMMIT = os.environ.get('CI_COMMIT_SHA')           # 替换为实际的环境变量名

    # 检查当前选择的模型是否提供了 API 密钥
    current_model = AI_MODELS["current_model"]
    if current_model not in AI_MODELS["models"]:
        print(f"错误: 未找到名为 '{current_model}' 的模型配置。", file=sys.stderr)
        sys.exit(1)

    model_config = AI_MODELS["models"][current_model]
    if not model_config["api_key"]:
        # 尝试从环境变量获取
        provider = model_config["provider"]
        if provider == "openai":
            model_config["api_key"] = os.environ.get("OPENAI_API_KEY", "")
        elif provider == "azure_openai":
            model_config["api_key"] = os.environ.get("AZURE_OPENAI_API_KEY", "")
        elif provider == "anthropic":
            model_config["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")
        elif provider == "google":
            model_config["api_key"] = os.environ.get("GOOGLE_API_KEY", "")
        elif provider == "grok":
            model_config["api_key"] = os.environ.get("GROK_API_KEY", "")
        elif provider == "deepseek":
            model_config["api_key"] = os.environ.get("DEEPSEEK_API_KEY", "")

        if not model_config["api_key"]:
            print(f"警告: 未设置 {provider} API 密钥。请在配置文件中设置 'api_key' 或设置相应的环境变量。", file=sys.stderr)
            print("将跳过 AI 测试生成步骤。")

    # 对于简单的本地测试，您可以比较 HEAD 与其父提交
    previous_commit_sha = GIT_CONFIG["default_previous_commit"]  # 从配置获取
    current_commit_sha = GIT_CONFIG["default_current_commit"]    # 从配置获取

    # 处理命令行参数
    model_name = None
    i = 1

    # 检查是否指定了模型
    if len(sys.argv) > i and sys.argv[i].startswith("--model="):
        model_name = sys.argv[i].split("=")[1]
        if model_name not in AI_MODELS["models"]:
            print(f"错误: 未找到名为 '{model_name}' 的模型配置。可用模型: {', '.join(AI_MODELS['models'].keys())}", file=sys.stderr)
            sys.exit(1)
        i += 1

    # 处理提交参数
    if len(sys.argv) > i:
        # 如果提供了一个参数，假设它是当前提交
        current_commit_sha = sys.argv[i]
        i += 1
        if len(sys.argv) > i:
            # 如果提供了两个参数，假设第一个是前一个提交，第二个是当前提交
            previous_commit_sha = current_commit_sha
            current_commit_sha = sys.argv[i]

    print(f"开始 AI 单元测试生成...")
    print(f"比较提交: {previous_commit_sha or 'HEAD~1'}...{current_commit_sha}")

    changed_files = get_changed_python_files(previous_commit_sha, current_commit_sha)

    if not changed_files:
        print("此提交中没有更改 Python 文件。退出。")
        sys.exit(0)

    print(f"找到 {len(changed_files)} 个更改的 Python 文件: {changed_files}")

    for file_path in changed_files:
        print(f"\n处理文件: {file_path}")
        code_snippets = parse_python_file(file_path)

        if not code_snippets:
            print(f"在 {file_path} 中找不到要为其生成测试的函数或方法。")
            continue

        print(f"找到 {len(code_snippets)} 个要处理的函数/方法。")

        for snippet in code_snippets:
            print(f"尝试为 {snippet['type']} '{snippet['name']}' 生成测试")
            # --- AI 集成步骤 ---
            generated_test_code = generate_tests_with_ai(snippet, model_name)

            # --- 保存测试步骤 ---
            if generated_test_code:
                save_generated_test(file_path, snippet, generated_test_code)
            else:
                print(f"为 {snippet['name']} 生成测试失败。")

    print("\nAI 单元测试生成过程完成。")
    print(f"生成的测试（如果有）保存在 '{GENERATED_TESTS_DIR}' 目录中。")
    print("确保您的 CI/CD 管道在其测试发现配置中包含此目录。")
