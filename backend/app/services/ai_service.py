from app.models.schemas import CodeSnippet
from app.config import PROMPT_TEMPLATES
from app.services.ai_factory import AIServiceFactory
from app.utils.logger import logger
import re

def validate_test_code(test_code: str, snippet: CodeSnippet, module_path: str) -> bool:
    """
    验证生成的测试代码是否包含必要的导入语句和正确的模块名

    Args:
        test_code: 生成的测试代码
        snippet: 代码片段
        module_path: 模块路径

    Returns:
        验证结果，True表示通过验证，False表示未通过
    """
    if not test_code:
        logger.warning("Generated test code is empty")
        return False

    # 检查是否包含导入语句
    if snippet.language == "python":
        # 强制使用 broadcast 模块名
        module_path = "broadcast"

        # 构建预期的导入语句模式
        import_patterns = []
        if snippet.class_name:
            # 类导入模式
            import_patterns.append(re.compile(rf"from\s+{re.escape(module_path)}\s+import\s+{re.escape(snippet.class_name)}"))
        else:
            # 函数导入模式
            import_patterns.append(re.compile(rf"from\s+{re.escape(module_path)}\s+import\s+{re.escape(snippet.name)}"))

        # 检查是否包含预期的导入语句
        import_found = False
        for pattern in import_patterns:
            if pattern.search(test_code):
                import_found = True
                break

        if not import_found:
            logger.warning(f"Missing import statement for {snippet.name}")
            return False

        # 检查是否包含pytest导入
        if "import pytest" not in test_code:
            logger.warning("Missing pytest import")
            return False

        # 检查是否包含测试函数
        test_func_pattern = re.compile(rf"def\s+test_\w*{re.escape(snippet.name)}")
        if not test_func_pattern.search(test_code):
            logger.warning(f"Missing test function for {snippet.name}")
            return False

        # 检查是否使用了错误的模块名
        if "from your_module import" in test_code:
            logger.warning("Using incorrect module name 'your_module'")
            return False

        # 检查mock.patch路径是否正确
        if "mock.patch" in test_code and "mock.patch('broadcast." not in test_code and "mock.patch(\"broadcast." not in test_code:
            logger.warning("Using incorrect mock.patch path, should use 'broadcast.'")
            return False

    return True

def generate_test_with_ai(snippet: CodeSnippet, enhanced_prompt: str = None, model_name: str = None) -> str:
    """
    使用AI生成测试代码

    Args:
        snippet: 代码片段
        enhanced_prompt: 增强的提示（可选，用于Java等特殊语言）
        model_name: AI模型名称

    Returns:
        生成的测试代码

    Raises:
        ValueError: 如果模型不存在或语言不支持
    """
    try:
        # 如果提供了增强的提示，直接使用
        if enhanced_prompt:
            prompt = enhanced_prompt
        else:
            # 获取提示模板
            if snippet.language not in PROMPT_TEMPLATES:
                raise ValueError(f"Unsupported language for test generation: {snippet.language}")

            prompt_template = PROMPT_TEMPLATES[snippet.language]

            # 构建提示
            code_type = "函数" if snippet.type == "function" else f"类 {snippet.class_name} 的方法"

            # 构建导入语句（根据语言不同而不同）
            import_statement = ""
            if snippet.language == "python":
                # 强制使用 broadcast 模块名
                module_path = "broadcast"

                # 记录模块路径
                logger.info(f"Using module path: {module_path} for function: {snippet.name}")

                # 构建导入语句 - 简化并强调 broadcast 模块
                if snippet.class_name:
                    # 如果是类方法，导入类
                    import_statement = f"# 被测代码的导入语句 - 这是必须的，不要修改这一行\nfrom {module_path} import {snippet.class_name}  # 必须使用broadcast模块名"
                else:
                    # 如果是函数，直接导入函数
                    import_statement = f"# 被测代码的导入语句 - 这是必须的，不要修改这一行\nfrom {module_path} import {snippet.name}  # 必须使用broadcast模块名"

                # 添加全局变量导入
                import_statement += f"\n\n# 如果需要访问其他函数或全局变量，也从broadcast导入\nfrom {module_path} import socketio  # 全局变量"

                # 添加常用的测试库导入
                import_statement += "\n\n# 测试所需的库\nimport pytest\nimport unittest\nfrom unittest import mock\nfrom unittest.mock import MagicMock, patch, Mock, call\nfrom datetime import datetime\nimport io\nimport sys"

                # 添加mock示例
                import_statement += f"\n\n# 当使用mock.patch时，必须使用'broadcast.socketio'作为路径，例如:\n# @pytest.fixture\n# def mock_socketio():\n#     with mock.patch('broadcast.socketio') as mock_socket:  # 注意这里是broadcast而不是your_module\n#         yield mock_socket"

            elif snippet.language == "java":
                # Java语言的导入语句处理
                logger.info(f"Processing Java code for: {snippet.name}")

                # Java不需要特殊的导入语句，模板中已经包含了标准的JUnit导入
                import_statement = ""

            prompt = prompt_template.format(
                code_type=code_type,
                code=snippet.code,
                import_statement=import_statement,
                class_name=snippet.class_name or "",
                function_name=snippet.name
            )

        # 使用AI服务工厂获取服务并生成测试
        ai_service = AIServiceFactory.get_service(model_name)

        # 最大重试次数
        max_retries = 3
        current_retry = 0

        # 强制使用 broadcast 模块名
        module_path = "broadcast"

        while current_retry < max_retries:
            # 生成测试代码
            test_code = ai_service.generate(prompt)

            # 验证测试代码
            if validate_test_code(test_code, snippet, module_path):
                logger.info(f"Generated valid test code for {snippet.name} on attempt {current_retry + 1}")
                return test_code

            # 如果验证失败，尝试自动修复
            logger.warning(f"Generated test code failed validation, attempting to fix")

            # 自动修复常见问题
            fixed_code = test_code

            # 修复导入语句
            if "from your_module import" in fixed_code:
                fixed_code = fixed_code.replace("from your_module import", f"from {module_path} import")
                logger.info("Fixed import statement: replaced 'your_module' with 'broadcast'")

            # 修复mock.patch路径
            if "mock.patch('your_module." in fixed_code:
                fixed_code = fixed_code.replace("mock.patch('your_module.", f"mock.patch('{module_path}.")
                logger.info("Fixed mock.patch path: replaced 'your_module' with 'broadcast'")

            if "mock.patch(\"your_module." in fixed_code:
                fixed_code = fixed_code.replace("mock.patch(\"your_module.", f"mock.patch(\"{module_path}.")
                logger.info("Fixed mock.patch path: replaced 'your_module' with 'broadcast'")

            # 添加缺失的导入语句
            if "import pytest" not in fixed_code:
                fixed_code = "import pytest\n" + fixed_code
                logger.info("Added missing pytest import")

            # 添加缺失的函数导入
            import_statement = f"from {module_path} import {snippet.class_name or snippet.name}"
            if import_statement not in fixed_code:
                fixed_code = import_statement + "\n" + fixed_code
                logger.info(f"Added missing import statement: {import_statement}")

            # 验证修复后的代码
            if validate_test_code(fixed_code, snippet, module_path):
                logger.info(f"Successfully fixed test code for {snippet.name}")
                return fixed_code

            # 如果自动修复失败，重试
            current_retry += 1
            logger.warning(f"Auto-fix failed, retrying ({current_retry}/{max_retries})")

            # 增强提示，强调导入语句的重要性
            if current_retry < max_retries:
                # 添加更强调导入语句的提示
                enhanced_prompt = prompt + f"""

极其重要的提示：
1. 必须使用 "from broadcast import {snippet.class_name or snippet.name}" 而不是 "from your_module import {snippet.class_name or snippet.name}"
2. 当使用mock.patch时，必须使用 'broadcast.socketio' 而不是 'your_module.socketio'
3. 必须包含 "import pytest"
4. 测试函数名必须以 "test_" 开头
"""
                prompt = enhanced_prompt

        # 如果所有重试都失败，创建一个基本的测试模板
        logger.error(f"Failed to generate valid test code for {snippet.name} after {max_retries} attempts")

        # 创建基本的测试模板
        template = f"""# 被测代码的导入语句
from {module_path} import {snippet.class_name or snippet.name}
from {module_path} import socketio  # 全局变量

# 测试所需的库
import pytest
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, Mock, call
from datetime import datetime
import io
import sys

@pytest.fixture
def mock_socketio():
    with mock.patch('broadcast.socketio') as mock_socket:  # 注意这里是broadcast而不是your_module
        yield mock_socket

def test_{snippet.name}_basic():
    \"\"\"基本测试 {snippet.name} 函数\"\"\"
    # 准备测试数据

    # 执行被测函数

    # 验证结果
    assert True  # 替换为实际的断言

# 以下是生成的测试代码，可能需要修复
"""

        # 尝试提取生成的测试函数
        test_functions = []
        if test_code:
            # 使用正则表达式提取测试函数
            func_pattern = re.compile(r'def\s+test_\w+\([^)]*\):[^#]*?(?=def|\Z)', re.DOTALL)
            matches = func_pattern.findall(test_code)
            if matches:
                test_functions = matches

        # 如果提取到了测试函数，添加到模板中
        if test_functions:
            for func in test_functions:
                # 修复函数中的模块名
                fixed_func = func.replace("your_module", module_path)
                template += "\n" + fixed_func

        return template

    except Exception as e:
        logger.error(f"Error generating test with AI: {e}")

        # 根据语言返回不同的错误模板
        if snippet.language == "java":
            # Java错误模板
            class_name = snippet.class_name or "Main"
            return f"""// 错误生成测试: {str(e)}
// 以下是基本的Java测试模板，请根据需要修改

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import org.mockito.Mockito;
import static org.mockito.Mockito.*;

class {class_name}Test {{

    @Test
    void test{snippet.name}Basic() {{
        // 准备测试数据

        // 执行被测方法

        // 验证结果
        assertTrue(true); // 替换为实际的断言
    }}

    @Test
    void test{snippet.name}EdgeCases() {{
        // 测试边缘情况
        assertTrue(true); // 替换为实际的断言
    }}
}}"""
        else:
            # Python错误模板（保持原有逻辑）
            module_path = "broadcast"
            return f"""# 错误生成测试: {str(e)}
# 以下是基本的测试模板，请根据需要修改

# 被测代码的导入语句
from {module_path} import {snippet.class_name or snippet.name}
from {module_path} import socketio  # 全局变量

# 测试所需的库
import pytest
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, Mock, call
from datetime import datetime
import io
import sys

@pytest.fixture
def mock_socketio():
    with mock.patch('broadcast.socketio') as mock_socket:  # 注意这里是broadcast而不是your_module
        yield mock_socket

def test_{snippet.name}_basic():
    \"\"\"基本测试 {snippet.name} 函数\"\"\"
    # 准备测试数据

    # 执行被测函数

    # 验证结果
    assert True  # 替换为实际的断言
"""

# 这些函数已移至ai_factory.py，不再需要
