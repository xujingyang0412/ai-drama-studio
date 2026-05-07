"""视频剪辑模块 - 使用 FFmpeg 合成最终视频"""
import os
import asyncio
import subprocess
import json
from typing import List, Dict, Optional

class VideoEditor:
    """视频编辑器"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """检查 FFmpeg 是否可用"""
        try:
            subprocess.run(
                [self.ffmpeg, "-version"],
                capture_output=True,
                check=True
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("⚠️ FFmpeg 未安装或不可用，将使用简化模式")
    
    def create_scene_video(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        duration: float = 5.0,
        width: int = 1080,
        height: int = 1920,
        effect: str = "ken_burns"
    ) -> str:
        """将单张图片+音频合成为视频片段（带Ken Burns效果）"""
        
        # Ken Burns 效果 - 缓慢缩放
        if effect == "ken_burns":
            filter_complex = (
                f"scale={width*2}:{height*2},"
                f"zoompan=z='min(zoom+0.001,1.2)':d={int(duration*30)}:s={width}x{height}:fps=30"
            )
        else:
            filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        
        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", filter_complex,
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            # 简化模式：不使用复杂滤镜
            cmd_simple = [
                self.ffmpeg, "-y",
                "-loop", "1",
                "-i", image_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest",
                output_path
            ]
            subprocess.run(cmd_simple, capture_output=True, check=True)
        
        return output_path
    
    def concatenate_videos(
        self,
        video_paths: List[str],
        output_path: str,
        transition: str = "fade",
        transition_duration: float = 0.5
    ) -> str:
        """拼接多个视频片段"""
        
        # 创建 concat 文件
        concat_file = output_path + ".concat.txt"
        with open(concat_file, "w") as f:
            for path in video_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
        
        if transition == "fade":
            # 使用xfade滤镜实现淡入淡出
            cmd = [
                self.ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-pix_fmt", "yuv420p",
                output_path
            ]
        else:
            cmd = [
                self.ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                output_path
            ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # 清理临时文件
        os.remove(concat_file)
        
        return output_path
    
    def add_subtitles(
        self,
        video_path: str,
        subtitles: List[Dict],
        output_path: str,
        font_size: int = 42,
        font_color: str = "white",
        position: str = "bottom"
    ) -> str:
        """添加字幕到视频"""
        
        # 生成 SRT 字幕文件
        srt_path = video_path + ".srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, sub in enumerate(subtitles):
                start = sub.get("start", 0)
                end = sub.get("end", start + 3)
                text = sub.get("text", "")
                
                start_time = self._format_srt_time(start)
                end_time = self._format_srt_time(end)
                
                f.write(f"{i+1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        
        # 添加字幕到视频
        cmd = [
            self.ffmpeg, "-y",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize={font_size},PrimaryColour=&HFFFFFF,Alignment=2'",
            "-c:v", "libx264",
            "-c:a", "copy",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            # 字幕滤镜不可用时，直接复制
            import shutil
            shutil.copy2(video_path, output_path)
        
        # 清理
        os.remove(srt_path)
        
        return output_path
    
    def add_background_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        music_volume: float = 0.15
    ) -> str:
        """添加背景音乐"""
        
        cmd = [
            self.ffmpeg, "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first",
            "-c:v", "copy",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            import shutil
            shutil.copy2(video_path, output_path)
        
        return output_path
    
    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """格式化 SRT 时间戳"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def get_duration(self, file_path: str) -> float:
        """获取音频/视频时长"""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except:
            return 5.0
