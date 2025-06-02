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

class GitSaveResponse(BaseModel):
    """Git保存响应模型"""
    urls: List[str]

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str
