from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import json
import asyncio
from app.services.gitlab_service import GitLabService
from app.services.git_service import GitHubService
from app.models.schemas import (
    GenerateTestRequest, GenerateTestResponse,
    UploadFileResponse, GitRepositoriesResponse, GitDirectoriesResponse,
    GitSaveRequest, GitSaveResponse, HealthResponse, GitLabCloneRequest,
    GitLabCloneResponse, GitHubCloneRequest, GitHubCloneResponse
)
from app.services.test_generator import generate_tests
from app.services.git_service import list_directories, save_to_git
from app.services.parser_factory import ParserFactory
from app.config import settings, AI_MODELS
from app.utils.logger import logger

router = APIRouter()

def build_gitlab_api_base(repo: str, server_url: str = "") -> tuple[str, str]:
    """
    统一的GitLab API基础URL构建函数

    Args:
        repo: 仓库标识符，可以是完整URL或项目路径
        server_url: 服务器地址参数

    Returns:
        tuple: (api_base, project_path)
    """
    logger.info(f"Building GitLab API base for repo: {repo}, server_url: {server_url}")

    # 解析仓库URL获取项目路径和服务器地址
    if repo.startswith("https://"):
        repo_url = repo.replace("https://", "")
    elif repo.startswith("http://"):
        repo_url = repo.replace("http://", "")
    else:
        repo_url = repo

    parts = repo_url.split("/")
    logger.info(f"URL parts: {parts}")

    # 处理不同的repo格式
    if len(parts) >= 3:
        # 完整URL格式: server/user/project 或 server/user/project.git
        gitlab_server = parts[0]
        project_path = "/".join(parts[1:])
        if project_path.endswith(".git"):
            project_path = project_path[:-4]

        # 构建GitLab API URL，使用正确的服务器地址
        if server_url and server_url.strip():
            # 如果提供了server_url参数，使用它
            api_base = server_url.rstrip('/')
            # 确保有协议前缀
            if not api_base.startswith(('http://', 'https://')):
                api_base = f"http://{api_base}"
            logger.info(f"Using provided server_url: {server_url} -> {api_base}")
        else:
            # 否则从repo URL中提取服务器地址
            if gitlab_server.startswith("gitlab.com"):
                api_base = "https://gitlab.com"
            else:
                # 对于自定义GitLab实例，根据原始repo格式确定协议
                if repo.startswith("https://"):
                    api_base = f"https://{gitlab_server}"
                else:
                    api_base = f"http://{gitlab_server}"
            logger.info(f"Extracted from repo URL: {api_base}")

    elif len(parts) >= 2:
        # 项目路径格式: user/project
        project_path = repo_url
        if project_path.endswith(".git"):
            project_path = project_path[:-4]

        # 必须有server_url参数
        if server_url and server_url.strip():
            api_base = server_url.rstrip('/')
            # 确保有协议前缀
            if not api_base.startswith(('http://', 'https://')):
                api_base = f"http://{api_base}"
            logger.info(f"Using server_url for project path: {server_url} -> {api_base}")
        else:
            raise ValueError("Server URL is required for project path format")

    else:
        raise ValueError("Invalid repository format")

    logger.info(f"Final result: api_base={api_base}, project_path={project_path}")
    return api_base, project_path

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
                if request.language == "java":
                    # 对于Java，使用增强的分析器生成针对性测试
                    try:
                        from app.services.ai_service import generate_test_with_ai
                        from app.models.schemas import CodeSnippet
                        from app.services.java_analyzer import create_enhanced_java_test_prompt

                        # 使用Java分析器创建增强的提示
                        enhanced_prompt = create_enhanced_java_test_prompt(request.code)

                        # 创建代码片段
                        code_snippet = CodeSnippet(
                            name=snippet["name"],
                            type=snippet["type"],
                            code=snippet["code"],  # 使用原始代码
                            language=request.language,
                            class_name=snippet.get("class_name")
                        )

                        # 使用增强的提示生成测试
                        test_code = generate_test_with_ai(code_snippet, enhanced_prompt, request.model)
                    except Exception as e:
                        logger.error(f"Java测试生成失败: {str(e)}")
                        test_code = f"// 生成测试失败: {str(e)}"
                else:
                    # 对于其他语言，使用基础生成器
                    try:
                        from app.services.ai_service import generate_test_with_ai
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
                        if request.language == "java":
                            # 对于Java，使用增强的分析器生成针对性测试
                            try:
                                from app.services.ai_service import generate_test_with_ai
                                from app.models.schemas import CodeSnippet
                                from app.services.java_analyzer import create_enhanced_java_test_prompt

                                # 使用Java分析器创建增强的提示
                                enhanced_prompt = create_enhanced_java_test_prompt(request.code)

                                # 创建代码片段
                                code_snippet = CodeSnippet(
                                    name=snippet["name"],
                                    type=snippet["type"],
                                    code=snippet["code"],  # 使用原始代码
                                    language=request.language,
                                    class_name=snippet.get("class_name")
                                )

                                # 使用增强的提示生成测试
                                test_code = generate_test_with_ai(code_snippet, enhanced_prompt, request.model)
                            except Exception as e:
                                logger.error(f"Java测试生成失败: {str(e)}")
                                test_code = f"// 生成测试失败: {str(e)}"
                        else:
                            # 对于其他语言，使用基础生成器
                            try:
                                from app.services.ai_service import generate_test_with_ai
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
async def get_repositories(
    token: str = Query(...),
    platform: str = Query(default="github"),
    server_url: str = Query(default="", description="自定义服务器地址，如 https://github.com 或 http://172.16.1.30")
):
    """获取仓库列表"""
    logger.info(f"Listing {platform} repositories from server: {server_url or 'default'}")

    if not token or token.strip() == "":
        logger.warning(f"{platform} token is empty")
        raise ValueError(f"{platform} token is required")

    try:
        git_service = get_git_service(platform, token, server_url)
        repos = git_service.list_repositories()

        logger.info(f"Found {len(repos)} repositories")
        return GitRepositoriesResponse(repositories=repos)

    except ValueError as ve:
        # 重新抛出已知的ValueError（如无效token）
        logger.error(f"Validation error: {ve}")
        raise ve
    except Exception as e:
        logger.error(f"Unexpected error listing {platform} repositories: {e}")
        raise ValueError(f"Failed to list {platform} repositories: {str(e)}")

def get_git_service(platform: str, token: str, server_url: str = ""):
    """
    获取Git服务实例

    Args:
        platform: 平台类型 ("github" 或 "gitlab")
        token: 访问令牌
        server_url: 自定义服务器地址（可选）

    Returns:
        Git服务实例
    """
    if platform == "gitlab":
        if server_url and server_url.strip():
            return GitLabService(token, server_url.strip())
        else:
            return GitLabService(token)  # 使用默认URL
    else:  # github
        if server_url and server_url.strip():
            return GitHubService(token, server_url.strip())
        else:
            return GitHubService(token)  # 使用默认URL

@router.get("/git/directories", response_model=GitDirectoriesResponse)
async def get_directories(
    repo: str = Query(...),
    token: str = Query(default=""),
    path: str = Query(""),
    platform: str = Query(default="github"),
    server_url: str = Query(default="", description="自定义服务器地址")
):
    """获取仓库目录列表"""
    logger.info(f"Listing directories for repo: {repo}, path: {path}, platform: {platform}, server: {server_url or 'default'}")

    # GitHub仍然需要token
    if not token and platform == "github":
        logger.warning("GitHub token is empty")
        raise ValueError("GitHub token is required")

    if not repo:
        logger.warning("Repository name is empty")
        raise ValueError("Repository name is required")

    if platform == "gitlab":
        if not token:
            # GitLab公共仓库，使用公共API
            logger.info("No token provided for GitLab, attempting to access public repository")
            try:
                import requests

                # 使用统一的URL构建函数
                api_base, project_path = build_gitlab_api_base(repo, server_url)

                # 构建GitLab API URL
                gitlab_api_url = f"{api_base}/api/v4/projects/{project_path.replace('/', '%2F')}/repository/tree"
                params = {"ref": "main"}  # 先尝试main分支
                if path:
                    params["path"] = path

                logger.info(f"Attempting to access GitLab API: {gitlab_api_url}")
                response = requests.get(gitlab_api_url, params=params, timeout=10)

                # 如果main分支失败，尝试master分支
                if response.status_code == 404:
                    logger.info("main branch not found, trying master branch")
                    params["ref"] = "master"
                    response = requests.get(gitlab_api_url, params=params, timeout=10)

                if response.status_code == 200:
                    items = response.json()
                    dirs = []
                    for item in items:
                        # 构建文件/目录的web URL
                        if item["type"] == "tree":
                            # 目录URL
                            item_url = f"{api_base}/{project_path}/-/tree/{params['ref']}/{item['path']}"
                        else:
                            # 文件URL
                            item_url = f"{api_base}/{project_path}/-/blob/{params['ref']}/{item['path']}"

                        dirs.append({
                            "name": item["name"],
                            "path": item["path"],
                            "type": "dir" if item["type"] == "tree" else "file",
                            "url": item_url  # 添加必需的url字段
                        })

                    logger.info(f"Found {len(dirs)} directories/files from public GitLab repository")
                    return GitDirectoriesResponse(directories=dirs)
                else:
                    logger.error(f"GitLab API response: {response.status_code}, {response.text[:200]}")
                    raise ValueError(f"Failed to access public repository: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"Error accessing public GitLab repository: {e}")
                raise ValueError(f"Failed to access public repository: {str(e)}")
        else:
            # 有token，使用GitLab API
            gitlab_service = get_git_service("gitlab", token, server_url)
            dirs = gitlab_service.list_directories(repo, path)
    else:
        # GitHub
        dirs = list_directories(repo, token, path)

    logger.info(f"Found {len(dirs)} directories/files")

    return GitDirectoriesResponse(directories=dirs)

@router.post("/git/save", response_model=GitSaveResponse)
async def save_tests_to_git(request: GitSaveRequest):
    """保存测试到代码仓库"""
    platform = request.platform if hasattr(request, "platform") else "github"
    logger.info(f"Saving tests to {platform} repo: {request.repo}, path: {request.path}")

    # 详细的调试信息
    logger.info(f"Save request debug info:")
    logger.info(f"- Platform: {platform}")
    logger.info(f"- Repository: {request.repo}")
    logger.info(f"- Path: {request.path}")
    logger.info(f"- Token present: {'Yes' if request.token else 'No'}")
    logger.info(f"- Token length: {len(request.token) if request.token else 0}")
    logger.info(f"- Server URL: {getattr(request, 'server_url', 'Not provided')}")
    logger.info(f"- Tests count: {len(request.tests) if request.tests else 0}")
    logger.info(f"- Language: {request.language}")

    if not request.token:
        logger.warning(f"{platform} token is empty")
        # 为GitLab提供更友好的错误信息
        if platform == "gitlab":
            raise ValueError("GitLab Personal Access Token is required for saving tests. Please provide a token with 'api' and 'write_repository' permissions.")
        else:
            raise ValueError(f"{platform} token is required")

    if not request.repo:
        logger.warning("Repository name is empty")
        raise ValueError("Repository name is required")

    if not request.tests:
        logger.warning("No tests to save")
        raise ValueError("No tests to save")

    if platform == "gitlab":
        # 获取服务器地址，如果没有提供则使用默认值
        server_url = request.server_url or ''
        gitlab_service = get_git_service("gitlab", request.token, server_url)
        urls = gitlab_service.save_tests(
            tests=request.tests,
            language=request.language,
            repo_full_name=request.repo,
            base_path=request.path
        )
    else:
        urls = save_to_git(
            tests=request.tests,
            language=request.language, 
            repo_full_name=request.repo,
            base_path=request.path,
            token=request.token
        )

    logger.info(f"Saved {len(urls)} test files to {platform}")
    return GitSaveResponse(urls=urls)

@router.get("/models")
async def get_models():
    """获取支持的AI模型列表"""
    return {"models": list(AI_MODELS.keys())}

@router.get("/languages")
async def get_languages():
    """获取支持的编程语言列表"""
    return {"languages": ParserFactory.get_supported_languages()}

@router.post("/git/gitlab/clone")
async def clone_gitlab_repo(request: GitLabCloneRequest):
    """克隆GitLab仓库"""
    logger.info(f"Cloning GitLab repo: {request.repo_url}")

    if not request.repo_url:
        logger.warning("Repository URL is empty")
        raise ValueError("Repository URL is required")

    # 如果没有令牌，尝试克隆公共仓库
    if not request.token or request.token.strip() == "":
        logger.info("No token provided, attempting to clone public repository")
        try:
            # 使用git命令直接克隆公共仓库
            import subprocess
            import tempfile
            import os

            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            clone_path = os.path.join(temp_dir, "repo")

            # 执行git clone命令
            result = subprocess.run(
                ["git", "clone", request.repo_url, clone_path],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                logger.info(f"Successfully cloned public repository to {clone_path}")

                # 构建基本的仓库信息，即使是公共仓库克隆
                try:
                    # 从URL解析仓库信息
                    repo_url_clean = request.repo_url
                    if repo_url_clean.startswith("http://"):
                        repo_url_clean = repo_url_clean.replace("http://", "")
                    elif repo_url_clean.startswith("https://"):
                        repo_url_clean = repo_url_clean.replace("https://", "")

                    parts = repo_url_clean.split("/")
                    if len(parts) >= 3:
                        project_path = "/".join(parts[1:])
                        if project_path.endswith(".git"):
                            project_path = project_path[:-4]

                        # 构建基本仓库信息
                        repo_info = {
                            "name": project_path.split('/')[-1],
                            "full_name": project_path,
                            "description": f"Public repository cloned from {request.repo_url}",
                            "private": False,
                            "default_branch": "main",  # 假设默认分支
                            "clone_url": request.repo_url,
                            "web_url": request.repo_url.replace('.git', '') if request.repo_url.endswith('.git') else request.repo_url
                        }

                        logger.info(f"Created basic repo info for public repository: {repo_info['full_name']}")
                        return GitLabCloneResponse(success=True, clone_path=clone_path, repo_info=repo_info)
                    else:
                        logger.warning(f"Could not parse repository path from URL: {request.repo_url}")

                except Exception as parse_error:
                    logger.warning(f"Failed to parse repository info from URL: {parse_error}")

                # 如果解析失败，返回没有repo_info的响应
                return GitLabCloneResponse(success=True, clone_path=clone_path)
            else:
                logger.error(f"Git clone failed: {result.stderr}")
                raise ValueError(f"Failed to clone repository: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("Git clone timeout")
            raise ValueError("Repository clone timeout")
        except Exception as e:
            logger.error(f"Error cloning public repository: {e}")
            raise ValueError(f"Failed to clone public repository: {str(e)}")
    else:
        # 有令牌，使用GitLab API
        server_url = request.server_url or ''
        git_service = get_git_service("gitlab", request.token, server_url)
        result = git_service.clone_repository(request.repo_url, request.path)
        return GitLabCloneResponse(
            success=result.success,
            clone_path=result.clone_path,
            repo_info=result.repo_info
        )

@router.get("/git/gitlab/project")
async def get_gitlab_project(
    project_id: str = Query(...),
    token: str = Query(...),
    server_url: str = Query(default="", description="自定义服务器地址")
):
    """获取GitLab项目信息"""
    logger.info(f"Getting GitLab project: {project_id} from server: {server_url or 'default'}")

    if not token:
        logger.warning("GitLab token is empty")
        raise ValueError("GitLab token is required")

    git_service = get_git_service("gitlab", token, server_url)
    return git_service.get_project(project_id)

@router.get("/git/file-content")
async def get_file_content(
    repo: str = Query(...),
    path: str = Query(...),
    token: str = Query(default=""),
    platform: str = Query(default="github"),
    server_url: str = Query(default="", description="自定义服务器地址")
):
    """获取文件内容"""
    logger.info(f"Getting file content from repo: {repo}, path: {path}, platform: {platform}, server: {server_url or 'default'}")

    # 对于URL模式的公共仓库，token可以为空
    if not token and platform == "github":
        logger.warning("GitHub token is empty")
        raise ValueError("GitHub token is required")

    # GitLab URL模式支持公共仓库，不需要token
    if not token and platform == "gitlab":
        logger.info("No token provided for GitLab, attempting to access public repository")

    if not repo:
        logger.warning("Repository name is empty")
        raise ValueError("Repository name is required")

    if not path:
        logger.warning("File path is empty")
        raise ValueError("File path is required")

    try:
        # 如果是GitLab且没有token，尝试通过公共API获取文件内容
        if platform == "gitlab" and not token:
            import requests

            # 使用统一的URL构建函数
            api_base, project_path = build_gitlab_api_base(repo, server_url)

            # 构建GitLab文件API URL
            gitlab_api_url = f"{api_base}/api/v4/projects/{project_path.replace('/', '%2F')}/repository/files/{path.replace('/', '%2F')}/raw"

            # 先尝试main分支
            params = {"ref": "main"}
            logger.info(f"Attempting to access GitLab file API: {gitlab_api_url}")
            response = requests.get(gitlab_api_url, params=params, timeout=10)

            # 如果main分支失败，尝试master分支
            if response.status_code == 404:
                logger.info("main branch not found, trying master branch")
                params["ref"] = "master"
                response = requests.get(gitlab_api_url, params=params, timeout=10)

            if response.status_code == 200:
                content = response.text

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

                result = {
                    "content": content,
                    "language": language,
                    "name": path.split('/')[-1],
                    "path": path
                }

                logger.info(f"File content retrieved from public GitLab repository: {path}")
                return result
            else:
                logger.error(f"GitLab file API response: {response.status_code}, {response.text[:200]}")
                raise ValueError(f"Failed to access public repository file: HTTP {response.status_code}")
        else:
            # 使用token访问私有仓库或GitHub
            git_service = get_git_service(platform, token, server_url)

            if platform == "github":
                # GitHub服务返回元组 (content, language)
                content, detected_language = git_service.get_file_content(repo, path)

                # 获取文件扩展名
                file_ext = path.split('.')[-1].lower() if '.' in path else ''

                # 确定语言（优先使用检测到的语言）
                language = detected_language
                if not language or language == 'Unknown':
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

                result = {
                    "content": content,
                    "language": language,
                    "name": path.split('/')[-1],
                    "path": path
                }

                logger.info(f"File content retrieved successfully from GitHub: {path}")
                logger.debug(f"Content preview: {content[:100]}...")

                return result
            else:
                # GitLab服务处理
                file_content_str = git_service.get_file_content(repo, path)

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

                result = {
                    "content": file_content_str,
                    "language": language,
                    "name": path.split('/')[-1],
                    "path": path
                }

                logger.info(f"File content retrieved successfully from GitLab: {path}")
                logger.debug(f"Content preview: {file_content_str[:100]}...")

                return result

    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        raise ValueError(f"Failed to get file content: {str(e)}")

@router.post("/git/github/clone")
async def clone_github_repo(request: GitHubCloneRequest):
    """克隆GitHub仓库"""
    logger.info(f"Cloning GitHub repo: {request.repo_url}")

    if not request.token:
        logger.warning("GitHub token is empty")
        raise ValueError("GitHub token is required")

    if not request.repo_url:
        logger.warning("Repository URL is empty")
        raise ValueError("Repository URL is required")

    try:
        git_service = GitHubService(request.token)
        result = git_service.clone_repository(request.repo_url, request.path)

        return GitHubCloneResponse(
            success=result["success"],
            clone_path=result["clone_path"],
            repo_info=result["repo_info"]
        )
    except Exception as e:
        logger.error(f"Error cloning GitHub repository: {e}")
        raise ValueError(f"Failed to clone repository: {str(e)}")

@router.post("/git/clone")
async def clone_repo_universal(platform: str, repo_url: str, token: str, path: str = "", server_url: str = ""):
    """通用仓库克隆接口，支持GitHub和GitLab"""
    logger.info(f"Cloning {platform} repo: {repo_url} from server: {server_url or 'default'}")

    if not token:
        logger.warning(f"{platform} token is empty")
        raise ValueError(f"{platform} token is required")

    if not repo_url:
        logger.warning("Repository URL is empty")
        raise ValueError("Repository URL is required")

    try:
        if platform.lower() == "github":
            git_service = get_git_service("github", token, server_url)
            result = git_service.clone_repository(repo_url, path if path else None)
            return {
                "success": result["success"],
                "clone_path": result["clone_path"],
                "repo_info": result["repo_info"],
                "platform": "github"
            }
        elif platform.lower() == "gitlab":
            git_service = get_git_service("gitlab", token, server_url)
            result = git_service.clone_repository(repo_url, path if path else None)
            return {
                "success": result.success,
                "clone_path": result.clone_path,
                "platform": "gitlab"
            }
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    except Exception as e:
        logger.error(f"Error cloning {platform} repository: {e}")
        raise ValueError(f"Failed to clone repository: {str(e)}")