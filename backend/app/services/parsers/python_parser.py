import ast
import inspect
from typing import List, Dict, Any, Optional
from app.models.schemas import CodeSnippet
from app.services.parsers.base_parser import BaseParser
from app.utils.logger import logger

class PythonParser(BaseParser):
    """Python代码解析器"""

    def parse_code(self, code: str, file_path: str = None) -> List[CodeSnippet]:
        """
        解析Python代码，提取函数和方法

        Args:
            code: Python代码字符串
            file_path: 代码文件路径，用于生成正确的导入语句

        Returns:
            代码片段列表
        """
        try:
            logger.info(f"开始解析Python代码，长度: {len(code)} 字符")

            # 检查代码是否为空
            if not code or not code.strip():
                logger.warning("代码为空，无法解析")
                return []

            # 尝试解析代码
            try:
                tree = ast.parse(code)
                logger.info("代码解析成功，开始提取函数和方法")
            except SyntaxError as se:
                logger.error(f"Python代码语法错误: {se}")
                # 尝试修复常见的语法问题
                fixed_code = self._try_fix_syntax(code)
                if fixed_code != code:
                    logger.info("尝试修复语法后重新解析")
                    tree = ast.parse(fixed_code)
                    code = fixed_code
                else:
                    raise

            snippets = []
            function_count = 0

            # 首先，直接查找顶级函数定义
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    function_count += 1
                    logger.info(f"找到顶级函数: {node.name}, 行号: {node.lineno}")

                    # 提取函数源代码
                    func_lines = code.splitlines()[node.lineno-1:node.end_lineno]
                    func_code = "\n".join(func_lines)

                    # 创建代码片段
                    snippet = CodeSnippet(
                        name=node.name,
                        type="function",
                        code=func_code,
                        language="python",
                        class_name=None,
                        file_path=file_path
                    )

                    snippets.append(snippet)

            # 然后，查找类和类方法
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    logger.info(f"找到类: {node.name}, 行号: {node.lineno}")

                    for class_node in ast.iter_child_nodes(node):
                        if isinstance(class_node, ast.FunctionDef):
                            function_count += 1
                            logger.info(f"找到类方法: {class_node.name}, 类: {node.name}, 行号: {class_node.lineno}")

                            # 提取方法源代码
                            method_lines = code.splitlines()[class_node.lineno-1:class_node.end_lineno]
                            method_code = "\n".join(method_lines)

                            # 创建代码片段
                            snippet = CodeSnippet(
                                name=class_node.name,
                                type="method",
                                code=method_code,
                                language="python",
                                class_name=node.name,
                                file_path=file_path
                            )

                            snippets.append(snippet)

            logger.info(f"解析完成，找到 {function_count} 个函数/方法，提取了 {len(snippets)} 个代码片段")

            # 如果没有找到任何函数，尝试使用正则表达式
            if not snippets:
                logger.warning("AST解析未找到函数，尝试使用正则表达式")
                regex_snippets = self._parse_with_regex(code, file_path)
                if regex_snippets:
                    logger.info(f"使用正则表达式找到 {len(regex_snippets)} 个函数")
                    snippets.extend(regex_snippets)

            return snippets

        except Exception as e:
            logger.error(f"解析Python代码时出错: {str(e)}", exc_info=True)
            # 尝试使用正则表达式作为备选方案
            try:
                logger.info("尝试使用正则表达式作为备选解析方法")
                return self._parse_with_regex(code, file_path)
            except Exception as regex_error:
                logger.error(f"正则表达式解析也失败: {str(regex_error)}")
                return []

    def _try_fix_syntax(self, code: str) -> str:
        """尝试修复常见的语法问题"""
        # 这里可以添加一些常见语法问题的修复逻辑
        return code

    def _parse_with_regex(self, code: str, file_path: str = None) -> List[CodeSnippet]:
        """使用正则表达式解析Python代码"""
        import re
        snippets = []

        # 匹配函数定义
        func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)(?:\s*->.*?)?:'
        matches = re.finditer(func_pattern, code)

        for match in matches:
            func_name = match.group(1)
            func_start = match.start()

            # 查找函数体结束位置
            lines = code.splitlines()
            line_no = code[:func_start].count('\n')
            indent = None
            func_end_line = line_no

            # 跳过函数定义行
            line_no += 1
            if line_no < len(lines):
                # 获取函数体的缩进级别
                first_line = lines[line_no]
                indent_match = re.match(r'^(\s+)', first_line)
                if indent_match:
                    indent = len(indent_match.group(1))

                # 查找函数体结束位置
                while line_no < len(lines):
                    if lines[line_no].strip() == '' or lines[line_no].strip().startswith('#'):
                        # 空行或注释行，继续
                        line_no += 1
                        func_end_line = line_no
                        continue

                    # 检查缩进级别
                    current_indent_match = re.match(r'^(\s+)', lines[line_no])
                    current_indent = len(current_indent_match.group(1)) if current_indent_match else 0

                    if indent is None or current_indent > indent:
                        # 仍在函数体内
                        line_no += 1
                        func_end_line = line_no
                    else:
                        # 函数体结束
                        break

            # 提取函数代码
            func_lines = lines[code[:func_start].count('\n'):func_end_line]
            func_code = '\n'.join(func_lines)

            # 创建代码片段
            snippet = CodeSnippet(
                name=func_name,
                type="function",
                code=func_code,
                language="python",
                class_name=None,
                file_path=file_path
            )

            snippets.append(snippet)
            logger.info(f"使用正则表达式找到函数: {func_name}")

        return snippets

    def extract_function_code(self, code: str, func_name: str) -> Optional[str]:
        """
        从代码中提取指定函数的源代码

        Args:
            code: 完整的Python代码
            func_name: 要提取的函数名

        Returns:
            函数源代码，如果未找到则返回None
        """
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    func_lines = code.splitlines()[node.lineno-1:node.end_lineno]
                    return "\n".join(func_lines)

            return None

        except Exception as e:
            logger.error(f"Error extracting function code: {e}")
            return None
