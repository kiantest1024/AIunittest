from github import Github
from typing import List
import os
import subprocess
import tempfile
import shutil
from app.models.schemas import TestResult, GitRepository, GitDirectory
from app.config import LANGUAGE_CONFIG
from app.utils.logger import logger
from app.services.base_git_service import BaseGitService

class GitHubService(BaseGitService):
    def __init__(self, token: str, github_url: str = None):
        """
        初始化 GitHub 服务

        Args:
            token: GitHub 访问令牌
            github_url: GitHub 服务器URL，如果为None则使用默认URL
        """
        self.token = token

        # 确定GitHub服务器URL
        if github_url is None:
            # 使用默认的GitHub.com
            from app.config import settings
            self.github_url = settings.GITHUB_DEFAULT_URL
            self.api_url = settings.GITHUB_DEFAULT_API_URL
            logger.info(f"Using default GitHub URL: {self.github_url}")
        else:
            # 使用用户提供的URL
            self.github_url = self._normalize_github_url(github_url)
            self.api_url = self._get_api_url(self.github_url)
            logger.info(f"Using custom GitHub URL: {self.github_url}")

        # 初始化GitHub客户端
        if self.api_url == "https://api.github.com":
            # 公共GitHub
            self.client = Github(token)
        else:
            # GitHub Enterprise
            self.client = Github(base_url=self.api_url, login_or_token=token)

        logger.info(f"GitHub service initialized for {self.github_url}")

    def _normalize_github_url(self, url: str) -> str:
        """
        标准化GitHub URL格式

        Args:
            url: 用户输入的URL

        Returns:
            标准化的URL
        """
        # 移除尾部斜杠
        url = url.rstrip('/')

        # 如果没有协议，默认添加https
        if not url.startswith(('http://', 'https://')):
            # 对于IP地址，使用http；对于域名，使用https
            if self._is_ip_address(url):
                url = f"http://{url}"
            else:
                url = f"https://{url}"

        logger.info(f"Normalized GitHub URL: {url}")
        return url

    def _get_api_url(self, github_url: str) -> str:
        """
        根据GitHub URL获取API URL

        Args:
            github_url: GitHub服务器URL

        Returns:
            API URL
        """
        if "github.com" in github_url:
            return "https://api.github.com"
        else:
            # GitHub Enterprise
            return f"{github_url}/api/v3"

    def _is_ip_address(self, url: str) -> bool:
        """检查是否为IP地址"""
        import re
        # 简单的IP地址检查
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$'
        return bool(re.match(ip_pattern, url))

    def list_repositories(self) -> List[GitRepository]:
        """
        列出用户的GitHub仓库

        Returns:
            仓库列表

        Raises:
            Exception: 如果列出仓库失败
        """
        try:
            # 验证token是否有效
            if not self.token or self.token == "invalid_token":
                raise ValueError("Invalid or missing GitHub token")

            user = self.client.get_user()
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
            error_msg = str(e).lower()
            if "401" in error_msg or "bad credentials" in error_msg or "unauthorized" in error_msg:
                raise ValueError("Invalid GitHub token")
            elif "403" in error_msg or "forbidden" in error_msg:
                raise ValueError("GitHub token lacks required permissions")
            elif "rate limit" in error_msg:
                raise ValueError("GitHub API rate limit exceeded")
            else:
                raise ValueError(f"Failed to list GitHub repositories: {str(e)}")

    def list_directories(self, repo_full_name: str, path: str = "") -> List[GitDirectory]:
        """
        列出仓库中的目录和文件

        Args:
            repo_full_name: 仓库全名（用户名/仓库名）
            path: 目录路径

        Returns:
            目录和文件列表

        Raises:
            Exception: 如果列出目录失败
        """
        try:
            repo = self.client.get_repo(repo_full_name)
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

    def save_to_git(self, tests: List[TestResult], language: str, repo_full_name: str, base_path: str, branch: str = "main") -> List[str]:
        """
        将生成的测试保存到Git仓库

        Args:
            tests: 测试结果列表
            language: 编程语言
            repo_full_name: 仓库全名（用户名/仓库名）
            base_path: 基础路径
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

            repo = self.client.get_repo(repo_full_name)
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

    def get_file_content(self, repo_full_name: str, file_path: str, ref: str = "main") -> tuple:
        """
        获取文件内容

        Args:
            repo_full_name: 仓库全名
            file_path: 文件路径
            ref: 分支或commit
        
        Returns:
            文件内容和语言信息的元组(content, language)
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            content = repo.get_contents(file_path, ref=ref)
            file_content = content.decoded_content.decode('utf-8')
            language = repo.get_languages().get(os.path.splitext(file_path)[1].lstrip('.'), 'Unknown')
            return file_content, language
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            raise

    def create_branch(self, repo_full_name: str, branch_name: str, source_branch: str = "main") -> None:
        """
        创建新分支

        Args:
            repo_full_name: 仓库全名
            branch_name: 新分支名称
            source_branch: 源分支名称
        """
        try:
            repo = self.client.get_repo(repo_full_name)

            # 获取源分支的SHA
            source_ref = repo.get_git_ref(f"heads/{source_branch}")
            source_sha = source_ref.object.sha

            # 创建新分支
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=source_sha
            )

            logger.info(f"Successfully created branch '{branch_name}' from '{source_branch}' in {repo_full_name}")
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            raise

    def create_pull_request(self, repo_full_name: str, title: str, body: str, head: str, base: str = "main") -> str:
        """
        创建Pull Request

        Args:
            repo_full_name: 仓库全名
            title: PR标题
            body: PR描述
            head: 源分支
            base: 目标分支

        Returns:
            PR URL
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )
            return pr.html_url
        except Exception as e:
            logger.error(f"Error creating pull request: {e}")
            raise

    def clone_repository(self, repo_url: str, local_path: str = None) -> dict:
        """
        克隆GitHub仓库

        Args:
            repo_url: GitHub仓库URL
            local_path: 本地保存路径（可选）

        Returns:
            包含克隆结果的字典
        """
        try:
            logger.info(f"Cloning GitHub repository: {repo_url}")

            # 解析仓库URL获取仓库信息
            repo_info = self._parse_github_url(repo_url)
            if not repo_info:
                raise ValueError("Invalid GitHub repository URL")

            # 获取仓库对象以验证访问权限
            repo = self.client.get_repo(repo_info['full_name'])

            # 如果没有指定本地路径，使用临时目录
            if not local_path:
                local_path = tempfile.mkdtemp(prefix=f"github_{repo_info['name']}_")

            # 构建带认证的克隆URL
            clone_url = f"https://{self.token}@github.com/{repo_info['full_name']}.git"

            # 执行git clone命令
            result = subprocess.run(
                ['git', 'clone', clone_url, local_path],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                raise Exception(f"Git clone failed: {result.stderr}")

            logger.info(f"Successfully cloned repository to: {local_path}")

            return {
                "success": True,
                "clone_path": local_path,
                "repo_info": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "url": repo.html_url,
                    "description": repo.description,
                    "default_branch": repo.default_branch,
                    "language": repo.language,
                    "private": repo.private
                }
            }

        except subprocess.TimeoutExpired:
            logger.error("Git clone timeout")
            raise Exception("Git clone timeout (5 minutes)")
        except Exception as e:
            logger.error(f"Error cloning GitHub repository: {e}")
            # 清理可能创建的目录
            if local_path and os.path.exists(local_path):
                try:
                    shutil.rmtree(local_path)
                except:
                    pass
            raise

    def _parse_github_url(self, repo_url: str) -> dict:
        """
        解析GitHub仓库URL

        Args:
            repo_url: GitHub仓库URL

        Returns:
            包含仓库信息的字典，如果解析失败返回None
        """
        try:
            # 移除协议前缀
            if repo_url.startswith("https://"):
                repo_url = repo_url[8:]
            elif repo_url.startswith("http://"):
                repo_url = repo_url[7:]

            # 移除github.com前缀
            if repo_url.startswith("github.com/"):
                repo_url = repo_url[11:]

            # 移除.git后缀
            if repo_url.endswith(".git"):
                repo_url = repo_url[:-4]

            # 分割路径
            parts = repo_url.split("/")
            if len(parts) >= 2:
                owner = parts[0]
                name = parts[1]
                full_name = f"{owner}/{name}"

                return {
                    "owner": owner,
                    "name": name,
                    "full_name": full_name
                }

            return None

        except Exception as e:
            logger.error(f"Error parsing GitHub URL: {e}")
            return None

    def create_branch(self, repo_full_name: str, branch_name: str, source_branch: str = "main") -> None:
        """
        创建新分支

        Args:
            repo_full_name: 仓库全名
            branch_name: 新分支名称
            source_branch: 源分支名称
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            source_ref = repo.get_git_ref(f"heads/{source_branch}")
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_ref.object.sha)
            logger.info(f"Created branch {branch_name} from {source_branch} in {repo_full_name}")
        except Exception as e:
            logger.error(f"Error creating branch {branch_name}: {e}")
            raise

    def create_pull_request(self, repo_full_name: str, title: str, body: str,
                          head_branch: str, base_branch: str = "main") -> str:
        """
        创建拉取请求

        Args:
            repo_full_name: 仓库全名
            title: PR标题
            body: PR描述
            head_branch: 源分支
            base_branch: 目标分支

        Returns:
            PR的URL
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            pr = repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
            logger.info(f"Created pull request #{pr.number} in {repo_full_name}")
            return pr.html_url
        except Exception as e:
            logger.error(f"Error creating pull request: {e}")
            raise

# 包装函数，用于向后兼容
def list_repositories(token: str) -> List[GitRepository]:
    """包装函数：列出GitHub仓库"""
    service = GitHubService(token)
    return service.list_repositories()

def list_directories(repo_full_name: str, token: str, path: str = "") -> List[GitDirectory]:
    """包装函数：列出GitHub目录"""
    service = GitHubService(token)
    return service.list_directories(repo_full_name, path)

def save_to_git(tests: List[TestResult], language: str, repo_full_name: str,
                base_path: str, token: str, branch: str = "main") -> List[str]:
    """包装函数：保存到GitHub"""
    service = GitHubService(token)
    return service.save_to_git(tests, language, repo_full_name, base_path, branch)
