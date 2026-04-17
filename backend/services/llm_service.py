"""
智谱GLM大模型服务
用于新闻摘要和标签生成
"""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI


class LLMService:
    """智谱GLM大模型服务类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化LLM服务
        """
        load_dotenv()
        
        
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not found in environment variables or provided")
        
        # 初始化OpenAI客户端（兼容智谱API）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4/",
        )
        
        # 模型配置
        self.model = "glm-4-flash"
        
    def get_news_summary_and_tags(self, news_content: str) -> Dict[str, any]:
        """
        获取新闻摘要和标签
        """
       
        system_prompt = """你是一个专业的新闻编辑，负责生成新闻摘要和标签。
        
        要求：
        1. 生成50-100字的新闻摘要，准确概括新闻核心内容
        2. 生成3个中文标签，每个标签2-4个字，反映新闻的关键主题
        3. 输出必须是严格的JSON格式，包含两个字段：summary和tags
        4. tags字段必须是包含3个字符串的数组
        
        示例输出格式：
        {
            "summary": "这里是50-100字的新闻摘要...",
            "tags": ["标签1", "标签2", "标签3"]
        }
        
        请严格按照要求处理新闻内容。"""
        
        # 构建用户消息
        user_message = f"请分析以下新闻内容，生成摘要和标签：\n\n{news_content}"
        
        try:
            # 调用智谱API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,  # 较低的温度以获得更稳定的输出
                max_tokens=500,
                response_format={"type": "json_object"}  # 确保返回JSON格式
            )
            
            # 解析响应
            result_text = response.choices[0].message.content
            
            # 解析JSON
            result = json.loads(result_text)
            
            # 验证结果格式
            if "summary" not in result or "tags" not in result:
                raise ValueError("API response missing required fields")
            
            if not isinstance(result["tags"], list) or len(result["tags"]) != 3:
                raise ValueError("Tags must be a list with exactly 3 items")
            
            # 确保摘要长度在合理范围内
            summary = result["summary"].strip()
            if len(summary) < 50 or len(summary) > 200:
                # 如果摘要长度不合适，可以重新处理
                summary = self._adjust_summary_length(summary)
            
            return {
                "summary": summary,
                "tags": [tag.strip() for tag in result["tags"]]
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse API response as JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"API call failed: {e}")
    
    def _adjust_summary_length(self, summary: str) -> str:
        """
        调整摘要长度到50-100字
        """
        # 简单的中文字数统计（一个中文字符算一个字）
        chinese_chars = [c for c in summary if '\u4e00' <= c <= '\u9fff']
        char_count = len(chinese_chars)
        
        if char_count < 50:
            # 如果太短，添加一些通用描述
            return summary + "。这是一篇重要的新闻报道，涉及多个方面的内容。"
        elif char_count > 100:
            # 如果太长，截断到100字左右
            # 找到第100个中文字符的位置
            chinese_count = 0
            for i, char in enumerate(summary):
                if '\u4e00' <= char <= '\u9fff':
                    chinese_count += 1
                    if chinese_count >= 100:
                        # 确保在句子结束处截断
                        for j in range(i, len(summary)):
                            if summary[j] in ['。', '！', '？', '；', '，']:
                                return summary[:j+1]
                        return summary[:i+1] + "。"
            return summary
        
        return summary
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 发送一个简单的测试请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=10
            )
            return response.choices[0].message.content is not None
        except Exception:
            return False


# 对外提供的函数接口
def get_news_summary_and_tags(news_content: str) -> Dict[str, any]:
    """
    获取新闻摘要和标签（对外接口）
    """
    if not news_content or not news_content.strip():
        raise ValueError("News content cannot be empty")
    
    service = LLMService()
    return service.get_news_summary_and_tags(news_content)

