"""
crawler_pipeline.py
完整的爬取流水线：
  1. rss_crawler  → 爬取新浪/澎湃首页，提取文章链接，生成 RSS XML
  2. content_extractor → 从 RSS 读取链接，抓取正文，写成 JSON
  3. db_pipeline  → 从 JSON 读取数据，写入数据库 + 向量库
"""

import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SCRAPER_DIR = Path(__file__).parent


def run_full_pipeline(max_items: int = 15) -> dict:
    """
    执行完整爬取流水线。
    返回统计信息字典：{"sina": n, "pengpai": m, "errors": [...]}
    """
    stats = {"sina": 0, "pengpai": 0, "errors": []}

    # ── Step 1: 抓取首页，生成 RSS ──────────────────────────────────────
    try:
        from scraper.rss_crawler import (
            fetch_page, parse_sina_news, parse_pengpai_news,
            generate_rss_feed, get_today_date
        )
        today = get_today_date()
        logger.info("[Pipeline] Step 1 - 抓取首页")

        sina_items, pengpai_items = [], []

        sina_html = fetch_page("https://www.sina.com.cn")
        if sina_html:
            sina_items = parse_sina_news(sina_html)
            rss_xml = generate_rss_feed(sina_items, f"新浪新闻({today})",
                                        "https://www.sina.com.cn", "新浪今日新闻")
            (SCRAPER_DIR / "sina_rss.xml").write_text(rss_xml, encoding="utf-8")
            logger.info(f"[Pipeline] 新浪 RSS 生成，{len(sina_items)} 条")
        else:
            logger.warning("[Pipeline] 新浪首页获取失败")
            stats["errors"].append("新浪首页获取失败")

        pengpai_html = fetch_page("https://www.thepaper.cn")
        if pengpai_html:
            pengpai_items = parse_pengpai_news(pengpai_html)
            rss_xml = generate_rss_feed(pengpai_items, f"澎湃新闻({today})",
                                        "https://www.thepaper.cn", "澎湃今日新闻")
            (SCRAPER_DIR / "pengpai_rss.xml").write_text(rss_xml, encoding="utf-8")
            logger.info(f"[Pipeline] 澎湃 RSS 生成，{len(pengpai_items)} 条")
        else:
            logger.warning("[Pipeline] 澎湃首页获取失败")
            stats["errors"].append("澎湃首页获取失败")

    except Exception as e:
        msg = f"Step1(RSS爬取)异常: {e}"
        logger.error(f"[Pipeline] {msg}")
        stats["errors"].append(msg)

    # ── Step 2: 提取正文，输出 JSON ──────────────────────────────────────
    try:
        from scraper.content_extractor import ContentExtractor
        extractor = ContentExtractor()
        logger.info("[Pipeline] Step 2 - 提取正文")

        for source, rss_name, json_name in [
            ("sina",     "sina_rss.xml",     "sina_content.json"),
            ("pengpai",  "pengpai_rss.xml",  "pengpai_content.json"),
        ]:
            rss_path  = SCRAPER_DIR / rss_name
            json_path = SCRAPER_DIR / json_name

            if not rss_path.exists():
                logger.warning(f"[Pipeline] {rss_name} 不存在，跳过")
                continue

            results = extractor.extract_from_rss_file(
                str(rss_path), str(json_path), max_items=max_items
            )
            logger.info(f"[Pipeline] {source} 正文提取完成，{len(results)} 条")

    except Exception as e:
        msg = f"Step2(正文提取)异常: {e}"
        logger.error(f"[Pipeline] {msg}")
        stats["errors"].append(msg)

    # ── Step 3: 写入数据库 + 向量库 ──────────────────────────────────────
    try:
        from scraper.db_pipeline import import_from_json
        logger.info("[Pipeline] Step 3 - 写入数据库")

        for source, json_name, stat_key in [
            ("sina",    "sina_content.json",    "sina"),
            ("pengpai", "pengpai_content.json", "pengpai"),
        ]:
            json_path = SCRAPER_DIR / json_name
            if not json_path.exists():
                logger.warning(f"[Pipeline] {json_name} 不存在，跳过")
                continue

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            import_from_json(str(json_path))
            stats[stat_key] = len(data)
            logger.info(f"[Pipeline] {source} 写入完成，{len(data)} 条")

    except Exception as e:
        msg = f"Step3(写库)异常: {e}"
        logger.error(f"[Pipeline] {msg}")
        stats["errors"].append(msg)

    logger.info(f"[Pipeline] 流水线完成 - {stats}")
    return stats
