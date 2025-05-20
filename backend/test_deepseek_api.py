"""
测试 DeepSeek API 连通性
"""
import os
import requests
import json
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 获取 DeepSeek API 密钥
api_key = os.getenv("DEEPSEEK_API_KEY", "sk-ace4ddbf5f454abda682b0c57df0d313")
if not api_key:
    print("错误: DeepSeek API 密钥未设置。")
    print("请在 .env 文件中设置有效的 DEEPSEEK_API_KEY。")
    exit(1)

# DeepSeek API 配置
api_base = "https://api.deepseek.com/v1"
# 使用 deepseek-chat 模型
model = "deepseek-chat"  # 或者尝试 "deepseek-reasoner"

# 测试请求
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Write a simple Python function to calculate factorial."}],
    "temperature": 0.7,
    "max_tokens": 500
}

url = f"{api_base}/chat/completions"

print(f"正在测试与 DeepSeek API 的连通性...")
print(f"API 基础 URL: {api_base}")
print(f"模型: {model}")
print(f"API 密钥: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")

try:
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        response_data = response.json()
        print("\n连接成功! DeepSeek API 响应:")
        print(f"状态码: {response.status_code}")

        # 提取生成的代码
        generated_text = response_data["choices"][0]["message"]["content"].strip()
        print("\n生成的代码:")
        print("=" * 50)
        print(generated_text)
        print("=" * 50)

        print("\nDeepSeek API 连通性测试通过!")
    else:
        print(f"\n错误: API 调用失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 401:
            print("\n认证失败。请检查您的 API 密钥是否有效。")
        elif response.status_code == 404:
            print("\nAPI 端点不存在。请检查 API 基础 URL 是否正确。")
        elif response.status_code == 429:
            print("\n请求过多。您可能已经超出了 API 速率限制。")

except Exception as e:
    print(f"\n错误: {str(e)}")
    print("\n连接测试失败。请检查您的网络连接和 API 配置。")
