from typing import Dict, Any
from app.services.parsers.python_parser import PythonParser
from app.services.parsers.java_parser import JavaParser
from app.services.parsers.go_parser import GoParser
from app.services.parsers.cpp_parser import CppParser
from app.services.parsers.csharp_parser import CSharpParser

class ParserFactory:
    """代码解析器工厂"""
    
    _parsers = {
        "python": PythonParser(),
        "java": JavaParser(),
        "go": GoParser(),
        "cpp": CppParser(),
        "csharp": CSharpParser()
    }
    
    @classmethod
    def get_parser(cls, language: str):
        """
        获取指定语言的解析器
        
        Args:
            language: 编程语言
            
        Returns:
            对应的解析器实例
        
        Raises:
            ValueError: 如果不支持指定的语言
        """
        if language not in cls._parsers:
            raise ValueError(f"Unsupported language: {language}")
        
        return cls._parsers[language]
    
    @classmethod
    def get_supported_languages(cls) -> list:
        """
        获取支持的语言列表
        
        Returns:
            支持的语言列表
        """
        return list(cls._parsers.keys())
