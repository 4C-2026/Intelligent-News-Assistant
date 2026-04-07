"""
智能新闻助手 - 增强版RAG提示词系统
统一但能自适应场景的提示词框架，支持三类问题自动识别和回答模板
"""

from typing import Dict, List, Optional, Tuple
import re


class EnhancedRAGPrompts:
    """
    增强版RAG提示词系统
    支持三类问题自动识别 + 对应回答模板 + 信息可信度强制标注
    """
    
    def __init__(self):
        # 问题类型识别关键词
        self.query_type_keywords = {
            "资讯查询": [
                "最近", "今天", "昨天", "本周", "本月", "最新", "有什么新闻", "新闻", "报道", "消息",
                "发生了什么", "大事", "热点", "头条", "要闻", "资讯", "动态", "进展", "情况"
            ],
            "深度分析": [
                "为什么", "原因", "影响", "后果", "意义", "价值", "作用", "趋势", "未来", "发展",
                "分析", "解读", "看法", "观点", "评价", "评估", "预测", "展望", "前景", "走向",
                "如何", "怎样", "解决方案", "对策", "建议", "措施", "方法", "途径"
            ],
            "闲聊开放": [
                "你还知道", "有什么好看", "推荐", "有意思", "有趣", "好玩", "随便聊聊", "聊聊",
                "说说", "谈谈", "讲一讲", "介绍一下", "还有什么", "其他", "别的", "更多",
                "随便", "随意", "都可以", "无所谓", "不知道问什么"
            ]
        }
        
        # 用户提问风格识别
        self.formal_keywords = [
            "请问", "请教", "咨询", "询问", "了解", "获取", "查询", "查找", "搜索",
            "能否", "可否", "是否可以", "麻烦", "劳烦", "辛苦", "感谢", "谢谢"
        ]
        
        self.casual_keywords = [
            "呢", "啊", "呀", "嘛", "吧", "哈", "嘿", "哦", "哟", "喂",
            "咋", "怎么", "怎么样", "啥", "什么", "干嘛", "干啥"
        ]
        
        # 信息可信度标注模板
        self.credibility_templates = {
            "fact": "✅ 据新闻报道",
            "analysis": "📊 结合新闻内容分析",
            "insufficient": "⚠️ 现有新闻未提及该细节"
        }
    
    def detect_query_type(self, question: str) -> Tuple[str, float]:
        """
        检测问题类型
        返回: (类型, 置信度)
        """
        question_lower = question.lower()
        
        scores = {
            "资讯查询": 0.0,
            "深度分析": 0.0,
            "闲聊开放": 0.0
        }
        
        # 关键词匹配
        for q_type, keywords in self.query_type_keywords.items():
            for keyword in keywords:
                if keyword in question_lower:
                    scores[q_type] += 1.0
        
        # 特殊模式匹配
        if re.search(r'最近.*[有没].*新闻', question_lower):
            scores["资讯查询"] += 2.0
        if re.search(r'今天.*[有没].*大事', question_lower):
            scores["资讯查询"] += 2.0
        if re.search(r'为什么.*[会能]', question_lower):
            scores["深度分析"] += 2.0
        if re.search(r'影响.*[是什么如何]', question_lower):
            scores["深度分析"] += 2.0
        if re.search(r'你还知道.*什么', question_lower):
            scores["闲聊开放"] += 2.0
        if re.search(r'有什么.*推荐', question_lower):
            scores["闲聊开放"] += 2.0
        
        # 找到最高分类型
        max_score = max(scores.values())
        if max_score == 0:
            return "资讯查询", 0.5  # 默认类型
        
        for q_type, score in scores.items():
            if score == max_score:
                confidence = min(score / 5.0, 1.0)  # 归一化到0-1
                return q_type, confidence
    
    def detect_user_style(self, question: str) -> str:
        """
        检测用户提问风格
        返回: "formal" 或 "casual"
        """
        question_lower = question.lower()
        
        formal_count = sum(1 for keyword in self.formal_keywords if keyword in question_lower)
        casual_count = sum(1 for keyword in self.casual_keywords if keyword in question_lower)
        
        # 如果包含正式关键词，优先判断为正式风格
        if formal_count > 0:
            return "formal"
        elif casual_count > 0:
            return "casual"
        else:
            # 默认根据句子长度、标点和用词判断
            # 包含"请"、"您"等敬语判断为正式
            if "请" in question or "您" in question or "请教" in question or "咨询" in question:
                return "formal"
            # 长句子且使用句号判断为正式
            elif len(question) > 15 and "。" in question:
                return "formal"
            else:
                return "casual"
    
    def get_answer_template(self, query_type: str) -> Dict[str, str]:
        """
        获取对应问题类型的回答模板
        """
        templates = {
            "资讯查询": {
                "name": "资讯查询类",
                "structure": "核心结论 + 分点梳理 + 来源引导",
                "template": """基于检索到的新闻内容，我将为您梳理相关信息：

{credibility_prefix}【核心结论】
{main_conclusion}

{credibility_prefix}【分点梳理】
1. {point_1}
2. {point_2}
3. {point_3}

{credibility_prefix}【来源引导】
以上信息主要来源于近期关于{news_topic}的相关报道。如需了解更多细节，可以关注后续的新闻报道。"""
            },
            "深度分析": {
                "name": "深度分析类",
                "structure": "背景 → 原因 → 影响 → 趋势",
                "template": """针对您的问题，我结合新闻内容进行以下分析：

{credibility_prefix}【背景概述】
{background}

{credibility_prefix}【主要原因】
{reasons}

{credibility_prefix}【潜在影响】
{impacts}

{credibility_prefix}【未来趋势】
{trends}

以上分析基于现有新闻报道，实际情况可能因后续发展而有所变化。"""
            },
            "闲聊开放": {
                "name": "闲聊开放类",
                "structure": "总结 + 引导 + 兴趣推荐",
                "template": """很高兴与您交流！根据您的问题，我结合新闻内容提供以下信息：

{credibility_prefix}【相关总结】
{summary}

{credibility_prefix}【话题引导】
{guidance}

{credibility_prefix}【兴趣推荐】
如果您对以下话题感兴趣，我可以为您查找更多相关信息：
1. {topic_1}
2. {topic_2}
3. {topic_3}

有什么其他想了解的吗？我很乐意继续为您服务！"""
            }
        }
        
        return templates.get(query_type, templates["资讯查询"])
    
    def get_credibility_prefix(self, info_type: str) -> str:
        """
        获取信息可信度标注前缀
        """
        return self.credibility_templates.get(info_type, self.credibility_templates["fact"])
    
    def build_system_prompt(self, query_type: str, user_style: str) -> str:
        """
        构建系统提示词
        """
        # 基础角色定义
        base_role = """你是一个专业的新闻助手，专门基于新闻内容进行问答。你的核心职责是：
1. 严格基于提供的新闻内容回答问题，严禁编造新闻中没有的事实、数据、原因
2. 保持回答的专业性、严谨性和可信度
3. 根据用户提问风格调整回答语气，做到自然流畅、不机械、不重复
4. 当新闻中没有用户要的信息时，不能简单说"我不知道"，要自然说明信息边界，并给出合理总结与引导
5. 绝对不能泄露任何内部字段，如新闻ID、数据库信息等"""
        
        # 根据用户风格调整语气要求
        style_requirements = {
            "formal": "用户提问较为正式，请使用专业、严谨、正式的语气回答，保持学术性和权威性。",
            "casual": "用户提问较为口语化，请使用自然、温和、亲切的语气回答，像朋友聊天一样自然流畅。"
        }
        
        # 获取回答模板信息
        template_info = self.get_answer_template(query_type)
        
        # 信息可信度标注规则
        credibility_rules = """## 信息可信度强制标注规则（必须严格遵守）：
1. ✅ 事实信息：必须标注「据新闻报道」前缀
2. 📊 分析推导：必须标注「结合新闻内容分析」前缀  
3. ⚠️ 信息不足：必须标注「现有新闻未提及该细节」前缀

标注位置：在每个信息段落或要点前添加相应标注前缀。"""
        
        # 构建完整系统提示词
        system_prompt = f"""{base_role}

## 当前问题类型：{template_info['name']}
**回答结构要求**：{template_info['structure']}

## 用户风格适配：
{style_requirements[user_style]}

{credibility_rules}

## 回答生成流程：
1. 首先分析新闻内容与用户问题的匹配度
2. 根据问题类型选择合适的回答模板结构
3. 为每个信息点添加正确的可信度标注
4. 按照用户风格调整语言表达
5. 确保回答完整、连贯、有价值

## 重要提醒：
- 如果新闻内容中没有直接相关信息，使用「⚠️ 现有新闻未提及该细节」标注，并提供相关背景信息或引导
- 避免使用"根据我的知识"、"我认为"等主观表述，所有信息必须基于新闻内容
- 保持回答的流畅性和自然度，不要显得机械或重复

现在请基于以上要求，结合提供的新闻内容回答用户问题。"""
        
        return system_prompt
    
    def build_user_prompt(self, conversation_history: str, current_question: str, news_context: str) -> str:
        """
        构建用户提示词
        """
        return f"""## 对话历史：
{conversation_history}

## 新闻内容：
{news_context}

## 当前用户问题：
{current_question}

请基于以上新闻内容和对话历史，按照系统提示的要求回答用户问题。"""


# 使用示例
if __name__ == "__main__":
    # 测试代码
    prompts = EnhancedRAGPrompts()
    
    # 测试问题类型检测
    test_questions = [
        "最近科技有什么新闻？",
        "为什么会发生这种情况？影响是什么？",
        "那你还知道啥？有什么好看的新闻？",
        "今天国际有什么大事？"
    ]
    
    print("=== 问题类型检测测试 ===")
    for question in test_questions:
        q_type, confidence = prompts.detect_query_type(question)
        style = prompts.detect_user_style(question)
        print(f"问题: {question}")
        print(f"  类型: {q_type} (置信度: {confidence:.2f})")
        print(f"  风格: {style}")
        print()
    
    # 测试系统提示词生成
    print("\n=== 系统提示词生成测试 ===")
    test_q_type = "资讯查询"
    test_style = "formal"
    system_prompt = prompts.build_system_prompt(test_q_type, test_style)
    print(f"问题类型: {test_q_type}")
    print(f"用户风格: {test_style}")
    print(f"系统提示词长度: {len(system_prompt)} 字符")
    print("\n前500字符预览:")
    print(system_prompt[:500] + "...")