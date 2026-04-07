import sys
import os
from pathlib import Path

# 添加 backend 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from database import get_db
from models import Article
from services.vector_store import add_news_batch

def sync_all_news_to_vector_store():
    """将 SQLite 中所有的新闻同步到 Chroma 向量库中"""
    try:
        print("开始获取数据库中的新闻...")
        db = next(get_db())
        articles = db.query(Article).all()
        
        if not articles:
            print("❌ 数据库中没有新闻，无需同步。")
            return
            
        print(f"找到 {len(articles)} 条新闻，准备进行向量化并存入 Chroma...")
        
        news_for_vector_store = []
        for article in articles:
            # 只有当文章有内容时才进行向量化
            if article.content:
                news_for_vector_store.append({
                    "article_id": article.id,
                    "content": article.content
                })
        
        if news_for_vector_store:
            print(f"实际准备进行向量化的新闻数量: {len(news_for_vector_store)}")
            success = add_news_batch(news_for_vector_store)
            
            if success:
                print("✅ 成功！所有新闻都已同步至向量数据库。")
            else:
                print("❌ 同步失败，请检查上面输出的具体错误。")
        else:
            print("⚠️ 新闻表中没有内容可供向量化。")
            
    except Exception as e:
        print(f"❌ 执行同步时出错: {e}")

if __name__ == "__main__":
    sync_all_news_to_vector_store()
