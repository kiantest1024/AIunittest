from pydantic import BaseModel
from typing import List, Optional

class CodeSnippet(BaseModel):
    """代码片段模型"""
    name: str
    type: str
    code: str
    language: str
    class_name: Optional[str] = None
    file_path: Optional[str] = None

class GenerateTestRequest(BaseModel):
    """生成测试请求模型"""
    code: str
    language: str
    model: str
    git_repo: Optional[str] = None
    git_path: Optional[str] = None

class TestResult(BaseModel):
    """测试结果模型"""
    name: str
    type: str
    test_code: str
    original_snippet: CodeSnippet
    file_name: Optional[str] = None

class GenerateTestResponse(BaseModel):
    """生成测试响应模型"""
    tests: List[TestResult]
    git_urls: Optional[List[str]] = None

class UploadFileResponse(BaseModel):
    """文件上传响应模型"""
    filename: str
    content: str
    language: Optional[str] = None

class GitRepository(BaseModel):
    """Git仓库模型"""
    name: str
    full_name: str
    url: str

class GitDirectory(BaseModel):
    """Git目录模型"""
    name: str
    path: str
    type: str
    url: str

class GitRepositoriesResponse(BaseModel):
    """Git仓库列表响应模型"""
    repositories: List[GitRepository]

class GitDirectoriesResponse(BaseModel):
    """Git目录列表响应模型"""
    directories: List[GitDirectory]

class GitSaveRequest(BaseModel):
    """Git保存请求模型"""
    tests: List[TestResult]
    language: str
    repo: str
    path: str
    token: str
    platform: str = "github"
    server_url: Optional[str] = None  # 自定义服务器地址

class GitSaveResponse(BaseModel):
    """Git保存响应模型,支持多个Git平台的URL响应"""
    urls: List[str]
    platform: str = "github"
class GitLabCloneRequest(BaseModel):
    """GitLab仓库克隆请求模型"""
    repo_url: str  # 统一使用repo_url字段名
    token: str
    path: str = ""
    server_url: str = ""  # 添加服务器地址字段

class GitLabCloneResponse(BaseModel):
    """GitLab仓库克隆响应模型"""
    success: bool
    clone_path: str
    repo_info: Optional[dict] = None  # 添加仓库信息字段，与GitHub保持一致

class GitHubCloneRequest(BaseModel):
    """GitHub仓库克隆请求模型"""
    repo_url: str
    token: str
    path: str = ""

class GitHubCloneResponse(BaseModel):
    """GitHub仓库克隆响应模型"""
    success: bool
    clone_path: str
    repo_info: dict = None

class GitServerConfigRequest(BaseModel):
    """Git服务器配置请求模型"""
    platform: str  # "github" 或 "gitlab"
    server_url: str  # 服务器地址，如 "https://github.com" 或 "http://172.16.1.30"
    token: str

class GitServerConfigResponse(BaseModel):
    """Git服务器配置响应模型"""
    success: bool
    message: str
    server_info: Optional[dict] = None

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str
