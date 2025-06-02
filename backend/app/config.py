import os
from typing import List

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
    "chatgpt4nano": {
        "provider": "openai",
        "api_key": settings.OPENAI_API_KEY,
        "api_base": "https://api.openai.com/v1",
        "model": "GPT-4.1 nano",
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 30,
    },
    "chatgpt4.1mini": {
        "provider": "openai",
        "api_key": settings.OPENAI_API_KEY,
        "api_base": "https://api.openai.com/v1",
        "model": "GPT-4.1 mini",
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
        "timeout": 1200,  # 增加超时时间到20分钟
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
