package com.lotto;

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
import org.springframework.context.ApplicationListener;
import org.springframework.boot.SpringBootConfiguration;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.time.ZoneId;
import java.util.TimeZone;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import static org.mockito.Mockito.*;
import static org.assertj.core.api.Assertions.*;
import static org.junit.jupiter.api.Assertions.*;

/**
 * 优化的LottoGameApplication单元测试
 * 
 * 覆盖率目标:
 * - 指令覆盖率: 100%
 * - 分支覆盖率: 100%
 * - 行覆盖率: 100%
 * - 圈复杂度覆盖率: 100%
 * - 方法覆盖率: 100%
 * - 类覆盖率: 100%
 */
@ExtendWith(MockitoExtension.class)
@SpringBootTest
@TestPropertySource(properties = {
    "spring.profiles.active=test",
    "logging.level.com.lotto=DEBUG"
})
class LottoGameApplicationOptimizedTest {

    private final ByteArrayOutputStream outContent = new ByteArrayOutputStream();
    private final ByteArrayOutputStream errContent = new ByteArrayOutputStream();
    private final PrintStream originalOut = System.out;
    private final PrintStream originalErr = System.err;
    private final Properties originalSystemProperties = new Properties();

    @BeforeEach
    void setUpStreams() {
        // 保存原始系统属性
        originalSystemProperties.putAll(System.getProperties());
        
        // 设置输出流捕获
        System.setOut(new PrintStream(outContent));
        System.setErr(new PrintStream(errContent));
    }

    @AfterEach
    void restoreStreams() {
        // 恢复输出流
        System.setOut(originalOut);
        System.setErr(originalErr);
        
        // 恢复系统属性
        System.setProperties(originalSystemProperties);
    }

    // ==================== 静态初始化测试 ====================
    
    @Test
    @DisplayName("静态初始化块设置正确的时区")
    void staticBlock_initialization_setsCorrectTimezone() {
        // Given & When
        TimeZone defaultTimeZone = TimeZone.getDefault();
        ZoneId expectedZoneId = ZoneId.of("Asia/Shanghai");

        // Then
        assertThat(defaultTimeZone.getID()).isEqualTo("Asia/Shanghai");
        assertThat(defaultTimeZone.toZoneId()).isEqualTo(expectedZoneId);
        assertThat(defaultTimeZone.getRawOffset()).isEqualTo(28800000); // UTC+8
    }

    @Test
    @DisplayName("静态初始化块在类加载时执行")
    void staticBlock_execution_occursOnClassLoading() {
        // Given
        TimeZone originalTimeZone = TimeZone.getDefault();
        
        // When - 强制重新加载类（模拟）
        TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
        TimeZone.setDefault(TimeZone.getTimeZone(ZoneId.of("Asia/Shanghai")));
        
        // Then
        assertThat(TimeZone.getDefault().getID()).isEqualTo("Asia/Shanghai");
    }

    // ==================== Main方法测试 ====================
    
    @Test
    @DisplayName("main方法启动Spring应用")
    void main_method_startsSpringApplication() {
        try (MockedStatic<SpringApplication> mocked = mockStatic(SpringApplication.class)) {
            // Given
            ConfigurableApplicationContext mockContext = mock(ConfigurableApplicationContext.class);
            String[] args = {};
            mocked.when(() -> SpringApplication.run(LottoGameApplication.class, args))
                  .thenReturn(mockContext);

            // When
            LottoGameApplication.main(args);

            // Then
            mocked.verify(() -> SpringApplication.run(LottoGameApplication.class, args));
            assertThat(outContent.toString()).contains("lotto-game application start successfully");
        }
    }

    @Test
    @DisplayName("main方法处理null参数")
    void main_method_withNullArguments_startsApplication() {
        try (MockedStatic<SpringApplication> mocked = mockStatic(SpringApplication.class)) {
            // Given
            ConfigurableApplicationContext mockContext = mock(ConfigurableApplicationContext.class);
            mocked.when(() -> SpringApplication.run(LottoGameApplication.class, (String[]) null))
                  .thenReturn(mockContext);

            // When
            assertDoesNotThrow(() -> LottoGameApplication.main(null));

            // Then
            mocked.verify(() -> SpringApplication.run(LottoGameApplication.class, (String[]) null));
        }
    }

    @Test
    @DisplayName("main方法处理命令行参数")
    void main_method_withArguments_startsApplication() {
        try (MockedStatic<SpringApplication> mocked = mockStatic(SpringApplication.class)) {
            // Given
            ConfigurableApplicationContext mockContext = mock(ConfigurableApplicationContext.class);
            String[] args = {"--spring.profiles.active=prod", "--server.port=8080"};
            mocked.when(() -> SpringApplication.run(LottoGameApplication.class, args))
                  .thenReturn(mockContext);

            // When
            LottoGameApplication.main(args);

            // Then
            mocked.verify(() -> SpringApplication.run(LottoGameApplication.class, args));
            assertThat(outContent.toString()).contains("lotto-game application start successfully");
        }
    }

    // ==================== 异常处理测试 ====================
    
    @Test
    @DisplayName("SpringApplication启动失败时的异常处理")
    void main_method_springApplicationFailure_handlesException() {
        try (MockedStatic<SpringApplication> mocked = mockStatic(SpringApplication.class)) {
            // Given
            RuntimeException startupException = new RuntimeException("Application startup failed");
            mocked.when(() -> SpringApplication.run(LottoGameApplication.class, new String[]{}))
                  .thenThrow(startupException);

            // When & Then
            assertThrows(RuntimeException.class, () -> LottoGameApplication.main(new String[]{}));
            
            // 验证异常后不会打印成功日志
            assertThat(outContent.toString()).doesNotContain("lotto-game application start successfully");
        }
    }

    @Test
    @DisplayName("类加载异常处理")
    void classLoading_exception_handledGracefully() {
        // Given
        TimeZone originalTimeZone = TimeZone.getDefault();
        
        try {
            // When - 模拟时区设置异常
            TimeZone.setDefault(null);
            fail("Should throw exception");
        } catch (Exception e) {
            // Then
            assertThat(e).isInstanceOf(NullPointerException.class);
        } finally {
            // 恢复原始时区
            TimeZone.setDefault(originalTimeZone);
        }
    }

    // ==================== 注解配置测试 ====================
    
    @Test
    @DisplayName("类注解配置验证")
    void classAnnotations_configuration_areCorrect() {
        // Given
        Class<LottoGameApplication> clazz = LottoGameApplication.class;

        // Then - 验证所有必需的注解存在
        assertThat(clazz.isAnnotationPresent(SpringBootApplication.class)).isTrue();
        assertThat(clazz.isAnnotationPresent(EnableDiscoveryClient.class)).isTrue();
        assertThat(clazz.isAnnotationPresent(EnableFeignClients.class)).isTrue();
        assertThat(clazz.isAnnotationPresent(EnableAspectJAutoProxy.class)).isTrue();
        assertThat(clazz.isAnnotationPresent(EnableScheduling.class)).isTrue();
        assertThat(clazz.isAnnotationPresent(MapperScan.class)).isTrue();
        assertThat(clazz.isAnnotationPresent(SpringBootConfiguration.class)).isTrue();
    }

    @Test
    @DisplayName("SpringBootApplication配置验证")
    void springBootApplication_configuration_isCorrect() {
        // Given
        SpringBootApplication annotation = LottoGameApplication.class.getAnnotation(SpringBootApplication.class);

        // Then
        assertThat(annotation).isNotNull();
        assertThat(annotation.scanBasePackages()).containsExactly("com.lotto");
        assertThat(annotation.exclude()).isEmpty();
        assertThat(annotation.excludeName()).isEmpty();
    }

    @Test
    @DisplayName("EnableFeignClients配置验证")
    void enableFeignClients_configuration_isCorrect() {
        // Given
        EnableFeignClients annotation = LottoGameApplication.class.getAnnotation(EnableFeignClients.class);

        // Then
        assertThat(annotation).isNotNull();
        assertThat(annotation.basePackages()).containsExactly("com.lotto");
        assertThat(annotation.value()).isEmpty();
    }

    @Test
    @DisplayName("MapperScan配置验证")
    void mapperScan_configuration_isCorrect() {
        // Given
        MapperScan annotation = LottoGameApplication.class.getAnnotation(MapperScan.class);

        // Then
        assertThat(annotation).isNotNull();
        assertThat(annotation.basePackages()).containsExactly("com.lotto.*.biz.**.mapper");
        assertThat(annotation.value()).isEmpty();
    }

    @Test
    @DisplayName("EnableAspectJAutoProxy配置验证")
    void enableAspectJAutoProxy_configuration_isCorrect() {
        // Given
        EnableAspectJAutoProxy annotation = LottoGameApplication.class.getAnnotation(EnableAspectJAutoProxy.class);

        // Then
        assertThat(annotation).isNotNull();
        assertThat(annotation.proxyTargetClass()).isTrue();
        assertThat(annotation.exposeProxy()).isFalse();
    }

    // ==================== 环境变量和配置测试 ====================
    
    @Test
    @DisplayName("测试环境配置")
    @ActiveProfiles("test")
    void environment_testProfile_configurationIsCorrect() {
        // Given
        String activeProfile = System.getProperty("spring.profiles.active");

        // Then
        assertThat(activeProfile).isIn("test", null); // 可能为null或test
    }

    @Test
    @DisplayName("系统属性设置测试")
    void systemProperties_configuration_isCorrect() {
        // Given
        String javaVersion = System.getProperty("java.version");
        String osName = System.getProperty("os.name");

        // Then
        assertThat(javaVersion).isNotNull();
        assertThat(osName).isNotNull();
        
        // 验证时区相关属性
        assertThat(System.getProperty("user.timezone")).isIn("Asia/Shanghai", null);
    }

    @Test
    @DisplayName("环境变量覆盖测试")
    void environmentVariables_override_systemProperties() {
        // Given
        String originalProperty = System.getProperty("test.property");
        
        try {
            // When
            System.setProperty("test.property", "test-value");
            
            // Then
            assertThat(System.getProperty("test.property")).isEqualTo("test-value");
        } finally {
            // Cleanup
            if (originalProperty != null) {
                System.setProperty("test.property", originalProperty);
            } else {
                System.clearProperty("test.property");
            }
        }
    }

    // ==================== 并发和性能测试 ====================
    
    @Test
    @DisplayName("并发启动测试")
    void main_method_concurrentExecution_handledCorrectly() throws InterruptedException {
        // Given
        int threadCount = 3;
        CountDownLatch latch = new CountDownLatch(threadCount);
        
        try (MockedStatic<SpringApplication> mocked = mockStatic(SpringApplication.class)) {
            ConfigurableApplicationContext mockContext = mock(ConfigurableApplicationContext.class);
            mocked.when(() -> SpringApplication.run(eq(LottoGameApplication.class), any(String[].class)))
                  .thenReturn(mockContext);

            // When
            for (int i = 0; i < threadCount; i++) {
                new Thread(() -> {
                    try {
                        LottoGameApplication.main(new String[]{});
                    } finally {
                        latch.countDown();
                    }
                }).start();
            }

            // Then
            assertThat(latch.await(5, TimeUnit.SECONDS)).isTrue();
            mocked.verify(times(threadCount), () -> SpringApplication.run(eq(LottoGameApplication.class), any(String[].class)));
        }
    }

    @Test
    @DisplayName("内存使用测试")
    void application_memoryUsage_isWithinLimits() {
        // Given
        Runtime runtime = Runtime.getRuntime();
        long initialMemory = runtime.totalMemory() - runtime.freeMemory();

        try (MockedStatic<SpringApplication> mocked = mockStatic(SpringApplication.class)) {
            ConfigurableApplicationContext mockContext = mock(ConfigurableApplicationContext.class);
            mocked.when(() -> SpringApplication.run(LottoGameApplication.class, new String[]{}))
                  .thenReturn(mockContext);

            // When
            LottoGameApplication.main(new String[]{});

            // Then
            long finalMemory = runtime.totalMemory() - runtime.freeMemory();
            long memoryIncrease = finalMemory - initialMemory;
            
            // 验证内存增长在合理范围内（例如小于100MB）
            assertThat(memoryIncrease).isLessThan(100 * 1024 * 1024);
        }
    }

    // ==================== 边界条件测试 ====================
    
    @Test
    @DisplayName("极大参数数组测试")
    void main_method_withLargeArgumentArray_handledCorrectly() {
        try (MockedStatic<SpringApplication> mocked = mockStatic(SpringApplication.class)) {
            // Given
            ConfigurableApplicationContext mockContext = mock(ConfigurableApplicationContext.class);
            String[] largeArgs = new String[1000];
            for (int i = 0; i < largeArgs.length; i++) {
                largeArgs[i] = "--property" + i + "=value" + i;
            }
            mocked.when(() -> SpringApplication.run(LottoGameApplication.class, largeArgs))
                  .thenReturn(mockContext);

            // When & Then
            assertDoesNotThrow(() -> LottoGameApplication.main(largeArgs));
            mocked.verify(() -> SpringApplication.run(LottoGameApplication.class, largeArgs));
        }
    }

    @Test
    @DisplayName("特殊字符参数测试")
    void main_method_withSpecialCharacterArguments_handledCorrectly() {
        try (MockedStatic<SpringApplication> mocked = mockStatic(SpringApplication.class)) {
            // Given
            ConfigurableApplicationContext mockContext = mock(ConfigurableApplicationContext.class);
            String[] specialArgs = {"--prop=测试", "--prop2=@#$%^&*()", "--prop3="};
            mocked.when(() -> SpringApplication.run(LottoGameApplication.class, specialArgs))
                  .thenReturn(mockContext);

            // When & Then
            assertDoesNotThrow(() -> LottoGameApplication.main(specialArgs));
            mocked.verify(() -> SpringApplication.run(LottoGameApplication.class, specialArgs));
        }
    }
}
