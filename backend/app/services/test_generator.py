from typing import List
from app.models.schemas import CodeSnippet, TestResult
from app.services.parser_factory import ParserFactory
from app.services.runnable_test_generator import generate_runnable_test, generate_test_file_name
from app.utils.logger import logger

def parse_code(code: str, language: str, file_path: str = None) -> List[CodeSnippet]:
    """
    解析代码，提取函数和方法

    Args:
        code: 代码字符串
        language: 编程语言
        file_path: 代码文件路径，用于生成正确的导入语句

    Returns:
        代码片段列表

    Raises:
        ValueError: 如果不支持指定的语言
    """
    parser = ParserFactory.get_parser(language)
    return parser.parse_code(code, file_path)

def generate_tests(code: str, language: str, model: str, file_path: str = None) -> List[TestResult]:
    """
    生成测试代码

    Args:
        code: 代码字符串
        language: 编程语言
        model: AI模型名称
        file_path: 代码文件路径，用于生成正确的导入语句

    Returns:
        测试结果列表

    Raises:
        ValueError: 如果不支持指定的语言或模型
    """
    # 解析代码
    snippets = parse_code(code, language, file_path)

    # 生成测试
    results = []
    for snippet in snippets:
        try:
            # 使用可运行测试生成器
            logger.info(f"Generating runnable test for {snippet.name}")
            test_code = generate_runnable_test(snippet, model)

            # 生成测试文件名
            test_file_name = generate_test_file_name(snippet)
            logger.info(f"Generated test file name: {test_file_name}")

            # 添加测试结果
            results.append(TestResult(
                name=snippet.name,
                type=snippet.type,
                test_code=test_code,
                original_snippet=snippet,
                file_name=test_file_name
            ))
        except Exception as e:
            logger.error(f"Error generating test for {snippet.name}: {e}")
            print(f"Error generating test for {snippet.name}: {e}")
            # 出错时仍然添加一个结果，但使用错误消息
            test_code = f"# Error generating test: {str(e)}\n\n# 请手动编写测试"
            results.append(TestResult(
                name=snippet.name,
                type=snippet.type,
                test_code=test_code,
                original_snippet=snippet,
                file_name=None
            ))

    return results

async def generate_tests_stream(code: str, language: str, model: str, file_path: str = None):
    """
    流式生成测试代码

    Args:
        code: 代码字符串
        language: 编程语言
        model: AI模型名称
        file_path: 代码文件路径，用于生成正确的导入语句

    Yields:
        测试结果，一次生成一个

    Raises:
        ValueError: 如果不支持指定的语言或模型
    """
    # 解析代码
    snippets = parse_code(code, language, file_path)

    # 生成测试
    for snippet in snippets:
        try:
            # 使用可运行测试生成器
            logger.info(f"Generating runnable test for {snippet.name}")
            test_code = generate_runnable_test(snippet, model)

            # 生成测试文件名
            test_file_name = generate_test_file_name(snippet)
            logger.info(f"Generated test file name: {test_file_name}")

            # 添加测试结果
            yield TestResult(
                name=snippet.name,
                type=snippet.type,
                test_code=test_code,
                original_snippet=snippet,
                file_name=test_file_name
            )
        except Exception as e:
            logger.error(f"Error generating test for {snippet.name}: {e}")
            print(f"Error generating test for {snippet.name}: {e}")
            # 出错时仍然添加一个结果，但使用错误消息
            test_code = f"# Error generating test: {str(e)}\n\n# 请手动编写测试"
            yield TestResult(
                name=snippet.name,
                type=snippet.type,
                test_code=test_code,
                original_snippet=snippet,
                file_name=None
            )
