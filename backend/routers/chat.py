from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services"))

from session_rag_service import answer_question_with_history

router = APIRouter(prefix="/api", tags=["chat"])


class ChatMessage(BaseModel):
    role: str  # "user"或"assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]  # 完整的对话历史消息数组


class ChatResponse(BaseModel):
    code: int
    message: str
    data: Dict[str, Any]


@router.post("/chat", response_model=ChatResponse)
async def chat_with_session_rag(request: ChatRequest):
    try:
        if not request.messages:
            return ChatResponse(
                code=400,
                message="对话历史不能为空",
                data={"answer": ""}
            )
        
    
        if request.messages[-1].role != "user":
            return ChatResponse(
                code=400,
                message="最后一条消息必须是用户消息",
                data={"answer": ""}
            )
        
       
        if not request.messages[-1].content or not request.messages[-1].content.strip():
            return ChatResponse(
                code=400,
                message="用户问题不能为空",
                data={"answer": ""}
            )
        
        # 将Pydantic模型转换为字典列表
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        
        answer = answer_question_with_history(messages_dict)
        
      
        return ChatResponse(
            code=0,
            message="success",
            data={"answer": answer}
        )
        
    except ValueError as e:
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
