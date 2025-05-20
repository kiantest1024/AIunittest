from typing import List, Dict, Any, Optional
from app.models.schemas import CodeSnippet, TestResult
from app.services.parser_factory import ParserFactory
from app.services.ai_service import generate_test_with_ai

def parse_code(code: str, language: str) -> List[CodeSnippet]:
    """
    解析代码，提取函数和方法

    Args:
        code: 代码字符串
        language: 编程语言

    Returns:
        代码片段列表

    Raises:
        ValueError: 如果不支持指定的语言
    """
    parser = ParserFactory.get_parser(language)
    return parser.parse_code(code)

def generate_tests(code: str, language: str, model: str) -> List[TestResult]:
    """
    生成测试代码

    Args:
        code: 代码字符串
        language: 编程语言
        model: AI模型名称

    Returns:
        测试结果列表

    Raises:
        ValueError: 如果不支持指定的语言或模型
    """
    # 解析代码
    snippets = parse_code(code, language)

    # 生成测试
    results = []
    for snippet in snippets:
        test_code = generate_test_with_ai(snippet, model)

        results.append(TestResult(
            name=snippet.name,
            type=snippet.type,
            test_code=test_code,
            original_snippet=snippet
        ))

    return results

async def generate_tests_stream(code: str, language: str, model: str):
    """
    流式生成测试代码

    Args:
        code: 代码字符串
        language: 编程语言
        model: AI模型名称

    Yields:
        测试结果，一次生成一个

    Raises:
        ValueError: 如果不支持指定的语言或模型
    """
    # 解析代码
    snippets = parse_code(code, language)

    # 生成测试
    for snippet in snippets:
        test_code = generate_test_with_ai(snippet, model)

        yield TestResult(
            name=snippet.name,
            type=snippet.type,
            test_code=test_code,
            original_snippet=snippet
        )
