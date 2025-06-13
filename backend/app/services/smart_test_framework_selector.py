"""
智能测试框架选择器 - 根据代码特征自动选择最适合的测试框架和策略
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.advanced_code_analyzer import ClassInfo, MethodInfo, ProjectContext
from app.utils.logger import logger

class TestFramework(Enum):
    """测试框架枚举"""
    JUNIT5 = "junit5"
    MOCKITO = "mockito"
    ASSERTJ = "assertj"
    HAMCREST = "hamcrest"
    SPRING_TEST = "spring-test"
    TESTCONTAINERS = "testcontainers"
    WIREMOCK = "wiremock"

@dataclass
class TestStrategy:
    """测试策略"""
    frameworks: List[TestFramework]
    mock_strategy: str
    assertion_style: str
    test_patterns: List[str]
    imports: List[str]
    annotations: List[str]

@dataclass
class MockStrategy:
    """Mock策略"""
    dependencies_to_mock: List[str]
    mock_type: str  # 'field', 'parameter', 'static'
    mock_annotations: List[str]
    setup_code: str

class SmartTestFrameworkSelector:
    """智能测试框架选择器"""
    
    def __init__(self):
        self.framework_rules = self._initialize_framework_rules()
        self.mock_rules = self._initialize_mock_rules()
    
    def select_test_strategy(self, class_info: ClassInfo, method_info: MethodInfo, 
                           project_context: ProjectContext) -> TestStrategy:
        """
        根据代码特征选择最适合的测试策略
        
        Args:
            class_info: 类信息
            method_info: 方法信息
            project_context: 项目上下文
            
        Returns:
            测试策略
        """
        # 基础框架选择
        frameworks = [TestFramework.JUNIT5]  # 默认使用JUnit 5
        
        # 根据类特征选择框架
        frameworks.extend(self._select_by_class_features(class_info))
        
        # 根据方法特征选择框架
        frameworks.extend(self._select_by_method_features(method_info))
        
        # 根据项目上下文选择框架
        frameworks.extend(self._select_by_project_context(project_context))
        
        # 去重
        frameworks = list(set(frameworks))
        
        # 选择Mock策略
        mock_strategy = self._select_mock_strategy(class_info, method_info, project_context)
        
        # 选择断言风格
        assertion_style = self._select_assertion_style(frameworks, project_context)
        
        # 选择测试模式
        test_patterns = self._select_test_patterns(class_info, method_info)
        
        # 生成导入语句
        imports = self._generate_imports(frameworks, assertion_style)
        
        # 生成注解
        annotations = self._generate_annotations(frameworks, class_info)
        
        return TestStrategy(
            frameworks=frameworks,
            mock_strategy=mock_strategy,
            assertion_style=assertion_style,
            test_patterns=test_patterns,
            imports=imports,
            annotations=annotations
        )
    
    def generate_mock_strategy(self, class_info: ClassInfo, method_info: MethodInfo) -> MockStrategy:
        """生成Mock策略"""
        dependencies_to_mock = []
        mock_type = "field"
        mock_annotations = []
        setup_code = ""
        
        # 分析需要Mock的依赖
        for field in class_info.fields:
            if self._should_mock_field(field):
                dependencies_to_mock.append(field['name'])
        
        # 根据Spring注解选择Mock策略
        if any(ann in class_info.annotations for ann in ['Service', 'Component']):
            mock_annotations.append("@ExtendWith(MockitoExtension.class)")
            mock_type = "field"
        elif 'Repository' in class_info.annotations:
            mock_annotations.append("@DataJpaTest")
            mock_type = "testcontainer"
        elif any(ann in class_info.annotations for ann in ['Controller', 'RestController']):
            mock_annotations.append("@WebMvcTest")
            mock_type = "spring_mock"
        
        # 生成Setup代码
        setup_code = self._generate_setup_code(dependencies_to_mock, mock_type)
        
        return MockStrategy(
            dependencies_to_mock=dependencies_to_mock,
            mock_type=mock_type,
            mock_annotations=mock_annotations,
            setup_code=setup_code
        )
    
    def _select_by_class_features(self, class_info: ClassInfo) -> List[TestFramework]:
        """根据类特征选择框架"""
        frameworks = []
        
        # Spring相关
        if any(ann in class_info.annotations for ann in ['Service', 'Component', 'Repository', 'Controller']):
            frameworks.append(TestFramework.SPRING_TEST)
            frameworks.append(TestFramework.MOCKITO)
        
        # Repository层
        if 'Repository' in class_info.annotations:
            frameworks.append(TestFramework.TESTCONTAINERS)
        
        # Controller层
        if any(ann in class_info.annotations for ann in ['Controller', 'RestController']):
            frameworks.append(TestFramework.WIREMOCK)
        
        # 检查是否有外部依赖
        if class_info.fields:
            frameworks.append(TestFramework.MOCKITO)
        
        return frameworks
    
    def _select_by_method_features(self, method_info: MethodInfo) -> List[TestFramework]:
        """根据方法特征选择框架"""
        frameworks = []
        
        # 复杂方法需要更强的断言
        if method_info.complexity > 5:
            frameworks.append(TestFramework.ASSERTJ)
        
        # 有异常声明的方法
        if method_info.exceptions:
            frameworks.append(TestFramework.ASSERTJ)
        
        # 有特定注解的方法
        if any(ann in method_info.annotations for ann in ['Transactional', 'Async']):
            frameworks.append(TestFramework.SPRING_TEST)
        
        return frameworks
    
    def _select_by_project_context(self, project_context: ProjectContext) -> List[TestFramework]:
        """根据项目上下文选择框架"""
        frameworks = []
        
        # 如果项目中有Spring
        if 'spring-test' in project_context.test_frameworks:
            frameworks.append(TestFramework.SPRING_TEST)
        
        # 如果有数据库操作
        if any('jpa' in dep.lower() or 'hibernate' in dep.lower() 
               for deps in project_context.dependencies.values() for dep in deps):
            frameworks.append(TestFramework.TESTCONTAINERS)
        
        return frameworks
    
    def _select_mock_strategy(self, class_info: ClassInfo, method_info: MethodInfo, 
                            project_context: ProjectContext) -> str:
        """选择Mock策略"""
        # Spring环境下的Mock策略
        if any(ann in class_info.annotations for ann in ['Service', 'Component']):
            return "field_injection"
        elif 'Repository' in class_info.annotations:
            return "testcontainer"
        elif any(ann in class_info.annotations for ann in ['Controller', 'RestController']):
            return "spring_mock_mvc"
        else:
            return "constructor_injection"
    
    def _select_assertion_style(self, frameworks: List[TestFramework], 
                              project_context: ProjectContext) -> str:
        """选择断言风格"""
        if TestFramework.ASSERTJ in frameworks:
            return "assertj"
        elif TestFramework.HAMCREST in frameworks:
            return "hamcrest"
        else:
            return "junit"
    
    def _select_test_patterns(self, class_info: ClassInfo, method_info: MethodInfo) -> List[str]:
        """选择测试模式"""
        patterns = ["happy_path", "boundary_conditions"]
        
        # 根据方法复杂度添加模式
        if method_info.complexity > 3:
            patterns.append("edge_cases")
        
        # 根据异常声明添加模式
        if method_info.exceptions:
            patterns.append("exception_scenarios")
        
        # 根据返回类型添加模式
        if method_info.return_type != "void":
            patterns.append("return_value_validation")
        
        # 根据参数添加模式
        if method_info.parameters:
            patterns.append("parameter_validation")
        
        return patterns
    
    def _generate_imports(self, frameworks: List[TestFramework], assertion_style: str) -> List[str]:
        """生成导入语句"""
        imports = [
            "import org.junit.jupiter.api.Test;",
            "import org.junit.jupiter.api.BeforeEach;",
            "import org.junit.jupiter.api.AfterEach;",
            "import org.junit.jupiter.api.DisplayName;"
        ]

        if TestFramework.MOCKITO in frameworks:
            imports.extend([
                "import org.mockito.Mock;",
                "import org.mockito.InjectMocks;",
                "import org.mockito.MockedStatic;",
                "import org.mockito.junit.jupiter.MockitoExtension;",
                "import org.junit.jupiter.api.extension.ExtendWith;",
                "import static org.mockito.Mockito.*;",
                "import static org.mockito.ArgumentMatchers.*;"
            ])

        if assertion_style == "assertj":
            imports.append("import static org.assertj.core.api.Assertions.*;")
        elif assertion_style == "hamcrest":
            imports.extend([
                "import static org.hamcrest.MatcherAssert.assertThat;",
                "import static org.hamcrest.Matchers.*;"
            ])
        else:
            imports.append("import static org.junit.jupiter.api.Assertions.*;")

        if TestFramework.SPRING_TEST in frameworks:
            imports.extend([
                "import org.springframework.boot.test.context.SpringBootTest;",
                "import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;"
            ])

        # 为Main类添加特殊导入
        imports.extend([
            "import java.io.ByteArrayOutputStream;",
            "import java.io.PrintStream;",
            "import javax.swing.SwingUtilities;"
        ])

        return imports
    
    def _generate_annotations(self, frameworks: List[TestFramework], class_info: ClassInfo) -> List[str]:
        """生成类注解"""
        annotations = []
        
        if TestFramework.MOCKITO in frameworks:
            annotations.append("@ExtendWith(MockitoExtension.class)")
        
        if TestFramework.SPRING_TEST in frameworks:
            if 'Repository' in class_info.annotations:
                annotations.append("@DataJpaTest")
            elif any(ann in class_info.annotations for ann in ['Controller', 'RestController']):
                annotations.append(f"@WebMvcTest({class_info.name}.class)")
            else:
                annotations.append("@SpringBootTest")
        
        return annotations
    
    def _should_mock_field(self, field: Dict) -> bool:
        """判断字段是否需要Mock"""
        # 检查是否有依赖注入注解
        injection_annotations = ['Autowired', 'Inject', 'Resource']
        return any(ann in field.get('annotations', []) for ann in injection_annotations)
    
    def _generate_setup_code(self, dependencies: List[str], mock_type: str) -> str:
        """生成Setup代码"""
        if not dependencies:
            return ""
        
        setup_lines = []
        
        if mock_type == "field":
            for dep in dependencies:
                setup_lines.append(f"    @Mock\n    private SomeService {dep};")
        elif mock_type == "testcontainer":
            setup_lines.append("    @Container\n    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(\"postgres:13\");")
        
        return "\n".join(setup_lines)
    
    def _initialize_framework_rules(self) -> Dict:
        """初始化框架选择规则"""
        return {
            'spring_service': [TestFramework.JUNIT5, TestFramework.MOCKITO, TestFramework.SPRING_TEST],
            'spring_repository': [TestFramework.JUNIT5, TestFramework.TESTCONTAINERS, TestFramework.SPRING_TEST],
            'spring_controller': [TestFramework.JUNIT5, TestFramework.SPRING_TEST, TestFramework.WIREMOCK],
            'complex_logic': [TestFramework.JUNIT5, TestFramework.ASSERTJ],
            'data_processing': [TestFramework.JUNIT5, TestFramework.ASSERTJ, TestFramework.MOCKITO]
        }
    
    def _initialize_mock_rules(self) -> Dict:
        """初始化Mock规则"""
        return {
            'external_service': 'mock',
            'database': 'testcontainer',
            'file_system': 'mock',
            'network': 'wiremock',
            'time': 'mock'
        }
