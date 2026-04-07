"""
智谱向量化服务
用于新闻正文和用户提问的向量化，统一使用智谱embedding-2模型
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
from openai import OpenAI


class EmbeddingService:
    """智谱向量化服务类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化向量化服务
        
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
        
        # 向量模型配置
        self.model = "embedding-2"
        
    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量表示
        
        Args:
            text: 需要向量化的文本（新闻正文或用户提问）
            
        Returns:
            List[float]: 文本的向量表示
            
        Raises:
            ValueError: 如果文本为空或只包含空白字符
            RuntimeError: 如果API调用失败
        """
        # 验证输入文本
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        
        try:
            # 调用智谱向量化API
            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip(),
                encoding_format="float"  # 确保返回浮点数列表
            )
            
            # 提取向量数据
            embedding = response.data[0].embedding
            
            # 验证向量维度（embedding-2模型通常是1024维）
            if not embedding or len(embedding) == 0:
                raise RuntimeError("API returned empty embedding")
            
            return embedding
            
        except Exception as e:
            # 包装异常，提供更清晰的错误信息
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg or "余额不足" in error_msg:
                raise RuntimeError("API rate limit exceeded or insufficient balance. Please check your API key balance.") from e
            elif "authentication" in error_msg or "api key" in error_msg or "401" in error_msg:
                raise RuntimeError("API authentication failed. Please check your ZHIPU_API_KEY.") from e
            elif "timeout" in error_msg:
                raise RuntimeError("API request timeout. Please check your network connection.") from e
            else:
                raise RuntimeError(f"Failed to get embedding: {e}") from e
            
    '''
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量获取文本的向量表示
        
        Args:
            texts: 需要向量化的文本列表
            
        Returns:
            List[List[float]]: 每个文本的向量表示列表
            
        Raises:
            ValueError: 如果文本列表为空或包含空文本
            RuntimeError: 如果API调用失败
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # 过滤空文本
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty or whitespace only")
        
        if len(valid_texts) != len(texts):
            print(f"Warning: {len(texts) - len(valid_texts)} empty texts were filtered out")
        
        try:
            # 调用智谱向量化API（批量）
            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                encoding_format="float"
            )
            
            # 提取所有向量数据
            embeddings = [data.embedding for data in response.data]
            
            # 验证返回的向量数量与输入文本数量一致
            if len(embeddings) != len(valid_texts):
                raise RuntimeError(f"API returned {len(embeddings)} embeddings, expected {len(valid_texts)}")
            
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Failed to get batch embeddings: {e}") from e
    '''
    


# 对外提供的函数接口
def get_embedding(text: str) -> List[float]:
    """
    获取文本的向量表示（对外接口）
    
    Args:
        text: 需要向量化的文本（新闻正文或用户提问）
        
    Returns:
        List[float]: 文本的向量表示
        
    Raises:
        ValueError: 如果文本为空或只包含空白字符
        RuntimeError: 如果API调用失败
        
    Example:
        >>> from embedding_service import get_embedding
        >>> vector = get_embedding("今天有什么重要新闻？")
        >>> print(f"向量维度: {len(vector)}")
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty or whitespace only")
    
    service = EmbeddingService()
    return service.get_embedding(text)

'''
def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    批量获取文本的向量表示（对外接口）
    
    Args:
        texts: 需要向量化的文本列表
        
    Returns:
        List[List[float]]: 每个文本的向量表示列表
        
    Raises:
        ValueError: 如果文本列表为空或包含空文本
        RuntimeError: 如果API调用失败
        
    Example:
        >>> from embedding_service import get_embeddings_batch
        >>> vectors = get_embeddings_batch(["新闻1", "新闻2", "问题"])
        >>> print(f"获取了 {len(vectors)} 个向量")
    """
    if not texts:
        raise ValueError("Texts list cannot be empty")
    
    service = EmbeddingService()
    return service.get_embeddings_batch(texts)
'''


        
   