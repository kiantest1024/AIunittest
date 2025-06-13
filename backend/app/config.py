import os
import hashlib
import json
from typing import List, Dict, Any
from pathlib import Path

# 尝试从 pydantic_settings 导入 BaseSettings（Pydantic v2）
try:
    from pydantic_settings import BaseSettings
# 如果失败，则从 pydantic 导入 BaseSettings（Pydantic v1）
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        # 如果两者都失败，使用简单的字典代替
        print("Warning: Neither pydantic v1 nor pydantic_settings is available. Using a simple dict for settings.")

        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

            class Config:
                pass

class Settings(BaseSettings):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 创建必要的目录
        os.makedirs(self.GIT_TEMP_DIR, exist_ok=True)
        os.makedirs(self.GIT_CACHE_DIR, exist_ok=True)
    """应用配置"""
    # 应用设置
    APP_NAME: str = "AI单元测试生成工具"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "为多种编程语言生成单元测试的Web工具"

    # API密钥
    # 使用环境变量或默认值
    # 注意：默认值仅用于开发环境，生产环境应使用环境变量或.env文件
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "sk-demo-openai-key-for-development-only")
    GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "demo-google-key-for-development-only")
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "sk-ant-api-demo-anthropic-key-for-development-only")
    GROK_API_KEY: str = os.environ.get("GROK_API_KEY", "gsk-demo-grok-key-for-development-only")
    DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "demo-deepseek-key-for-development-only")

    # CORS设置
    CORS_ORIGINS: List[str] = ["*", "http://localhost:3000"]

    # 生成的测试文件保存目录
    GENERATED_TESTS_DIR: str = "tests/generated"
    TEMP_DIR: str = "temp"
    CACHE_DIR: str = "cache"
    
    # Git缓存配置
    GIT_CACHE_TIMEOUT: int = 3600  # 1小时
    GIT_MAX_CACHE_SIZE: int = 1024 * 1024 * 100  # 100MB

    # Git服务配置
    GIT_TEMP_DIR: str = os.path.join(os.path.dirname(__file__), "../temp")
    GIT_CACHE_DIR: str = os.path.join(os.path.dirname(__file__), "../cache")
    
    # GitHub配置
    GITHUB_DEFAULT_URL: str = "https://github.com"
    GITHUB_DEFAULT_API_URL: str = "https://api.github.com"
    GITHUB_DEFAULT_BRANCH: str = "main"

    # GitLab配置
    GITLAB_DEFAULT_URL: str = "https://gitlab.com"
    GITLAB_DEFAULT_API_URL: str = "https://gitlab.com/api/v4"
    GITLAB_DEFAULT_BRANCH: str = "master"
    GITLAB_CLONE_DEPTH: int = 1

    # 向后兼容的环境变量支持
    GITLAB_API_URL: str = os.environ.get("GITLAB_API_URL", GITLAB_DEFAULT_API_URL)

    class Config:
        env_file = ".env"

settings = Settings()

# AI配置管理器
class AIConfigManager:
    """AI配置管理器，支持动态配置和密码保护"""

    def __init__(self):
        self.config_file = Path(__file__).parent / "ai_config.json"
        self.admin_password_hash = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # "password"的SHA256
        self._load_config()

    def _load_config(self):
        """加载AI配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.custom_models = config_data.get('custom_models', {})
                    self.system_models = config_data.get('system_models', {})
                    self.default_model = config_data.get('default_model', 'deepseek-V3')
                    # 更新管理员密码哈希（如果配置文件中有的话）
                    if 'admin_password_hash' in config_data:
                        self.admin_password_hash = config_data['admin_password_hash']
            except Exception as e:
                print(f"Error loading AI config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置"""
        self.custom_models = {}
        self.system_models = self._get_default_system_models()
        self.default_model = 'deepseek-V3'
        self._save_config()

    def _save_config(self):
        """保存配置到文件"""
        config_data = {
            'custom_models': self.custom_models,
            'system_models': self.system_models,
            'default_model': self.default_model,
            'admin_password_hash': self.admin_password_hash,
            'last_updated': str(Path(__file__).stat().st_mtime)
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving AI config: {e}")

    def verify_password(self, password: str) -> bool:
        """验证管理员密码"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.admin_password_hash

    def change_password(self, old_password: str, new_password: str) -> bool:
        """修改管理员密码"""
        if not self.verify_password(old_password):
            return False
        self.admin_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        self._save_config()
        return True

    def get_all_models(self) -> Dict[str, Any]:
        """获取所有可用模型"""
        all_models = {}
        all_models.update(self.system_models)
        all_models.update(self.custom_models)
        return all_models

    def add_custom_model(self, model_name: str, model_config: Dict[str, Any]) -> bool:
        """添加自定义模型"""
        try:
            self.custom_models[model_name] = model_config
            self._save_config()
            return True
        except Exception as e:
            print(f"Error adding custom model: {e}")
            return False

    def update_model(self, model_name: str, model_config: Dict[str, Any]) -> bool:
        """更新模型配置"""
        try:
            if model_name in self.system_models:
                self.system_models[model_name] = model_config
            else:
                self.custom_models[model_name] = model_config
            self._save_config()
            return True
        except Exception as e:
            print(f"Error updating model: {e}")
            return False

    def delete_custom_model(self, model_name: str) -> bool:
        """删除自定义模型"""
        try:
            if model_name in self.custom_models:
                del self.custom_models[model_name]
                self._save_config()
                return True
            return False
        except Exception as e:
            print(f"Error deleting custom model: {e}")
            return False

    def set_default_model(self, model_name: str) -> bool:
        """设置默认模型"""
        all_models = self.get_all_models()
        if model_name in all_models:
            self.default_model = model_name
            self._save_config()
            return True
        return False

    def _get_default_system_models(self) -> Dict[str, Any]:
        """获取默认系统模型配置"""
        return {
            "chatgpt4nano": {
                "provider": "openai",
                "api_key": settings.OPENAI_API_KEY,
                "api_base": "https://api.openai.com/v1",
                "model": "GPT-4.1 nano",
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 30,
                "is_system": True
            },
            "chatgpt4.1mini": {
                "provider": "openai",
                "api_key": settings.OPENAI_API_KEY,
                "api_base": "https://api.openai.com/v1",
                "model": "GPT-4.1 mini",
                "temperature": 0.7,
                "max_tokens": 4000,
                "timeout": 60,
                "is_system": True
            },
            "google_gemini": {
                "provider": "google",
                "api_key": settings.GOOGLE_API_KEY,
                "api_base": "https://generativelanguage.googleapis.com/v1beta",
                "model": "gemini-pro",
                "temperature": 0.7,
                "max_tokens": 2048,
                "timeout": 30,
                "is_system": True
            },
            "anthropic_claude": {
                "provider": "anthropic",
                "api_key": settings.ANTHROPIC_API_KEY,
                "api_base": "https://api.anthropic.com/v1",
                "model": "claude-3-opus-20240229",
                "temperature": 0.7,
                "max_tokens": 4000,
                "timeout": 60,
                "is_system": True
            },
            "xai_grok": {
                "provider": "grok",
                "api_key": settings.GROK_API_KEY,
                "api_base": "https://api.grok.ai/v1",
                "model": "grok-1",
                "temperature": 0.7,
                "max_tokens": 4000,
                "timeout": 60,
                "is_system": True
            },
            "deepseek-V3": {
                "provider": "deepseek",
                "api_key": settings.DEEPSEEK_API_KEY,
                "api_base": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 4000,
                "timeout": 300,
                "is_system": True
            },
            "deepseek-R1": {
                "provider": "deepseek",
                "api_key": settings.DEEPSEEK_API_KEY,
                "api_base": "https://api.deepseek.com/v1",
                "model": "deepseek-reasoner",
                "temperature": 0.7,
                "max_tokens": 8000,
                "timeout": 1200,
                "is_system": True
            }
        }

# 创建全局AI配置管理器实例
ai_config_manager = AIConfigManager()

# AI模型配置（动态获取）
def get_ai_models() -> Dict[str, Any]:
    """获取当前AI模型配置"""
    return ai_config_manager.get_all_models()

# 为了向后兼容，保留AI_MODELS变量
AI_MODELS = get_ai_models()

# 语言配置
LANGUAGE_CONFIG = {
    "python": {
        "file_extensions": [".py"],
        "test_framework": "pytest",
        "test_file_prefix": "test_"
    },
    "java": {
        "file_extensions": [".java"],
        "test_framework": "junit",
        "test_file_suffix": "Test"
    },
    "go": {
        "file_extensions": [".go"],
        "test_framework": "testing",
        "test_file_suffix": "_test"
    },
    "cpp": {
        "file_extensions": [".cpp", ".h", ".hpp"],
        "test_framework": "gtest",
        "test_file_suffix": "_test"
    },
    "csharp": {
        "file_extensions": [".cs"],
        "test_framework": "nunit",
        "test_file_suffix": "Tests"
    }
}

# 提示模板
PROMPT_TEMPLATES = {
    "python": """
请为以下Python {code_type}生成可直接运行的单元测试代码:

```python
{code}
```
作为资深测试工程师，请基于以下[代码片段]和[需求描述]，生成满足以下要求的单元测试：

1. 分析代码结构
   - 识别被测函数/类的输入输出
   - 提取边界条件和异常处理逻辑
   - 标注代码中的依赖项（需Mock的部分）

2. 生成测试用例（按优先级排序）
   - 基础功能验证（Happy Path）
   - 边界值测试（最小/最大/临界值）
   - 异常场景（非法输入/错误处理）
   - 状态变化验证（有状态对象）

3. 技术要求
   - 使用[指定测试框架]（如JUnit/Pytest）
   - 包含断言说明文档
   - 覆盖率目标：语句覆盖90%+，分支覆盖85%+
   - 处理外部依赖（Mockito/Patch示例）

请生成完整的、可直接运行的测试代码，包括所有必要的导入语句、测试函数和断言。
测试应该全面覆盖代码的功能，包括正常情况和边缘情况。
使用pytest框架，并遵循以下指南:

1. 测试函数名应以'test_'开头
2. 使用描述性的测试函数名称，清晰表明测试的目的
3. 为每个测试用例添加清晰的注释，说明测试的目的和预期结果
4. 包含必要的mock对象或测试夹具，模拟外部依赖
5. 使用有意义的断言消息，便于理解测试失败的原因
6. 考虑边缘情况和异常处理，包括空值、边界值、异常输入等
7. 确保测试是独立的，不依赖于其他测试的执行顺序
8. 使用参数化测试减少重复代码
9. 添加必要的setup和teardown代码，确保测试环境的一致性

请仅返回可直接运行的测试代码，不要包含任何解释或额外的文本。
测试代码必须包含被测函数/类的导入语句，这是最关键的部分。
""",

    "java": """
请为以下Java {code_type}生成单元测试代码:

```java
{code}
```
作为Java测试架构师，生成符合JUnit5企业级规范的测试类：

代码分析要求：
1. 识别空安全注解（@NonNull等）
2. 标注需要Mock的静态方法
3. 分析泛型类型边界
4. 识别多线程安全隐患

测试生成规范：
[技术要求]
- 使用@ParameterizedTest + @CsvSource数据驱动
- 对时间相关测试使用@Timeout
- 使用AssertJ进行流式断言
- 必须验证void方法的副作用
- 包含Jacoco覆盖率配置示例
- BigDecimal比较使用Comparator

请生成完整的测试代码，包括必要的导入语句、测试类和断言。
测试应该全面覆盖代码的功能，包括正常情况和边缘情况。
使用JUnit 5框架，并遵循以下指南:

1. 测试类名应为"{class_name}Test"
2. 使用@Test注解标记测试方法
3. 使用描述性的测试方法名称
4. 为每个测试用例添加清晰的注释
5. 使用Mockito进行必要的模拟
6. 使用断言方法验证结果
7. 考虑边缘情况和异常处理

假设可以使用以下导入语句:
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import org.mockito.Mockito;
import static org.mockito.Mockito.*;

请仅返回测试代码，不要包含任何解释或额外的文本。
""",

    "go": """
请为以下Go {code_type}生成单元测试代码:

```go
{code}
```
作为Go测试专家，生成符合GoConvey规范的表格驱动测试：

代码分析要求：
1. 识别接口实现完整性
2. 标注并发安全风险点
3. 分析error处理模式
4. 识别time.Now()等非幂等调用

测试生成规范：
[技术要求]
- 使用t.Run实现子测试
- 必须包含并行测试标记
- 使用testify/assert进行断言
- 对time依赖使用clock.Mock
- 包含覆盖率指令：go test -coverprofile=coverage.out
- 使用httptest处理HTTP依赖

请生成完整的测试代码，包括必要的导入语句和测试函数。
测试应该全面覆盖代码的功能，包括正常情况和边缘情况。
使用Go标准testing包，并遵循以下指南:

1. 测试函数名应为"Test{function_name}"
2. 使用t.Run()进行子测试
3. 使用描述性的测试名称
4. 为每个测试用例添加清晰的注释
5. 使用testify/mock进行必要的模拟
6. 使用断言验证结果
7. 考虑边缘情况和错误处理

假设可以使用以下导入语句:
import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

请仅返回测试代码，不要包含任何解释或额外的文本。
""",

    "cpp": """
请为以下C++ {code_type}生成单元测试代码:

```cpp
{code}
```
作为C++测试工程师，生成符合Google Test规范的测试套件：

代码分析要求：
1. 识别指针所有权边界
2. 标注模板特化需求
3. 分析异常安全保证级别
4. 识别移动语义使用点

测试生成规范：
[技术要求]
- 使用TEST_P实现参数化
- 对浮点比较使用EXPECT_NEAR
- 必须包含死亡测试（EXPECT_DEATH）
- 内存泄漏检测使用Valgrind指令
- 模板测试需要类型参数化
- 包含覆盖率生成指令：gcc --coverage

请生成完整的测试代码，包括必要的头文件和测试用例。
测试应该全面覆盖代码的功能，包括正常情况和边缘情况。
使用Google Test框架，并遵循以下指南:

1. 测试用例名应反映被测试的类或函数
2. 使用TEST或TEST_F宏定义测试
3. 使用描述性的测试名称
4. 为每个测试用例添加清晰的注释
5. 使用GMock进行必要的模拟
6. 使用EXPECT_*或ASSERT_*宏进行断言
7. 考虑边缘情况和异常处理

假设可以使用以下头文件:
#include <gtest/gtest.h>
#include <gmock/gmock.h>

请仅返回测试代码，不要包含任何解释或额外的文本。
""",

    "csharp": """
请为以下C# {code_type}生成单元测试代码:

```csharp
{code}
```

请生成完整的测试代码，包括必要的using语句和测试方法。
测试应该全面覆盖代码的功能，包括正常情况和边缘情况。
使用NUnit框架，并遵循以下指南:

1. 测试类名应为"{class_name}Tests"
2. 使用[Test]特性标记测试方法
3. 使用描述性的测试方法名称
4. 为每个测试用例添加清晰的注释
5. 使用Moq进行必要的模拟
6. 使用Assert类进行断言
7. 考虑边缘情况和异常处理

假设可以使用以下using语句:
using NUnit.Framework;
using Moq;
using System;
using System.Collections.Generic;

请仅返回测试代码，不要包含任何解释或额外的文本。
"""
}
