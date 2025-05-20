import os
from typing import Dict, Any, List

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

    class Config:
        env_file = ".env"

settings = Settings()

# AI模型配置
AI_MODELS = {
    "openai_gpt35": {
        "provider": "openai",
        "api_key": settings.OPENAI_API_KEY,
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 30,
    },
    "openai_gpt4": {
        "provider": "openai",
        "api_key": settings.OPENAI_API_KEY,
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 4000,
        "timeout": 60,
    },
    "google_gemini": {
        "provider": "google",
        "api_key": settings.GOOGLE_API_KEY,
        "api_base": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-pro",
        "temperature": 0.7,
        "max_tokens": 2048,
        "timeout": 30,
    },
    "anthropic_claude": {
        "provider": "anthropic",
        "api_key": settings.ANTHROPIC_API_KEY,
        "api_base": "https://api.anthropic.com/v1",
        "model": "claude-3-opus-20240229",
        "temperature": 0.7,
        "max_tokens": 4000,
        "timeout": 60,
    },
    "xai_grok": {
        "provider": "grok",
        "api_key": settings.GROK_API_KEY,
        "api_base": "https://api.grok.ai/v1",
        "model": "grok-1",
        "temperature": 0.7,
        "max_tokens": 4000,
        "timeout": 60,
    },
    "deepseek-V3": {
        "provider": "deepseek",
        "api_key": "sk-ace4ddbf5f454abda682b0c57df0d313",  # 您确认的有效 API 密钥
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",  # 使用 deepseek-chat 模型
        "temperature": 0.7,
        "max_tokens": 4000,
        "timeout": 300,
    },
    "deepseek-R1": {
        "provider": "deepseek",
        "api_key": "sk-ace4ddbf5f454abda682b0c57df0d313",  # 您确认的有效 API 密钥
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-reasoner",  # 使用 deepseek-reasoner 模型
        "temperature": 0.7,
        "max_tokens": 8000,  # 增加最大token数
        "timeout": 600,  # 增加超时时间到10分钟
    }
}

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
""",

    "java": """
请为以下Java {code_type}生成单元测试代码:

```java
{code}
```

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
