import json
import re
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models import Article
from services.vector_store import add_news, add_news_batch
from services.llm_service import get_news_summary_and_tags

def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    
    # 尝试多种日期格式
    formats = [
        '%a, %d %b %Y %H:%M:%S GMT',  # RSS格式
        '%Y-%m-%d %H:%M',  # 2026-03-28 10:30
        '%Y-%m-%d',  # 2026-03-28
        '%Y年%m月%d日 %H:%M',  # 2026年03月28日 10:30
        '%Y-%m-%dT%H:%M:%S',  # ISO格式
        '%Y/%m/%d %H:%M',  # 2026/03/28 10:30
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None

def import_from_json(json_file):
    """从JSON文件导入数据到数据库"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        db = next(get_db())
        
       
        news_for_vector_store = []
        
        for item in data:
            title = item.get('title', '')
            content = item.get('content', '')
            link = item.get('link', '')
            publish_time = item.get('publish_time', '') or item.get('pub_date', '')
            
            # 解析发布时间
            published_at = parse_date(publish_time)
            
            # 检查是否已存在
            existing = db.query(Article).filter_by(title=title, source_url=link).first()
            
            if not existing:
                summary = item.get("summary", "")
                raw_tags = item.get("tags", "")
                cover_image = item.get("cover_image", None)
                
                
                is_valid = True
                if not summary or not raw_tags or raw_tags == "未分类":
                    try:
                        if content:
                            print(f"正在使用大模型分析和审核文章: {title[:20]}...")
                            llm_result = get_news_summary_and_tags(content[:3000])
                            
                            is_valid = llm_result.get("is_valid", True)
                            
                            if not is_valid:
                                reason = llm_result.get("reason", "未知原因")
                                print(f"🚫 垃圾内容已拦截: {title[:20]}... | 原因: {reason}")
                                continue  # 跳过这条数据，不入库
                            
                            summary = llm_result.get("summary", content[:100] + '...')
                            raw_tags = llm_result.get("tags", [])
                    except Exception as e:
                        print(f"⚠️ 大模型处理文章失败: {e}")
                        summary = content[:100] + '...' if content else ''
                        raw_tags = []
                
               
                if not is_valid:
                    continue

                # 解析出原始标签列表
                if isinstance(raw_tags, str):
                    tag_list = [t.strip() for t in raw_tags.split(",") if t.strip()]
                elif isinstance(raw_tags, list):
                    tag_list = [str(t).strip() for t in raw_tags if str(t).strip()]
                else:
                    tag_list = []
                    
                # 【终极强制映射】
                text_for_mapping = title + " " + summary + " " + " ".join(tag_list)
                main_cat = "社会" # 默认兜底
                
                # 关键词词典
                keywords = {
                    "国际": ["以色列", "伊朗", "特朗普", "乌克兰", "中巴", "世卫", "外国", "国际", "外交", "联合国", "冲突"],
                    "财经": ["经济", "航司", "暴跌", "运力", "财晓得", "出海", "股市", "财经", "企业", "商业", "关税", "金融"],
                    "科技": ["航天", "AI", "Sora", "无人机", "科技", "芯片", "模型", "算法", "太空", "数据", "网络"],
                    "教育": ["校庆", "教育", "高校", "大学", "学生", "学校", "未成年人"],
                    "娱乐": ["音乐", "版权", "单依纯", "李荣浩", "娱乐", "短剧", "电影", "明星", "网红", "流量"],
                    "健康": ["输液", "男童", "健康", "医院", "医疗", "疾病", "药企", "医保"],
                    "体育": ["体育", "足球", "篮球", "比赛", "奥运", "夺冠"]
                }
                
              
                for cat, words in keywords.items():
                    if any(w in text_for_mapping for w in words):
                        main_cat = cat
                        break
                        
                standard_categories = ["科技", "财经", "体育", "娱乐", "国际", "社会", "教育", "健康"]
                
                # 把原有的不属于标准分类的词筛出来作为后缀
                sub_tags = [t for t in tag_list if t not in standard_categories]
                
                # 组装最终标签：标准分类排第一，后面接两个小标签
                final_tags_list = [main_cat] + sub_tags[:2]
                final_tags_str = ",".join(final_tags_list)

                article = Article(
                    title=title,
                    content=content,
                    summary=summary,
                    tags=final_tags_str,
                    source_url=link,
                    cover_image=cover_image,
                    published_at=published_at
                )
                db.add(article)
                
                # 等待数据库分配ID后，再添加到向量库
                db.flush()  # 刷新数据库，获取ID
                
                # 添加到向量库批次
                news_for_vector_store.append({
                    "article_id": article.id,
                    "content": content
                })
        
        db.commit()
        print(f'成功导入 {len(data)} 条数据到数据库')
        
       
        if news_for_vector_store:
            print(f'正在将 {len(news_for_vector_store)} 条新闻添加到向量库...')
            try:
                success = add_news_batch(news_for_vector_store)
                if success:
                    print(f'✅ 成功添加 {len(news_for_vector_store)} 条新闻到向量库')
                else:
                    print('❌ 添加到向量库失败')
            except Exception as e:
                print(f'❌ 添加到向量库时出错: {e}')
        else:
            print('⚠️ 没有新新闻需要添加到向量库')
        
    except Exception as e:
        print(f'❌ 导入失败: {e}')
        if 'db' in locals():
            db.rollback()
            db.close()

def main():
    script_dir = Path(__file__).parent
    
   
    sina_json = script_dir / 'sina_content.json'
    if sina_json.exists():
        print('导入新浪新闻...')
        import_from_json(str(sina_json))
    else:
        print(f'⚠️ 新浪新闻文件不存在: {sina_json}')
    
   
    pengpai_json = script_dir / 'pengpai_content.json'
    if pengpai_json.exists():
        print('导入澎湃新闻...')
        import_from_json(str(pengpai_json))
    else:
        print(f'⚠️ 澎湃新闻文件不存在: {pengpai_json}')
    
    print('\n数据导入完成！')

if __name__ == '__main__':
    main()