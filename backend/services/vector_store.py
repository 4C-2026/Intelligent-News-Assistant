"""
新闻RAG系统的向量存储与检索模块
封装Chroma向量库的操作，实现新闻向量的存储和检索
"""

import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# 添加services目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))
#  固定项目根目录（永远不变，不随运行目录变化）
PROJECT_ROOT = Path(__file__).parent.parent  # vector_store.py 在 backend/services/ → 回到根目录
FIXED_CHROMA_DIR = str(PROJECT_ROOT / "chroma_db")  #  固定向量库路径

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("错误: 未安装chromadb，请运行: pip install chromadb")
    sys.exit(1)

from embedding_service import get_embedding


class VectorStore:
    """
    向量存储类，封装Chroma向量数据库的操作
    
    功能：
    1. 单篇新闻存入向量库
    2. 批量新闻存入向量库  
    3. 根据向量进行相似度检索
    
    元数据存储：
    - article_id: 新闻在数据库的唯一ID（对应Article.id）
    """
    
    def __init__(self, persist_directory: str = FIXED_CHROMA_DIR, collection_name: str = "news_collection"):
        """
        初始化Chroma向量数据库连接
        
        Args:
            persist_directory: 向量数据库持久化存储目录
            collection_name: 集合名称，用于存储新闻向量
        """
        # 确保存储目录存在
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(allow_reset=True)
        )
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # 获取或创建集合
        try:
            # 尝试获取现有集合
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✅ 已加载现有向量集合: {collection_name}")
        except Exception:
            # 创建新集合
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "新闻向量存储集合"}
            )
            print(f"✅ 已创建新向量集合: {collection_name}")
    
    def add_news(self, article_id: int, content: str) -> bool:
        """
        单篇新闻添加到向量库
        
        Args:
            article_id: 新闻在数据库的唯一ID
            content: 新闻正文内容
            
        Returns:
            bool: 添加是否成功
            
        Raises:
            ValueError: 如果输入参数无效
            RuntimeError: 如果向量化或存储失败
        """
        # 参数验证
        if not content or not content.strip():
            raise ValueError("新闻内容不能为空")
        
        if not isinstance(article_id, int) or article_id <= 0:
            raise ValueError("article_id必须是正整数")
        
        try:
            # 获取新闻内容的向量
            print(f"🔍 正在向量化新闻 (ID: {article_id})...")
            embedding = get_embedding(content)
            
            # 准备元数据（只存储article_id）
            metadata = {
                "article_id": article_id
            }
            
            # 添加到向量库
            self.collection.add(
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[str(article_id)]  # Chroma ID使用字符串格式
            )
            
            print(f"✅ 新闻已添加到向量库 (ID: {article_id})")
            return True
            
        except Exception as e:
            error_msg = f"添加新闻到向量库失败: {e}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e
    
    def add_news_batch(self, news_list: List[Dict[str, Any]]) -> bool:
        """
        批量添加新闻到向量库
        
        Args:
            news_list: 新闻列表，每个元素是包含article_id, content的字典
            
        Returns:
            bool: 批量添加是否成功
            
        Raises:
            ValueError: 如果输入参数无效
            RuntimeError: 如果向量化或存储失败
            
        Example:
            >>> news_list = [
            ...     {"article_id": 1, "content": "新闻内容1"},
            ...     {"article_id": 2, "content": "新闻内容2"},
            ... ]
            >>> vector_store.add_news_batch(news_list)
        """
        if not news_list:
            raise ValueError("新闻列表不能为空")
        
        # 验证新闻列表格式
        for i, news in enumerate(news_list):
            if not isinstance(news, dict):
                raise ValueError(f"第{i+1}个新闻不是字典格式")
            
            required_keys = ["article_id", "content"]
            for key in required_keys:
                if key not in news:
                    raise ValueError(f"第{i+1}个新闻缺少'{key}'字段")
            
            if not isinstance(news["article_id"], int) or news["article_id"] <= 0:
                raise ValueError(f"第{i+1}个新闻的article_id必须是正整数")
            
            if not news["content"] or not str(news["content"]).strip():
                raise ValueError(f"第{i+1}个新闻的内容不能为空")
        
        try:
            print(f"🔍 正在批量处理 {len(news_list)} 篇新闻...")
            
            # 批量获取向量
            contents = [str(news["content"]).strip() for news in news_list]
            embeddings = []
            
            # 循环处理每篇新闻的向量化
            for i, content in enumerate(contents):
                print(f"  正在向量化第 {i+1}/{len(contents)} 篇新闻...")
                embedding = get_embedding(content)
                embeddings.append(embedding)
            
            # 准备元数据（只存储article_id）和ID
            metadatas = []
            ids = []
            
            for news in news_list:
                metadata = {
                    "article_id": news["article_id"]
                }
                metadatas.append(metadata)
                ids.append(str(news["article_id"]))
            
            # 批量添加到向量库
            self.collection.add(
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ 批量添加成功！共添加 {len(news_list)} 篇新闻到向量库")
            return True
            
        except Exception as e:
            error_msg = f"批量添加新闻到向量库失败: {e}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e
    
    def search_by_vector(self, vector: List[float], n_results: int = 5) -> List[int]:
        """
        根据向量检索相似新闻
        
        Args:
            vector: 查询向量
            n_results: 返回的最相似新闻数量，默认5条
            
        Returns:
            List[int]: 相似新闻的ID列表（article_id）
                
        Raises:
            ValueError: 如果向量为空或n_results无效
            RuntimeError: 如果检索失败
        """
        if not vector:
            raise ValueError("查询向量不能为空")
        
        if n_results <= 0:
            raise ValueError("n_results必须大于0")
        
        try:
            # 在向量库中搜索相似新闻
            print(f"🔍 正在检索最相似的 {n_results} 条新闻...")
            results = self.collection.query(
                query_embeddings=[vector],
                n_results=n_results,
                include=["metadatas"]
            )
            
            # 解析结果，只返回article_id列表
            article_ids = []
            
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    metadata = results["metadatas"][0][i]
                    article_ids.append(int(metadata["article_id"]))
            
            print(f"✅ 检索完成，找到 {len(article_ids)} 条相似新闻")
            return article_ids
            
        except Exception as e:
            error_msg = f"检索相似新闻失败: {e}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e
    

# ============================================================================
# 对外函数接口
# ============================================================================

# 全局VectorStore实例
_vector_store_instance = None

def _get_vector_store() -> VectorStore:
    """
    获取全局VectorStore实例（单例模式）
    
    Returns:
        VectorStore: 全局向量存储实例
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance

def add_news(article_id: int, content: str) -> bool:
    """
    单篇新闻存入向量库（对外接口）
    
    Args:
        article_id: 新闻在数据库的唯一ID
        content: 新闻正文内容
        
    Returns:
        bool: 添加是否成功
        
    Raises:
        ValueError: 如果输入参数无效
        RuntimeError: 如果向量化或存储失败
        
    Example:
        >>> from vector_store import add_news
        >>> success = add_news(1, "这是一篇新闻内容...")
        >>> print(f"添加结果: {success}")
    """
    vector_store = _get_vector_store()
    return vector_store.add_news(article_id, content)

def add_news_batch(news_list: List[Dict[str, Any]]) -> bool:
    """
    批量新闻存入向量库（对外接口）
    
    Args:
        news_list: 新闻列表，每个元素是包含article_id, content的字典
        
    Returns:
        bool: 批量添加是否成功
        
    Raises:
        ValueError: 如果输入参数无效
        RuntimeError: 如果向量化或存储失败
        
    Example:
        >>> from vector_store import add_news_batch
        >>> news_list = [
        ...     {"article_id": 1, "content": "新闻内容1"},
        ...     {"article_id": 2, "content": "新闻内容2"},
        ... ]
        >>> success = add_news_batch(news_list)
        >>> print(f"批量添加结果: {success}")
    """
    vector_store = _get_vector_store()
    return vector_store.add_news_batch(news_list)

def search_by_vector(vector: List[float], n_results: int = 5) -> List[int]:
    """
    根据向量检索相似新闻（对外接口）
    
    Args:
        vector: 查询向量
        n_results: 返回的最相似新闻数量，默认5条
        
    Returns:
        List[int]: 相似新闻的ID列表（article_id）
            
    Raises:
        ValueError: 如果向量为空或n_results无效
        RuntimeError: 如果检索失败
        
    Example:
        >>> from vector_store import search_by_vector
        >>> from embedding_service import get_embedding
        >>> 
        >>> # 先获取查询文本的向量
        >>> query_vector = get_embedding("今天有什么重要新闻？")
        >>> 
        >>> # 检索相似新闻
        >>> results = search_by_vector(query_vector, n_results=3)
        >>> print(f"找到 {len(results)} 条相似新闻: {results}")
    """
    vector_store = _get_vector_store()
    return vector_store.search_by_vector(vector, n_results)
