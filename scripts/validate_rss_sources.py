#!/usr/bin/env python3
"""
RSS源配置验证脚本
验证RSS源的有效性和可访问性
"""

import requests
import feedparser
from urllib.parse import urlparse
import time

# 你提供的RSS源列表（提取URL）
RSS_SOURCES = [
    # 宏观经济
    "https://www.bls.gov/news/news_releases.rss",
    "https://www.bea.gov/news/rss.xml", 
    "https://www.census.gov/rss/newsroom.xml",
    "https://www.oecd.org/newsroom/newsroom_rss.xml",
    "https://www.imf.org/en/rss/press-release",
    "https://blogs.worldbank.org/feed",
    
    # 央行
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://www.ecb.europa.eu/rss/press.html",
    "https://www.bankofengland.co.uk/rss/news",
    "https://www.boj.or.jp/en/rss/whatsnew.xml",
    
    # 交易所和监管
    "https://www.sec.gov/news/pressreleases.rss",
    "https://www.hkex.com.hk/News/News-Release/News-Release?format=rss",
    "https://www.nasdaq.com/feed/rssoutbound?category=All",
    
    # 投行研究
    "https://www.goldmansachs.com/insights/rss.xml",
    "https://www.brookings.edu/topic/economy/feed/",
]

def check_rss_source(url, timeout=10):
    """检查单个RSS源的有效性"""
    try:
        print(f"🔍 检查: {url}")
        
        # 检查HTTP响应
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
        
        # 检查RSS格式
        feed = feedparser.parse(url)
        if feed.bozo:
            print(f"   ⚠️  RSS格式警告: {feed.bozo_exception}")
        
        entry_count = len(feed.entries)
        if entry_count == 0:
            print(f"   ⚠️  RSS源为空")
            return False
        
        print(f"   ✅ 有效，包含 {entry_count} 条条目")
        
        # 显示最新条目示例
        if feed.entries:
            latest = feed.entries[0]
            title = latest.get('title', 'No title')[:50]
            print(f"      最新: {title}...")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"   ❌ 超时")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ 连接错误")
        return False
    except Exception as e:
        print(f"   ❌ 其他错误: {e}")
        return False

def main():
    """验证所有RSS源"""
    print("📊 RSS源配置验证开始...\n")
    
    valid_sources = []
    invalid_sources = []
    
    for url in RSS_SOURCES:
        if check_rss_source(url):
            valid_sources.append(url)
        else:
            invalid_sources.append(url)
        time.sleep(1)  # 避免请求过快
        print()
    
    print("=" * 60)
    print("📋 验证结果总结:")
    print(f"✅ 有效源: {len(valid_sources)}")
    print(f"❌ 无效源: {len(invalid_sources)}")
    
    if valid_sources:
        print("\n🎯 推荐配置 (有效的RSS源):")
        print("# 高优先级 (每分钟)")
        high_priority = [
            "https://www.federalreserve.gov/feeds/press_all.xml",
            "https://www.sec.gov/news/pressreleases.rss", 
            "https://www.hkex.com.hk/News/News-Release/News-Release?format=rss"
        ]
        for url in high_priority:
            if url in valid_sources:
                print(f"  {url}")
        
        print("\n# 中优先级 (每5分钟)")
        medium_priority = [
            "https://www.nasdaq.com/feed/rssoutbound?category=All",
            "https://www.bls.gov/news/news_releases.rss",
            "https://www.ecb.europa.eu/rss/press.html"
        ]
        for url in medium_priority:
            if url in valid_sources:
                print(f"  {url}")
                
        print("\n# 低优先级 (每15分钟)")
        for url in valid_sources:
            if url not in high_priority and url not in medium_priority:
                print(f"  {url}")
    
    if invalid_sources:
        print(f"\n⚠️  需要检查的源:")
        for url in invalid_sources:
            print(f"  {url}")

if __name__ == "__main__":
    main()