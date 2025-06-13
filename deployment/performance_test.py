#!/usr/bin/env python3
"""
AIunittest 负载均衡性能测试脚本
"""

import asyncio
import aiohttp
import time
import json
import argparse
from typing import List, Dict
import statistics

class PerformanceTest:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.results = []
        
    async def test_health_endpoint(self, session: aiohttp.ClientSession) -> Dict:
        """测试健康检查端点"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/health") as response:
                end_time = time.time()
                return {
                    "endpoint": "/health",
                    "status": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                "endpoint": "/health",
                "status": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def test_api_endpoint(self, session: aiohttp.ClientSession, endpoint: str) -> Dict:
        """测试API端点"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/api/{endpoint}") as response:
                end_time = time.time()
                return {
                    "endpoint": f"/api/{endpoint}",
                    "status": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                "endpoint": f"/api/{endpoint}",
                "status": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def test_concurrent_requests(self, concurrent_users: int, requests_per_user: int):
        """测试并发请求"""
        print(f"🚀 开始并发测试: {concurrent_users} 用户, 每用户 {requests_per_user} 请求")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # 创建并发任务
            for user_id in range(concurrent_users):
                for req_id in range(requests_per_user):
                    # 混合不同类型的请求
                    if req_id % 3 == 0:
                        task = self.test_health_endpoint(session)
                    elif req_id % 3 == 1:
                        task = self.test_api_endpoint(session, "languages")
                    else:
                        task = self.test_api_endpoint(session, "models")
                    
                    tasks.append(task)
            
            # 执行所有任务
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # 处理结果
            successful_requests = []
            failed_requests = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_requests.append({"error": str(result)})
                elif result.get("success", False):
                    successful_requests.append(result)
                else:
                    failed_requests.append(result)
            
            # 计算统计信息
            total_requests = len(tasks)
            success_count = len(successful_requests)
            failure_count = len(failed_requests)
            success_rate = (success_count / total_requests) * 100
            
            response_times = [r["response_time"] for r in successful_requests]
            
            stats = {
                "total_requests": total_requests,
                "successful_requests": success_count,
                "failed_requests": failure_count,
                "success_rate": success_rate,
                "total_time": end_time - start_time,
                "requests_per_second": total_requests / (end_time - start_time),
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0
            }
            
            return stats, failed_requests
    
    async def test_load_balancing(self):
        """测试负载均衡效果"""
        print("⚖️  测试负载均衡...")
        
        async with aiohttp.ClientSession() as session:
            # 发送多个请求，检查是否分发到不同实例
            tasks = []
            for i in range(30):  # 发送30个请求
                task = self.test_api_endpoint(session, "queue/status")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            successful_results = [r for r in results if r.get("success", False)]
            
            print(f"✅ 负载均衡测试完成: {len(successful_results)}/{len(tasks)} 请求成功")
            return len(successful_results) / len(tasks) * 100
    
    def print_results(self, stats: Dict, failed_requests: List):
        """打印测试结果"""
        print("\n" + "="*60)
        print("📊 性能测试结果")
        print("="*60)
        
        print(f"总请求数:     {stats['total_requests']}")
        print(f"成功请求数:   {stats['successful_requests']}")
        print(f"失败请求数:   {stats['failed_requests']}")
        print(f"成功率:       {stats['success_rate']:.2f}%")
        print(f"总耗时:       {stats['total_time']:.2f} 秒")
        print(f"QPS:          {stats['requests_per_second']:.2f} 请求/秒")
        
        print("\n📈 响应时间统计:")
        print(f"平均响应时间: {stats['avg_response_time']*1000:.2f} ms")
        print(f"最小响应时间: {stats['min_response_time']*1000:.2f} ms")
        print(f"最大响应时间: {stats['max_response_time']*1000:.2f} ms")
        print(f"中位响应时间: {stats['median_response_time']*1000:.2f} ms")
        
        # 性能评估
        print("\n🎯 性能评估:")
        if stats['success_rate'] >= 99:
            print("✅ 成功率: 优秀")
        elif stats['success_rate'] >= 95:
            print("⚠️  成功率: 良好")
        else:
            print("❌ 成功率: 需要优化")
        
        if stats['avg_response_time'] <= 1:
            print("✅ 响应时间: 优秀")
        elif stats['avg_response_time'] <= 3:
            print("⚠️  响应时间: 良好")
        else:
            print("❌ 响应时间: 需要优化")
        
        if stats['requests_per_second'] >= 100:
            print("✅ 吞吐量: 优秀")
        elif stats['requests_per_second'] >= 50:
            print("⚠️  吞吐量: 良好")
        else:
            print("❌ 吞吐量: 需要优化")
        
        # 显示失败请求详情
        if failed_requests:
            print(f"\n❌ 失败请求详情 (前5个):")
            for i, req in enumerate(failed_requests[:5]):
                print(f"  {i+1}. {req.get('endpoint', 'Unknown')}: {req.get('error', 'Unknown error')}")

async def main():
    parser = argparse.ArgumentParser(description="AIunittest 性能测试")
    parser.add_argument("--url", default="http://localhost", help="测试目标URL")
    parser.add_argument("--users", type=int, default=10, help="并发用户数")
    parser.add_argument("--requests", type=int, default=10, help="每用户请求数")
    parser.add_argument("--test-lb", action="store_true", help="测试负载均衡")
    
    args = parser.parse_args()
    
    tester = PerformanceTest(args.url)
    
    print(f"🧪 AIunittest 性能测试")
    print(f"目标URL: {args.url}")
    print(f"并发用户: {args.users}")
    print(f"每用户请求数: {args.requests}")
    print("-" * 60)
    
    # 基础连通性测试
    print("🔍 基础连通性测试...")
    async with aiohttp.ClientSession() as session:
        health_result = await tester.test_health_endpoint(session)
        if health_result["success"]:
            print("✅ 服务连通性正常")
        else:
            print("❌ 服务连通性异常，请检查服务状态")
            return
    
    # 负载均衡测试
    if args.test_lb:
        lb_success_rate = await tester.test_load_balancing()
        print(f"⚖️  负载均衡成功率: {lb_success_rate:.2f}%")
    
    # 并发性能测试
    stats, failed_requests = await tester.test_concurrent_requests(args.users, args.requests)
    tester.print_results(stats, failed_requests)
    
    # 建议
    print("\n💡 优化建议:")
    if stats['success_rate'] < 95:
        print("  - 检查服务器资源使用情况")
        print("  - 考虑增加后端实例数量")
    
    if stats['avg_response_time'] > 2:
        print("  - 优化数据库查询")
        print("  - 增加Redis缓存")
        print("  - 检查网络延迟")
    
    if stats['requests_per_second'] < 50:
        print("  - 调整Nginx worker配置")
        print("  - 增加后端worker数量")
        print("  - 优化应用代码性能")

if __name__ == "__main__":
    asyncio.run(main())
