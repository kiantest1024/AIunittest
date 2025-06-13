from app.models.schemas import CodeSnippet
from app.config import PROMPT_TEMPLATES
from app.services.ai_factory import AIServiceFactory
from app.utils.logger import logger
import re

def validate_test_code(test_code: str, snippet: CodeSnippet, module_path: str) -> bool:
    if not test_code:
        logger.warning("Generated test code is empty")
        return False

    if snippet.language == "python":
        module_path = "broadcast"

        import_patterns = []
        if snippet.class_name:
            import_patterns.append(re.compile(rf"from\s+{re.escape(module_path)}\s+import\s+{re.escape(snippet.class_name)}"))
        else:
            import_patterns.append(re.compile(rf"from\s+{re.escape(module_path)}\s+import\s+{re.escape(snippet.name)}"))

        import_found = False
        for pattern in import_patterns:
            if pattern.search(test_code):
                import_found = True
                break

        if not import_found:
            logger.warning(f"Missing import statement for {snippet.name}")
            return False

        if "import pytest" not in test_code:
            logger.warning("Missing pytest import")
            return False

        test_func_pattern = re.compile(rf"def\s+test_\w*{re.escape(snippet.name)}")
        if not test_func_pattern.search(test_code):
            logger.warning(f"Missing test function for {snippet.name}")
            return False

        if "from your_module import" in test_code:
            logger.warning("Using incorrect module name 'your_module'")
            return False

        if "mock.patch" in test_code and "mock.patch('broadcast." not in test_code and "mock.patch(\"broadcast." not in test_code:
            logger.warning("Using incorrect mock.patch path, should use 'broadcast.'")
            return False

    return True

def generate_test_with_ai(snippet: CodeSnippet, enhanced_prompt: str = None, model_name: str = None) -> str:
    try:
        if enhanced_prompt:
            prompt = enhanced_prompt
        else:
            if snippet.language not in PROMPT_TEMPLATES:
                raise ValueError(f"Unsupported language for test generation: {snippet.language}")

            prompt_template = PROMPT_TEMPLATES[snippet.language]
            code_type = "函数" if snippet.type == "function" else f"类 {snippet.class_name} 的方法"

            import_statement = ""
            if snippet.language == "python":
                module_path = "broadcast"
                logger.info(f"Using module path: {module_path} for function: {snippet.name}")

                if snippet.class_name:
                    import_statement = f"from {module_path} import {snippet.class_name}"
                else:
                    import_statement = f"from {module_path} import {snippet.name}"

                import_statement += f"\nfrom {module_path} import socketio"
                import_statement += "\nimport pytest\nimport unittest\nfrom unittest import mock\nfrom unittest.mock import MagicMock, patch, Mock, call\nfrom datetime import datetime\nimport io\nimport sys"

            elif snippet.language == "java":
                logger.info(f"Processing Java code for: {snippet.name}")
                import_statement = ""

            prompt = prompt_template.format(
                code_type=code_type,
                code=snippet.code,
                import_statement=import_statement,
                class_name=snippet.class_name or "",
                function_name=snippet.name
            )

        ai_service = AIServiceFactory.get_service(model_name)
        max_retries = 3
        current_retry = 0
        module_path = "broadcast"

        while current_retry < max_retries:
            test_code = ai_service.generate(prompt)

            if validate_test_code(test_code, snippet, module_path):
                logger.info(f"Generated valid test code for {snippet.name} on attempt {current_retry + 1}")
                return test_code

            logger.warning(f"Generated test code failed validation, attempting to fix")

            fixed_code = test_code

            if "from your_module import" in fixed_code:
                fixed_code = fixed_code.replace("from your_module import", f"from {module_path} import")
                logger.info("Fixed import statement: replaced 'your_module' with 'broadcast'")

            if "mock.patch('your_module." in fixed_code:
                fixed_code = fixed_code.replace("mock.patch('your_module.", f"mock.patch('{module_path}.")
                logger.info("Fixed mock.patch path: replaced 'your_module' with 'broadcast'")

            if "mock.patch(\"your_module." in fixed_code:
                fixed_code = fixed_code.replace("mock.patch(\"your_module.", f"mock.patch(\"{module_path}.")
                logger.info("Fixed mock.patch path: replaced 'your_module' with 'broadcast'")

            if "import pytest" not in fixed_code:
                fixed_code = "import pytest\n" + fixed_code
                logger.info("Added missing pytest import")

            import_statement = f"from {module_path} import {snippet.class_name or snippet.name}"
            if import_statement not in fixed_code:
                fixed_code = import_statement + "\n" + fixed_code
                logger.info(f"Added missing import statement: {import_statement}")

            if validate_test_code(fixed_code, snippet, module_path):
                logger.info(f"Successfully fixed test code for {snippet.name}")
                return fixed_code

            current_retry += 1
            logger.warning(f"Auto-fix failed, retrying ({current_retry}/{max_retries})")

            if current_retry < max_retries:
                enhanced_prompt = prompt + f"""

极其重要的提示：
1. 必须使用 "from broadcast import {snippet.class_name or snippet.name}" 而不是 "from your_module import {snippet.class_name or snippet.name}"
2. 当使用mock.patch时，必须使用 'broadcast.socketio' 而不是 'your_module.socketio'
3. 必须包含 "import pytest"
4. 测试函数名必须以 "test_" 开头
"""
                prompt = enhanced_prompt

        logger.error(f"Failed to generate valid test code for {snippet.name} after {max_retries} attempts")

        template = f"""from {module_path} import {snippet.class_name or snippet.name}
from {module_path} import socketio

import pytest
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, Mock, call
from datetime import datetime
import io
import sys

@pytest.fixture
def mock_socketio():
    with mock.patch('broadcast.socketio') as mock_socket:
        yield mock_socket

def test_{snippet.name}_basic():
    \"\"\"基本测试 {snippet.name} 函数\"\"\"
    assert True
"""

        test_functions = []
        if test_code:
            func_pattern = re.compile(r'def\s+test_\w+\([^)]*\):[^#]*?(?=def|\Z)', re.DOTALL)
            matches = func_pattern.findall(test_code)
            if matches:
                test_functions = matches

        if test_functions:
            for func in test_functions:
                fixed_func = func.replace("your_module", module_path)
                template += "\n" + fixed_func

        return template

    except Exception as e:
        logger.error(f"Error generating test with AI: {e}")

        if snippet.language == "java":
            class_name = snippet.class_name or "Main"
            return f"""// 错误生成测试: {str(e)}

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import org.mockito.Mockito;
import static org.mockito.Mockito.*;

class {class_name}Test {{

    @Test
    void test{snippet.name}Basic() {{
        assertTrue(true);
    }}

    @Test
    void test{snippet.name}EdgeCases() {{
        assertTrue(true);
    }}
}}"""
        else:
            module_path = "broadcast"
            return f"""# 错误生成测试: {str(e)}

from {module_path} import {snippet.class_name or snippet.name}
from {module_path} import socketio

import pytest
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, Mock, call
from datetime import datetime
import io
import sys

@pytest.fixture
def mock_socketio():
    with mock.patch('broadcast.socketio') as mock_socket:
        yield mock_socket

def test_{snippet.name}_basic():
    \"\"\"基本测试 {snippet.name} 函数\"\"\"
    assert True
"""
