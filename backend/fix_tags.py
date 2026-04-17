import sys
import os
from pathlib import Path

# 添加 backend 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from models import Article
from services.llm_service import get_news_summary_and_tags

def refresh_tags():
    db = SessionLocal()
    articles = db.query(Article).all()
    print(f"找到 {len(articles)} 篇文章，开始重新生成标签...")
    
    for idx, article in enumerate(articles):
        if not article.content:
            continue
            
        print(f"[{idx+1}/{len(articles)}] 正在处理: {article.title[:20]}")
        try:
            # 取前 1500 字，避免超大模型限制
            content = article.content[:1500]
            result = get_news_summary_and_tags(content)
            
            # 更新标签
            tags_list = result.get("tags", [])
            if isinstance(tags_list, list) and len(tags_list) > 0:
                new_tags_str = ",".join(tags_list)
                article.tags = new_tags_str
                print(f"    生成新标签: {new_tags_str}")
                
                # 如果原来的摘要为空或太短，也一并更新
                if not article.summary or len(article.summary) < 20:
                    article.summary = result.get("summary", "")
                    
                db.commit()
        except Exception as e:
            print(f"    处理失败: {e}")
            db.rollback()

if __name__ == "__main__":
    refresh_tags()
