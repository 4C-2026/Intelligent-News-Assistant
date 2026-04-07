import requests
from bs4 import BeautifulSoup
import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
import re

def generate_rss_feed(items, title, link, description):
    rss = Element('rss', {'version': '2.0'})
    channel = SubElement(rss, 'channel')
    
    SubElement(channel, 'title').text = title
    SubElement(channel, 'link').text = link
    SubElement(channel, 'description').text = description
    SubElement(channel, 'lastBuildDate').text = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    for item in items:
        item_elem = SubElement(channel, 'item')
        SubElement(item_elem, 'title').text = item.get('title', '')
        SubElement(item_elem, 'link').text = item.get('link', '')
        SubElement(item_elem, 'description').text = item.get('description', '')
        if item.get('pubDate'):
            SubElement(item_elem, 'pubDate').text = item['pubDate']
    
    xml_str = tostring(rss, encoding='utf-8')
    dom = parseString(xml_str)
    return dom.toprettyxml(indent='  ')

def fetch_page(url, timeout=15):
    """获取网页内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text
    except Exception as e:
        print(f'获取页面失败 {url}: {e}')
        return None

def get_today_date():
    """获取今天的日期字符串，格式：2026-03-28"""
    return datetime.datetime.now().strftime('%Y-%m-%d')

def is_today_news(url, today_date):
    """判断是否是今天的新闻"""
    # 检查URL中是否包含今天的日期
    return today_date in url

def extract_date_from_sina_url(url):
    """从新浪新闻URL中提取日期"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', url)
    if match:
        return match.group(1)
    return None

def format_date_for_rss(date_str):
    """将日期字符串格式化为RSS标准格式"""
    try:
        # 尝试解析带时间的日期格式，例如：2026-03-28 10:30
        if ' ' in date_str:
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        else:
            # 只解析日期，添加默认时间 12:00:00
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            date_obj = date_obj.replace(hour=12, minute=0, second=0)
        return date_obj.strftime('%a, %d %b %Y %H:%M:%S GMT')
    except:
        return datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')

def parse_sina_news(html_content):
    """提取新浪新闻的具体文章链接"""
    soup = BeautifulSoup(html_content, 'html.parser')
    news_items = []
    seen = set()
    
    # 新浪新闻文章链接模式
    news_patterns = [
        r'https?://news\.sina\.com\.cn/[^/]+/\d{4}-\d{2}-\d{2}/doc-[a-z0-9]+\.shtml',
        r'https?://finance\.sina\.com\.cn/[^/]+/\d{4}-\d{2}-\d{2}/doc-[a-z0-9]+\.shtml',
        r'https?://sports\.sina\.com\.cn/[^/]+/\d{4}-\d{2}-\d{2}/doc-[a-z0-9]+\.shtml',
        r'https?://tech\.sina\.com\.cn/[^/]+/\d{4}-\d{2}-\d{2}/doc-[a-z0-9]+\.shtml',
        r'https?://ent\.sina\.com\.cn/[^/]+/\d{4}-\d{2}-\d{2}/doc-[a-z0-9]+\.shtml',
        r'https?://mil\.news\.sina\.com\.cn/[^/]+/\d{4}-\d{2}-\d{2}/doc-[a-z0-9]+\.shtml',
    ]
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        
        # 过滤条件：文本长度、不是导航链接
        if len(text) < 10 or len(text) > 100:
            continue
        if href.startswith('javascript'):
            continue
            
        # 检查是否是新闻文章链接
        is_news = False
        for pattern in news_patterns:
            if re.match(pattern, href):
                is_news = True
                break
        
        # 如果没有匹配到模式，检查链接特征
        if not is_news:
            # 检查是否包含日期和doc-
            if '/doc-' in href and re.search(r'\d{4}-\d{2}-\d{2}', href):
                is_news = True
            # 排除频道首页
            if href.endswith('.com.cn/') or href.endswith('.com.cn') or '/index' in href:
                is_news = False
        
        if is_news:
            if not href.startswith('http'):
                href = 'https:' + href if href.startswith('//') else 'https://www.sina.com.cn' + href
            
            key = href
            if key not in seen:
                seen.add(key)
                # 提取日期
                date_str = extract_date_from_sina_url(href)
                pub_date = format_date_for_rss(date_str) if date_str else datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
                
                news_items.append({
                    'title': text,
                    'link': href,
                    'description': text,
                    'pubDate': pub_date,
                    'date': date_str  # 保存原始日期字符串
                })
    
    return news_items[:30]  # 限制数量

def extract_pengpai_publish_time(html):
    """从澎湃新闻页面中提取发布时间"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # 首先尝试从特定的class元素中提取时间
    time_selectors = [
        '.news_time',
        '.publish_time',
        '.article-meta',
        '.time',
        '.date',
        '.news-info'
    ]
    
    for selector in time_selectors:
        time_elem = soup.select_one(selector)
        if time_elem:
            text = time_elem.get_text(strip=True)
            # 匹配日期格式，例如：2026-03-28 10:30
            match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', text)
            if match:
                return f'{match.group(1)} {match.group(2)}'
            # 匹配日期格式，例如：2026年03月28日 10:30
            match = re.search(r'(\d{4})年(\d{2})月(\d{2})日\s+(\d{2}):(\d{2})', text)
            if match:
                return f'{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}'
    
    # 如果没有找到，从整个页面的文本中提取时间
    all_text = soup.get_text()
    # 匹配日期格式，例如：2026-03-28 17:28
    match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', all_text)
    if match:
        return f'{match.group(1)} {match.group(2)}'
    
    return None

def parse_pengpai_news(html_content):
    """提取澎湃新闻的具体文章链接"""
    soup = BeautifulSoup(html_content, 'html.parser')
    news_items = []
    seen = set()
    
    # 澎湃新闻文章链接模式
    news_pattern = r'https?://www\.thepaper\.cn/newsDetail_forward_\d+'
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        
        # 过滤条件
        if len(text) < 10 or len(text) > 100:
            continue
        if href.startswith('javascript'):
            continue
        
        # 检查是否是新闻文章链接
        is_news = False
        
        # 完整链接
        if re.match(news_pattern, href):
            is_news = True
        # 相对链接
        elif href.startswith('/newsDetail_forward_'):
            is_news = True
            href = 'https://www.thepaper.cn' + href
        
        if is_news:
            key = href
            if key not in seen:
                seen.add(key)
                
                # 访问新闻页面提取发布时间
                news_html = fetch_page(href)
                publish_time = None
                if news_html:
                    publish_time = extract_pengpai_publish_time(news_html)
                
                # 如果没有提取到时间，使用今天的日期
                date_str = publish_time if publish_time else get_today_date()
                pub_date = format_date_for_rss(date_str)
                
                news_items.append({
                    'title': text,
                    'link': href,
                    'description': text,
                    'pubDate': pub_date,
                    'date': date_str  # 保存原始日期字符串
                })
    
    return news_items[:20]  # 限制数量

def split_html_sources(file_path):
    """从123文件中分离两个网页的源码"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    sina_html = ''
    pengpai_html = ''
    
    marker1 = '这是第一个网页的源码'
    marker2 = '这是第二个网页的源码'
    
    if marker1 in content:
        parts = content.split(marker1)
        if len(parts) > 1:
            sina_html = parts[0].strip()
            remaining = parts[1]
            
            if marker2 in remaining:
                parts2 = remaining.split(marker2)
                if len(parts2) > 0:
                    pengpai_html = parts2[0].strip()
    
    return sina_html, pengpai_html

def main():
    from pathlib import Path
    
    print('正在从网站获取最新新闻...')
    today = get_today_date()
    print(f'今天日期: {today}')
    
    script_dir = Path(__file__).parent
    
    # 直接从网站获取内容
    print('获取新浪新闻...')
    sina_html = fetch_page('https://www.sina.com.cn')
    print(f'新浪网页源码长度: {len(sina_html)} 字符' if sina_html else '❌ 获取新浪新闻失败')
    
    print('获取澎湃新闻...')
    pengpai_html = fetch_page('https://www.thepaper.cn')
    print(f'澎湃网页源码长度: {len(pengpai_html)} 字符' if pengpai_html else '❌ 获取澎湃新闻失败')
    
    if sina_html:
        print('正在解析新浪新闻...')
        sina_items = parse_sina_news(sina_html)
        if sina_items:
            sina_rss = generate_rss_feed(
                sina_items,
                f'新浪新闻 ({today})',
                'https://www.sina.com.cn',
                f'新浪网今日新闻资讯 ({today})'
            )
            
            sina_rss_path = script_dir / 'sina_rss.xml'
            with open(sina_rss_path, 'w', encoding='utf-8') as f:
                f.write(sina_rss)
            print(f'✅ 新浪新闻 RSS 已生成，包含 {len(sina_items)} 条新闻: {sina_rss_path}')
        else:
            print('⚠️ 未找到新浪新闻')
    
    if pengpai_html:
        print('正在解析澎湃新闻...')
        pengpai_items = parse_pengpai_news(pengpai_html)
        if pengpai_items:
            pengpai_rss = generate_rss_feed(
                pengpai_items,
                f'澎湃新闻 ({today})',
                'https://www.thepaper.cn',
                f'澎湃新闻今日资讯 ({today})'
            )
            
            pengpai_rss_path = script_dir / 'pengpai_rss.xml'
            with open(pengpai_rss_path, 'w', encoding='utf-8') as f:
                f.write(pengpai_rss)
            print(f'✅ 澎湃新闻 RSS 已生成，包含 {len(pengpai_items)} 条新闻: {pengpai_rss_path}')
        else:
            print('⚠️ 未找到澎湃新闻')
    
    print('\n✅ 完成！')

if __name__ == '__main__':
    main()