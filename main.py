#!/usr/bin/env python3
"""
🎬 AI Drama Studio - 一句话生成完整短剧
从剧本到成片，全自动化

Usage:
    python main.py --prompt "一个程序员穿越到古代"
    python main.py --prompt "霸道总裁" --duration 60 --style funny
    python main.py --batch scripts.txt --output ./output
"""
import asyncio
import os
import sys
import json
import time
from typing import Optional

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from config import config
from core.pipeline import DramaPipeline
from core.script_gen import generate_script, script_to_json

if HAS_RICH:
    console = Console()
else:
    class FakeConsole:
        def print(self, *args, **kwargs):
            text = args[0] if args else ""
            if isinstance(text, str):
                print(text)
            else:
                print(text)
        def status(self, *args, **kwargs):
            class FakeStatus:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def update(self, *args, **kwargs): pass
            return FakeStatus()
    console = FakeConsole()

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════╗
║     🎬 AI Drama Studio v1.0.0          ║
║     一句话生成完整短剧                    ║
║     从剧本到成片，全自动化                ║
╚══════════════════════════════════════════╝
    """
    if HAS_RICH:
        console.print(Panel(banner.strip(), style="bold cyan"))
    else:
        print(banner)

async def generate_single(
    prompt: str,
    duration: int = 60,
    genre: str = "auto",
    style: str = "default",
    output_name: Optional[str] = None,
    skip_video: bool = False
):
    """生成单个短剧"""
    
    pipeline = DramaPipeline(config)
    
    if skip_video:
        # 仅生成剧本，不生成视频
        console.print("\n📝 仅生成剧本模式\n")
        script = await generate_script(
            prompt=prompt,
            duration=duration,
            genre=genre,
            style=style,
            api_key=config.llm_api_key,
            model=config.llm_model,
            base_url=config.llm_base_url
        )
        
        output_path = os.path.join(config.output_dir, f"{output_name or 'script'}_script.json")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(script_to_json(script))
        
        console.print(f"[green]✅ 剧本已保存到: {output_path}[/green]")
        console.print(f"   标题: {script.title}")
        console.print(f"   类型: {script.genre}")
        console.print(f"   场景数: {len(script.scenes)}")
        console.print(f"   时长: {script.total_duration}秒")
        return
    
    result = await pipeline.run(
        prompt=prompt,
        duration=duration,
        genre=genre,
        style=style,
        output_name=output_name
    )
    
    if result.success:
        console.print(f"\n[green bold]🎉 成功！[/green bold]")
        console.print(f"   输出文件: {result.output_path}")
        console.print(f"   剧本文件: {result.script_path}")
    else:
        console.print(f"\n[red]❌ 失败: {result.error}[/red]")

async def generate_batch(batch_file: str, output_dir: str):
    """批量生成短剧"""
    
    if not os.path.exists(batch_file):
        console.print(f"[red]❌ 批量文件不存在: {batch_file}[/red]")
        return
    
    with open(batch_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    console.print(f"[cyan]📋 共 {len(lines)} 个任务[/cyan]\n")
    
    pipeline = DramaPipeline(config)
    
    for i, line in enumerate(lines, 1):
        console.print(f"\n[cyan]━━━ 任务 {i}/{len(lines)} ━━━[/cyan]")
        
        # 解析配置（支持 JSON 或纯文本）
        try:
            data = json.loads(line)
            prompt = data.get("prompt", "")
            duration = data.get("duration", 60)
            genre = data.get("genre", "auto")
        except json.JSONDecodeError:
            prompt = line
            duration = 60
            genre = "auto"
        
        if not prompt:
            continue
        
        result = await pipeline.run(
            prompt=prompt,
            duration=duration,
            genre=genre,
            output_name=f"batch_{i:03d}"
        )
        
        if result.success:
            console.print(f"[green]✅ 任务{i}完成: {result.output_path}[/green]")
        else:
            console.print(f"[red]❌ 任务{i}失败: {result.error}[/red]")
        
        # 避免API限流
        if i < len(lines):
            console.print("[dim]⏳ 等待3秒避免限流...[/dim]")
            await asyncio.sleep(3)

def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🎬 AI Drama Studio - 一句话生成完整短剧",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --prompt "一个程序员穿越到古代，用现代知识改变命运"
  %(prog)s --prompt "霸道总裁爱上女程序员" --duration 60 --style funny
  %(prog)s --prompt "悬疑：办公室里的秘密" --genre suspense --script-only
  %(prog)s --batch scripts.txt --output ./output
        """
    )
    
    parser.add_argument("--prompt", "-p", type=str, help="短剧主题/描述")
    parser.add_argument("--duration", "-d", type=int, default=60, help="目标时长（秒），默认60")
    parser.add_argument("--genre", "-g", type=str, default="auto", 
                       choices=["auto", "urban", "ancient", "suspense", "comedy", "romance"],
                       help="类型")
    parser.add_argument("--style", "-s", type=str, default="default",
                       choices=["default", "funny", "dramatic", "suspense", "romantic"],
                       help="风格")
    parser.add_argument("--output", "-o", type=str, help="输出文件名（不含扩展名）")
    parser.add_argument("--batch", "-b", type=str, help="批量生成的配置文件")
    parser.add_argument("--script-only", action="store_true", help="仅生成剧本，不生成视频")
    parser.add_argument("--config", type=str, help="自定义配置文件路径")
    
    args = parser.parse_args()
    
    # 加载自定义配置
    if args.config:
        console.print(f"[yellow]⚠️ 自定义配置功能开发中...[/yellow]")
    
    print_banner()
    
    # 检查 API Key
    if not config.llm_api_key and not args.script_only:
        console.print("[yellow]⚠️ 未设置 API Key，将使用占位图片模式[/yellow]")
        console.print("[dim]设置方法: export OPENAI_API_KEY=your_key[/dim]")
        console.print("[dim]         export LLM_API_KEY=your_key[/dim]\n")
    
    # 执行
    if args.batch:
        asyncio.run(generate_batch(args.batch, args.output or config.output_dir))
    elif args.prompt:
        asyncio.run(generate_single(
            prompt=args.prompt,
            duration=args.duration,
            genre=args.genre,
            style=args.style,
            output_name=args.output,
            skip_video=args.script_only
        ))
    else:
        # 交互模式
        console.print("[cyan]🎭 交互模式 - 输入短剧主题开始创作[/cyan]")
        console.print("[dim]输入 'quit' 退出[/dim]\n")
        
        while True:
            try:
                prompt = console.input("[bold green]>>> 请输入短剧主题: [/bold green]")
                if prompt.lower() in ("quit", "exit", "q"):
                    console.print("[cyan]👋 再见！[/cyan]")
                    break
                if not prompt.strip():
                    continue
                
                asyncio.run(generate_single(prompt=prompt))
                
            except KeyboardInterrupt:
                console.print("\n[cyan]👋 再见！[/cyan]")
                break
            except EOFError:
                break

if __name__ == "__main__":
    main()
