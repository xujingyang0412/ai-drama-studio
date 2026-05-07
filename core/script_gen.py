"""AI 剧本生成模块"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Scene:
    """场景数据"""
    scene_id: int
    location: str
    time: str
    characters: List[str]
    dialogue: List[Dict[str, str]]  # [{"character": "xxx", "line": "xxx"}]
    action: str
    emotion: str
    duration: int  # 秒
    image_prompt: str
    voice_text: str

@dataclass
class Script:
    """剧本数据"""
    title: str
    genre: str
    theme: str
    scenes: List[Scene]
    total_duration: int
    synopsis: str

# 剧本模板
SCRIPT_SYSTEM_PROMPT = """你是一个专业的短视频编剧，擅长创作各种类型的短剧剧本。

你的任务是根据用户给出的主题/关键词，生成一个完整的短剧剧本。

要求：
1. 剧本时长控制在用户指定的时长内（默认60秒）
2. 节奏紧凑，开头3秒必须抓住注意力
3. 对话要口语化、有感染力
4. 每个场景要详细描述画面内容，用于AI图片生成
5. 适合竖屏短视频观看

输出格式为JSON：
{
  "title": "短剧标题",
  "genre": "类型（都市/古风/悬疑/搞笑/情感）",
  "theme": "核心主题",
  "synopsis": "一句话剧情简介",
  "scenes": [
    {
      "scene_id": 1,
      "location": "场景地点",
      "time": "时间（白天/夜晚/黄昏）",
      "characters": ["角色1", "角色2"],
      "dialogue": [
        {"character": "角色1", "line": "台词内容"}
      ],
      "action": "人物动作描述",
      "emotion": "情绪氛围",
      "duration": 8,
      "image_prompt": "英文画面描述，用于AI生成图片，包含场景、人物、光线、氛围",
      "voice_text": "旁白/配音文字（如有）"
    }
  ]
}"""

SCRIPT_USER_PROMPT = """请根据以下主题生成短剧剧本：

主题：{prompt}
类型偏好：{genre}
目标时长：{duration}秒
风格：{style}

请直接输出JSON格式的剧本，不要包含其他说明文字。"""

def _generate_demo_script(prompt: str, duration: int = 60) -> Script:
    """生成Demo剧本（无API时使用）"""
    scene_count = max(3, min(8, duration // 8))
    scene_duration = duration // scene_count
    
    scenes = []
    for i in range(scene_count):
        scene = Scene(
            scene_id=i + 1,
            location=["城市街道", "办公室", "咖啡厅", "公园", "家中客厅"][i % 5],
            time=["白天", "夜晚", "黄昏", "清晨"][i % 4],
            characters=["主角", "配角"],
            dialogue=[
                {"character": "主角", "line": f"这是第{i+1}幕的台词，关于：{prompt}"},
                {"character": "配角", "line": "我理解你的意思..."}
            ],
            action="人物在场景中活动",
            emotion="戏剧性",
            duration=scene_duration,
            image_prompt=f"Cinematic scene {i+1}: {prompt}, dramatic lighting, vertical format",
            voice_text=f"旁白：{prompt}的故事正在继续..."
        )
        scenes.append(scene)
    
    return Script(
        title=f"{prompt[:20]}..." if len(prompt) > 20 else prompt,
        genre="都市",
        theme=prompt,
        scenes=scenes,
        total_duration=duration,
        synopsis=prompt
    )

async def generate_script(
    prompt: str,
    duration: int = 60,
    genre: str = "auto",
    style: str = "default",
    api_key: str = "",
    model: str = "gpt-4o-mini",
    base_url: str = None
) -> Script:
    """使用AI生成剧本，无API时使用Demo模式"""
    
    if not api_key:
        return _generate_demo_script(prompt, duration)
    
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("请安装 openai: pip install openai")
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    user_prompt = SCRIPT_USER_PROMPT.format(
        prompt=prompt,
        genre=genre,
        duration=duration,
        style=style
    )
    
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    data = json.loads(content)
    
    scenes = []
    for s in data.get("scenes", []):
        scene = Scene(
            scene_id=s["scene_id"],
            location=s.get("location", ""),
            time=s.get("time", "白天"),
            characters=s.get("characters", []),
            dialogue=s.get("dialogue", []),
            action=s.get("action", ""),
            emotion=s.get("emotion", "neutral"),
            duration=s.get("duration", 5),
            image_prompt=s.get("image_prompt", ""),
            voice_text=s.get("voice_text", "")
        )
        scenes.append(scene)
    
    return Script(
        title=data.get("title", "未命名短剧"),
        genre=data.get("genre", "都市"),
        theme=data.get("theme", prompt),
        scenes=scenes,
        total_duration=sum(s.duration for s in scenes),
        synopsis=data.get("synopsis", "")
    )

def script_to_json(script: Script) -> str:
    """剧本转JSON字符串"""
    return json.dumps({
        "title": script.title,
        "genre": script.genre,
        "theme": script.theme,
        "synopsis": script.synopsis,
        "total_duration": script.total_duration,
        "scenes": [
            {
                "scene_id": s.scene_id,
                "location": s.location,
                "time": s.time,
                "characters": s.characters,
                "dialogue": s.dialogue,
                "action": s.action,
                "emotion": s.emotion,
                "duration": s.duration,
                "image_prompt": s.image_prompt,
                "voice_text": s.voice_text
            }
            for s in script.scenes
        ]
    }, ensure_ascii=False, indent=2)
