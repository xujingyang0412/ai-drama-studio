"""AI Drama Studio - 完整流水线"""
import os
import asyncio
import json
import time
from typing import Optional
from dataclasses import dataclass

from .script_gen import Script, Scene, generate_script, script_to_json
from .image_gen import generate_scene_image
from .voice_gen import generate_dialogue_voices, generate_narration
from .video_edit import VideoEditor

@dataclass
class PipelineResult:
    """流水线执行结果"""
    success: bool
    output_path: str = ""
    script_path: str = ""
    duration: float = 0
    scenes_count: int = 0
    error: str = ""

class DramaPipeline:
    """短剧生成流水线"""
    
    def __init__(self, config):
        self.config = config
        self.editor = VideoEditor(config.ffmpeg_path)
        self.temp_dir = config.temp_dir
        self.output_dir = config.output_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def run(
        self,
        prompt: str,
        duration: int = 60,
        genre: str = "auto",
        style: str = "default",
        output_name: Optional[str] = None
    ) -> PipelineResult:
        """执行完整流水线"""
        
        start_time = time.time()
        
        # 生成输出文件名
        if not output_name:
            timestamp = int(time.time())
            output_name = f"drama_{timestamp}"
        
        script_path = os.path.join(self.output_dir, f"{output_name}_script.json")
        output_path = os.path.join(self.output_dir, f"{output_name}.mp4")
        
        try:
            # ============ 第1步：生成剧本 ============
            print("📝 第1步：正在生成剧本...")
            script = await generate_script(
                prompt=prompt,
                duration=duration,
                genre=genre,
                style=style,
                api_key=self.config.llm_api_key,
                model=self.config.llm_model,
                base_url=self.config.llm_base_url
            )
            
            # 保存剧本
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_to_json(script))
            print(f"   ✅ 剧本生成完成：{script.title} ({len(script.scenes)}个场景)")
            
            # ============ 第2步：生成画面 ============
            print("🖼️ 第2步：正在生成画面...")
            scene_images = []
            for scene in script.scenes:
                image_path = os.path.join(self.temp_dir, f"scene_{scene.scene_id:03d}.png")
                await generate_scene_image(
                    prompt=scene.image_prompt,
                    output_path=image_path,
                    provider=self.config.image_provider,
                    api_key=self.config.image_api_key
                )
                scene_images.append(image_path)
                print(f"   ✅ 场景{scene.scene_id}画面生成完成")
            
            # ============ 第3步：生成语音 ============
            print("🗣️ 第3步：正在生成语音...")
            scene_audios = []
            for scene in script.scenes:
                scene_audio_dir = os.path.join(self.temp_dir, f"scene_{scene.scene_id:03d}")
                os.makedirs(scene_audio_dir, exist_ok=True)
                
                # 生成对话语音
                if scene.dialogue:
                    dialogue_results = await generate_dialogue_voices(
                        dialogue=scene.dialogue,
                        output_dir=scene_audio_dir,
                        provider=self.config.voice_provider,
                        api_key=self.config.voice_api_key
                    )
                    
                    # 合并对话音频
                    if dialogue_results:
                        merged_audio = os.path.join(scene_audio_dir, "merged_dialogue.mp3")
                        self._merge_audio_files(
                            [r["audio_path"] for r in dialogue_results],
                            merged_audio
                        )
                        scene_audios.append(merged_audio)
                        print(f"   ✅ 场景{scene.scene_id}对话语音生成完成")
                        continue
                
                # 生成旁白语音
                if scene.voice_text:
                    narration_path = os.path.join(scene_audio_dir, "narration.mp3")
                    await generate_narration(
                        text=scene.voice_text,
                        output_path=narration_path,
                        provider=self.config.voice_provider,
                        api_key=self.config.voice_api_key
                    )
                    scene_audios.append(narration_path)
                    print(f"   ✅ 场景{scene.scene_id}旁白语音生成完成")
                else:
                    # 生成静音音频作为占位
                    silence_path = os.path.join(scene_audio_dir, "silence.mp3")
                    self._generate_silence(silence_path, scene.duration)
                    scene_audios.append(silence_path)
            
            # ============ 第4步：合成视频 ============
            print("🎬 第4步：正在合成视频...")
            scene_videos = []
            for i, scene in enumerate(script.scenes):
                scene_video = os.path.join(self.temp_dir, f"scene_{scene.scene_id:03d}.mp4")
                self.editor.create_scene_video(
                    image_path=scene_images[i],
                    audio_path=scene_audios[i],
                    output_path=scene_video,
                    duration=scene.duration
                )
                scene_videos.append(scene_video)
                print(f"   ✅ 场景{scene.scene_id}视频合成完成")
            
            # ============ 第5步：拼接成片 ============
            print("🎞️ 第5步：正在拼接成片...")
            self.editor.concatenate_videos(
                video_paths=scene_videos,
                output_path=output_path,
                transition="fade"
            )
            
            elapsed = time.time() - start_time
            print(f"\n🎉 短剧生成完成！")
            print(f"   标题：{script.title}")
            print(f"   时长：{script.total_duration}秒")
            print(f"   场景：{len(script.scenes)}个")
            print(f"   耗时：{elapsed:.1f}秒")
            print(f"   输出：{output_path}")
            
            return PipelineResult(
                success=True,
                output_path=output_path,
                script_path=script_path,
                duration=elapsed,
                scenes_count=len(script.scenes)
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ 流水线执行失败：{e}")
            return PipelineResult(
                success=False,
                error=str(e),
                duration=elapsed
            )
    
    def _merge_audio_files(self, audio_paths: list, output_path: str):
        """合并多个音频文件"""
        import subprocess
        
        if len(audio_paths) == 1:
            import shutil
            shutil.copy2(audio_paths[0], output_path)
            return
        
        # 使用 ffmpeg concat 合并
        concat_file = output_path + ".txt"
        with open(concat_file, "w") as f:
            for path in audio_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
        
        cmd = [
            self.config.ffmpeg_path, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except:
            import shutil
            shutil.copy2(audio_paths[0], output_path)
        
        os.remove(concat_file)
    
    def _generate_silence(self, output_path: str, duration: float):
        """生成静音音频"""
        import subprocess
        
        cmd = [
            self.config.ffmpeg_path, "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            "-c:a", "libmp3lame",
            "-b:a", "128k",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except:
            # 创建空文件作为占位
            with open(output_path, "wb") as f:
                pass
