import re
from typing import List, Dict, Any, Optional, Tuple
from app.models.schemas import CodeSnippet
from app.services.parsers.base_parser import BaseParser
from app.utils.logger import logger

class CppParser(BaseParser):
    """C++代码解析器"""

    def parse_code(self, code: str) -> List[CodeSnippet]:
        """
        解析C++代码，提取函数和方法

        Args:
            code: C++代码字符串

        Returns:
            代码片段列表
        """
        try:
            snippets = []

            # 查找类定义
            class_matches = list(re.finditer(r'class\s+([A-Za-z0-9_]+)(?:\s*:\s*(?:public|protected|private)\s+[A-Za-z0-9_]+)?\s*\{', code))
            class_ranges = []

            for class_match in class_matches:
                class_name = class_match.group(1)
                class_start = class_match.start()

                # 查找类结束位置
                class_end = self._find_closing_brace(code, class_start)
                class_ranges.append((class_start, class_end, class_name))

            # 查找类方法
            for start, end, class_name in class_ranges:
                class_code = code[start:end]

                # 查找方法定义
                method_pattern = r'(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:explicit\s+)?(?:const\s+)?(?:[A-Za-z0-9_:]+(?:<[^>]*>)?(?:\s*\*|\s*&)?\s+)?([A-Za-z0-9_]+)\s*\([^)]*\)(?:\s*const)?\s*(?:noexcept)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*0)?\s*\{'
                method_matches = re.finditer(method_pattern, class_code)

                for method_match in method_matches:
                    method_name = method_match.group(1)
                    if method_name == class_name:  # 构造函数
                        continue

                    method_start = method_match.start()
                    method_end = self._find_closing_brace(class_code, method_start)

                    method_code = class_code[method_start:method_end]

                    snippets.append(CodeSnippet(
                        name=method_name,
                        type="method",
                        code=method_code,
                        language="cpp",
                        class_name=class_name
                    ))

            # 查找全局函数
            func_pattern = r'(?:static\s+)?(?:inline\s+)?(?:[A-Za-z0-9_:]+(?:<[^>]*>)?(?:\s*\*|\s*&)?\s+)?([A-Za-z0-9_]+)\s*\([^)]*\)(?:\s*const)?\s*(?:noexcept)?\s*\{'
            func_matches = re.finditer(func_pattern, code)

            for func_match in func_matches:
                func_start = func_match.start()

                # 检查是否在类内
                in_class = False
                for start, end, _ in class_ranges:
                    if start <= func_start <= end:
                        in_class = True
                        break

                if not in_class:
                    func_name = func_match.group(1)
                    func_end = self._find_closing_brace(code, func_start)

                    func_code = code[func_start:func_end]

                    snippets.append(CodeSnippet(
                        name=func_name,
                        type="function",
                        code=func_code,
                        language="cpp",
                        class_name=None
                    ))

            return snippets

        except Exception as e:
            logger.error(f"Error parsing C++ code: {e}")
            return []

    # 使用基类的find_closing_brace方法
