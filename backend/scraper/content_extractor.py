import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse
import time
import datetime

class ContentExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def clean_text(self, text):
        """清洗文本中的常见噪音词汇"""
        if not text:
            return text
            
        # 需要整行删除的无意义关键词
        noise_keywords = [
            '查看更多', '开始答题', '扫码下载', '澎湃新闻客户端', 
            'Android版', 'iPhone版', 'iPad版', '关于澎湃', 
            '加入澎湃', '联系我们', '广告合作', '网络谣言', 
            '返回顶部', '分享至', '特别声明', '下载客户端',
            '登录', '无障碍', '+1', '听全文', '运动家', '参与评论',
            '原标题', '阅读量', '阅读下一篇', '新浪新闻APP', '新浪新闻客户端',
            '新浪财经', '新浪体育', '新浪娱乐', '新浪科技', '新浪网', '未经授权',
            '不得转载', '免责声明', '相关阅读', '延伸阅读', '猜你喜欢', '点击查看',
            '评论区', '发表评论', '全部评论', '分享到', '朋友圈', '微信扫描', '二维码',
            '责任编辑', '校对', '来源：', '点击查看全文', '点赞', '收藏', '转发', '视频号',
            # 澎湃新闻特有噪声关键词
            '法律声明', '隐私政策', '沪ICP备', '沪公网安备', '互联网新闻信息服务许可证',
            '增值电信业务经营许可证', '© 2014-', '澎湃矩阵', '澎湃新闻微博', '澎湃新闻公众号',
            '澎湃新闻抖音号', '派生万物开放平台', 'IP SHANGHAI', 'SIXTH TONE', '澎湃新闻报料：',
            '我要举报', '报料热线:', '报料邮箱:', '图片编辑：', 'x新闻报料',
            '10%公司', '一号专案', '全球速报', '澎湃评论', '大国外交', '绿政公署', '长三角政商',
            '澎湃特约评论员', '澎湃新闻', '澎湃评论', '隐私政策', '法律声明', '图片编辑',
            '反馈', '澎湃新闻记者 ', '沈轲', '张艳', '美数课', '字号',
            '澎湃号', '澎湃新闻记者', '澎湃新闻编辑', '澎湃新闻实习生', '澎湃新闻特约记者',
            '澎湃新闻特约评论员', '澎湃新闻特约撰稿人', '澎湃新闻特约编辑', '澎湃新闻特约实习生',
            '新浪新闻记者', '新浪新闻编辑', '新浪新闻实习生', '新浪新闻特约记者',
            '新浪新闻特约评论员', '新浪新闻特约撰稿人', '新浪新闻特约编辑', '新浪新闻特约实习生',
            '记者', '编辑', '实习生', '特约记者', '特约评论员', '特约撰稿人', '特约编辑', '特约实习生',
            '文/', '文/图', '图/', '图/文', '摄影/', '摄影/图', '图/摄影',
            '（完）', '（全文完）', '（结束）', '（全文结束）', '（终）', '（全文终）',
            '点击进入专题', '专题：', '更多精彩内容', '精彩推荐', '热门推荐', '推荐阅读',
            '往期回顾', '历史文章', '相关专题', '专题报道', '系列报道', '连续报道',
            '声明：', '注：', '备注：', '说明：', '提示：', '提醒：', '注意：',
            '版权声明', '版权归', '版权所有', '转载请联系', '转载须知', '转载声明',
            '合作媒体', '媒体合作', '战略合作', '合作伙伴', '合作机构', '支持机构',
            '广告位', '广告内容', '广告合作', '商业合作', '商务合作', '品牌合作','澎湃首席评论员','与归'
        ]
        
        lines = text.split('\n')
        cleaned_lines = []
        
        # 强干扰词，只要段落中包含这些词，不管多长都直接整段丢弃
        strong_noise_keywords = [
            '阅读排行榜', '评论排行榜', '相关新闻投资热点', '点击加载更多', 
            '尽在新浪财经', '新浪财经APP', '加载中点击加载更多', '扫二维码',
            '澎湃新闻报料：021-962866', '报料热线: 021-962866', '报料邮箱: news@thepaper.cn',
            '沪ICP备14003370号', '沪公网安备31010602000299号', '互联网新闻信息服务许可证：31120170006',
            '增值电信业务经营许可证：沪B2-2017116', '© 2014-2026 上海东方报业有限公司',
            '新浪新闻APP下载', '澎湃新闻APP下载', '客户端下载', 'APP下载',
            '意见反馈', '用户反馈', '联系我们', '关于我们', '网站地图', '站点地图',
            '隐私条款', '服务条款', '使用条款', '用户协议', '注册协议', '登录协议',
            '举报中心', '举报电话', '举报邮箱', '投诉电话', '投诉邮箱', '维权电话',
            '不良信息举报', '违法和不良信息举报', '网络举报', '互联网举报'
        ]
        
        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                continue
                
            
            if any(kw in line_strip for kw in strong_noise_keywords):
                continue
                
           
            if len(line_strip) < 60 and any(kw in line_strip for kw in noise_keywords):
                continue
                
           
            if line_strip.startswith(('责任编辑', '来源：', '校对：', '撰文：', '原标题：', '延伸阅读', '相关阅读')):
                continue
                
           
            if len(line_strip) <= 2 and not re.search(r'[a-zA-Z0-9\u4e00-\u9fa5]', line_strip):
                continue
                
            cleaned_lines.append(line_strip)
            
        return '\n'.join(cleaned_lines)
    
    def fetch_page(self, url, timeout=10):
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
        except Exception as e:
            print(f'获取页面失败 {url}: {e}')
            return None
    
    def extract_sina_content(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取第一张有意义的图片作为封面
        cover_image = None
        
        # 尝试多种可能的内容选择器
        content_selectors = [
            '#artibody',  # 新浪新闻正文
            '.article-content',
            '#article_content',
            '.content',
            '#content',
            'article',
            '.main-content',
            '.article-body'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                if not cover_image:
                    img = content_elem.find('img')
                    if img and img.get('src') and not img.get('src').endswith('.gif'):
                        cover_image = img.get('src')
                        if cover_image.startswith('//'):
                            cover_image = 'https:' + cover_image
                            
                # 移除脚本和样式
                for script in content_elem.find_all(['script', 'style', 'iframe', 'nav']):
                    script.decompose()
                
                # 尝试逐段提取以保持更好的结构
                paragraphs = content_elem.find_all(['p', 'div', 'span'])
                if paragraphs and len(paragraphs) > 2:
                    texts = []
                    for p in paragraphs:
                        t = p.get_text(strip=True)
                        if t and len(t) > 5: # 忽略太短的无意义标签
                            texts.append(t)
                    # 去重，因为嵌套标签可能会导致重复提取
                    unique_texts = []
                    for t in texts:
                        if t not in unique_texts:
                            unique_texts.append(t)
                    text = '\n'.join(unique_texts)
                else:
                    text = content_elem.get_text(separator='\n', strip=True)
                    
                
                text = re.sub(r'\n{2,}', '\n', text)
                text = self.clean_text(text)
                return text[:8000], cover_image  # 增加长度限制
        
        # 如果没有找到特定选择器，尝试提取主要内容
        body = soup.find('body')
        if body:
            if not cover_image:
                img = body.find('img')
                if img and img.get('src') and not img.get('src').endswith('.gif') and len(img.get('src')) > 10:
                    cover_image = img.get('src')
                    if cover_image.startswith('//'):
                        cover_image = 'https:' + cover_image
                        
            # 移除导航、广告等
            for elem in body.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style', 'iframe']):
                elem.decompose()
            
            text = body.get_text(separator='\n', strip=True)
            text = re.sub(r'\n{2,}', '\n', text)
            text = self.clean_text(text)
            return text[:8000], cover_image  # 增加长度限制
        
        return None, None
    
    def extract_pengpai_content(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        
        cover_image = None
        
       
        content_selectors = [
            '.news_txt',  # 澎湃新闻正文
            '.content',
            '#content',
            'article',
            '.article-content',
            '.main-content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                if not cover_image:
                    img = content_elem.find('img')
                    if img and img.get('src'):
                        cover_image = img.get('src')
                        
                for script in content_elem.find_all(['script', 'style', 'iframe', 'nav']):
                    script.decompose()
                
                # 澎湃新闻通常用 <p> 标签分段
                paragraphs = content_elem.find_all('p')
                if paragraphs:
                    texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                    text = '\n'.join(texts)
                else:
                    text = content_elem.get_text(separator='\n', strip=True)
                    
                text = re.sub(r'\n{2,}', '\n', text)
                text = self.clean_text(text)
                return text, cover_image
        
        body = soup.find('body')
        if body:
            if not cover_image:
                img = body.find('img')
                if img and img.get('src') and len(img.get('src')) > 10:
                    cover_image = img.get('src')
                    
            for elem in body.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style', 'iframe']):
                elem.decompose()
            
            text = body.get_text(separator='\n', strip=True)
            text = re.sub(r'\n{2,}', '\n', text)
            text = self.clean_text(text)
            return text[:8000], cover_image
        
        return None, None
    
    def extract_sina_publish_time(self, html):
        """提取新浪新闻的发布时间"""
        soup = BeautifulSoup(html, 'html.parser')
        
        
        time_selectors = [
            '.date',
            '#pub_date',
            '.pubdate',
            '.publish_time',
            '.artInfo',
            '.article-meta',
            '.time-source'
        ]
        
        for selector in time_selectors:
            time_elem = soup.select_one(selector)
            if time_elem:
                text = time_elem.get_text(strip=True)
                # 匹配日期格式，例如：2026年03月28日 10:30
                match = re.search(r'(\d{4})[年\-](\d{2})[月\-](\d{2})[日\s](\d{2}):(\d{2})', text)
                if match:
                    year, month, day, hour, minute = match.groups()
                    return f'{year}-{month}-{day} {hour}:{minute}'
        
        # 从URL中提取日期
        return None
    
    def extract_pengpai_publish_time(self, html):
        """提取澎湃新闻的发布时间"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尝试多种可能的时间选择器
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
        
        return None
    
    def extract_content(self, url):
        domain = urlparse(url).netloc
        
        html = self.fetch_page(url)
        if not html:
            return None, None, None
        
        content = None
        publish_time = None
        cover_image = None
        
        if 'sina.com.cn' in domain:
            content, cover_image = self.extract_sina_content(html)
            publish_time = self.extract_sina_publish_time(html)
        elif 'thepaper.cn' in domain:
            content, cover_image = self.extract_pengpai_content(html)
            publish_time = self.extract_pengpai_publish_time(html)
        else:
            # 通用提取方法
            soup = BeautifulSoup(html, 'html.parser')
            body = soup.find('body')
            if body:
                img = body.find('img')
                if img and img.get('src') and len(img.get('src')) > 10:
                    cover_image = img.get('src')
                    
                for elem in body.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style', 'iframe']):
                    elem.decompose()
                
                text = body.get_text(separator='\n', strip=True)
                text = re.sub(r'\n{2,}', '\n', text)
                text = self.clean_text(text)
                content = text[:8000]
            
            # 尝试提取时间
            time_elem = soup.find(['time', 'span'], class_=re.compile(r'time|date|publish'))
            if time_elem:
                publish_time = time_elem.get_text(strip=True)
        
        return content, publish_time, cover_image
    
    def extract_from_rss_file(self, rss_file_path, output_file_path, max_items=10):
        import xml.etree.ElementTree as ET
        
        try:
            tree = ET.parse(rss_file_path)
            root = tree.getroot()
            
            results = []
            items = root.findall('.//item')
            
            print(f'从 {rss_file_path} 中找到 {len(items)} 条新闻')
            
            for i, item in enumerate(items[:max_items]):
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                
                title_text = title.text if title is not None else ''
                link_text = link.text if link is not None else ''
                pub_date_text = pub_date.text if pub_date is not None else ''
                
                print(f'[{i+1}/{min(len(items), max_items)}] 正在提取: {title_text[:50]}...')
                
                if link_text:
                    content, publish_time, cover_image = self.extract_content(link_text)
                    if content:
                        # 确保内容足够长且有意义，有些网页可能提取到了一堆乱码或仅有标题
                        if len(content) < 50:
                            content += "\n（提取到的正文过短，可能内容受限，请访问原链接查看全貌。）"
                            
                        results.append({
                            'title': title_text,
                            'link': link_text,
                            'content': content[:8000],  # 放宽限制存储长度，保留更完整新闻
                            'cover_image': cover_image,
                            'publish_time': publish_time or pub_date_text,
                            'pub_date': pub_date_text
                        })
                    else:
                        results.append({
                            'title': title_text,
                            'link': link_text,
                            'content': '提取失败',
                            'cover_image': None,
                            'publish_time': pub_date_text,
                            'pub_date': pub_date_text
                        })
                    
                    time.sleep(0.5)  # 避免请求过快
            
            
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f'提取完成，已保存到 {output_file_path}')
            return results
            
        except Exception as e:
            print(f'处理 RSS 文件失败: {e}')
            return []

def main():
    from pathlib import Path
    
    extractor = ContentExtractor()
    script_dir = Path(__file__).parent
    
    # 提取新浪新闻正文
    sina_rss = script_dir / 'sina_rss.xml'
    sina_json = script_dir / 'sina_content.json'
    
    if sina_rss.exists():
        print('=== 提取新浪新闻正文 ===')
        sina_results = extractor.extract_from_rss_file(
            str(sina_rss),
            str(sina_json),
            max_items=10
        )
    else:
        print(f'⚠️ 新浪 RSS 文件不存在: {sina_rss}')
        sina_results = []
    
    # 提取澎湃新闻正文
    pengpai_rss = script_dir / 'pengpai_rss.xml'
    pengpai_json = script_dir / 'pengpai_content.json'
    
    if pengpai_rss.exists():
        print('\n=== 提取澎湃新闻正文 ===')
        pengpai_results = extractor.extract_from_rss_file(
            str(pengpai_rss),
            str(pengpai_json),
            max_items=10
        )
    else:
        print(f'⚠️ 澎湃 RSS 文件不存在: {pengpai_rss}')
        pengpai_results = []
    
    print('\n=== 提取完成 ===')
    print(f'新浪新闻: {len(sina_results)} 条')
    print(f'澎湃新闻: {len(pengpai_results)} 条')

if __name__ == '__main__':
    main()