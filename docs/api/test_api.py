#!/usr/bin/env python3
"""
Finance News API 测试脚本

用于验证API功能的简单测试脚本
"""

import requests
import json
import sys
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_api_health():
    """测试API基本连通性"""
    try:
        response = requests.get(f"{API_BASE_URL}/news?limit=1", timeout=5)
        if response.status_code == 200:
            print("✅ API服务正常运行")
            return True
        else:
            print(f"❌ API返回错误状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保服务正在运行")
        return False
    except requests.exceptions.Timeout:
        print("❌ API请求超时")
        return False
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def test_news_list():
    """测试新闻列表获取"""
    print("\n📰 测试新闻列表获取...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/news?limit=5")
        response.raise_for_status()
        
        news = response.json()
        if isinstance(news, list):
            print(f"✅ 成功获取 {len(news)} 条新闻")
            if news:
                sample = news[0]
                required_fields = ['id', 'source', 'url', 'title', 'summary', 'published_at']
                missing_fields = [field for field in required_fields if field not in sample]
                
                if not missing_fields:
                    print("✅ 新闻数据格式正确")
                    print(f"   示例标题: {sample['title'][:50]}...")
                    return True
                else:
                    print(f"❌ 新闻数据缺少字段: {missing_fields}")
                    return False
            else:
                print("⚠️  返回的新闻列表为空")
                return True  # 空列表也是有效响应
        else:
            print("❌ 返回数据格式错误，应该是数组")
            return False
            
    except Exception as e:
        print(f"❌ 新闻列表测试失败: {e}")
        return False

def test_news_search():
    """测试新闻搜索功能"""
    print("\n🔍 测试新闻搜索功能...")
    
    search_terms = ["SEC", "Hong Kong", "regulatory"]
    
    for term in search_terms:
        try:
            response = requests.get(f"{API_BASE_URL}/news", params={"q": term, "limit": 3})
            response.raise_for_status()
            
            results = response.json()
            print(f"✅ 搜索 '{term}': 找到 {len(results)} 条结果")
            
            # 验证搜索结果相关性
            if results:
                relevant_count = 0
                for article in results:
                    title_match = term.lower() in article['title'].lower()
                    summary_match = term.lower() in article['summary'].lower()
                    if title_match or summary_match:
                        relevant_count += 1
                
                relevance_ratio = relevant_count / len(results)
                if relevance_ratio > 0.5:  # 至少50%相关
                    print(f"   搜索相关性良好: {relevant_count}/{len(results)} 相关")
                else:
                    print(f"   ⚠️  搜索相关性较低: {relevant_count}/{len(results)} 相关")
                    
        except Exception as e:
            print(f"❌ 搜索 '{term}' 失败: {e}")
            return False
    
    return True

def test_api_parameters():
    """测试API参数验证"""
    print("\n⚙️  测试API参数...")
    
    # 测试limit参数
    test_cases = [
        {"limit": 1, "expected_max": 1},
        {"limit": 10, "expected_max": 10},
        {"limit": 100, "expected_max": 100},
    ]
    
    for case in test_cases:
        try:
            response = requests.get(f"{API_BASE_URL}/news", params=case)
            response.raise_for_status()
            
            results = response.json()
            actual_count = len(results)
            expected_max = case["expected_max"]
            
            if actual_count <= expected_max:
                print(f"✅ limit={expected_max}: 返回 {actual_count} 条记录")
            else:
                print(f"❌ limit={expected_max}: 预期最多 {expected_max} 条，实际返回 {actual_count} 条")
                return False
                
        except Exception as e:
            print(f"❌ 参数测试失败: {e}")
            return False
    
    return True

def test_data_quality():
    """测试数据质量"""
    print("\n📊 测试数据质量...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/news?limit=20")
        response.raise_for_status()
        
        news = response.json()
        if not news:
            print("⚠️  没有数据进行质量检查")
            return True
        
        # 检查数据完整性
        complete_articles = 0
        for article in news:
            if all(article.get(field) for field in ['title', 'summary', 'url', 'published_at']):
                complete_articles += 1
        
        completeness_ratio = complete_articles / len(news)
        print(f"✅ 数据完整性: {complete_articles}/{len(news)} ({completeness_ratio:.1%})")
        
        # 检查URL有效性
        valid_urls = 0
        for article in news:
            url = article.get('url', '')
            if url.startswith(('http://', 'https://')):
                valid_urls += 1
        
        url_validity_ratio = valid_urls / len(news)
        print(f"✅ URL有效性: {valid_urls}/{len(news)} ({url_validity_ratio:.1%})")
        
        # 检查时间格式
        valid_times = 0
        for article in news:
            try:
                datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                valid_times += 1
            except:
                pass
        
        time_validity_ratio = valid_times / len(news)
        print(f"✅ 时间格式: {valid_times}/{len(news)} ({time_validity_ratio:.1%})")
        
        return completeness_ratio > 0.8 and url_validity_ratio > 0.9 and time_validity_ratio > 0.9
        
    except Exception as e:
        print(f"❌ 数据质量测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🧪 Finance News API 测试开始...")
    print("=" * 50)
    
    test_results = []
    
    # 运行各项测试
    tests = [
        ("API连通性", test_api_health),
        ("新闻列表", test_news_list),
        ("搜索功能", test_news_search),
        ("参数验证", test_api_parameters),
        ("数据质量", test_data_quality),
    ]
    
    for test_name, test_func in tests:
        result = test_func()
        test_results.append((test_name, result))
    
    # 输出测试总结
    print("\n" + "=" * 50)
    print("🏁 测试总结:")
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(test_results)} 项测试通过")
    
    if passed == len(test_results):
        print("🎉 所有测试通过！API功能正常")
        return 0
    else:
        print("⚠️  部分测试失败，请检查API服务")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)