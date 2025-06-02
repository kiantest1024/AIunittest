from fastapi import APIRouter, UploadFile, File, Form, Depends, Query, status
from fastapi.responses import StreamingResponse
from typing import List, Optional, AsyncIterator
import os
import sys
import json
import asyncio

# 动态调整导入路径
try:
    # 从backend目录运行时
    from app.models.schemas import (
        GenerateTestRequest, GenerateTestResponse, TestResult,
        UploadFileResponse, GitRepositoriesResponse, GitDirectoriesResponse,
        GitSaveRequest, GitSaveResponse, HealthResponse
    )
    from app.services.test_generator import generate_tests, generate_tests_stream
    from app.services.git_service import list_repositories, list_directories, save_to_git
    from app.services.parser_factory import ParserFactory
    from app.config import settings, AI_MODELS
    from app.utils.logger import logger
except ImportError:
    # 从app目录运行时
    from models.schemas import (
        GenerateTestRequest, GenerateTestResponse, TestResult,
        UploadFileResponse, GitRepositoriesResponse, GitDirectoriesResponse,
        GitSaveRequest, GitSaveResponse, HealthResponse
    )
    from services.test_generator import generate_tests, generate_tests_stream
    from services.git_service import list_repositories, list_directories, save_to_git
    from services.parser_factory import ParserFactory
    from config import settings, AI_MODELS
    from utils.logger import logger

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION
    )

@router.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test(request: GenerateTestRequest):
    """生成测试代码"""
    # 检查语言是否支持
    if request.language not in ParserFactory.get_supported_languages():
        logger.warning(f"Unsupported language: {request.language}")
        raise ValueError(f"Unsupported language: {request.language}")

    # 检查模型是否支持
    if request.model not in AI_MODELS:
        logger.warning(f"Unsupported model: {request.model}")
        raise ValueError(f"Unsupported model: {request.model}")

    # 生成测试
    logger.info(f"Generating tests for language: {request.language}, model: {request.model}")
    # 如果提供了 Git 信息，使用文件路径
    file_path = None
    if request.git_repo and request.git_path:
        file_path = request.git_path
        logger.info(f"Using file path from Git: {file_path}")

    tests = generate_tests(request.code, request.language, request.model, file_path)
    logger.info(f"Generated {len(tests)} tests")

    return GenerateTestResponse(tests=tests)

@router.post("/generate-test-direct")
async def generate_test_direct(request: GenerateTestRequest):
    """直接生成测试代码（非流式）"""
    try:
        # 检查语言是否支持
        if request.language not in ParserFactory.get_supported_languages():
            logger.warning(f"Unsupported language: {request.language}")
            return {"error": f"Unsupported language: {request.language}"}

        # 检查模型是否支持
        if request.model not in AI_MODELS:
            logger.warning(f"Unsupported model: {request.model}")
            return {"error": f"Unsupported model: {request.model}"}

        # 检查代码是否为空
        if not request.code or not request.code.strip():
            logger.warning("Empty code provided")
            return {"error": "Empty code provided"}

        logger.info(f"Directly generating tests for language: {request.language}, model: {request.model}")
        logger.info(f"Code length: {len(request.code)} characters")
        logger.info(f"Code preview: {request.code[:100]}...")

        # 解析代码
        if request.language == "python":
            snippets = parse_python_code_direct(request.code)
        else:
            # 对于其他语言，尝试使用已导入的解析器
            try:
                parser = ParserFactory.get_parser(request.language)
                snippets = [s.dict() for s in parser.parse_code(request.code)]
            except Exception as e:
                logger.error(f"解析 {request.language} 代码失败: {str(e)}")
                snippets = []

        logger.info(f"解析到 {len(snippets)} 个代码片段")

        # 如果没有找到任何代码片段，直接返回警告
        if not snippets:
            logger.warning("No code snippets found")
            return {
                "success": False,
                "message": "没有找到可以生成测试的函数或方法",
                "tests": []
            }

        # 记录找到的代码片段
        for i, snippet in enumerate(snippets):
            logger.info(f"代码片段 {i+1}: {snippet['name']} ({snippet['type']})")
            logger.info(f"代码片段预览: {snippet['code'][:100]}...")

        # 生成测试
        tests = []
        for snippet in snippets:
            try:
                logger.info(f"为 {snippet['name']} 生成测试")

                # 生成测试代码
                if request.language == "python":
                    test_code = generate_python_test_direct(snippet, request.model)
                else:
                    # 对于其他语言，尝试使用已导入的生成器
                    try:
                        from app.services.test_generator import generate_test_with_ai
                        from app.models.schemas import CodeSnippet

                        # 转换为 CodeSnippet 对象
                        code_snippet = CodeSnippet(
                            name=snippet["name"],
                            type=snippet["type"],
                            code=snippet["code"],
                            language=request.language,
                            class_name=snippet.get("class_name")
                        )

                        test_code = generate_test_with_ai(code_snippet, request.model)
                    except Exception as e:
                        logger.error(f"生成 {request.language} 测试失败: {str(e)}")
                        test_code = f"// 生成测试失败: {str(e)}"

                if test_code:
                    logger.info(f"成功生成测试: {snippet['name']}")
                    tests.append({
                        "name": snippet["name"],
                        "type": snippet["type"],
                        "test_code": test_code,
                        "original_snippet": {
                            "name": snippet["name"],
                            "type": snippet["type"],
                            "code": snippet["code"],
                            "language": request.language,
                            "class_name": snippet.get("class_name")
                        }
                    })
                else:
                    logger.warning(f"为 {snippet['name']} 生成测试失败")
            except Exception as e:
                logger.error(f"为 {snippet['name']} 生成测试时出错: {str(e)}", exc_info=True)

        # 返回结果
        return {
            "success": True,
            "message": f"成功生成 {len(tests)} 个测试用例",
            "tests": tests
        }
    except Exception as e:
        logger.error(f"生成测试时出错: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"生成测试时出错: {str(e)}",
            "tests": []
        }

# 直接解析 Python 代码，不依赖复杂的导入
def parse_python_code_direct(code: str):
    """
    直接解析 Python 代码，提取函数和方法

    Args:
        code: Python 代码字符串

    Returns:
        代码片段列表，每个片段包含 name, type, code 字段
    """
    import ast
    import re

    logger.info(f"直接解析 Python 代码，长度: {len(code)} 字符")

    # 结果列表
    snippets = []

    # 尝试使用 AST 解析
    try:
        tree = ast.parse(code)

        # 查找顶级函数
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                logger.info(f"找到函数: {func_name}")

                # 提取函数代码
                func_lines = code.splitlines()[node.lineno-1:node.end_lineno]
                func_code = "\n".join(func_lines)

                snippets.append({
                    "name": func_name,
                    "type": "function",
                    "code": func_code
                })

        # 查找类和方法
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                logger.info(f"找到类: {class_name}")

                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        method_name = child.name
                        logger.info(f"找到方法: {method_name} 在类 {class_name} 中")

                        # 提取方法代码
                        method_lines = code.splitlines()[child.lineno-1:child.end_lineno]
                        method_code = "\n".join(method_lines)

                        snippets.append({
                            "name": method_name,
                            "type": "method",
                            "code": method_code,
                            "class_name": class_name
                        })

    except Exception as e:
        logger.error(f"AST 解析失败: {str(e)}")

        # 如果 AST 解析失败，尝试使用正则表达式
        try:
            # 匹配函数定义
            func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)(?:\s*->.*?)?:'
            matches = re.finditer(func_pattern, code)

            for match in matches:
                func_name = match.group(1)
                func_start = match.start()
                logger.info(f"使用正则表达式找到函数: {func_name}")

                # 查找函数体结束位置
                lines = code.splitlines()
                line_no = code[:func_start].count('\n')
                indent = None
                func_end_line = line_no

                # 跳过函数定义行
                line_no += 1
                if line_no < len(lines):
                    # 获取函数体的缩进级别
                    first_line = lines[line_no]
                    indent_match = re.match(r'^(\s+)', first_line)
                    if indent_match:
                        indent = len(indent_match.group(1))

                    # 查找函数体结束位置
                    while line_no < len(lines):
                        if line_no >= len(lines):
                            break

                        if lines[line_no].strip() == '' or lines[line_no].strip().startswith('#'):
                            # 空行或注释行，继续
                            line_no += 1
                            func_end_line = line_no
                            continue

                        # 检查缩进级别
                        current_line = lines[line_no]
                        if not current_line.strip():
                            line_no += 1
                            func_end_line = line_no
                            continue

                        current_indent_match = re.match(r'^(\s+)', current_line)
                        current_indent = len(current_indent_match.group(1)) if current_indent_match else 0

                        if indent is None or current_indent > indent:
                            # 仍在函数体内
                            line_no += 1
                            func_end_line = line_no
                        else:
                            # 函数体结束
                            break

                # 提取函数代码
                func_lines = lines[code[:func_start].count('\n'):func_end_line]
                func_code = '\n'.join(func_lines)

                snippets.append({
                    "name": func_name,
                    "type": "function",
                    "code": func_code
                })

        except Exception as regex_error:
            logger.error(f"正则表达式解析也失败: {str(regex_error)}")

    logger.info(f"解析完成，找到 {len(snippets)} 个代码片段")
    return snippets

# 直接生成 Python 测试代码，不依赖复杂的导入
def generate_python_test_direct(code_snippet, model_name):
    """
    直接生成 Python 测试代码

    Args:
        code_snippet: 代码片段，包含 name, type, code 字段
        model_name: 模型名称

    Returns:
        生成的测试代码
    """
    # 构建提示
    prompt_template = """
请为以下Python {code_type}生成单元测试代码:

```python
{code}
```

请生成完整的测试代码，包括必要的导入语句、测试函数和断言。
测试应该全面覆盖代码的功能，包括正常情况和边缘情况。
使用pytest框架，并遵循以下指南:

1. 测试函数名应以'test_'开头
2. 使用描述性的测试函数名称
3. 为每个测试用例添加清晰的注释
4. 包含必要的mock对象或测试夹具
5. 使用有意义的断言消息
6. 考虑边缘情况和异常处理

假设可以使用以下导入语句: {import_statement}

请仅返回测试代码，不要包含任何解释或额外的文本。
"""

    prompt = prompt_template.format(
        code_type=code_snippet["type"],
        code=code_snippet["code"],
        import_statement="import unittest, pytest, mock"
    )

    logger.info(f"生成提示长度: {len(prompt)} 字符")

    # 使用 AI 模型生成测试代码
    try:
        # 尝试使用已导入的 AI 模型
        from app.services.ai_factory import AIServiceFactory
        ai_service = AIServiceFactory.get_service(model_name)
        test_code = ai_service.generate(prompt)
        return test_code
    except Exception as e:
        logger.error(f"使用 AI 服务生成测试失败: {str(e)}")

        # 如果失败，返回一个简单的测试模板
        return f"""
import pytest
from unittest import mock

def test_{code_snippet["name"]}():
    \"\"\"
    测试 {code_snippet["name"]} 函数

    注意: 这是一个自动生成的测试模板，因为 AI 生成失败。
    请根据函数的实际行为修改此测试。
    \"\"\"
    # 设置
    # TODO: 设置测试环境

    # 执行
    # TODO: 调用被测函数

    # 断言
    # TODO: 添加断言
    assert True  # 替换为实际断言
"""

@router.post("/generate-test-stream")
async def generate_test_stream(request: GenerateTestRequest):
    """流式生成测试代码"""
    try:
        # 检查语言是否支持
        supported_languages = ["python", "java", "go", "cpp", "csharp"]
        if request.language not in supported_languages:
            logger.warning(f"Unsupported language: {request.language}")
            return StreamingResponse(
                [json.dumps({"error": f"Unsupported language: {request.language}"}) + "\n"],
                media_type="application/x-ndjson"
            )

        # 检查模型是否支持
        if request.model not in AI_MODELS:
            logger.warning(f"Unsupported model: {request.model}")
            return StreamingResponse(
                [json.dumps({"error": f"Unsupported model: {request.model}"}) + "\n"],
                media_type="application/x-ndjson"
            )

        # 检查代码是否为空
        if not request.code or not request.code.strip():
            logger.warning("Empty code provided")
            return StreamingResponse(
                [json.dumps({"error": "Empty code provided"}) + "\n"],
                media_type="application/x-ndjson"
            )

        logger.info(f"Streaming tests for language: {request.language}, model: {request.model}")
        logger.info(f"Code length: {len(request.code)} characters")
        logger.info(f"Code preview: {request.code[:100]}...")

        async def stream_generator():
            try:
                # 发送初始消息
                yield json.dumps({
                    "status": "started",
                    "message": "开始生成测试用例"
                }) + "\n"

                # 如果提供了 Git 信息，使用文件路径
                file_path = None
                if request.git_repo and request.git_path:
                    file_path = request.git_path
                    logger.info(f"Using file path from Git: {file_path}")

                # 解析代码
                if request.language == "python":
                    snippets = parse_python_code_direct(request.code)
                else:
                    # 对于其他语言，尝试使用已导入的解析器
                    try:
                        parser = ParserFactory.get_parser(request.language)
                        snippets = [s.dict() for s in parser.parse_code(request.code, file_path)]
                    except Exception as e:
                        logger.error(f"解析 {request.language} 代码失败: {str(e)}")
                        snippets = []

                logger.info(f"解析到 {len(snippets)} 个代码片段")

                # 如果没有找到任何代码片段，直接返回警告
                if not snippets:
                    logger.warning("No code snippets found")
                    yield json.dumps({
                        "status": "warning",
                        "message": "没有找到可以生成测试的函数或方法"
                    }) + "\n"
                    return

                # 记录找到的代码片段
                for i, snippet in enumerate(snippets):
                    logger.info(f"代码片段 {i+1}: {snippet['name']} ({snippet['type']})")
                    logger.info(f"代码片段预览: {snippet['code'][:100]}...")

                # 计数器
                count = 0

                # 为每个代码片段生成测试
                for snippet in snippets:
                    try:
                        logger.info(f"为 {snippet['name']} 生成测试")

                        # 生成测试代码
                        if request.language == "python":
                            test_code = generate_python_test_direct(snippet, request.model)
                        else:
                            # 对于其他语言，尝试使用已导入的生成器
                            try:
                                from app.services.test_generator import generate_test_with_ai
                                from app.models.schemas import CodeSnippet

                                # 转换为 CodeSnippet 对象
                                code_snippet = CodeSnippet(
                                    name=snippet["name"],
                                    type=snippet["type"],
                                    code=snippet["code"],
                                    language=request.language,
                                    class_name=snippet.get("class_name")
                                )

                                test_code = generate_test_with_ai(code_snippet, request.model)
                            except Exception as e:
                                logger.error(f"生成 {request.language} 测试失败: {str(e)}")
                                test_code = f"// 生成测试失败: {str(e)}"

                        if test_code:
                            count += 1
                            logger.info(f"成功生成测试 {count}: {snippet['name']}")

                            # 将结果转换为JSON字符串，添加更多信息
                            yield json.dumps({
                                "name": snippet["name"],
                                "type": snippet["type"],
                                "test_code": test_code,
                                "success": True,
                                "message": f"成功生成测试: {snippet['name']}"
                            }) + "\n"
                        else:
                            logger.warning(f"为 {snippet['name']} 生成测试失败")

                        # 添加短暂延迟，确保客户端能够处理
                        await asyncio.sleep(0.1)

                    except Exception as snippet_error:
                        logger.error(f"为 {snippet['name']} 生成测试时出错: {str(snippet_error)}", exc_info=True)
                        yield json.dumps({
                            "status": "error",
                            "message": f"为 {snippet['name']} 生成测试时出错: {str(snippet_error)}"
                        }) + "\n"

                # 如果没有生成任何测试
                if count == 0:
                    logger.warning("No tests were generated")
                    yield json.dumps({
                        "status": "warning",
                        "message": "没有找到可以生成测试的函数或方法"
                    }) + "\n"
                else:
                    # 发送完成消息
                    yield json.dumps({
                        "status": "completed",
                        "message": f"成功生成 {count} 个测试用例",
                        "test_count": count,
                        "success": True
                    }) + "\n"

            except Exception as e:
                logger.error(f"Error in stream generator: {str(e)}", exc_info=True)
                yield json.dumps({
                    "error": str(e),
                    "status": "error"
                }) + "\n"

        return StreamingResponse(
            stream_generator(),
            media_type="application/x-ndjson"
        )
    except Exception as e:
        logger.error(f"Error setting up streaming: {str(e)}", exc_info=True)
        return StreamingResponse(
            [json.dumps({"error": f"Failed to set up streaming: {str(e)}"}) + "\n"],
            media_type="application/x-ndjson"
        )

@router.post("/upload-file", response_model=UploadFileResponse)
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    logger.info(f"Uploading file: {file.filename}")

    # 读取文件内容
    try:
        content = await file.read()
        content_str = content.decode("utf-8")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise ValueError(f"Error reading file: {str(e)}")

    # 根据文件扩展名确定语言
    filename = file.filename
    language = None

    if filename.endswith(".py"):
        language = "python"
    elif filename.endswith(".java"):
        language = "java"
    elif filename.endswith(".go"):
        language = "go"
    elif filename.endswith((".cpp", ".h", ".hpp")):
        language = "cpp"
    elif filename.endswith(".cs"):
        language = "csharp"
    else:
        logger.warning(f"Unsupported file type: {filename}")

    logger.info(f"File uploaded successfully: {filename}, language: {language}")

    return UploadFileResponse(
        filename=filename,
        content=content_str,
        language=language
    )

@router.get("/git/repositories", response_model=GitRepositoriesResponse)
async def get_repositories(token: str = Query(...)):
    """获取GitHub仓库列表"""
    logger.info("Listing GitHub repositories")

    if not token:
        logger.warning("GitHub token is empty")
        raise ValueError("GitHub token is required")

    repos = list_repositories(token)
    logger.info(f"Found {len(repos)} repositories")

    return GitRepositoriesResponse(repositories=repos)

@router.get("/git/directories", response_model=GitDirectoriesResponse)
async def get_directories(repo: str = Query(...), token: str = Query(...), path: str = Query("")):
    """获取GitHub仓库目录列表"""
    logger.info(f"Listing directories for repo: {repo}, path: {path}")

    if not token:
        logger.warning("GitHub token is empty")
        raise ValueError("GitHub token is required")

    if not repo:
        logger.warning("Repository name is empty")
        raise ValueError("Repository name is required")

    dirs = list_directories(repo, token, path)
    logger.info(f"Found {len(dirs)} directories/files")

    return GitDirectoriesResponse(directories=dirs)

@router.post("/git/save", response_model=GitSaveResponse)
async def save_tests_to_git(request: GitSaveRequest):
    """保存测试到GitHub仓库"""
    logger.info(f"Saving tests to GitHub repo: {request.repo}, path: {request.path}")

    if not request.token:
        logger.warning("GitHub token is empty")
        raise ValueError("GitHub token is required")

    if not request.repo:
        logger.warning("Repository name is empty")
        raise ValueError("Repository name is required")

    if not request.tests:
        logger.warning("No tests to save")
        raise ValueError("No tests to save")

    urls = save_to_git(
        tests=request.tests,
        language=request.language,
        repo_full_name=request.repo,
        base_path=request.path,
        token=request.token
    )

    logger.info(f"Saved {len(urls)} test files to GitHub")
    return GitSaveResponse(urls=urls)

@router.get("/models")
async def get_models():
    """获取支持的AI模型列表"""
    return {"models": list(AI_MODELS.keys())}

@router.get("/languages")
async def get_languages():
    """获取支持的编程语言列表"""
    return {"languages": ParserFactory.get_supported_languages()}

@router.get("/git/file-content")
async def get_file_content(repo: str = Query(...), path: str = Query(...), token: str = Query(...)):
    """获取GitHub文件内容"""
    logger.info(f"Getting file content from repo: {repo}, path: {path}")

    if not token:
        logger.warning("GitHub token is empty")
        raise ValueError("GitHub token is required")

    if not repo:
        logger.warning("Repository name is empty")
        raise ValueError("Repository name is required")

    if not path:
        logger.warning("File path is empty")
        raise ValueError("File path is required")

    try:
        from github import Github

        # 创建GitHub客户端
        g = Github(token)

        # 获取仓库
        repository = g.get_repo(repo)

        # 获取文件内容
        file_content = repository.get_contents(path)

        # 获取文件扩展名
        file_ext = path.split('.')[-1].lower() if '.' in path else ''

        # 确定语言
        language = None
        if file_ext == 'py':
            language = 'python'
        elif file_ext == 'java':
            language = 'java'
        elif file_ext == 'go':
            language = 'go'
        elif file_ext in ['cpp', 'h', 'hpp']:
            language = 'cpp'
        elif file_ext == 'cs':
            language = 'csharp'

        # 解码内容
        try:
            content = file_content.decoded_content.decode('utf-8')
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                content = file_content.decoded_content.decode('latin-1')
            except Exception as e:
                logger.error(f"Failed to decode file content: {e}")
                content = "// 无法解码文件内容，可能是二进制文件"

        logger.info(f"File content retrieved successfully: {path}")
        logger.debug(f"Content preview: {content[:100]}...")

        result = {
            "content": content,
            "language": language,
            "name": file_content.name,
            "path": file_content.path
        }

        return result

    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        raise ValueError(f"Failed to get file content: {str(e)}")
