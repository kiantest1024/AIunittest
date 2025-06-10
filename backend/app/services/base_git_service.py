from typing import List
from abc import ABC, abstractmethod
from app.models.schemas import TestResult, GitRepository, GitDirectory
from app.utils.logger import logger

class BaseGitService(ABC):
    """Git服务基类，定义了所有Git操作的接口"""

    def __init__(self, token: str):
        """
        初始化Git服务
        
        Args:
            token: 访问令牌
        """
        self.token = token

    @abstractmethod
    def list_repositories(self) -> List[GitRepository]:
        """
        列出用户的代码仓库
        
        Returns:
            仓库列表
        """
        pass

    @abstractmethod
    def list_directories(self, repo_full_name: str, path: str = "") -> List[GitDirectory]:
        """
        列出仓库中的目录和文件
        
        Args:
            repo_full_name: 仓库全名
            path: 目录路径
            
        Returns:
            目录和文件列表
        """
        pass

    @abstractmethod
    def save_to_git(self, tests: List[TestResult], language: str, repo_full_name: str, 
                    base_path: str, branch: str = "main") -> List[str]:
        """
        将生成的测试保存到Git仓库
        
        Args:
            tests: 测试结果列表
            language: 编程语言
            repo_full_name: 仓库全名
            base_path: 基础路径
            branch: 分支名称
            
        Returns:
            保存的文件URL列表
        """
        pass

    @abstractmethod
    def get_file_content(self, repo_full_name: str, path: str) -> str:
        """
        获取文件内容
        
        Args:
            repo_full_name: 仓库全名
            path: 文件路径
            
        Returns:
            文件内容
        """
        pass

    @abstractmethod
    def create_branch(self, repo_full_name: str, branch_name: str, source_branch: str = "main") -> None:
        """
        创建新分支
        
        Args:
            repo_full_name: 仓库全名
            branch_name: 新分支名称
            source_branch: 源分支名称
        """
        pass

    @abstractmethod
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
        pass
