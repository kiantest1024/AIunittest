"""
增强的测试生成器 - 实现上下文感知的智能测试生成
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.models.schemas import CodeSnippet
from app.services.advanced_code_analyzer import AdvancedCodeAnalyzer, ClassInfo, MethodInfo, ProjectContext
from app.services.smart_test_framework_selector import SmartTestFrameworkSelector, TestStrategy
from app.services.ai_factory import AIServiceFactory
from app.utils.logger import logger

@dataclass
class TestCase:
    """测试用例"""
    name: str
    description: str
    setup: str
    execution: str
    assertion: str
    category: str  # happy_path, boundary, exception, etc.

@dataclass
class EnhancedTestResult:
    """增强的测试结果"""
    test_class_name: str
    imports: List[str]
    class_annotations: List[str]
    setup_code: str
    test_cases: List[TestCase]
    helper_methods: List[str]
    estimated_coverage: float

class EnhancedTestGenerator:
    """增强的测试生成器"""
    
    def __init__(self):
        self.code_analyzer = AdvancedCodeAnalyzer()
        self.framework_selector = SmartTestFrameworkSelector()
        
    def generate_enhanced_test(self, code: str, language: str, model_name: str,
                             file_path: Optional[str] = None) -> str:
        """
        生成增强的测试代码

        Args:
            code: 源代码
            language: 编程语言
            model_name: AI模型名称
            file_path: 文件路径

        Returns:
            生成的测试代码
        """
        try:
            if language.lower() != 'java':
                # 对于非Java语言，使用原有逻辑
                return self._generate_basic_test(code, language, model_name)

            # 分析Java代码
            class_info, project_context = self.code_analyzer.analyze_java_file(code, file_path)

            # 如果没有找到方法，或者只有main方法，使用整体生成策略
            testable_methods = [m for m in class_info.methods if self._should_generate_test(m)]

            if not testable_methods or (len(testable_methods) == 1 and testable_methods[0].name == 'main'):
                # 为整个类生成测试，特别处理main方法
                return self._generate_class_level_test(class_info, project_context, model_name, code)

            # 生成所有方法的测试
            all_test_results = []

            for method_info in testable_methods:
                test_result = self._generate_method_test(
                    class_info, method_info, project_context, model_name, code
                )
                all_test_results.append(test_result)

            # 合并测试结果
            final_test_code = self._merge_test_results(class_info, all_test_results)

            return final_test_code

        except Exception as e:
            logger.error(f"Error in enhanced test generation: {e}")
            # 降级到基础测试生成
            return self._generate_basic_test(code, language, model_name)
    
    def _generate_class_level_test(self, class_info: ClassInfo, project_context: ProjectContext,
                                 model_name: str, original_code: str) -> str:
        """为整个类生成测试，特别适用于Main类或简单类"""

        # 选择测试策略（使用第一个方法或创建默认方法信息）
        if class_info.methods:
            method_info = class_info.methods[0]
        else:
            # 创建默认方法信息
            method_info = MethodInfo(
                name="main",
                parameters=[],
                return_type="void",
                exceptions=[],
                visibility="public",
                is_static=True,
                complexity=3,
                annotations=[]
            )

        test_strategy = self.framework_selector.select_test_strategy(
            class_info, method_info, project_context
        )

        # 构建专门的类级别提示
        enhanced_prompt = self._build_class_level_prompt(
            class_info, project_context, test_strategy, original_code
        )

        # 使用AI生成测试
        ai_service = AIServiceFactory.get_service(model_name)
        generated_code = ai_service.generate(enhanced_prompt)

        return generated_code

    def _generate_method_test(self, class_info: ClassInfo, method_info: MethodInfo,
                            project_context: ProjectContext, model_name: str, original_code: str = "") -> EnhancedTestResult:
        """为单个方法生成测试"""
        
        # 选择测试策略
        test_strategy = self.framework_selector.select_test_strategy(
            class_info, method_info, project_context
        )
        
        # 生成Mock策略
        mock_strategy = self.framework_selector.generate_mock_strategy(class_info, method_info)
        
        # 构建上下文感知的提示
        enhanced_prompt = self._build_enhanced_prompt(
            class_info, method_info, project_context, test_strategy
        )
        
        # 使用AI生成测试
        ai_service = AIServiceFactory.get_service(model_name)
        generated_code = ai_service.generate(enhanced_prompt)
        
        # 解析生成的测试代码
        test_cases = self._parse_generated_tests(generated_code)
        
        # 估算覆盖率
        estimated_coverage = self._estimate_coverage(method_info, test_cases)
        
        return EnhancedTestResult(
            test_class_name=f"{class_info.name}Test",
            imports=test_strategy.imports,
            class_annotations=test_strategy.annotations,
            setup_code=mock_strategy.setup_code,
            test_cases=test_cases,
            helper_methods=[],
            estimated_coverage=estimated_coverage
        )
    
    def _build_enhanced_prompt(self, class_info: ClassInfo, method_info: MethodInfo, 
                             project_context: ProjectContext, test_strategy: TestStrategy) -> str:
        """构建增强的提示"""
        
        # 基础信息
        base_info = f"""
你是一个资深Java测试工程师，请为以下方法生成高质量的单元测试：

类名: {class_info.name}
包名: {class_info.package}
方法名: {method_info.name}
返回类型: {method_info.return_type}
参数: {self._format_parameters(method_info.parameters)}
异常: {', '.join(method_info.exceptions) if method_info.exceptions else '无'}
可见性: {method_info.visibility}
复杂度: {method_info.complexity}
"""
        
        # 项目上下文
        context_info = f"""
项目上下文:
- 技术栈: {', '.join([fw.value for fw in test_strategy.frameworks])}
- 相关依赖: {', '.join(project_context.dependencies.get('direct', [])[:3])}
- Spring配置: {', '.join(project_context.spring_configs)}
- 自定义异常: {', '.join(project_context.custom_exceptions[:3])}
- DTO/Entity类: {', '.join(project_context.dto_entities[:3])}
"""
        
        # 测试要求
        requirements = f"""
测试要求:
1. 使用 {test_strategy.assertion_style} 风格的断言
2. 覆盖以下场景: {', '.join(test_strategy.test_patterns)}
3. 使用 {test_strategy.mock_strategy} Mock策略
4. 遵循项目命名规范: {project_context.project_patterns.get('test_naming', 'methodName_scenario_expected')}
5. 包含至少3个有意义的断言
6. 添加 @DisplayName 注解描述测试目的

必需的导入语句:
{chr(10).join(test_strategy.imports)}

类注解:
{chr(10).join(test_strategy.annotations)}
"""
        
        # 方法代码
        method_code = self._extract_method_from_class(class_info, method_info)
        
        code_section = f"""
被测试的方法代码:
```java
{method_code}
```
"""
        
        # 生成指导
        generation_guide = """
请生成完整的测试类，包括:
1. 正确的包声明和导入语句
2. 类注解和字段声明
3. @BeforeEach 设置方法（如需要）
4. 多个测试方法，覆盖不同场景
5. 私有辅助方法（如需要）

测试方法命名格式: test{MethodName}_{Scenario}_{ExpectedResult}
例如: testCalculateTotal_WithValidItems_ReturnsCorrectSum
"""
        
        return f"{base_info}\n{context_info}\n{requirements}\n{code_section}\n{generation_guide}"

    def _build_class_level_prompt(self, class_info: ClassInfo, project_context: ProjectContext,
                                test_strategy: TestStrategy, original_code: str) -> str:
        """构建类级别的增强提示"""

        # 分析类的特点
        has_main_method = any(m.name == 'main' and m.is_static for m in class_info.methods)
        is_application_class = has_main_method or 'main' in class_info.name.lower()

        # 基础信息
        base_info = f"""
你是一个资深Java测试工程师，请为以下Java类生成完整的单元测试：

类名: {class_info.name}
包名: {class_info.package}
类型: {'应用程序入口类' if is_application_class else '普通类'}
方法数量: {len(class_info.methods)}
主要方法: {', '.join([m.name for m in class_info.methods[:3]])}
"""

        # 项目上下文
        context_info = f"""
项目上下文:
- 技术栈: {', '.join([fw.value for fw in test_strategy.frameworks])}
- 相关依赖: {', '.join(project_context.dependencies.get('direct', [])[:3])}
- Spring配置: {', '.join(project_context.spring_configs) if project_context.spring_configs else '无'}
- 自定义异常: {', '.join(project_context.custom_exceptions[:3]) if project_context.custom_exceptions else '无'}
"""

        # 特殊要求（针对Main类）
        if is_application_class:
            special_requirements = """
特殊测试要求（针对应用程序入口类）:
1. 测试main方法的各种场景（正常启动、异常处理）
2. 使用PowerMockito或Mockito测试静态方法调用
3. 测试GUI组件初始化（如果有）
4. 测试数据库连接（如果有）
5. 测试异常情况下的错误处理
6. 使用System.setOut()捕获控制台输出进行验证
"""
        else:
            special_requirements = """
测试要求:
1. 覆盖所有公共方法
2. 测试正常流程和异常流程
3. 使用适当的Mock策略
4. 包含边界值测试
"""

        # 测试框架要求
        framework_requirements = f"""
测试框架要求:
1. 使用 {test_strategy.assertion_style} 风格的断言
2. 使用 {test_strategy.mock_strategy} Mock策略
3. 遵循命名规范: testMethodName_scenario_expectedResult
4. 添加 @DisplayName 注解描述测试目的
5. 包含 @BeforeEach 和 @AfterEach 方法（如需要）

必需的导入语句:
{chr(10).join(test_strategy.imports)}

类注解:
{chr(10).join(test_strategy.annotations)}
"""

        # 完整的源代码
        code_section = f"""
完整的源代码:
```java
{original_code}
```
"""

        # 生成指导
        if is_application_class:
            generation_guide = """
请生成完整的测试类，特别注意:
1. 为main方法生成多个测试场景
2. 使用ByteArrayOutputStream捕获System.out输出
3. 使用Mockito.mockStatic()模拟静态方法调用
4. 测试GUI组件的初始化（使用SwingUtilities.invokeAndWait）
5. 测试数据库连接成功和失败的情况
6. 测试异常处理逻辑

测试方法示例:
- testMain_NormalExecution_StartsApplicationSuccessfully()
- testMain_DatabaseConnectionFails_ShowsErrorAndExits()
- testMain_GuiInitializationFails_HandlesExceptionGracefully()
"""
        else:
            generation_guide = """
请生成完整的测试类，包括:
1. 正确的包声明和导入语句
2. 类注解和字段声明
3. @BeforeEach 设置方法
4. 多个测试方法，覆盖不同场景
5. @AfterEach 清理方法（如需要）

测试方法命名格式: test{MethodName}_{Scenario}_{ExpectedResult}
"""

        return f"{base_info}\n{context_info}\n{special_requirements}\n{framework_requirements}\n{code_section}\n{generation_guide}"
    
    def _format_parameters(self, parameters: List[Dict[str, str]]) -> str:
        """格式化参数列表"""
        if not parameters:
            return "无参数"
        
        param_strs = []
        for param in parameters:
            param_str = f"{param['type']} {param['name']}"
            if param.get('annotations'):
                param_str = f"@{', @'.join(param['annotations'])} {param_str}"
            param_strs.append(param_str)
        
        return ', '.join(param_strs)
    
    def _extract_method_from_class(self, class_info: ClassInfo, method_info: MethodInfo) -> str:
        """从类中提取方法代码"""
        # 这里应该从原始代码中提取方法，简化实现
        return f"""
public {method_info.return_type} {method_info.name}({self._format_parameters(method_info.parameters)}) {{
    // 方法实现
    // 复杂度: {method_info.complexity}
    // 异常: {', '.join(method_info.exceptions)}
}}
"""
    
    def _parse_generated_tests(self, generated_code: str) -> List[TestCase]:
        """解析生成的测试代码"""
        test_cases = []
        
        # 使用正则表达式提取测试方法
        test_method_pattern = r'@Test\s*(?:@DisplayName\("([^"]+)"\)\s*)?public\s+void\s+(\w+)\([^)]*\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
        
        matches = re.finditer(test_method_pattern, generated_code, re.DOTALL)
        
        for match in matches:
            display_name = match.group(1) or "测试用例"
            method_name = match.group(2)
            method_body = match.group(3)
            
            # 分析测试用例类型
            category = self._categorize_test_case(method_name, method_body)
            
            test_case = TestCase(
                name=method_name,
                description=display_name,
                setup="// Setup code extracted from method body",
                execution="// Execution code extracted from method body", 
                assertion="// Assertion code extracted from method body",
                category=category
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _categorize_test_case(self, method_name: str, method_body: str) -> str:
        """分类测试用例"""
        method_name_lower = method_name.lower()
        method_body_lower = method_body.lower()
        
        if 'exception' in method_name_lower or 'throws' in method_body_lower:
            return 'exception'
        elif 'boundary' in method_name_lower or 'edge' in method_name_lower:
            return 'boundary'
        elif 'invalid' in method_name_lower or 'null' in method_name_lower:
            return 'negative'
        else:
            return 'happy_path'
    
    def _estimate_coverage(self, method_info: MethodInfo, test_cases: List[TestCase]) -> float:
        """估算测试覆盖率"""
        base_coverage = 60.0  # 基础覆盖率
        
        # 根据测试用例数量调整
        coverage_per_case = min(10.0, 40.0 / max(1, method_info.complexity))
        coverage = base_coverage + len(test_cases) * coverage_per_case
        
        # 根据测试类型调整
        categories = set(tc.category for tc in test_cases)
        if 'exception' in categories:
            coverage += 10.0
        if 'boundary' in categories:
            coverage += 10.0
        if 'negative' in categories:
            coverage += 5.0
        
        return min(95.0, coverage)
    
    def _should_generate_test(self, method_info: MethodInfo) -> bool:
        """判断是否应该为方法生成测试"""
        # 跳过私有方法，但保留main方法
        if method_info.visibility == 'private' and method_info.name != 'main':
            return False

        # 保留main方法，即使它是静态的
        if method_info.name == 'main':
            return True

        # 跳过简单的getter/setter
        if (method_info.name.startswith('get') or method_info.name.startswith('set') or
            method_info.name.startswith('is')) and method_info.complexity <= 1:
            return False

        return True
    
    def _merge_test_results(self, class_info: ClassInfo, test_results: List[EnhancedTestResult]) -> str:
        """合并测试结果为完整的测试类"""
        if not test_results:
            return "// No tests generated"
        
        # 合并导入语句
        all_imports = set()
        for result in test_results:
            all_imports.update(result.imports)
        
        # 合并注解
        all_annotations = set()
        for result in test_results:
            all_annotations.update(result.class_annotations)
        
        # 构建测试类
        test_class_code = f"""package {class_info.package};

{chr(10).join(sorted(all_imports))}

{chr(10).join(all_annotations)}
class {class_info.name}Test {{

    @InjectMocks
    private {class_info.name} {class_info.name.lower()};
    
    {chr(10).join(set(result.setup_code for result in test_results if result.setup_code))}
    
    @BeforeEach
    void setUp() {{
        // 初始化测试环境
    }}
"""
        
        # 添加所有测试方法
        for result in test_results:
            for test_case in result.test_cases:
                test_class_code += f"""
    
    @Test
    @DisplayName("{test_case.description}")
    void {test_case.name}() {{
        {test_case.setup}
        
        {test_case.execution}
        
        {test_case.assertion}
    }}"""
        
        test_class_code += "\n}"
        
        return test_class_code
    
    def _generate_basic_test(self, code: str, language: str, model_name: str) -> str:
        """生成基础测试（降级方案）"""
        # 使用原有的测试生成逻辑
        from app.services.ai_service import generate_test_with_ai
        from app.models.schemas import CodeSnippet
        
        snippet = CodeSnippet(
            name="unknown",
            type="function",
            code=code,
            language=language
        )
        
        return generate_test_with_ai(snippet, model_name)

class TestCodeValidator:
    """测试代码验证器"""

    def __init__(self):
        self.compilation_errors = []
        self.style_warnings = []

    def validate_test_code(self, test_code: str, original_class: ClassInfo) -> Dict[str, Any]:
        """
        验证生成的测试代码

        Args:
            test_code: 生成的测试代码
            original_class: 原始类信息

        Returns:
            验证结果
        """
        result = {
            'is_valid': True,
            'compilation_errors': [],
            'style_warnings': [],
            'coverage_estimate': 0.0,
            'suggestions': []
        }

        # 语法检查
        syntax_errors = self._check_syntax(test_code)
        result['compilation_errors'].extend(syntax_errors)

        # 风格检查
        style_issues = self._check_style(test_code)
        result['style_warnings'].extend(style_issues)

        # 覆盖率估算
        result['coverage_estimate'] = self._estimate_test_coverage(test_code, original_class)

        # 生成改进建议
        result['suggestions'] = self._generate_suggestions(test_code, original_class)

        result['is_valid'] = len(result['compilation_errors']) == 0

        return result

    def _check_syntax(self, test_code: str) -> List[str]:
        """检查语法错误"""
        errors = []

        # 检查基本语法结构
        if not re.search(r'class\s+\w+Test', test_code):
            errors.append("Missing test class declaration")

        if not re.search(r'@Test', test_code):
            errors.append("No test methods found")

        # 检查导入语句
        if 'import org.junit.jupiter.api.Test' not in test_code:
            errors.append("Missing JUnit 5 Test import")

        # 检查括号匹配
        if test_code.count('{') != test_code.count('}'):
            errors.append("Unmatched braces")

        if test_code.count('(') != test_code.count(')'):
            errors.append("Unmatched parentheses")

        return errors

    def _check_style(self, test_code: str) -> List[str]:
        """检查代码风格"""
        warnings = []

        # 检查测试方法命名
        test_methods = re.findall(r'void\s+(\w+)\s*\(', test_code)
        for method in test_methods:
            if not method.startswith('test'):
                warnings.append(f"Test method '{method}' should start with 'test'")

        # 检查是否有断言
        if not re.search(r'assert\w+\(', test_code):
            warnings.append("No assertions found in test code")

        # 检查是否有@DisplayName
        test_count = len(re.findall(r'@Test', test_code))
        display_name_count = len(re.findall(r'@DisplayName', test_code))
        if display_name_count < test_count:
            warnings.append("Some test methods missing @DisplayName annotation")

        return warnings

    def _estimate_test_coverage(self, test_code: str, original_class: ClassInfo) -> float:
        """估算测试覆盖率"""
        test_method_count = len(re.findall(r'@Test', test_code))
        original_method_count = len([m for m in original_class.methods if m.visibility == 'public'])

        if original_method_count == 0:
            return 0.0

        base_coverage = min(90.0, (test_method_count / original_method_count) * 60.0)

        # 检查异常测试
        if re.search(r'assertThrows|expectThrows', test_code):
            base_coverage += 10.0

        # 检查边界值测试
        if re.search(r'null|empty|zero|negative', test_code, re.IGNORECASE):
            base_coverage += 10.0

        return min(95.0, base_coverage)

    def _generate_suggestions(self, test_code: str, original_class: ClassInfo) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 检查是否缺少某些测试场景
        if not re.search(r'null', test_code, re.IGNORECASE):
            suggestions.append("Consider adding null parameter tests")

        if not re.search(r'exception|throws', test_code, re.IGNORECASE):
            suggestions.append("Consider adding exception scenario tests")

        # 检查Mock使用
        if '@Mock' not in test_code and len(original_class.fields) > 0:
            suggestions.append("Consider using @Mock for dependencies")

        return suggestions
