import javalang
from typing import List, Dict, Any, Optional
from app.models.schemas import CodeSnippet
from app.services.parsers.base_parser import BaseParser
from app.utils.logger import logger

class JavaParser(BaseParser):
    """Java代码解析器"""

    def parse_code(self, code: str) -> List[CodeSnippet]:
        """
        解析Java代码，提取方法和类

        Args:
            code: Java代码字符串

        Returns:
            代码片段列表
        """
        try:
            tree = javalang.parse.parse(code)
            snippets = []

            # 遍历所有类
            for path, class_node in tree.filter(javalang.tree.ClassDeclaration):
                class_name = class_node.name

                # 遍历类中的所有方法
                for method_node in class_node.methods:
                    method_code = self.extract_method_code(code, method_node)

                    snippets.append(CodeSnippet(
                        name=method_node.name,
                        type="method",
                        code=method_code,
                        language="java",
                        class_name=class_name
                    ))

            return snippets

        except Exception as e:
            logger.error(f"Error parsing Java code: {e}")
            return []

    def extract_method_code(self, code_str: str, method_node) -> str:
        """
        提取Java方法代码的简化实现

        Args:
            code_str: 完整的Java代码
            method_node: 方法节点

        Returns:
            方法源代码
        """
        if not hasattr(method_node, 'position') or method_node.position is None:
            return ""

        # 使用源代码位置信息
        start_line = method_node.position.line - 1

        # 使用基类的方法提取函数体
        return self.extract_function_body(code_str, start_line)
