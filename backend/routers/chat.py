"""
会话RAG对话接口
提供基于检索增强生成的会话式新闻问答功能
支持多轮上下文对话和查询重构
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import sys
from pathlib import Path

# 添加services目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "services"))

from session_rag_service import answer_question_with_history

# 创建路由器
router = APIRouter(prefix="/api", tags=["chat"])


class ChatMessage(BaseModel):
    """对话消息模型"""
    role: str  # "user" 或 "assistant"
    content: str


class ChatRequest(BaseModel):
    """会话聊天请求模型"""
    messages: List[ChatMessage]  # 完整的对话历史消息数组


class ChatResponse(BaseModel):
    """聊天响应模型"""
    code: int
    message: str
    data: Dict[str, Any]


@router.post("/chat", response_model=ChatResponse)
async def chat_with_session_rag(request: ChatRequest):
    """
    会话RAG对话接口
    
    接收完整的对话历史，调用会话RAG服务生成回答
    
    Args:
        request: 包含完整对话历史的请求体
        
    Returns:
        ChatResponse: 统一格式的响应，包含RAG生成的答案
        
    Example:
        POST /api/chat
        {
            "messages": [
                {"role": "user", "content": "俄罗斯和乌克兰的冲突有什么最新进展？"},
                {"role": "assistant", "content": "根据相关新闻，俄罗斯和乌克兰的冲突在..."},
                {"role": "user", "content": "乌克兰呢？"}
            ]
        }
        
        Response:
        {
            "code": 0,
            "message": "success",
            "data": {
                "answer": "根据相关新闻内容，乌克兰在..."
            }
        }
    """
    try:
        # 验证消息数组是否为空
        if not request.messages:
            return ChatResponse(
                code=400,
                message="对话历史不能为空",
                data={"answer": ""}
            )
        
        # 验证最后一条消息是否是用户消息
        if request.messages[-1].role != "user":
            return ChatResponse(
                code=400,
                message="最后一条消息必须是用户消息",
                data={"answer": ""}
            )
        
        # 验证最后一条消息内容是否为空
        if not request.messages[-1].content or not request.messages[-1].content.strip():
            return ChatResponse(
                code=400,
                message="用户问题不能为空",
                data={"answer": ""}
            )
        
        # 将Pydantic模型转换为字典列表
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # 调用会话RAG服务生成答案
        answer = answer_question_with_history(messages_dict)
        
        # 返回成功响应
        return ChatResponse(
            code=0,
            message="success",
            data={"answer": answer}
        )
        
    except ValueError as e:
        # 输入验证错误
        return ChatResponse(
            code=400,
            message=str(e),
            data={"answer": ""}
        )
        
    except RuntimeError as e:
        # RAG处理错误
        error_msg = str(e)
        if "API调用频率限制" in error_msg:
            return ChatResponse(
                code=429,
                message="API调用频率限制，请稍后重试",
                data={"answer": ""}
            )
        elif "API认证失败" in error_msg:
            return ChatResponse(
                code=401,
                message="API认证失败，请检查API密钥",
                data={"answer": ""}
            )
        elif "API请求超时" in error_msg:
            return ChatResponse(
                code=504,
                message="API请求超时，请检查网络连接",
                data={"answer": ""}
            )
        else:
            return ChatResponse(
                code=500,
                message=f"会话RAG处理失败: {error_msg}",
                data={"answer": ""}
            )
            
    except Exception as e:
        # 其他未知错误
        return ChatResponse(
            code=500,
            message=f"服务器内部错误: {str(e)}",
            data={"answer": ""}
        )


# 健康检查端点
@router.get("/chat/health")
async def health_check():
    """健康检查接口"""
    try:
        # 简单测试会话RAG服务是否可用
        test_messages = [
            {"role": "user", "content": "测试"}
        ]
        _ = answer_question_with_history(test_messages)
        return ChatResponse(
            code=0,
            message="会话RAG服务运行正常",
            data={"status": "healthy"}
        )
    except Exception as e:
        return ChatResponse(
            code=503,
            message=f"会话RAG服务不可用: {str(e)}",
            data={"status": "unhealthy"}
        )


    # 运行测试服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)