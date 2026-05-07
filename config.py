"""AI Drama Studio - 配置管理"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    """全局配置"""
    
    # AI 模型配置
    llm_provider: str = "openai"  # openai / deepseek / dashscope
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    
    # 图片生成配置
    image_provider: str = "dalle"  # dalle / dashscope / local
    image_api_key: str = ""
    image_model: str = "dall-e-3"
    image_size: str = "1024x1792"  # 竖屏9:16
    
    # 语音配置
    voice_provider: str = "edge-tts"  # edge-tts / azure
    voice_api_key: str = ""
    default_voice: str = "zh-CN-YunxiNeural"
    
    # 视频配置
    video_fps: int = 30
    video_resolution: str = "1080x1920"  # 竖屏
    video_duration: int = 60  # 默认60秒
    output_dir: str = "./output"
    temp_dir: str = "./temp"
    
    # FFmpeg
    ffmpeg_path: str = "ffmpeg"
    
    def __post_init__(self):
        """从环境变量加载配置"""
        self.llm_api_key = os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", ""))
        self.image_api_key = os.getenv("IMAGE_API_KEY", self.llm_api_key)
        self.voice_api_key = os.getenv("VOICE_API_KEY", "")
        
        if os.getenv("LLM_BASE_URL"):
            self.llm_base_url = os.getenv("LLM_BASE_URL")
        if os.getenv("LLM_MODEL"):
            self.llm_model = os.getenv("LLM_MODEL")
        if os.getenv("LLM_PROVIDER"):
            self.llm_provider = os.getenv("LLM_PROVIDER")
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

# 全局配置实例
config = Config()
