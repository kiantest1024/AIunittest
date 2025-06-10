"""
Java代码分析器 - 专门用于分析Java代码特征并生成针对性的测试提示
"""

import re
import logging
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)

class JavaCodeAnalyzer:
    """Java代码分析器"""
    
    def __init__(self):
        self.spring_boot_annotations = {
            '@SpringBootApplication',
            '@EnableDiscoveryClient', 
            '@EnableFeignClients',
            '@MapperScan',
            '@EnableAspectJAutoProxy',
            '@EnableScheduling',
            '@SpringBootConfiguration',
            '@ComponentScan',
            '@EnableAutoConfiguration'
        }
        
        self.test_frameworks = {
            'junit5': ['@Test', '@BeforeEach', '@AfterEach', '@DisplayName'],
            'mockito': ['@Mock', '@MockBean', '@InjectMocks', 'MockedStatic'],
            'assertj': ['assertThat', 'Assertions.assertThat'],
            'spring_test': ['@SpringBootTest', '@TestPropertySource', '@MockBean']
        }
    
    def analyze_code(self, code: str) -> Dict:
        """
        分析Java代码并返回特征信息
        
        Args:
            code: Java源代码
            
        Returns:
            包含代码特征的字典
        """
        analysis = {
            'is_spring_boot_app': False,
            'is_main_class': False,
            'has_static_block': False,
            'annotations': [],
            'methods': [],
            'static_methods': [],
            'imports': [],
            'package': None,
            'class_name': None,
            'spring_features': [],
            'test_coverage_areas': [],
            'recommended_test_types': []
        }
        
        try:
            # 基础信息提取
            analysis['package'] = self._extract_package(code)
            analysis['class_name'] = self._extract_class_name(code)
            analysis['imports'] = self._extract_imports(code)
            analysis['annotations'] = self._extract_annotations(code)
            analysis['methods'] = self._extract_methods(code)
            analysis['static_methods'] = self._extract_static_methods(code)
            
            # Spring Boot特征检测
            analysis['is_spring_boot_app'] = self._is_spring_boot_application(code)
            analysis['is_main_class'] = self._has_main_method(code)
            analysis['has_static_block'] = self._has_static_block(code)
            
            # Spring特性分析
            analysis['spring_features'] = self._analyze_spring_features(code)
            
            # 测试覆盖区域建议
            analysis['test_coverage_areas'] = self._suggest_test_coverage_areas(analysis)
            
            # 推荐测试类型
            analysis['recommended_test_types'] = self._recommend_test_types(analysis)
            
            logger.info(f"Java代码分析完成: {analysis['class_name']}")
            
        except Exception as e:
            logger.error(f"Java代码分析失败: {e}")
            
        return analysis
    
    def _extract_package(self, code: str) -> Optional[str]:
        """提取包名"""
        match = re.search(r'package\s+([\w.]+)\s*;', code)
        return match.group(1) if match else None
    
    def _extract_class_name(self, code: str) -> Optional[str]:
        """提取类名"""
        match = re.search(r'public\s+class\s+(\w+)', code)
        return match.group(1) if match else None
    
    def _extract_imports(self, code: str) -> List[str]:
        """提取导入语句"""
        imports = re.findall(r'import\s+([\w.*]+)\s*;', code)
        return imports
    
    def _extract_annotations(self, code: str) -> List[str]:
        """提取注解"""
        annotations = re.findall(r'@(\w+)(?:\([^)]*\))?', code)
        return [f'@{ann}' for ann in annotations]
    
    def _extract_methods(self, code: str) -> List[Dict]:
        """提取方法信息"""
        methods = []
        # 匹配方法定义
        method_pattern = r'(public|private|protected)?\s*(static)?\s*(\w+)\s+(\w+)\s*\([^)]*\)\s*\{'
        matches = re.finditer(method_pattern, code)
        
        for match in matches:
            visibility = match.group(1) or 'package'
            is_static = bool(match.group(2))
            return_type = match.group(3)
            method_name = match.group(4)
            
            methods.append({
                'name': method_name,
                'visibility': visibility,
                'is_static': is_static,
                'return_type': return_type
            })
        
        return methods
    
    def _extract_static_methods(self, code: str) -> List[str]:
        """提取静态方法"""
        static_methods = []
        for method in self._extract_methods(code):
            if method['is_static']:
                static_methods.append(method['name'])
        return static_methods
    
    def _is_spring_boot_application(self, code: str) -> bool:
        """检测是否为Spring Boot应用"""
        return '@SpringBootApplication' in code
    
    def _has_main_method(self, code: str) -> bool:
        """检测是否有main方法"""
        return 'public static void main' in code
    
    def _has_static_block(self, code: str) -> bool:
        """检测是否有静态初始化块"""
        return 'static {' in code or 'static{' in code
    
    def _analyze_spring_features(self, code: str) -> List[str]:
        """分析Spring特性"""
        features = []
        
        if '@SpringBootApplication' in code:
            features.append('spring_boot_application')
        if '@EnableDiscoveryClient' in code:
            features.append('service_discovery')
        if '@EnableFeignClients' in code:
            features.append('feign_clients')
        if '@MapperScan' in code:
            features.append('mybatis_mappers')
        if '@EnableAspectJAutoProxy' in code:
            features.append('aop_proxy')
        if '@EnableScheduling' in code:
            features.append('scheduling')
        if 'scanBasePackages' in code:
            features.append('component_scan')
        if 'basePackages' in code:
            features.append('package_scanning')
        if 'TimeZone.setDefault' in code:
            features.append('timezone_setting')
        if 'SpringApplication.run' in code:
            features.append('spring_application_runner')
            
        return features
    
    def _suggest_test_coverage_areas(self, analysis: Dict) -> List[str]:
        """建议测试覆盖区域"""
        areas = []
        
        # 基础覆盖
        areas.extend(['instruction_coverage', 'branch_coverage', 'method_coverage'])
        
        # Spring Boot特殊覆盖
        if analysis['is_spring_boot_app']:
            areas.extend([
                'annotation_configuration_test',
                'spring_context_loading_test',
                'bean_definition_test'
            ])
        
        if analysis['is_main_class']:
            areas.extend([
                'main_method_test',
                'application_startup_test',
                'command_line_args_test'
            ])
        
        if analysis['has_static_block']:
            areas.extend([
                'static_initialization_test',
                'class_loading_test'
            ])
        
        if 'service_discovery' in analysis['spring_features']:
            areas.append('service_discovery_config_test')
        
        if 'feign_clients' in analysis['spring_features']:
            areas.append('feign_client_config_test')
        
        if 'mybatis_mappers' in analysis['spring_features']:
            areas.append('mapper_scan_config_test')
        
        if 'aop_proxy' in analysis['spring_features']:
            areas.append('aop_proxy_config_test')
        
        if 'scheduling' in analysis['spring_features']:
            areas.append('scheduling_config_test')
        
        if 'timezone_setting' in analysis['spring_features']:
            areas.append('timezone_setting_test')
        
        return areas
    
    def _recommend_test_types(self, analysis: Dict) -> List[str]:
        """推荐测试类型"""
        test_types = ['unit_test']
        
        if analysis['is_spring_boot_app']:
            test_types.extend([
                'spring_boot_test',
                'configuration_test',
                'context_test'
            ])
        
        if analysis['is_main_class']:
            test_types.append('application_test')
        
        if analysis['spring_features']:
            test_types.append('integration_test')
        
        return test_types

def create_enhanced_java_test_prompt(code: str) -> str:
    """
    基于代码分析创建增强的Java测试生成提示
    
    Args:
        code: Java源代码
        
    Returns:
        增强的测试生成提示
    """
    analyzer = JavaCodeAnalyzer()
    analysis = analyzer.analyze_code(code)
    
    # 基础提示模板
    prompt = f"""
你是一个资深Java测试工程师，请为以下Java代码生成全面的单元测试：

源代码:
```java
{code}
```

## 代码分析结果：
- 类名: {analysis['class_name']}
- 包名: {analysis['package']}
- Spring Boot应用: {'是' if analysis['is_spring_boot_app'] else '否'}
- 主类: {'是' if analysis['is_main_class'] else '否'}
- 静态初始化块: {'是' if analysis['has_static_block'] else '否'}
- Spring特性: {', '.join(analysis['spring_features'])}

## 测试覆盖要求：
{chr(10).join([f'- {area}' for area in analysis['test_coverage_areas']])}

## 推荐测试类型：
{chr(10).join([f'- {test_type}' for test_type in analysis['recommended_test_types']])}
"""
    
    # 根据分析结果添加特定的测试指导
    if analysis['is_spring_boot_app']:
        prompt += """
## Spring Boot应用特殊测试要求：
1. **注解配置测试**：验证所有Spring注解的正确配置
2. **配置属性验证**：测试scanBasePackages、basePackages等配置
3. **Spring上下文测试**：验证应用上下文正确加载
4. **Bean定义测试**：确保所有必要的Bean被正确定义
"""
    
    if analysis['is_main_class']:
        prompt += """
## 主类测试要求：
1. **main方法测试**：多种参数组合测试
2. **应用启动测试**：正常启动和异常处理
3. **命令行参数测试**：null、空数组、有效参数
4. **控制台输出验证**：日志和输出内容验证
"""
    
    if analysis['has_static_block']:
        prompt += """
## 静态初始化测试要求：
1. **静态块执行测试**：验证静态初始化正确执行
2. **类加载顺序测试**：确保初始化顺序正确
3. **静态变量测试**：验证静态变量正确设置
"""
    
    prompt += """
## 高级覆盖率要求：
### 指令覆盖率（Statement Coverage）：
- 覆盖所有可执行语句
- 包括静态初始化块、main方法、异常处理

### 分支覆盖率（Branch Coverage）：
- 测试所有条件分支
- 包括if-else、try-catch、条件注解

### 行覆盖率（Line Coverage）：
- 确保每一行代码都被执行
- 包括注解配置、方法调用

### 圈复杂度覆盖率（Cyclomatic Complexity）：
- 测试所有独立路径
- 覆盖异常处理路径

### 方法覆盖率（Method Coverage）：
- 测试所有公共方法
- 包括静态方法、构造方法

### 类覆盖率（Class Coverage）：
- 验证类的完整性
- 包括注解配置、继承关系

## 深入优化方向：
### 1. 异常处理测试：
- SpringApplication启动失败
- 类加载异常
- 配置加载失败
- 运行时异常

### 2. 环境变量测试：
- 不同Profile环境
- 系统属性设置
- 环境变量覆盖

### 3. 配置属性测试：
- 条件配置验证
- 属性绑定测试
- 配置优先级

### 4. 上下文测试：
- Spring上下文加载
- Bean生命周期
- 依赖注入验证

### 5. 事件处理测试：
- 应用启动事件
- 上下文刷新事件
- 应用关闭事件

### 6. 条件配置测试：
- @ConditionalOn注解
- Profile条件
- 属性条件

## 必需的导入语句：
```java
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.boot.context.event.ApplicationStartedEvent;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.boot.test.mock.mockito.MockBean;
import static org.mockito.Mockito.*;
import static org.assertj.core.api.Assertions.*;
import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.time.ZoneId;
import java.util.TimeZone;
import java.util.Properties;
```

## 测试用例要求：
1. **完整的异常处理测试** - 覆盖所有异常路径
2. **环境变量和配置测试** - 验证不同环境配置
3. **Spring上下文集成测试** - 验证上下文加载和Bean
4. **事件处理测试** - 测试应用生命周期事件
5. **条件配置测试** - 验证条件注解和Profile
6. **边界条件测试** - 测试极端情况和边界值
7. **并发和性能测试** - 验证多线程和性能

请生成完整、可运行的测试代码，确保高覆盖率和测试质量。测试方法命名格式：testMethodName_scenario_expectedResult
"""
    
    return prompt
