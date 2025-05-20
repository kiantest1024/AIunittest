import re
from typing import List, Dict, Any, Optional
from app.models.schemas import CodeSnippet
from app.services.parsers.base_parser import BaseParser
from app.utils.logger import logger

class CSharpParser(BaseParser):
    """C#代码解析器"""

    def parse_code(self, code: str) -> List[CodeSnippet]:
        """
        解析C#代码，提取方法和类

        Args:
            code: C#代码字符串

        Returns:
            代码片段列表
        """
        try:
            snippets = []

            # 查找类定义
            class_pattern = r'(?:public|private|protected|internal|static)?\s+(?:abstract|sealed)?\s+class\s+([A-Za-z0-9_]+)(?:\s*:\s*[A-Za-z0-9_,\s<>]+)?\s*\{'
            class_matches = list(re.finditer(class_pattern, code))

            # 查找类方法
            for class_match in class_matches:
                class_name = class_match.group(1)
                class_start = class_match.start()

                # 确定类结束位置
                brace_count = 0
                class_end = class_start

                for j in range(class_start, len(code)):
                    if code[j] == '{':
                        brace_count += 1
                    elif code[j] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            class_end = j + 1
                            break

                class_code = code[class_start:class_end]

                # 在类内查找方法
                method_pattern = r'(?:public|private|protected|internal|static|virtual|override|abstract|sealed|async)(?:\s+(?:public|private|protected|internal|static|virtual|override|abstract|sealed|async))*\s+(?:[A-Za-z0-9_<>[\],\s]+)\s+([A-Za-z0-9_]+)\s*\([^)]*\)(?:\s*where\s+[^{]+)?\s*\{'
                method_matches = re.finditer(method_pattern, class_code)

                for method_match in method_matches:
                    method_name = method_match.group(1)
                    if method_name == class_name:  # 构造函数
                        continue

                    method_start = method_match.start()

                    # 查找方法体结束位置
                    brace_count = 0
                    method_end = method_start

                    for j in range(method_start, len(class_code)):
                        if class_code[j] == '{':
                            brace_count += 1
                        elif class_code[j] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                method_end = j + 1
                                break

                    method_code = class_code[method_start:method_end]

                    snippets.append(CodeSnippet(
                        name=method_name,
                        type="method",
                        code=method_code,
                        language="csharp",
                        class_name=class_name
                    ))

            # 查找全局函数（在C#中不常见，但可能存在于静态类中）
            # 排除类定义内的代码
            class_ranges = [(m.start(), m.end()) for m in class_matches]

            func_pattern = r'(?:public|private|protected|internal|static|async)(?:\s+(?:public|private|protected|internal|static|async))*\s+(?:[A-Za-z0-9_<>[\],\s]+)\s+([A-Za-z0-9_]+)\s*\([^)]*\)(?:\s*where\s+[^{]+)?\s*\{'
            func_matches = re.finditer(func_pattern, code)

            for func_match in func_matches:
                func_start = func_match.start()

                # 检查是否在类内
                in_class = False
                for start, end in class_ranges:
                    if start <= func_start <= end:
                        in_class = True
                        break

                if not in_class:
                    func_name = func_match.group(1)

                    # 查找函数体结束位置
                    brace_count = 0
                    func_end = func_start

                    for j in range(func_start, len(code)):
                        if code[j] == '{':
                            brace_count += 1
                        elif code[j] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                func_end = j + 1
                                break

                    func_code = code[func_start:func_end]

                    snippets.append(CodeSnippet(
                        name=func_name,
                        type="function",
                        code=func_code,
                        language="csharp",
                        class_name=None
                    ))

            return snippets

        except Exception as e:
            logger.error(f"Error parsing C# code: {e}")
            return []
