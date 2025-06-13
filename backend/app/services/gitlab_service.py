from typing import List
import os
import gitlab
from ..utils.logger import logger
from ..config import settings
from ..models.schemas import GitLabCloneResponse
from .base_git_service import BaseGitService

class GitLabService(BaseGitService):
    """GitLab 服务类，处理所有 GitLab 相关操作"""

    def __init__(self, token: str, gitlab_url: str = None):
        """
        初始化 GitLab 服务

        Args:
            token: GitLab 访问令牌
            gitlab_url: GitLab 服务器URL，如果为None则使用默认URL
        """
        if not token or token.strip() == "":
            raise ValueError("GitLab token is required")

        self.token = token.strip()

        # 确定GitLab服务器URL
        if gitlab_url is None:
            # 使用默认的GitLab.com
            self.gitlab_url = settings.GITLAB_DEFAULT_URL
            logger.info(f"Using default GitLab URL: {self.gitlab_url}")
        else:
            # 使用用户提供的URL
            self.gitlab_url = self._normalize_gitlab_url(gitlab_url)
            logger.info(f"Using custom GitLab URL: {self.gitlab_url}")

        try:
            logger.info(f"Initializing GitLab service with URL: {self.gitlab_url}")
            logger.info(f"Token format: {self.token[:10]}... (length: {len(self.token)})")
            self.gl = gitlab.Gitlab(url=self.gitlab_url, private_token=self.token)
            logger.info(f"GitLab service initialized successfully for {self.gitlab_url}")
        except Exception as e:
            logger.error(f"Failed to initialize GitLab service: {e}")
            logger.error(f"Token used: {self.token[:10]}...")
            logger.error(f"URL used: {self.gitlab_url}")
            raise ValueError(f"Failed to initialize GitLab service: {e}")

    def _normalize_gitlab_url(self, url: str) -> str:
        """
        标准化GitLab URL格式

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

        # 移除可能的/api/v4后缀
        if url.endswith('/api/v4'):
            url = url[:-7]

        logger.info(f"Normalized GitLab URL: {url}")
        return url

    def _is_ip_address(self, url: str) -> bool:
        """检查是否为IP地址"""
        import re
        # 简单的IP地址检查
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$'
        return bool(re.match(ip_pattern, url))
    
    def clone_repository(self, repo_url: str, local_path: str) -> GitLabCloneResponse:
        """
        克隆 GitLab 仓库

        Args:
            repo_url: GitLab 仓库 URL 或项目路径
            local_path: 本地保存路径

        Returns:
            包含克隆结果的响应对象
        """
        try:
            logger.info(f"Cloning GitLab repository: {repo_url} to {local_path}")

            # 使用统一的项目获取方法
            project = self._get_project(repo_url)
            logger.info(f"Successfully got project: {project.name} (ID: {project.id})")

            # 获取克隆URL
            clone_url = project.http_url_to_repo
            logger.info(f"Original clone URL: {clone_url}")

            # 构建带认证的克隆URL
            # 对于GitLab，使用oauth2:token格式进行认证
            if clone_url.startswith("http://"):
                # 插入认证信息到HTTP URL中
                auth_url = clone_url.replace("http://", f"http://oauth2:{self.token}@")
            elif clone_url.startswith("https://"):
                # 插入认证信息到HTTPS URL中
                auth_url = clone_url.replace("https://", f"https://oauth2:{self.token}@")
            else:
                # 如果URL格式不符合预期，使用原始URL
                auth_url = clone_url

            logger.info(f"Authenticated clone URL: {auth_url[:50]}...")

            # 确保本地路径存在
            import os
            import tempfile

            # 如果没有指定本地路径，创建临时目录
            if not local_path:
                temp_dir = tempfile.mkdtemp()
                local_path = os.path.join(temp_dir, project.name)
                logger.info(f"Created temporary clone path: {local_path}")
            elif not os.path.exists(os.path.dirname(local_path)):
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 使用subprocess执行克隆命令以获得更好的错误处理
            import subprocess
            clone_command = ["git", "clone", auth_url, local_path]
            logger.info(f"Executing clone command: git clone [authenticated_url] {local_path}")

            try:
                result = subprocess.run(
                    clone_command,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )

                if result.returncode == 0:
                    logger.info(f"Successfully cloned repository to: {local_path}")

                    # 构建仓库信息，与GitHub格式保持一致
                    repo_info = {
                        "name": project.name,
                        "full_name": project.path_with_namespace,
                        "description": project.description or "",
                        "private": project.visibility == "private",
                        "default_branch": getattr(project, 'default_branch', 'main'),
                        "clone_url": project.http_url_to_repo,
                        "web_url": project.web_url
                    }

                    return GitLabCloneResponse(
                        success=True,
                        clone_path=local_path,
                        repo_info=repo_info
                    )
                else:
                    logger.error(f"Git clone failed with exit code: {result.returncode}")
                    logger.error(f"Git clone stderr: {result.stderr}")
                    logger.error(f"Git clone stdout: {result.stdout}")
                    raise ValueError(f"Git clone failed: {result.stderr}")

            except subprocess.TimeoutExpired:
                logger.error("Git clone timeout")
                raise ValueError("Repository clone timeout")
            except Exception as subprocess_error:
                logger.error(f"Error executing git clone: {subprocess_error}")
                raise ValueError(f"Failed to execute git clone: {str(subprocess_error)}")

        except Exception as e:
            logger.error(f"Error cloning GitLab repository: {str(e)}")
            raise ValueError(f"Failed to clone repository: {str(e)}")
    
    def list_directories(self, repo_url: str, path: str = "") -> List[dict]:
        """
        列出仓库中的文件和目录

        Args:
            repo_url: GitLab 仓库 URL 或项目路径 (如: kian/backend-lotto-game)
            path: 要列出内容的目录路径

        Returns:
            文件和目录列表
        """
        try:
            logger.info(f"Listing directories for repo: {repo_url}, path: {path}")

            # 解析项目路径 - 支持多种格式
            project_path = self._parse_project_path(repo_url)
            logger.info(f"Parsed project path: {project_path}")

            # 获取项目实例
            project = self.gl.projects.get(project_path)
            logger.info(f"Got project: {project.name} (ID: {project.id})")

            # 获取项目的默认分支
            default_branch = getattr(project, 'default_branch', 'master')
            logger.info(f"Project default branch: {default_branch}")

            # 尝试获取文件列表，如果默认分支失败则尝试其他常见分支
            items = None
            branches_to_try = [default_branch, 'main', 'master', 'develop']
            # 去重并保持顺序
            branches_to_try = list(dict.fromkeys(branches_to_try))

            for branch in branches_to_try:
                try:
                    logger.info(f"Trying branch: {branch}")
                    items = project.repository_tree(path=path, ref=branch)
                    logger.info(f"Successfully found {len(items)} items using branch: {branch}")
                    # 更新使用的分支
                    default_branch = branch
                    break
                except Exception as branch_error:
                    logger.warning(f"Branch '{branch}' failed: {branch_error}")
                    continue

            if items is None:
                raise ValueError(f"Could not access repository tree with any branch: {branches_to_try}")

            # 转换为统一格式
            result = []
            for item in items:
                # 构建文件/目录的URL，使用项目的默认分支
                if item["type"] == "tree":
                    # 目录URL
                    item_url = f"{self.gitlab_url}/{project_path}/-/tree/{default_branch}/{item['path']}"
                else:
                    # 文件URL
                    item_url = f"{self.gitlab_url}/{project_path}/-/blob/{default_branch}/{item['path']}"

                result.append({
                    "name": item["name"],
                    "path": item["path"],
                    "type": "dir" if item["type"] == "tree" else "file",
                    "url": item_url
                })

            return result

        except Exception as e:
            logger.error(f"Error listing GitLab files: {str(e)}")
            logger.error(f"Repo URL: {repo_url}, Path: {path}")
            raise
    
    def save_to_git(self, repo_url: str, file_path: str, content: str, message: str) -> str:
        """
        保存文件到 GitLab 仓库
        
        Args:
            repo_url: GitLab 仓库 URL
            file_path: 文件路径
            content: 文件内容
            message: 提交信息
            
        Returns:
            文件的 URL
        """
        try:
            # 解析项目路径
            if repo_url.startswith("https://"):
                repo_url = repo_url.replace("https://", "")
            parts = repo_url.split("/")
            project_path = "/".join(parts[1:])
            if project_path.endswith(".git"):
                project_path = project_path[:-4]
            
            # 获取项目实例
            project = self.gl.projects.get(project_path)
            
            # 创建或更新文件
            file_data = {
                'branch': 'master',
                'content': content,
                'commit_message': message
            }
            
            try:
                # 尝试更新文件
                f = project.files.get(file_path=file_path, ref='master')
                f.content = content
                f.save(branch='master', commit_message=message)
            except gitlab.exceptions.GitlabGetError:
                # 文件不存在，创建新文件
                project.files.create(file_data, file_path)
            
            # 返回文件URL
            return f"{repo_url}/blob/master/{file_path}"
            
        except Exception as e:
            logger.error(f"Error saving file to GitLab: {str(e)}")
            raise

    def create_branch(self, repo_full_name: str, branch_name: str, source_branch: str = "main") -> None:
        """
        在仓库中创建新分支

        Args:
            repo_full_name: 仓库全名 (格式: owner/repo)
            branch_name: 新分支名称
            source_branch: 源分支名称
        """
        try:
            # 获取项目实例
            project = self.gl.projects.get(repo_full_name)

            # 创建分支
            project.branches.create({
                'branch': branch_name,
                'ref': source_branch
            })
            logger.info(f"Created branch {branch_name} from {source_branch} in {repo_full_name}")

        except Exception as e:
            logger.error(f"Error creating GitLab branch: {str(e)}")
            raise
    
    def create_pull_request(self, repo_full_name: str, title: str, body: str,
                          head_branch: str, base_branch: str = "main") -> str:
        """
        创建合并请求

        Args:
            repo_full_name: 仓库全名 (格式: owner/repo)
            title: 合并请求标题
            body: 合并请求描述
            head_branch: 源分支
            base_branch: 目标分支

        Returns:
            合并请求的 URL
        """
        try:
            # 获取项目实例
            project = self.gl.projects.get(repo_full_name)

            # 创建合并请求
            mr = project.mergerequests.create({
                'source_branch': head_branch,
                'target_branch': base_branch,
                'title': title,
                'description': body
            })

            logger.info(f"Created merge request !{mr.iid} in {repo_full_name}")
            return mr.web_url

        except Exception as e:
            logger.error(f"Error creating GitLab merge request: {str(e)}")
            raise
            
    def _parse_repo_url(self, repo_url: str) -> str:
        """解析 GitLab 仓库 URL 获取项目路径"""
        if repo_url.startswith("https://"):
            repo_url = repo_url.replace("https://", "")
        parts = repo_url.split("/")
        project_path = "/".join(parts[1:])
        if project_path.endswith(".git"):
            project_path = project_path[:-4]
        return project_path

    def _parse_project_path(self, repo_input: str) -> str:
        """
        解析项目路径，支持多种输入格式

        Args:
            repo_input: 可以是以下格式之一:
                - full_name: kian/backend-lotto-game
                - URL: http://172.16.1.30/kian/backend-lotto-game
                - URL: https://gitlab.com/kian/backend-lotto-game

        Returns:
            项目路径用于GitLab API调用
        """
        logger.info(f"Parsing project path from: {repo_input}")

        # 如果是完整URL，解析出项目路径
        if repo_input.startswith(("http://", "https://")):
            # 移除协议
            if repo_input.startswith("https://"):
                repo_input = repo_input.replace("https://", "")
            elif repo_input.startswith("http://"):
                repo_input = repo_input.replace("http://", "")

            # 分割路径
            parts = repo_input.split("/")
            if len(parts) >= 3:
                # 格式: gitlab.com/user/project 或 172.16.1.30/user/project
                project_path = "/".join(parts[1:])
                if project_path.endswith(".git"):
                    project_path = project_path[:-4]
                logger.info(f"Extracted project path from URL: {project_path}")
                return project_path
            else:
                raise ValueError(f"Invalid URL format: {repo_input}")

        # 如果不是URL，假设是 full_name 格式 (user/project)
        elif "/" in repo_input:
            # 移除可能的.git后缀
            project_path = repo_input
            if project_path.endswith(".git"):
                project_path = project_path[:-4]
            logger.info(f"Using full_name format: {project_path}")
            return project_path

        else:
            # 可能是项目名称，但我们需要完整路径
            raise ValueError(f"Invalid project format: {repo_input}. Expected format: 'user/project' or full URL")
        
    def _get_project(self, repo_url: str):
        """获取 GitLab 项目实例"""
        project_path = self._parse_project_path(repo_url)

        # 尝试不同的方式获取项目
        try:
            # 方法1: 使用URL编码的项目路径
            encoded_path = project_path.replace('/', '%2F')
            logger.info(f"Trying to get project with encoded path: {encoded_path}")
            return self.gl.projects.get(encoded_path)
        except Exception as e1:
            logger.warning(f"Failed to get project with encoded path: {e1}")

            try:
                # 方法2: 直接使用项目路径（某些GitLab版本支持）
                logger.info(f"Trying to get project with direct path: {project_path}")
                return self.gl.projects.get(project_path)
            except Exception as e2:
                logger.warning(f"Failed to get project with direct path: {e2}")

                try:
                    # 方法3: 通过搜索找到项目ID，然后使用ID获取
                    logger.info(f"Trying to find project by searching: {project_path}")
                    projects = self.gl.projects.list(search=project_path.split('/')[-1])
                    for project in projects:
                        if project.path_with_namespace == project_path:
                            logger.info(f"Found project by search, using ID: {project.id}")
                            return self.gl.projects.get(project.id)

                    # 如果搜索也失败，抛出原始错误
                    raise e1

                except Exception as e3:
                    logger.error(f"All methods failed to get project: {project_path}")
                    logger.error(f"  - Encoded path error: {e1}")
                    logger.error(f"  - Direct path error: {e2}")
                    logger.error(f"  - Search error: {e3}")
                    raise e1
        
    def list_repositories(self) -> List[dict]:
        """列出所有可访问的仓库"""
        try:
            # 验证token是否有效
            if not self.token or self.token == "invalid_token":
                logger.error("Invalid or missing GitLab token")
                raise ValueError("Invalid or missing GitLab token")

            # 验证token - 直接尝试获取项目列表来验证
            logger.info(f"Validating GitLab token: {self.token[:10]}...")

            # 获取项目列表，使用更宽松的参数
            try:
                # 先尝试获取用户拥有的项目
                projects = self.gl.projects.list(owned=True, per_page=100)
                logger.info(f"Found {len(projects)} owned projects")

                # 如果没有拥有的项目，尝试获取用户可访问的项目
                if len(projects) == 0:
                    projects = self.gl.projects.list(membership=True, per_page=100)
                    logger.info(f"Found {len(projects)} accessible projects")

            except Exception as list_error:
                logger.error(f"Error listing GitLab projects: {list_error}")
                # 检查是否是401错误（权限问题）
                if "401" in str(list_error) or "Unauthorized" in str(list_error):
                    logger.error("GitLab token lacks required permissions")
                    raise ValueError("Invalid GitLab token or insufficient permissions. Please ensure your token has 'api' or 'read_api' scope.")

                # 尝试更基本的API调用
                try:
                    projects = self.gl.projects.list(per_page=50)
                    logger.info(f"Found {len(projects)} projects with basic listing")
                except Exception as basic_error:
                    logger.error(f"Basic project listing also failed: {basic_error}")
                    if "401" in str(basic_error) or "Unauthorized" in str(basic_error):
                        raise ValueError("Invalid GitLab token or insufficient permissions. Please ensure your token has 'api' or 'read_api' scope.")
                    else:
                        raise ValueError(f"Failed to list GitLab repositories: {basic_error}")

            repositories = []
            for project in projects:
                try:
                    repositories.append({
                        "name": project.name,
                        "full_name": project.path_with_namespace,  # 添加full_name字段以兼容GitHub格式
                        "url": project.web_url,
                        "description": project.description or "",
                        "private": project.visibility == "private",
                        "default_branch": getattr(project, 'default_branch', 'main')
                    })
                except Exception as project_error:
                    logger.warning(f"Error processing project {project.name}: {project_error}")
                    continue

            logger.info(f"Successfully processed {len(repositories)} GitLab repositories")
            return repositories

        except gitlab.exceptions.GitlabAuthenticationError as auth_error:
            logger.error(f"GitLab authentication failed: {auth_error}")
            raise ValueError("Invalid GitLab token")
        except ValueError as ve:
            # 重新抛出已知的ValueError
            raise ve
        except Exception as e:
            logger.error(f"Unexpected error listing GitLab repositories: {str(e)}")
            raise ValueError(f"Failed to list GitLab repositories: {str(e)}")
            
    def get_file_content(self, repo_url: str, file_path: str, ref: str = None) -> str:
        """获取文件内容"""
        try:
            project = self._get_project(repo_url)

            # 如果没有指定分支，使用项目的默认分支
            if ref is None:
                ref = getattr(project, 'default_branch', 'master')
                logger.info(f"Using project default branch for file content: {ref}")

            # 尝试获取文件内容，如果指定分支失败则尝试其他常见分支
            branches_to_try = [ref, 'main', 'master', 'develop'] if ref else ['main', 'master', 'develop']
            # 去重并保持顺序
            branches_to_try = list(dict.fromkeys(branches_to_try))

            for branch in branches_to_try:
                try:
                    logger.info(f"Trying to get file content from branch: {branch}")
                    f = project.files.get(file_path=file_path, ref=branch)
                    content = f.decode().decode('utf-8')
                    logger.info(f"Successfully got file content from branch: {branch}")
                    return content
                except Exception as branch_error:
                    logger.warning(f"Failed to get file from branch '{branch}': {branch_error}")
                    continue

            # 如果所有分支都失败了
            raise ValueError(f"Could not get file content from any branch: {branches_to_try}")

        except Exception as e:
            logger.error(f"Error getting file content from GitLab: {str(e)}")
            logger.error(f"Repo URL: {repo_url}, File path: {file_path}")
            raise

    def save_tests(self, tests, language: str, repo_full_name: str, base_path: str) -> list:
        """
        将生成的测试保存到GitLab仓库

        Args:
            tests: 测试结果列表
            language: 编程语言
            repo_full_name: 仓库全名
            base_path: 基础路径

        Returns:
            保存的文件URL列表
        """
        try:
            logger.info(f"Starting save_tests to GitLab with parameters:")
            logger.info(f"  - language: {language}")
            logger.info(f"  - repo_full_name: {repo_full_name}")
            logger.info(f"  - base_path: {base_path}")
            logger.info(f"  - tests count: {len(tests)}")

            # 获取项目实例
            project = self._get_project(repo_full_name)

            # 获取项目的默认分支
            default_branch = getattr(project, 'default_branch', 'main')
            logger.info(f"Using project default branch: {default_branch}")

            urls = []

            # 获取语言配置
            from app.config import LANGUAGE_CONFIG
            lang_config = LANGUAGE_CONFIG.get(language, {})
            file_extension = lang_config.get("file_extensions", [".py"])[0]
            logger.info(f"Using file extension: {file_extension} for language: {language}")

            # 规范化基础路径
            normalized_base_path = base_path.replace('\\', '/') if base_path else ""
            logger.info(f"Normalized base path: '{normalized_base_path}'")

            for test in tests:
                # 构建测试文件名
                if hasattr(test, 'original_snippet') and hasattr(test.original_snippet, 'class_name') and test.original_snippet.class_name:
                    # 对于类方法，使用 ClassName_methodName 格式
                    file_name = f"{test.original_snippet.class_name}_{test.original_snippet.name}{file_extension}"
                elif hasattr(test, 'original_snippet') and hasattr(test.original_snippet, 'name'):
                    # 对于函数，直接使用函数名
                    file_name = f"{test.original_snippet.name}{file_extension}"
                else:
                    # 如果没有原始代码片段信息，使用测试名称
                    file_name = f"{test.name}{file_extension}"

                # 构建文件路径
                if normalized_base_path:
                    if not normalized_base_path.endswith('/'):
                        normalized_base_path += '/'
                    file_path = normalized_base_path + file_name
                else:
                    file_path = file_name

                logger.info(f"Constructed file path: '{file_path}'")

                # 保存文件到GitLab
                try:
                    # 检查文件是否已存在
                    try:
                        existing_file = project.files.get(file_path=file_path, ref=default_branch)
                        # 文件存在，更新它
                        logger.info(f"File exists, updating: '{file_path}'")
                        existing_file.content = test.test_code
                        existing_file.save(branch=default_branch, commit_message=f"Update {file_name} with AI generated tests")

                        # 构建文件URL
                        file_url = f"{self.gitlab_url}/{repo_full_name}/-/blob/{default_branch}/{file_path}"
                        logger.info(f"Successfully updated file: '{file_path}', URL: {file_url}")
                        urls.append(file_url)

                    except Exception as not_found_error:
                        # 检查是否是文件不存在的错误
                        if "404" in str(not_found_error) or "not found" in str(not_found_error).lower():
                            # 文件不存在，创建新文件
                            logger.info(f"File does not exist, creating new file: '{file_path}'")
                            file_data = {
                                'file_path': file_path,
                                'branch': default_branch,
                                'content': test.test_code,
                                'commit_message': f"Add {file_name} with AI generated tests"
                            }
                            project.files.create(file_data)

                            # 构建文件URL
                            file_url = f"{self.gitlab_url}/{repo_full_name}/-/blob/{default_branch}/{file_path}"
                            logger.info(f"Successfully created file: '{file_path}', URL: {file_url}")
                            urls.append(file_url)
                        else:
                            # 其他错误，重新抛出
                            logger.error(f"Error checking if file exists: {not_found_error}")
                            raise not_found_error

                except Exception as e:
                    logger.error(f"Error saving file '{file_path}': {e}")
                    raise

            logger.info(f"Saved {len(urls)} files to GitLab repository {repo_full_name}")
            return urls

        except Exception as e:
            logger.error(f"Error saving tests to GitLab: {e}")
            raise
