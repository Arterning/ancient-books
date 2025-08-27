
# services/translation_service.py
import openai
from typing import List
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    """翻译服务类"""
    
    def __init__(self, api_key: str = None):
        if api_key:
            openai.api_key = api_key
    
    def translate_text(self, text: str, target_language: str = 'zh-cn') -> str:
        """
        翻译文本
        
        Args:
            text: 待翻译文本
            target_language: 目标语言
            
        Returns:
            str: 翻译结果
        """
        try:
            if target_language == 'zh-cn':
                prompt = f"请将以下古文翻译成现代简体中文，保持原意，语言流畅自然：\n\n{text}"
            elif target_language == 'en':
                prompt = f"Please translate the following classical Chinese text into English, maintaining the original meaning:\n\n{text}"
            else:
                prompt = f"请翻译以下文本：\n\n{text}"
            
            # 这里可以替换为其他翻译API，如百度翻译、腾讯翻译等
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的古文翻译专家。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            translation = response.choices[0].message.content.strip()
            return translation
            
        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            return f"翻译失败: {str(e)}"
    
    def batch_translate(self, texts: List[str], target_language: str = 'zh-cn') -> List[str]:
        """
        批量翻译
        
        Args:
            texts: 待翻译文本列表
            target_language: 目标语言
            
        Returns:
            List[str]: 翻译结果列表
        """
        translations = []
        for text in texts:
            translation = self.translate_text(text, target_language)
            translations.append(translation)
        
        return translations