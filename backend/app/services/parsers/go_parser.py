import re
from typing import List, Dict, Any, Optional
from app.models.schemas import CodeSnippet
from app.services.parsers.base_parser import BaseParser
from app.utils.logger import logger

class GoParser(BaseParser):
    """Go代码解析器"""

    def parse_code(self, code: str) -> List[CodeSnippet]:
        """
        解析Go代码，提取函数和方法

        Args:
            code: Go代码字符串

        Returns:
            代码片段列表
        """
        try:
            snippets = []
            lines = code.splitlines()
            i = 0

            while i < len(lines):
                line = lines[i]
                # 查找函数定义
                if re.match(r'\s*func\s+', line):
                    func_start = i
                    func_name = ""
                    class_name = None

                    # 提取函数名和接收器（如果有）
                    match = re.search(r'func\s+(?:\(([^)]+)\)\s+)?([A-Za-z0-9_]+)', line)
                    if match:
                        receiver, func_name = match.groups()
                        if receiver:
                            # 提取接收器类型
                            receiver_match = re.search(r'\s*\w+\s+\*?([A-Za-z0-9_]+)', receiver)
                            if receiver_match:
                                class_name = receiver_match.group(1)

                    # 查找函数体结束
                    brace_count = 0
                    func_end = func_start

                    for j in range(i, len(lines)):
                        line_j = lines[j]
                        for char in line_j:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1

                        if brace_count > 0:
                            func_end = j

                        if brace_count == 0 and '{' in line_j:
                            func_end = j
                            break

                    func_code = "\n".join(lines[func_start:func_end+1])

                    snippets.append(CodeSnippet(
                        name=func_name,
                        type="method" if class_name else "function",
                        code=func_code,
                        language="go",
                        class_name=class_name
                    ))

                    i = func_end
                i += 1

            return snippets

        except Exception as e:
            logger.error(f"Error parsing Go code: {e}")
            return []
