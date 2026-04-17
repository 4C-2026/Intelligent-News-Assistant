"""
智能新闻助手会话RAG核心服务
基于检索增强生成（RAG）的会话式新闻问答系统
支持多轮上下文对话和查询重构
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

# 添加services目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from embedding_service import get_embedding
from vector_store import search_by_vector
from dotenv import load_dotenv
from openai import OpenAI

# 导入数据库相关模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import SessionLocal
from models.article import Article


@dataclass
class Message:
    """对话消息数据类"""
    role: str  # "user" 或 "assistant"
    content: str


class SessionRAGService:
    """
    会话RAG核心服务类
    实现基于检索增强生成的会话式新闻问答功能
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化会话RAG服务
        
        Args:
            api_key: 智谱API密钥，如果为None则从环境变量读取
        """
        # 加载环境变量
        load_dotenv()
        
        # 获取API密钥
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
        
        # 向量检索配置
        self.top_k = 3  # 检索最相关的3篇新闻
        
        # 查询重构配置
        self.query_reconstruction_temperature = 0.1  # 较低温度以获得更稳定的查询重构
        
        # 最终回答生成配置
        self.answer_generation_temperature = 0.3
        
        # 导入增强提示词系统
        try:
            from enhanced_rag_prompts import EnhancedRAGPrompts
            self.enhanced_prompts = EnhancedRAGPrompts()
            print("✅ 已启用增强版RAG提示词系统")
        except ImportError as e:
            raise ImportError(f"无法导入增强提示词系统: {e}")
    
    def _reconstruct_query(self, messages: List[Dict[str, str]]) -> str:
        """
        重构查询语句
        基于对话历史，使用大模型生成完整、清晰、可直接检索的查询语句
        
        Args:
            messages: 完整的对话历史消息数组，格式为 [{"role": str, "content": str}, ...]
            
        Returns:
            str: 重构后的查询语句
            
        Raises:
            RuntimeError: 如果查询重构失败
        """
        try:
            # 构建查询重构的提示词
            system_prompt = """你是一个专业的查询重构助手。你的任务是根据对话历史，将用户的当前问题重构为完整、清晰、可直接用于信息检索的查询语句。

要求：
1. 理解对话的上下文和背景
2. 将省略、指代或不完整的表达重构为完整的查询
3. 保持查询的准确性和相关性
4. 输出必须是单一的、可直接用于检索的查询语句
5. 使用中文

示例：
对话历史：
- 用户：俄罗斯和乌克兰的冲突有什么最新进展？
- 助手：根据相关新闻，俄罗斯和乌克兰的冲突在...
- 用户：乌克兰呢？

重构查询：乌克兰在俄乌冲突中的最新情况和地位

请根据以下对话历史重构查询："""
            
            # 将对话历史格式化为文本
            conversation_text = ""
            for msg in messages:
                role = "用户" if msg["role"] == "user" else "助手"
                conversation_text += f"- {role}: {msg['content']}\n"
            
            user_prompt = f"{conversation_text}\n重构查询："
            
            # 调用大模型进行查询重构
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.query_reconstruction_temperature,
                max_tokens=100
            )
            
            reconstructed_query = response.choices[0].message.content.strip()
            
            # 清理查询结果
            if reconstructed_query.startswith("重构查询："):
                reconstructed_query = reconstructed_query.replace("重构查询：", "").strip()
            
            print(f"🔍 原始问题: '{messages[-1]['content']}'")
            print(f"🔍 重构查询: '{reconstructed_query}'")
            
            return reconstructed_query
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                raise RuntimeError("API调用频率限制，请稍后重试")
            elif "authentication" in error_msg or "api key" in error_msg:
                raise RuntimeError("API认证失败，请检查API密钥")
            elif "timeout" in error_msg:
                raise RuntimeError("API请求超时，请检查网络连接")
            else:
                raise RuntimeError(f"查询重构失败: {e}")
    
    def _get_news_content_by_id(self, article_id: int) -> str:
        """
        根据article_id获取新闻内容（从数据库查询）
        
        Args:
            article_id: 新闻ID
            
        Returns:
            str: 新闻正文内容
            
        Raises:
            ValueError: 如果article_id不存在于数据库中
        """
        # 创建数据库会话
        db = SessionLocal()
        try:
            # 查询数据库中的新闻
            article = db.query(Article).filter(Article.id == article_id).first()
            
            if not article:
                raise ValueError(f"Article ID {article_id} not found in database")
            
            return article.content
        finally:
            # 确保关闭数据库会话
            db.close()
    
    def _build_prompt(self, messages: List[Dict[str, str]], context: str) -> Tuple[str, str]:
        """
        构建问答Prompt，包含对话历史和新闻上下文
        
        Args:
            messages: 完整的对话历史消息数组
            context: 检索到的新闻上下文
            
        Returns:
            Tuple[str, str]: (system_prompt, user_prompt)
        """
        # 只使用增强提示词系统
        return self._build_enhanced_prompt(messages, context)
    
    
    def _build_enhanced_prompt(self, messages: List[Dict[str, str]], context: str) -> Tuple[str, str]:
        """
        构建增强版问答Prompt，使用自适应提示词系统
        
        Args:
            messages: 完整的对话历史消息数组
            context: 检索到的新闻上下文
            
        Returns:
            Tuple[str, str]: (system_prompt, user_prompt)
        """
        # 将对话历史格式化为文本（排除最后一条用户消息）
        conversation_history = ""
        for i, msg in enumerate(messages[:-1]):  # 排除最后一条用户消息
            role = "用户" if msg["role"] == "user" else "助手"
            conversation_history += f"{role}: {msg['content']}\n"
        
        # 获取当前用户问题
        current_question = messages[-1]["content"] if messages else ""
        
        # 分析问题类型和用户风格
        question_analysis = self._analyze_question(current_question)
        
        print(f"🔍 增强提示词分析:")
        print(f"  问题类型: {question_analysis['query_type']} ({question_analysis['template_name']})")
        print(f"  置信度: {question_analysis['confidence']:.2f}")
        print(f"  用户风格: {question_analysis['user_style']}")
        print(f"  回答结构: {question_analysis['template_structure']}")
        
        # 构建系统提示词
        system_prompt = self.enhanced_prompts.build_system_prompt(
            question_analysis["query_type"],
            question_analysis["user_style"]
        )
        
        # 构建用户提示词
        user_prompt = self.enhanced_prompts.build_user_prompt(
            conversation_history,
            current_question,
            context
        )
        
        return system_prompt, user_prompt
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """
        分析用户问题（增强提示词系统专用）
        
        Args:
            question: 用户问题
            
        Returns:
            Dict: 包含问题分析结果
        """
        # 检测问题类型
        query_type, confidence = self.enhanced_prompts.detect_query_type(question)
        
        # 检测用户风格
        user_style = self.enhanced_prompts.detect_user_style(question)
        
        # 获取回答模板信息
        template_info = self.enhanced_prompts.get_answer_template(query_type)
        
        return {
            "query_type": query_type,
            "confidence": confidence,
            "user_style": user_style,
            "template_name": template_info["name"],
            "template_structure": template_info["structure"]
        }
    
    def _call_llm_for_answer(self, prompt: Tuple[str, str]) -> str:
        """
        调用大模型生成答案
        
        Args:
            prompt: 增强提示词格式的元组(system_prompt, user_prompt)
            
        Returns:
            str: 模型生成的答案
        """
        try:
            # 增强提示词格式：元组(system_prompt, user_prompt)
            system_prompt, user_prompt = prompt
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.answer_generation_temperature,
                max_tokens=1000  # 增加token限制以容纳结构化回答
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                raise RuntimeError("API调用频率限制，请稍后重试")
            elif "authentication" in error_msg or "api key" in error_msg:
                raise RuntimeError("API认证失败，请检查API密钥")
            elif "timeout" in error_msg:
                raise RuntimeError("API请求超时，请检查网络连接")
            else:
                raise RuntimeError(f"调用大模型失败: {e}")
    
    def answer_question_with_history(self, messages: List[Dict[str, str]]) -> str:
        """
        会话RAG核心功能：基于对话历史回答用户问题
        
        流程：
        1. 验证输入和对话历史
        2. 使用大模型重构查询语句
        3. 将重构后的查询进行向量化
        4. 在向量库中进行相似度检索，得到最相关的article_id
        5. 根据article_id获取新闻正文内容
        6. 将对话历史 + 新闻上下文 + 当前问题拼接成Prompt
        7. 调用大模型生成回答
        8. 返回最终答案（字符串）
        
        Args:
            messages: 完整的对话历史消息数组，格式为 [{"role": str, "content": str}, ...]
                    最后一条消息必须是用户消息
            
        Returns:
            str: 最终答案
                
        Raises:
            ValueError: 如果问题为空或消息格式无效
            RuntimeError: 如果向量化、检索或模型调用失败
        """
        import time
        start_time = time.time()
        
        # 1. 验证输入
        if not messages:
            raise ValueError("对话历史不能为空")
        
        # 检查最后一条消息是否是用户消息
        if messages[-1]["role"] != "user":
            raise ValueError("最后一条消息必须是用户消息")
        
        current_question = messages[-1]["content"].strip()
        if not current_question:
            raise ValueError("用户问题不能为空")
        
        print(f"🔍 处理会话问题: '{current_question}'")
        print(f"🔍 对话历史长度: {len(messages)} 条消息")
        
        try:
            # 2. 重构查询语句
            print("  正在重构查询语句...")
            reconstructed_query = self._reconstruct_query(messages)
            
            # 3. 将重构后的查询进行向量化
            print("  正在向量化重构查询...")
            query_vector = get_embedding(reconstructed_query)
            
            # 4. 在向量库中进行相似度检索
            print(f"  正在检索最相关的 {self.top_k} 篇新闻...")
            relevant_items = search_by_vector(query_vector, n_results=self.top_k)
            
            if not relevant_items:
                return "抱歉，目前没有找到相关的新闻内容来回答您的问题。"
            
            # 提取文章ID列表
            relevant_article_ids = [item[0] for item in relevant_items]
            print(f"  找到相关新闻ID: {relevant_article_ids}")
            
            # 5. 获取新闻内容
            context_parts = []
            for article_id in relevant_article_ids:
                try:
                    content = self._get_news_content_by_id(article_id)
                    # 移除新闻ID信息，避免泄露内部字段（与增强版本保持一致）
                    context_parts.append(f"{content}\n")
                except ValueError:
                    print(f"  警告: 新闻ID {article_id} 不存在于数据库中")
                    continue
            
            if not context_parts:
                return "抱歉，检索到的新闻内容暂时无法访问。"
            
            context = "\n".join(context_parts)
            
            # 6. 分析问题类型和用户风格
            print("  分析问题类型和用户风格...")
            question_analysis = self._analyze_question(current_question)
            
            # 7. 构建Prompt
            print("  构建Prompt...")
            prompt = self._build_prompt(messages, context)
            
            # 8. 调用大模型生成回答
            print("  调用大模型生成答案...")
            answer = self._call_llm_for_answer(prompt)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            print(f"✅ 会话问题处理完成，耗时: {processing_time:.2f}秒")
            if question_analysis:
                print(f"✅ 问题类型: {question_analysis['query_type']}")
                print(f"✅ 用户风格: {question_analysis['user_style']}")
            
            return answer
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            raise RuntimeError(f"会话RAG处理失败: {e}") from e
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 测试结果
        """
        try:
            # 测试智谱API连接
            print("🔍 测试智谱API连接...")
            
            # 发送一个简单的测试请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个测试助手，请回复'连接成功'。"},
                    {"role": "user", "content": "请回复'连接成功'"}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            # 检查响应
            if response.choices[0].message.content.strip() == "连接成功":
                print("✅ API连接测试成功")
                return True
            else:
                print(f"⚠️ API响应异常: {response.choices[0].message.content}")
                return False
                
        except Exception as e:
            print(f"❌ API连接测试失败: {e}")
            return False


# 对外提供的函数接口
def answer_question_with_history(messages: List[Dict[str, str]]) -> str:
    """
    会话RAG问答功能（对外接口）
    
    Args:
        messages: 完整的对话历史消息数组，格式为 [{"role": str, "content": str}, ...]
                最后一条消息必须是用户消息
        
    Returns:
        str: 最终答案
            
    Raises:
        ValueError: 如果问题为空或消息格式无效
        RuntimeError: 如果向量化、检索或模型调用失败
        
    Example:
        >>> from session_rag_service import answer_question_with_history
        >>> messages = [
        ...     {"role": "user", "content": "俄罗斯和乌克兰的冲突有什么最新进展？"},
        ...     {"role": "assistant", "content": "根据相关新闻，俄罗斯和乌克兰的冲突在..."},
        ...     {"role": "user", "content": "乌克兰呢？"}
        ... ]
        >>> answer = answer_question_with_history(messages)
        >>> print(f"答案: {answer}")
    """
    if not messages:
        raise ValueError("对话历史不能为空")
    
    if messages[-1]["role"] != "user":
        raise ValueError("最后一条消息必须是用户消息")
    
    service = SessionRAGService()
    return service.answer_question_with_history(messages)


def test_session_rag_service() -> bool:
    """
    测试会话RAG服务连接
    
    Returns:
        bool: 连接是否成功
    """
    try:
        service = SessionRAGService()
        return service.test_connection()
    except Exception:
        return False


