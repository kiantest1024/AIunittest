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
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        urls = []

        # 获取语言配置
        lang_config = LANGUAGE_CONFIG.get(language, {})
        test_file_prefix = lang_config.get("test_file_prefix", "test_")
        test_file_suffix = lang_config.get("test_file_suffix", "")
        file_extension = lang_config.get("file_extensions", [".py"])[0]

        for test in tests:
            # 构建测试文件名
            if test.original_snippet.class_name:
                file_name = f"{test_file_prefix}{test.original_snippet.class_name}{test_file_suffix}{file_extension}"
            else:
                file_name = f"{test_file_prefix}{test.original_snippet.name}{test_file_suffix}{file_extension}"

            # 构建文件路径
            file_path = os.path.join(base_path, file_name)

            # 检查文件是否已存在
            try:
                existing_content = repo.get_contents(file_path, ref=branch)
                # 如果文件存在，更新它
                logger.info(f"Updating existing file: {file_path}")
                response = repo.update_file(
                    path=file_path,
                    message=f"Update {file_name} with AI generated tests",
                    content=test.test_code,
                    sha=existing_content.sha,
                    branch=branch
                )
                urls.append(response["content"].html_url)
            except Exception as e:
                # 如果文件不存在，创建它
                logger.info(f"Creating new file: {file_path}")
                response = repo.create_file(
                    path=file_path,
                    message=f"Add {file_name} with AI generated tests",
                    content=test.test_code,
                    branch=branch
                )
                urls.append(response["content"].html_url)

        logger.info(f"Saved {len(urls)} files to {repo_full_name}/{base_path}")
        return urls
    except Exception as e:
        logger.error(f"Error saving to Git: {e}")
        raise
