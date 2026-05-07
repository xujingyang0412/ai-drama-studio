"""AI 画面生成模块"""
import os
import asyncio
import httpx
from typing import Optional

async def generate_image_dalle(
    prompt: str,
    output_path: str,
    api_key: str,
    model: str = "dall-e-3",
    size: str = "1024x1792",
    quality: str = "standard"
) -> str:
    """使用 DALL-E 生成图片"""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("请安装 openai: pip install openai")
    
    client = AsyncOpenAI(api_key=api_key)
    
    response = await client.images.generate(
        model=model,
        prompt=f"Cinematic still, {prompt}, vertical format 9:16, high quality, detailed, professional photography",
        size=size,
        quality=quality,
        n=1
    )
    
    image_url = response.data[0].url
    
    # 下载图片
    async with httpx.AsyncClient() as http_client:
        img_response = await http_client.get(image_url)
        with open(output_path, "wb") as f:
            f.write(img_response.content)
    
    return output_path

async def generate_image_dashscope(
    prompt: str,
    output_path: str,
    api_key: str,
    model: str = "wanx-v1"
) -> str:
    """使用通义万相生成图片"""
    # TODO: 实现通义万相API
    raise NotImplementedError("通义万相API待实现")

async def generate_image_placeholder(
    prompt: str,
    output_path: str,
    width: int = 1080,
    height: int = 1920
) -> str:
    """生成占位图片（用于无API时的测试）"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        # 如果没有 Pillow，创建最小的占位文件
        with open(output_path, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n')
        return output_path
    
    # 创建渐变背景
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # 渐变色
    colors = [
        ((20, 30, 48), (36, 59, 85)),   # 深蓝
        ((44, 62, 80), (52, 152, 219)),  # 蓝色
        ((45, 52, 54), (149, 165, 166)), # 灰色
    ]
    
    import random
    c1, c2 = random.choice(colors)
    
    for y in range(height):
        r = int(c1[0] + (c2[0] - c1[0]) * y / height)
        g = int(c1[1] + (c2[1] - c1[1]) * y / height)
        b = int(c1[2] + (c2[2] - c1[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # 添加文字（场景描述）
    text = prompt[:50] + "..." if len(prompt) > 50 else prompt
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # 文字居中
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, height // 2), text, fill=(255, 255, 255), font=font)
    
    img.save(output_path, "PNG")
    return output_path

async def generate_scene_image(
    prompt: str,
    output_path: str,
    provider: str = "dalle",
    api_key: str = "",
    **kwargs
) -> str:
    """统一图片生成接口"""
    if provider == "dalle" and api_key:
        return await generate_image_dalle(prompt, output_path, api_key, **kwargs)
    elif provider == "dashscope" and api_key:
        return await generate_image_dashscope(prompt, output_path, api_key, **kwargs)
    else:
        return await generate_image_placeholder(prompt, output_path, **kwargs)
