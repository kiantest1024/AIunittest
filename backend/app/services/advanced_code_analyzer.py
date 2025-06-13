"""
高级代码分析器 - 实现混合方法（文件级+项目上下文）的测试生成
"""

import re
import ast
import javalang
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

from app.models.schemas import CodeSnippet
from app.utils.logger import logger

@dataclass
class MethodInfo:
    """方法信息"""
    name: str
    parameters: List[Dict[str, str]]
    return_type: str
    exceptions: List[str]
    visibility: str
    is_static: bool
    complexity: int
    annotations: List[str]
    javadoc: Optional[str] = None

@dataclass
class ClassInfo:
    """类信息"""
    name: str
    package: str
    imports: List[str]
    extends: Optional[str]
    implements: List[str]
    annotations: List[str]
    methods: List[MethodInfo]
    fields: List[Dict[str, Any]]
    is_interface: bool = False
    is_abstract: bool = False

@dataclass
class ProjectContext:
    """项目上下文信息"""
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    spring_configs: List[str] = field(default_factory=list)
    custom_exceptions: List[str] = field(default_factory=list)
    dto_entities: List[str] = field(default_factory=list)
    test_frameworks: List[str] = field(default_factory=list)
    project_patterns: Dict[str, Any] = field(default_factory=dict)

class AdvancedCodeAnalyzer:
    """高级代码分析器"""
    
    def __init__(self):
        self.project_context = ProjectContext()
        
    def analyze_java_file(self, code: str, file_path: Optional[str] = None) -> Tuple[ClassInfo, ProjectContext]:
        """
        分析Java文件，提取详细的类信息和项目上下文
        
        Args:
            code: Java源代码
            file_path: 文件路径（可选）
            
        Returns:
            (类信息, 项目上下文)
        """
        try:
            tree = javalang.parse.parse(code)
            
            # 提取包名
            package_name = tree.package.name if tree.package else ""
            
            # 提取导入
            imports = []
            if tree.imports:
                imports = [imp.path for imp in tree.imports]
            
            # 分析类声明
            class_declarations = list(tree.filter(javalang.tree.ClassDeclaration))
            if not class_declarations:
                raise ValueError("No class declaration found")
                
            _, class_node = class_declarations[0]
            
            # 构建类信息
            class_info = ClassInfo(
                name=class_node.name,
                package=package_name,
                imports=imports,
                extends=class_node.extends.name if class_node.extends else None,
                implements=[impl.name for impl in (class_node.implements or [])],
                annotations=self._extract_annotations(class_node),
                methods=[],
                fields=self._extract_fields(class_node),
                is_interface=isinstance(class_node, javalang.tree.InterfaceDeclaration),
                is_abstract=self._is_abstract(class_node)
            )
            
            # 分析方法
            for method_node in class_node.methods or []:
                method_info = self._analyze_method(method_node, code)
                class_info.methods.append(method_info)
            
            # 收集项目上下文
            project_context = self._gather_project_context(class_info, file_path)
            
            return class_info, project_context
            
        except Exception as e:
            logger.error(f"Error analyzing Java file: {e}")
            raise
    
    def _analyze_method(self, method_node, code: str) -> MethodInfo:
        """分析方法详细信息"""
        # 提取参数
        parameters = []
        if method_node.parameters:
            for param in method_node.parameters:
                param_info = {
                    'name': param.name,
                    'type': self._get_type_name(param.type),
                    'annotations': self._extract_annotations(param)
                }
                parameters.append(param_info)
        
        # 提取返回类型
        return_type = self._get_type_name(method_node.return_type) if method_node.return_type else "void"
        
        # 提取异常声明
        exceptions = []
        if method_node.throws:
            exceptions = [exc.name for exc in method_node.throws]
        
        # 计算圈复杂度
        complexity = self._calculate_complexity(method_node, code)
        
        # 提取可见性
        visibility = self._get_visibility(method_node.modifiers)
        
        # 检查是否为静态方法
        is_static = 'static' in (method_node.modifiers or [])
        
        # 提取注解
        annotations = self._extract_annotations(method_node)
        
        return MethodInfo(
            name=method_node.name,
            parameters=parameters,
            return_type=return_type,
            exceptions=exceptions,
            visibility=visibility,
            is_static=is_static,
            complexity=complexity,
            annotations=annotations
        )
    
    def _gather_project_context(self, class_info: ClassInfo, file_path: Optional[str]) -> ProjectContext:
        """收集项目上下文信息"""
        context = ProjectContext()
        
        # 分析依赖关系
        context.dependencies = self._analyze_dependencies(class_info)
        
        # 检测Spring框架
        if self._detect_spring_framework(class_info):
            context.test_frameworks.append("spring-test")
            context.spring_configs = self._find_spring_configs(class_info)
        
        # 检测测试框架
        context.test_frameworks.extend(self._detect_test_frameworks(class_info))
        
        # 识别自定义异常
        context.custom_exceptions = self._find_custom_exceptions(class_info)
        
        # 识别DTO/Entity类
        context.dto_entities = self._find_dto_entities(class_info)
        
        # 分析项目模式
        context.project_patterns = self._analyze_project_patterns(class_info)
        
        return context
    
    def _extract_annotations(self, node) -> List[str]:
        """提取注解"""
        annotations = []
        if hasattr(node, 'annotations') and node.annotations:
            for annotation in node.annotations:
                if hasattr(annotation, 'name'):
                    annotations.append(annotation.name)
        return annotations
    
    def _extract_fields(self, class_node) -> List[Dict[str, Any]]:
        """提取类字段"""
        fields = []
        if hasattr(class_node, 'fields'):
            for field in class_node.fields:
                for declarator in field.declarators:
                    field_info = {
                        'name': declarator.name,
                        'type': self._get_type_name(field.type),
                        'modifiers': field.modifiers or [],
                        'annotations': self._extract_annotations(field)
                    }
                    fields.append(field_info)
        return fields
    
    def _get_type_name(self, type_node) -> str:
        """获取类型名称"""
        if not type_node:
            return "void"
        
        if hasattr(type_node, 'name'):
            return type_node.name
        elif hasattr(type_node, 'element_type'):
            # 数组类型
            return f"{self._get_type_name(type_node.element_type)}[]"
        elif hasattr(type_node, 'arguments'):
            # 泛型类型
            base_type = self._get_type_name(type_node.name) if hasattr(type_node, 'name') else str(type_node)
            if type_node.arguments:
                args = [self._get_type_name(arg) for arg in type_node.arguments]
                return f"{base_type}<{', '.join(args)}>"
            return base_type
        else:
            return str(type_node)
    
    def _calculate_complexity(self, method_node, code: str) -> int:
        """计算圈复杂度（简化版）"""
        complexity = 1  # 基础复杂度
        
        # 通过代码字符串计算（简化实现）
        method_code = str(method_node)
        
        # 计算控制流语句
        control_statements = ['if', 'else', 'while', 'for', 'switch', 'case', 'catch', '&&', '||', '?']
        for statement in control_statements:
            complexity += method_code.count(statement)
        
        return complexity
    
    def _get_visibility(self, modifiers: Optional[List[str]]) -> str:
        """获取可见性"""
        if not modifiers:
            return "package"
        
        if 'public' in modifiers:
            return "public"
        elif 'private' in modifiers:
            return "private"
        elif 'protected' in modifiers:
            return "protected"
        else:
            return "package"
    
    def _is_abstract(self, class_node) -> bool:
        """检查是否为抽象类"""
        return 'abstract' in (class_node.modifiers or [])
    
    def _analyze_dependencies(self, class_info: ClassInfo) -> Dict[str, List[str]]:
        """分析依赖关系"""
        dependencies = {
            'direct': [],
            'spring': [],
            'data': [],
            'external': []
        }
        
        for import_path in class_info.imports:
            if 'springframework' in import_path:
                dependencies['spring'].append(import_path)
            elif any(keyword in import_path.lower() for keyword in ['entity', 'dto', 'model', 'domain']):
                dependencies['data'].append(import_path)
            elif import_path.startswith('java.') or import_path.startswith('javax.'):
                dependencies['external'].append(import_path)
            else:
                dependencies['direct'].append(import_path)
        
        return dependencies
    
    def _detect_spring_framework(self, class_info: ClassInfo) -> bool:
        """检测是否使用Spring框架"""
        spring_annotations = ['Service', 'Component', 'Repository', 'Controller', 'RestController', 'Configuration']
        spring_imports = ['springframework']
        
        # 检查注解
        for annotation in class_info.annotations:
            if annotation in spring_annotations:
                return True
        
        # 检查导入
        for import_path in class_info.imports:
            if any(spring_import in import_path for spring_import in spring_imports):
                return True
        
        return False
    
    def _find_spring_configs(self, class_info: ClassInfo) -> List[str]:
        """查找Spring配置"""
        configs = []
        
        # 基于注解推断配置
        if 'Repository' in class_info.annotations:
            configs.append("@DataJpaTest")
        elif 'Service' in class_info.annotations:
            configs.append("@ExtendWith(MockitoExtension.class)")
        elif any(ann in class_info.annotations for ann in ['Controller', 'RestController']):
            configs.append("@WebMvcTest")
        
        return configs
    
    def _detect_test_frameworks(self, class_info: ClassInfo) -> List[str]:
        """检测测试框架"""
        frameworks = ["junit5"]  # 默认使用JUnit 5
        
        # 检查是否需要Mockito
        if any('Service' in ann or 'Repository' in ann for ann in class_info.annotations):
            frameworks.append("mockito")
        
        # 检查是否需要Spring Test
        if self._detect_spring_framework(class_info):
            frameworks.append("spring-test")
        
        # 检查是否需要Testcontainers
        if any('Repository' in ann for ann in class_info.annotations):
            frameworks.append("testcontainers")
        
        return frameworks
    
    def _find_custom_exceptions(self, class_info: ClassInfo) -> List[str]:
        """查找自定义异常"""
        exceptions = []
        
        for method in class_info.methods:
            for exception in method.exceptions:
                if not exception.startswith('java.') and not exception.startswith('javax.'):
                    exceptions.append(exception)
        
        return list(set(exceptions))
    
    def _find_dto_entities(self, class_info: ClassInfo) -> List[str]:
        """查找DTO/Entity类"""
        dto_entities = []
        
        for import_path in class_info.imports:
            if any(keyword in import_path.lower() for keyword in ['dto', 'entity', 'model', 'domain']):
                class_name = import_path.split('.')[-1]
                dto_entities.append(class_name)
        
        return dto_entities
    
    def _analyze_project_patterns(self, class_info: ClassInfo) -> Dict[str, Any]:
        """分析项目模式"""
        patterns = {
            'naming_convention': 'camelCase',
            'test_naming': 'methodName_scenario_expected',
            'architecture': 'layered'
        }
        
        # 基于类名和注解推断架构模式
        if any(ann in class_info.annotations for ann in ['Controller', 'RestController']):
            patterns['layer'] = 'controller'
        elif 'Service' in class_info.annotations:
            patterns['layer'] = 'service'
        elif 'Repository' in class_info.annotations:
            patterns['layer'] = 'repository'
        
        return patterns
