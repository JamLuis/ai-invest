#!/usr/bin/env python3
"""
RSS源测试脚本 - 验证所有配置的RSS源是否可访问并包含有效内容
"""

import os
import sys
import requests
import feedparser
from urllib.parse import urlparse
from datetime import datetime
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_env_file():
    """加载.env文件中的配置"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    
    return env_vars

def test_rss_source(url, priority="unknown"):
    """测试单个RSS源"""
    print(f"\n🔍 测试 [{priority}] {url}")
    
    try:
        # 首先检查HTTP响应
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; AI-Invest RSS Tester/1.0)'
        })
        
        if response.status_code != 200:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
        
        # 检查内容类型
        content_type = response.headers.get('content-type', '')
        if 'xml' not in content_type and 'rss' not in content_type:
            print(f"⚠️  内容类型可疑: {content_type}")
        
        # 解析RSS
        feed = feedparser.parse(url)
        
        if feed.bozo:
            print(f"⚠️  RSS解析警告: {feed.bozo_exception}")
        
        if not hasattr(feed, 'entries') or len(feed.entries) == 0:
            print(f"❌ 没有找到RSS条目")
            return False
        
        # 检查基本信息
        feed_title = feed.feed.get('title', 'Unknown')
        entry_count = len(feed.entries)
        latest_entry = feed.entries[0] if feed.entries else None
        
        print(f"✅ RSS正常")
        print(f"   📰 源标题: {feed_title}")
        print(f"   📊 条目数量: {entry_count}")
        
        if latest_entry:
            title = latest_entry.get('title', 'No title')[:60]
            pub_date = latest_entry.get('published', 'Unknown date')
            print(f"   🆕 最新条目: {title}...")
            print(f"   📅 发布时间: {pub_date}")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接错误")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

def main():
    print("🚀 AI-Invest RSS源测试开始")
    print("=" * 50)
    
    # 加载环境变量
    env_vars = load_env_file()
    if not env_vars:
        print("❌ 无法加载.env文件")
        return
    
    # 测试各优先级RSS源
    test_groups = [
        ("FEEDS_HIGH_PRIORITY", "高优先级"),
        ("FEEDS_MEDIUM_PRIORITY", "中优先级"), 
        ("FEEDS_LOW_PRIORITY", "低优先级"),
        ("FEEDS_RESEARCH", "研究源"),
        ("FEEDS_INTERNATIONAL", "国际源")
    ]
    
    total_sources = 0
    successful_sources = 0
    
    for env_key, group_name in test_groups:
        feeds_str = env_vars.get(env_key, "")
        if not feeds_str:
            continue
            
        print(f"\n📂 测试 {group_name} 源组")
        print("-" * 30)
        
        feeds = [url.strip() for url in feeds_str.split(",") if url.strip()]
        
        for url in feeds:
            total_sources += 1
            if test_rss_source(url, group_name):
                successful_sources += 1
            time.sleep(1)  # 避免请求过于频繁
    
    # 汇总结果
    print("\n" + "=" * 50)
    print(f"📊 测试总结")
    print(f"   总源数: {total_sources}")
    print(f"   成功数: {successful_sources}")
    print(f"   失败数: {total_sources - successful_sources}")
    print(f"   成功率: {successful_sources/total_sources*100:.1f}%" if total_sources > 0 else "0%")
    
    if successful_sources == total_sources:
        print("🎉 所有RSS源测试通过！")
    else:
        print(f"⚠️  有 {total_sources - successful_sources} 个源需要检查")

if __name__ == "__main__":
    main()