# backend/insert_test_data.py
"""
    插入假数据
"""

from database import SessionLocal
from models.article import Article
from datetime import datetime

def insert_test_data():
    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(Article).count() > 0:
            print("数据库已有数据，跳过插入")
            return

        # 准备测试数据
        test_articles = [
            Article(
                title="OpenAI 发布 GPT-5 预览版，性能大幅提升",
                content="OpenAI 今日宣布推出 GPT-5 预览版，在推理、多模态理解和长文本处理方面均有显著改进。新模型支持高达 100 万 token 的上下文，能够一次性处理整本书籍。",
                summary="OpenAI 推出 GPT-5 预览版，支持超长上下文，性能显著提升。",
                tags="AI,科技,OpenAI",
                source_url="https://example.com/news/1",
                published_at=datetime.now()
            ),
            Article(
                title="国内首个自主可控的向量数据库开源发布",
                content="清华大学与智谱 AI 联合发布了国内首个完全自主可控的向量数据库 OpenVector，支持亿级向量检索，性能超越国际主流产品，为国产大模型生态提供关键基础设施。",
                summary="国内首个自主可控向量数据库开源，支持亿级检索。",
                tags="AI,数据库,国产",
                source_url="https://example.com/news/2",
                published_at=datetime.now()
            ),
            Article(
                title="欧盟通过全球首个 AI 监管法案，划定高风险应用边界",
                content="欧洲议会正式通过《人工智能法案》，成为全球首部全面监管 AI 的法律。法案根据风险等级对 AI 系统进行分类，禁止实时生物识别监控等高风险应用。",
                summary="欧盟通过全球首个 AI 监管法案，按风险等级监管。",
                tags="政策,AI,国际",
                source_url="https://example.com/news/3",
                published_at=datetime.now()
            ),
            Article(
                title="前端框架 Vue 3.5 正式发布，性能提升显著",
                content="Vue.js 团队宣布 Vue 3.5 正式版发布，带来了响应式系统重写、内存使用减少 56%、服务端渲染性能提升等多项改进。",
                summary="Vue 3.5 正式发布，响应式系统重写，性能大幅提升。",
                tags="前端,技术,Vue",
                source_url="https://example.com/news/4",
                published_at=datetime.now()
            ),
            Article(
                title="科学家利用 AI 发现新型抗生素，对抗耐药菌",
                content="麻省理工学院的研究团队利用深度学习模型，成功发现了一种新型抗生素，该化合物能够有效杀灭此前对所有已知抗生素耐药的细菌。",
                summary="AI 发现新型抗生素，可对抗耐药菌。",
                tags="医疗,AI,科研",
                source_url="https://example.com/news/5",
                published_at=datetime.now()
            ),
        ]
        db.add_all(test_articles)
        db.commit()
        print(f"成功插入 {len(test_articles)} 条测试新闻")
    finally:
        db.close()

if __name__ == "__main__":
    insert_test_data()
    
    