from app.models.schemas import CodeSnippet
from app.config import PROMPT_TEMPLATES
from app.services.ai_factory import AIServiceFactory
from app.utils.logger import logger

def generate_test_with_ai(snippet: CodeSnippet, model_name: str) -> str:
    """
    使用AI生成测试代码

    Args:
        snippet: 代码片段
        model_name: AI模型名称

    Returns:
        生成的测试代码

    Raises:
        ValueError: 如果模型不存在或语言不支持
    """
    try:
        # 获取提示模板
        if snippet.language not in PROMPT_TEMPLATES:
            raise ValueError(f"Unsupported language for test generation: {snippet.language}")

        prompt_template = PROMPT_TEMPLATES[snippet.language]

        # 构建提示
        code_type = "函数" if snippet.type == "function" else f"类 {snippet.class_name} 的方法"

        # 构建导入语句（根据语言不同而不同）
        import_statement = ""
        if snippet.language == "python":
            if snippet.class_name:
                import_statement = f"from your_module import {snippet.class_name}"
            else:
                import_statement = f"from your_module import {snippet.name}"

        prompt = prompt_template.format(
            code_type=code_type,
            code=snippet.code,
            import_statement=import_statement,
            class_name=snippet.class_name or "",
            function_name=snippet.name
        )

        # 使用AI服务工厂获取服务并生成测试
        ai_service = AIServiceFactory.get_service(model_name)
        return ai_service.generate(prompt)

    except Exception as e:
        logger.error(f"Error generating test with AI: {e}")
        return f"// Error generating test: {str(e)}"

# 这些函数已移至ai_factory.py，不再需要
