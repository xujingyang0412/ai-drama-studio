"""AI 语音合成模块"""
import os
import asyncio
from typing import Optional

# 角色声音映射
CHARACTER_VOICES = {
    "男青年": "zh-CN-YunxiNeural",
    "女青年": "zh-CN-XiaoyiNeural",
    "男中年": "zh-CN-YunjianNeural",
    "女中年": "zh-CN-XiaochenNeural",
    "旁白": "zh-CN-YunxiNeural",
    "老人": "zh-CN-YunyangNeural",
    "小孩": "zh-CN-XiaoxiaoNeural",
}

async def generate_voice_edge_tts(
    text: str,
    output_path: str,
    voice: str = "zh-CN-YunxiNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> str:
    """使用 Edge-TTS 生成语音（免费）"""
    try:
        import edge_tts
    except ImportError:
        raise ImportError("请安装 edge-tts: pip install edge-tts")
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)
    return output_path

async def generate_voice_openai(
    text: str,
    output_path: str,
    api_key: str,
    model: str = "tts-1",
    voice: str = "alloy"
) -> str:
    """使用 OpenAI TTS 生成语音"""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("请安装 openai: pip install openai")
    
    client = AsyncOpenAI(api_key=api_key)
    
    response = await client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="mp3"
    )
    
    response.stream_to_file(output_path)
    return output_path

async def generate_dialogue_voices(
    dialogue: list,
    output_dir: str,
    provider: str = "edge-tts",
    api_key: str = ""
) -> list:
    """为对话中的每一句生成语音
    
    dialogue: [{"character": "角色名", "line": "台词"}]
    返回: [{"character": "角色名", "line": "台词", "audio_path": "音频路径"}]
    """
    results = []
    
    for i, item in enumerate(dialogue):
        character = item.get("character", "旁白")
        line = item.get("line", "")
        
        if not line.strip():
            continue
        
        # 根据角色选择声音
        voice = CHARACTER_VOICES.get(character, "zh-CN-YunxiNeural")
        output_path = os.path.join(output_dir, f"dialogue_{i:03d}.mp3")
        
        try:
            if provider == "edge-tts":
                await generate_voice_edge_tts(line, output_path, voice)
            elif provider == "openai" and api_key:
                await generate_voice_openai(line, output_path, api_key)
            
            results.append({
                "character": character,
                "line": line,
                "audio_path": output_path
            })
        except Exception as e:
            print(f"⚠️ 语音生成失败 [{character}]: {e}")
            continue
    
    return results

async def generate_narration(
    text: str,
    output_path: str,
    provider: str = "edge-tts",
    api_key: str = "",
    voice: str = "zh-CN-YunxiNeural"
) -> str:
    """生成旁白/解说语音"""
    if provider == "edge-tts":
        return await generate_voice_edge_tts(text, output_path, voice)
    elif provider == "openai" and api_key:
        return await generate_voice_openai(text, output_path, api_key)
    else:
        raise ValueError(f"不支持的语音提供商: {provider}")
