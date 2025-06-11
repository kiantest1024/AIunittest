from typing import List, Optional

# 根据运行位置动态调整导入路径
try:
    from app.models.schemas import CodeSnippet
except ModuleNotFoundError:
    from models.schemas import CodeSnippet

class BaseParser:
    """代码解析器基类"""
    
    def parse_code(self, code: str) -> List[CodeSnippet]:
        """
        解析代码，提取函数和方法
        
        Args:
            code: 代码字符串
            
        Returns:
            代码片段列表
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def find_closing_brace(self, code: str, start_pos: int) -> int:
        """
        查找匹配的右大括号位置
        
        Args:
            code: 代码字符串
            start_pos: 起始位置
            
        Returns:
            右大括号位置
        """
        brace_count = 0
        found_opening_brace = False
        
        for i in range(start_pos, len(code)):
            if code[i] == '{':
                found_opening_brace = True
                brace_count += 1
            elif code[i] == '}':
                brace_count -= 1
            
            if found_opening_brace and brace_count == 0:
                return i + 1
        
        return len(code)
    
    def extract_function_body(self, code: str, start_line: int, end_line: Optional[int] = None) -> str:
        """
        提取函数体
        
        Args:
            code: 代码字符串
            start_line: 起始行号（0-indexed）
            end_line: 结束行号（0-indexed），如果为None则自动查找
            
        Returns:
            函数体代码
        """
        lines = code.splitlines()
        
        if end_line is None:
            # 查找函数体结束位置
            brace_count = 0
            found_opening_brace = False
            end_line = start_line
            
            for i in range(start_line, len(lines)):
                line = lines[i]
                for char in line:
                    if char == '{':
                        found_opening_brace = True
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                if found_opening_brace and brace_count == 0:
                    end_line = i
                    break
                
                end_line = i
        
        return "\n".join(lines[start_line:end_line+1])
