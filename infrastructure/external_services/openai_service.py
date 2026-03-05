"""
OpenAI API集成服务
"""
from typing import Optional, Dict, Any, List
import openai
from shared.config.settings import get_settings

settings = get_settings()

class OpenAIService:
    """OpenAI API服务封装"""
    
    def __init__(self):
        """初始化OpenAI服务"""
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
    
    def evaluate_speech_transcript(self, transcript: str, topic: str = None) -> Dict[str, Any]:
        """
        评估口语 transcript 并返回详细评估结果
        
        Args:
            transcript: 口语转文本内容
            topic: 相关话题（可选）
            
        Returns:
            Dict: 包含各项评分和反馈的评估结果
        """
        if not transcript:
            return {"error": "Empty transcript provided"}
        
        # 构建评估提示
        prompt = f"""
        你是一位专业的雅思口语考官，请根据以下 transcript 评估考生的口语表现。
        按照雅思口语评分标准（流利度与连贯性、词汇多样性、语法多样性与准确性、发音）进行评分。
        
        {f"话题: {topic}" if topic else ""}
        Transcript: {transcript}
        
        请提供以下内容：
        1. 总体评分（1-9分）
        2. 各项细分评分（流利度、词汇、语法、发音，每项1-9分）
        3. 详细反馈，包括优点和需要改进的地方
        4. 具体的改进建议
        
        请以JSON格式返回，包含以下字段：
        - overall_score: 总体评分
        - fluency_score: 流利度评分
        - vocabulary_score: 词汇评分
        - grammar_score: 语法评分
        - pronunciation_score: 发音评分
        - strengths: 优点列表
        - weaknesses: 缺点列表
        - suggestions: 改进建议列表
        - feedback: 总体反馈文本
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的雅思口语考官，精通雅思评分标准。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 降低随机性，提高评估一致性
                response_format={"type": "json_object"}
            )
            
            return response['choices'][0]['message']['content']
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_ielts_topic(self, part_type: str = "general", difficulty: str = "medium") -> Dict[str, Any]:
        """
        生成雅思口语话题
        
        Args:
            part_type: 话题类型（general, part1, part2, part3）
            difficulty: 难度级别（easy, medium, hard）
            
        Returns:
            Dict: 包含话题和相关问题的字典
        """
        prompt = f"""
        请生成一个适合雅思口语考试的话题，具体要求如下：
        - 类型：{part_type}
        - 难度：{difficulty}
        - 符合最新雅思考试趋势
        
        请提供以下内容：
        1. 话题标题
        2. 话题描述
        3. 相关问题（根据part类型提供适当数量的问题）
        
        请以JSON格式返回，包含以下字段：
        - title: 话题标题
        - description: 话题描述
        - questions: 问题列表
        - part_type: 话题类型
        - difficulty: 难度级别
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的雅思口语考试命题专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            return response['choices'][0]['message']['content']
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_dialogue_response(self, context: str, user_input: str, dialogue_history: List[Dict[str, str]], 
                                 part_type: str = "general", difficulty: str = "medium") -> str:
        """
        生成雅思口语对话回应
        
        Args:
            context: 对话上下文/话题
            user_input: 用户最新输入
            dialogue_history: 对话历史
            part_type: 对话类型
            difficulty: 难度级别
            
        Returns:
            str: AI考官的回应
        """
        # 构建对话历史提示
        history_prompt = "\n".join([f"{'考官' if turn['speaker'] == 'ai_examiner' else '考生'}: {turn['content']}" 
                                  for turn in dialogue_history])
        
        prompt = f"""
        你正在扮演一位雅思口语考官，进行一场{difficulty}难度的{part_type}部分考试。
        
        话题: {context}
        
        对话历史:
        {history_prompt}
        
        考生最新回答: {user_input}
        
        请根据以下要求生成你的回应：
        1. 保持自然的对话流畅性
        2. 根据考生回答提出相关的跟进问题
        3. 适当调整问题难度，保持挑战性但不过于困难
        4. 使用符合雅思考官风格的语言和提问方式
        5. 回应应简洁明了，引导对话继续进行
        
        请直接输出你的回应内容，不要添加任何额外的标记或说明。
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的雅思口语考官，正在进行口语测试。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response['choices'][0]['message']['content']
            
        except Exception as e:
            return f"抱歉，我无法生成回应。错误：{str(e)}"