from github import Github
from typing import List
import os
from app.models.schemas import TestResult, GitRepository, GitDirectory
from app.config import LANGUAGE_CONFIG
from app.utils.logger import logger

def list_repositories(token: str) -> List[GitRepository]:
    """
    列出用户的GitHub仓库

    Args:
        token: GitHub访问令牌

    Returns:
        仓库列表

    Raises:
        Exception: 如果列出仓库失败
    """
    try:
        g = Github(token)
        user = g.get_user()
        repos = []

        for repo in user.get_repos():
            repos.append(GitRepository(
                name=repo.name,
                full_name=repo.full_name,
                url=repo.html_url
            ))

        logger.info(f"Found {len(repos)} repositories")
        return repos
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        raise

def list_directories(repo_full_name: str, token: str, path: str = "") -> List[GitDirectory]:
    """
    列出仓库中的目录和文件

    Args:
        repo_full_name: 仓库全名（用户名/仓库名）
        token: GitHub访问令牌
        path: 目录路径

    Returns:
        目录和文件列表

    Raises:
        Exception: 如果列出目录失败
    """
    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        contents = []

        for content in repo.get_contents(path):
            contents.append(GitDirectory(
                name=content.name,
                path=content.path,
                type="dir" if content.type == "dir" else "file",
                url=content.html_url
            ))

        logger.info(f"Found {len(contents)} items in {repo_full_name}/{path}")
        return contents
    except Exception as e:
        logger.error(f"Error listing directories: {e}")
        raise

def save_to_git(tests: List[TestResult], language: str, repo_full_name: str, base_path: str, token: str, branch: str = "main") -> List[str]:
    """
    将生成的测试保存到Git仓库

    Args:
        tests: 测试结果列表
        language: 编程语言
        repo_full_name: 仓库全名（用户名/仓库名）
        base_path: 基础路径
        token: GitHub访问令牌
        branch: 分支名称

    Returns:
        保存的文件URL列表

    Raises:
        Exception: 如果保存失败
    """
    try:
        logger.info(f"Starting save_to_git with parameters:")
        logger.info(f"  - language: {language}")
        logger.info(f"  - repo_full_name: {repo_full_name}")
        logger.info(f"  - base_path: {base_path}")
        logger.info(f"  - branch: {branch}")
        logger.info(f"  - tests count: {len(tests)}")

        # 初始化 GitHub 客户端
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        urls = []

        # 获取语言配置
        lang_config = LANGUAGE_CONFIG.get(language, {})
        file_extension = lang_config.get("file_extensions", [".py"])[0]
        logger.info(f"Using file extension: {file_extension} for language: {language}")

        # 规范化基础路径
        normalized_base_path = base_path.replace('\\', '/') if base_path else ""
        logger.info(f"Normalized base path: '{normalized_base_path}'")

        # 记录上传目录
        logger.info(f"Saving tests directly to path: '{normalized_base_path}'")

        for test in tests:
            # 构建测试文件名 - 不使用前缀或后缀，直接使用函数/方法名
            if test.original_snippet.class_name:
                # 对于类方法，使用 ClassName_methodName 格式
                file_name = f"{test.original_snippet.class_name}_{test.original_snippet.name}{file_extension}"
            else:
                # 对于函数，直接使用函数名
                file_name = f"{test.original_snippet.name}{file_extension}"

            # 构建文件路径 - 直接放在选择的文件夹中，使用正斜杠作为路径分隔符
            # 确保路径末尾有斜杠
            if normalized_base_path:
                if not normalized_base_path.endswith('/'):
                    normalized_base_path += '/'
                file_path = normalized_base_path + file_name
            else:
                file_path = file_name

            logger.info(f"Constructed file path: '{file_path}'")

            # 检查文件是否已存在
            try:
                try:
                    # 尝试获取文件内容，检查文件是否存在
                    existing_content = repo.get_contents(file_path, ref=branch)
                    # 如果文件存在，更新它
                    logger.info(f"File exists, updating: '{file_path}'")
                    response = repo.update_file(
                        path=file_path,
                        message=f"Update {file_name} with AI generated tests",
                        content=test.test_code,
                        sha=existing_content.sha,
                        branch=branch
                    )
                    file_url = response["content"].html_url
                    logger.info(f"Successfully updated file: '{file_path}', URL: {file_url}")
                    urls.append(file_url)
                except Exception as not_found_error:
                    # 检查是否是文件不存在的错误
                    if "404" in str(not_found_error) or "not found" in str(not_found_error).lower():
                        # 如果文件不存在，创建它
                        logger.info(f"File does not exist, creating new file: '{file_path}'")
                        response = repo.create_file(
                            path=file_path,
                            message=f"Add {file_name} with AI generated tests",
                            content=test.test_code,
                            branch=branch
                        )
                        file_url = response["content"].html_url
                        logger.info(f"Successfully created file: '{file_path}', URL: {file_url}")
                        urls.append(file_url)
                    else:
                        # 如果是其他错误，重新抛出
                        logger.error(f"Error checking if file exists: {not_found_error}")
                        raise not_found_error
            except Exception as e:
                # 捕获所有其他错误
                logger.error(f"Error saving file '{file_path}': {e}")
                raise

        logger.info(f"Saved {len(urls)} files to {repo_full_name}/{base_path}")
        return urls
    except Exception as e:
        logger.error(f"Error saving to Git: {e}")
        raise
