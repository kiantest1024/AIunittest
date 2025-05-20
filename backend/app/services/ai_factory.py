from typing import Dict, Any, Callable, Optional
import requests
from functools import wraps
from abc import ABC, abstractmethod
from app.config import AI_MODELS
from app.utils.logger import logger

# 错误处理装饰器
def api_error_handler(provider_name: str):
    """
    API错误处理装饰器

    Args:
        provider_name: 提供商名称
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error calling {provider_name} API: {e}")
                raise
        return wrapper
    return decorator

class BaseAIService(ABC):
    """AI服务基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI服务

        Args:
            config: 配置信息
        """
        self.config = config

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        生成文本

        Args:
            prompt: 提示文本

        Returns:
            生成的文本
        """
        pass

    def extract_code_blocks(self, text: str) -> str:
        """
        从文本中提取代码块

        Args:
            text: 包含代码块的文本

        Returns:
            提取的代码块，如果没有代码块则返回原文本
        """
        if "```" in text:
            code_blocks = []
            lines = text.split("\n")
            in_code_block = False
            current_block = []

            for line in lines:
                if line.startswith("```"):
                    if in_code_block:
                        code_blocks.append("\n".join(current_block))
                        current_block = []
                    in_code_block = not in_code_block
                    continue

                if in_code_block:
                    current_block.append(line)

            if code_blocks:
                return code_blocks[0]

        return text

    def _make_api_request(self, url: str, headers: Dict[str, str], payload: Dict[str, Any], skip_key_validation: bool = False) -> Dict[str, Any]:
        """
        发送API请求

        Args:
            url: API地址
            headers: 请求头
            payload: 请求体
            skip_key_validation: 是否跳过API密钥验证

        Returns:
            API响应

        Raises:
            Exception: 如果API调用失败
        """
        # 检查API密钥是否有效
        if not skip_key_validation:
            api_key = self.config.get("api_key", "")
            provider = self.config.get("provider", "")

            # 根据不同的提供商检查API密钥
            if not api_key:
                raise Exception(
                    f"Missing API key for {provider}. Please set a valid API key in the .env file or environment variables. "
                    "See the .env.example file for the required format."
                )

            # 检查是否使用了默认密钥
            if (provider == "openai" and api_key.startswith(("sk-demo"))) or \
               (provider == "anthropic" and api_key.startswith(("sk-ant-api-demo"))) or \
               (provider == "grok" and api_key.startswith(("gsk-demo"))) or \
               (provider == "deepseek" and (api_key == "your-deepseek-api-key" or api_key == "your-actual-deepseek-api-key" or api_key == "demo-deepseek-key-for-development-only")) or \
               (provider == "google" and api_key.startswith(("demo-"))):
                raise Exception(
                    f"Invalid {provider} API key. Please set a valid API key in the .env file or environment variables. "
                    "See the .env.example file for the required format."
                )

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config["timeout"]
            )

            if response.status_code == 401:
                raise Exception(
                    f"Authentication failed: {response.text}. "
                    "Please check your API key and make sure it is valid."
                )
            elif response.status_code != 200:
                raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request error: {str(e)}")

class OpenAIService(BaseAIService):
    """OpenAI服务"""

    @api_error_handler("OpenAI")
    def generate(self, prompt: str) -> str:
        """
        使用OpenAI生成文本

        Args:
            prompt: 提示文本

        Returns:
            生成的文本
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['api_key']}"
        }

        payload = {
            "model": self.config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"]
        }

        url = f"{self.config['api_base']}/chat/completions"
        response_data = self._make_api_request(url, headers, payload)
        test_code = response_data["choices"][0]["message"]["content"].strip()

        return self.extract_code_blocks(test_code)

class GoogleService(BaseAIService):
    """Google Gemini服务"""

    @api_error_handler("Google")
    def generate(self, prompt: str) -> str:
        """
        使用Google Gemini生成文本

        Args:
            prompt: 提示文本

        Returns:
            生成的文本
        """
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.config["temperature"],
                "maxOutputTokens": self.config["max_tokens"],
                "topP": 0.95,
                "topK": 40
            }
        }

        url = f"{self.config['api_base']}/models/{self.config['model']}:generateContent?key={self.config['api_key']}"
        response_data = self._make_api_request(url, headers, payload)
        test_code = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()

        return self.extract_code_blocks(test_code)

class AnthropicService(BaseAIService):
    """Anthropic Claude服务"""

    @api_error_handler("Anthropic")
    def generate(self, prompt: str) -> str:
        """
        使用Anthropic Claude生成文本

        Args:
            prompt: 提示文本

        Returns:
            生成的文本
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config["api_key"],
            "anthropic-version": "2023-06-01"
        }

        # 检查是否使用新版Claude API (Claude 3)
        if "claude-3" in self.config["model"]:
            payload = {
                "model": self.config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config["temperature"],
                "max_tokens": self.config["max_tokens"]
            }

            url = f"{self.config['api_base']}/messages"
            response_data = self._make_api_request(url, headers, payload)
            test_code = response_data["content"][0]["text"].strip()
        else:
            # 旧版Claude API
            payload = {
                "model": self.config["model"],
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "temperature": self.config["temperature"],
                "max_tokens_to_sample": self.config["max_tokens"]
            }

            url = f"{self.config['api_base']}/complete"
            response_data = self._make_api_request(url, headers, payload)
            test_code = response_data["completion"].strip()

        return self.extract_code_blocks(test_code)

class GrokService(BaseAIService):
    """xAI Grok服务"""

    @api_error_handler("Grok")
    def generate(self, prompt: str) -> str:
        """
        使用xAI Grok生成文本

        Args:
            prompt: 提示文本

        Returns:
            生成的文本
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['api_key']}"
        }

        payload = {
            "model": self.config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"]
        }

        url = f"{self.config['api_base']}/chat/completions"
        response_data = self._make_api_request(url, headers, payload)
        test_code = response_data["choices"][0]["message"]["content"].strip()

        return self.extract_code_blocks(test_code)

class DeepSeekService(BaseAIService):
    """DeepSeek服务"""

    @api_error_handler("DeepSeek")
    def generate(self, prompt: str) -> str:
        """
        使用DeepSeek生成文本

        Args:
            prompt: 提示文本

        Returns:
            生成的文本
        """
        # 直接使用配置中的 API 密钥，不进行验证
        api_key = self.config.get("api_key", "")
        print(f"Using DeepSeek API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
        print(f"Using DeepSeek model: {self.config.get('model', 'unknown')}")

        # 设置请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # 设置请求体
        payload = {
            "model": self.config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"]
        }

        # 打印请求信息（不包含完整的 API 密钥）
        print(f"DeepSeek API request:")
        print(f"URL: {self.config['api_base']}/chat/completions")
        print(f"Model: {self.config['model']}")
        print(f"Temperature: {self.config['temperature']}")
        print(f"Max tokens: {self.config['max_tokens']}")

        # 发送请求
        url = f"{self.config['api_base']}/chat/completions"
        try:
            # 跳过 API 密钥验证
            response_data = self._make_api_request(url, headers, payload, skip_key_validation=True)
            test_code = response_data["choices"][0]["message"]["content"].strip()
            return self.extract_code_blocks(test_code)
        except Exception as e:
            # 添加更详细的错误信息
            error_msg = str(e)
            print(f"DeepSeek API error: {error_msg}")

            if "401" in error_msg:
                raise Exception(
                    f"DeepSeek API authentication failed: {error_msg}. "
                    "Please check your API key in the .env file."
                )
            elif "404" in error_msg:
                raise Exception(
                    f"DeepSeek API endpoint not found: {error_msg}. "
                    "Please check the API base URL in the config."
                )
            elif "429" in error_msg:
                raise Exception(
                    f"DeepSeek API rate limit exceeded: {error_msg}. "
                    "Please try again later or reduce the frequency of requests."
                )
            else:
                raise Exception(f"DeepSeek API error: {error_msg}")

class AIServiceFactory:
    """AI服务工厂"""

    @staticmethod
    def get_service(model_name: str) -> BaseAIService:
        """
        获取AI服务

        Args:
            model_name: 模型名称

        Returns:
            AI服务实例

        Raises:
            ValueError: 如果模型不存在或提供商不支持
        """
        if model_name not in AI_MODELS:
            raise ValueError(f"Unknown model: {model_name}")

        model_config = AI_MODELS[model_name]
        provider = model_config["provider"]

        if provider == "openai":
            return OpenAIService(model_config)
        elif provider == "google":
            return GoogleService(model_config)
        elif provider == "anthropic":
            return AnthropicService(model_config)
        elif provider == "grok":
            return GrokService(model_config)
        elif provider == "deepseek":
            return DeepSeekService(model_config)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
