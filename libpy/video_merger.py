#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频合成器 - 将图片和音频合成为视频，支持字幕添加
"""

import os
import sys
import re
from datetime import timedelta
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip
from PIL import Image


class SubtitleParser:
    """SRT字幕解析器"""
    
    @staticmethod
    def parse_timestamp(timestamp_str):
        """
        解析SRT时间戳格式 (HH:MM:SS,mmm) 为秒数
        
        Args:
            timestamp_str (str): SRT格式时间戳
            
        Returns:
            float: 时间戳（秒）
        """
        # 将逗号替换为点号以便解析毫秒
        timestamp_str = timestamp_str.replace(',', '.')
        
        # 解析时:分:秒.毫秒
        parts = timestamp_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        return total_seconds
    
    @staticmethod
    def parse_srt_file(srt_path):
        """
        解析SRT字幕文件
        
        Args:
            srt_path (str): SRT文件路径
            
        Returns:
            list: 字幕条目列表，每个条目包含start, end, text
        """
        if not os.path.exists(srt_path):
            raise FileNotFoundError(f"字幕文件不存在: {srt_path}")
        
        subtitles = []
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 按空行分割字幕块
        subtitle_blocks = re.split(r'\n\s*\n', content)
        
        for block in subtitle_blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # 序号
                index = lines[0].strip()
                
                # 时间戳行
                timestamp_line = lines[1].strip()
                timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timestamp_line)
                
                if timestamp_match:
                    start_time = SubtitleParser.parse_timestamp(timestamp_match.group(1))
                    end_time = SubtitleParser.parse_timestamp(timestamp_match.group(2))
                    
                    # 字幕文本（可能有多行）
                    text = '\n'.join(lines[2:]).strip()
                    
                    subtitles.append({
                        'index': int(index),
                        'start': start_time,
                        'end': end_time,
                        'text': text
                    })
        
        return subtitles


class VideoMerger:
    """视频合成器类"""
    
    def __init__(self):
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        self.supported_audio_formats = ['.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac']
        self.supported_subtitle_formats = ['.srt']
    
    def validate_files(self, image_path, audio_path, subtitle_path=None):
        """验证输入文件"""
        # 检查文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        if subtitle_path and not os.path.exists(subtitle_path):
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
        
        # 检查文件格式
        image_ext = os.path.splitext(image_path)[1].lower()
        audio_ext = os.path.splitext(audio_path)[1].lower()
        
        if image_ext not in self.supported_image_formats:
            raise ValueError(f"不支持的图片格式: {image_ext}")
        
        if audio_ext not in self.supported_audio_formats:
            raise ValueError(f"不支持的音频格式: {audio_ext}")
        
        if subtitle_path:
            subtitle_ext = os.path.splitext(subtitle_path)[1].lower()
            if subtitle_ext not in self.supported_subtitle_formats:
                raise ValueError(f"不支持的字幕格式: {subtitle_ext}")
    
    def get_image_info(self, image_path):
        """获取图片信息"""
        with Image.open(image_path) as img:
            width, height = img.size
            return width, height
    
    def get_available_font(self, preferred_font='Arial'):
        """
        获取可用的字体
        
        Args:
            preferred_font (str): 首选字体名称
            
        Returns:
            str or None: 可用的字体路径或名称，如果都不可用则返回None
        """
        import platform
        import os
        
        system = platform.system()
        
        # 定义不同系统的常用字体路径
        font_paths = {
            'Windows': [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/simsun.ttc',  # 宋体，支持中文
                'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
                'C:/Windows/Fonts/calibri.ttf',
            ],
            'Darwin': [  # macOS
                '/System/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/System/Library/Fonts/PingFang.ttc',  # 苹方，支持中文
                '/Library/Fonts/Arial.ttf',
            ],
            'Linux': [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # 支持中文
                '/usr/share/fonts/TTF/DejaVuSans.ttf',
            ]
        }
        
        # 检查系统字体
        if system in font_paths:
            for font_path in font_paths[system]:
                if os.path.exists(font_path):
                    return font_path
        
        # 尝试使用系统默认字体名称
        default_fonts = ['Arial', 'Helvetica', 'DejaVu-Sans', 'Liberation-Sans']
        
        # 如果是中文内容，优先使用支持中文的字体
        chinese_fonts = ['SimSun', 'Microsoft-YaHei', 'PingFang-SC', 'Noto-Sans-CJK']
        
        return None  # 如果找不到字体，返回None使用默认设置

    def create_subtitle_clips(self, subtitles, video_size, font_size=24, font_color='white', 
                            font_family='Arial', stroke_color='black', stroke_width=2):
        """
        创建字幕剪辑
        
        Args:
            subtitles (list): 字幕数据列表
            video_size (tuple): 视频尺寸 (width, height)
            font_size (int): 字体大小
            font_color (str): 字体颜色
            font_family (str): 字体族
            stroke_color (str): 描边颜色
            stroke_width (int): 描边宽度
            
        Returns:
            list: TextClip对象列表
        """
        subtitle_clips = []
        video_width, video_height = video_size
        
        # 获取可用字体
        available_font = self.get_available_font(font_family)
        
        for subtitle in subtitles:
            text_clip = None
            
            # 尝试多种方法创建文本剪辑
            creation_methods = [
                # 方法1: 完整参数（如果有可用字体）
                lambda: TextClip(
                    txt=subtitle['text'],
                    fontsize=font_size,
                    color=font_color,
                    font=available_font,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width
                ).set_start(subtitle['start']).set_end(subtitle['end']) if available_font else None,
                
                # 方法2: 无字体的完整参数
                lambda: TextClip(
                    txt=subtitle['text'],
                    fontsize=font_size,
                    color=font_color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width
                ).set_start(subtitle['start']).set_end(subtitle['end']),
                
                # 方法3: 最简参数
                lambda: TextClip(
                    txt=subtitle['text'],
                    fontsize=font_size,
                    color=font_color
                ).set_start(subtitle['start']).set_end(subtitle['end']),
                
                # 方法4: 极简参数
                lambda: TextClip(
                    txt=subtitle['text'],
                    fontsize=font_size
                ).set_start(subtitle['start']).set_end(subtitle['end'])
            ]
            
            # 依次尝试各种创建方法
            for i, method in enumerate(creation_methods, 1):
                try:
                    text_clip = method()
                    if text_clip:
                        # 设置字幕位置（底部居中）
                        text_clip = text_clip.set_position(('center', video_height - font_size * 3))
                        subtitle_clips.append(text_clip)
                        
                        if i == 1:
                            print(f"✅ 字幕 {subtitle.get('index', '?')} 使用完整参数创建成功")
                        else:
                            print(f"⚠️ 字幕 {subtitle.get('index', '?')} 使用备选方法 {i} 创建成功")
                        break
                except Exception as e:
                    if i == len(creation_methods):
                        print(f"❌ 字幕 {subtitle.get('index', '?')} 所有创建方法都失败: {str(e)}")
                    continue
        
        return subtitle_clips
    
    def merge_image_audio(self, image_path, audio_path, output_path, fps=24, subtitle_path=None,
                         subtitle_style=None):
        """
        合成图片和音频为视频，支持字幕
        
        Args:
            image_path (str): 图片文件路径
            audio_path (str): 音频文件路径
            output_path (str): 输出视频路径
            fps (int): 视频帧率，默认24
            subtitle_path (str): 字幕文件路径（可选）
            subtitle_style (dict): 字幕样式配置（可选）
        """
        try:
            # 验证输入文件
            self.validate_files(image_path, audio_path, subtitle_path)
            
            print(f"开始处理...")
            print(f"图片文件: {image_path}")
            print(f"音频文件: {audio_path}")
            print(f"输出文件: {output_path}")
            if subtitle_path:
                print(f"字幕文件: {subtitle_path}")
            
            # 获取图片信息
            width, height = self.get_image_info(image_path)
            print(f"图片尺寸: {width}x{height}")
            
            # 加载音频文件
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            print(f"音频时长: {audio_duration:.2f}秒")
            
            # 创建图片剪辑，持续时间与音频相同
            image_clip = ImageClip(image_path, duration=audio_duration)
            image_clip = image_clip.set_fps(fps)
            
            # 准备合成的剪辑列表
            clips = [image_clip]
            
            # 处理字幕
            if subtitle_path:
                print("正在解析字幕文件...")
                subtitles = SubtitleParser.parse_srt_file(subtitle_path)
                print(f"解析到 {len(subtitles)} 条字幕")
                
                # 设置字幕样式
                default_style = {
                    'font_size': max(16, min(width, height) // 30),  # 根据视频尺寸自适应字体大小
                    'font_color': 'white',
                    'font_family': 'Arial',
                    'stroke_color': 'black',
                    'stroke_width': 2
                }
                
                if subtitle_style:
                    default_style.update(subtitle_style)
                
                # 创建字幕剪辑
                subtitle_clips = self.create_subtitle_clips(
                    subtitles, 
                    (width, height), 
                    **default_style
                )
                
                if subtitle_clips:
                    clips.extend(subtitle_clips)
                    print(f"成功创建 {len(subtitle_clips)} 个字幕剪辑")
                else:
                    print("警告: 没有成功创建字幕剪辑")
            
            # 合成所有剪辑
            if len(clips) > 1:
                final_clip = CompositeVideoClip(clips)
            else:
                final_clip = clips[0]
            
            # 添加音频
            final_clip = final_clip.set_audio(audio_clip)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 导出视频
            print("正在生成视频...")
            final_clip.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # 清理资源
            audio_clip.close()
            image_clip.close()
            final_clip.close()
            
            print(f"视频生成完成: {output_path}")
            
        except Exception as e:
            print(f"错误: {str(e)}")
            raise
    
    def merge_with_custom_duration(self, image_path, audio_path, output_path, 
                                 duration=None, fps=24, subtitle_path=None, subtitle_style=None):
        """
        使用自定义时长合成视频，支持字幕
        
        Args:
            image_path (str): 图片文件路径
            audio_path (str): 音频文件路径
            output_path (str): 输出视频路径
            duration (float): 自定义视频时长（秒），如果为None则使用音频时长
            fps (int): 视频帧率，默认24
            subtitle_path (str): 字幕文件路径（可选）
            subtitle_style (dict): 字幕样式配置（可选）
        """
        try:
            # 验证输入文件
            self.validate_files(image_path, audio_path, subtitle_path)
            
            print(f"开始处理（自定义时长模式）...")
            
            # 加载音频文件
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            
            # 确定最终视频时长
            if duration is None:
                final_duration = audio_duration
            else:
                final_duration = min(duration, audio_duration)  # 不超过音频时长
            
            print(f"音频时长: {audio_duration:.2f}秒")
            print(f"视频时长: {final_duration:.2f}秒")
            
            # 获取图片信息
            width, height = self.get_image_info(image_path)
            
            # 创建图片剪辑
            image_clip = ImageClip(image_path, duration=final_duration)
            image_clip = image_clip.set_fps(fps)
            
            # 截取音频到指定时长
            if final_duration < audio_duration:
                audio_clip = audio_clip.subclip(0, final_duration)
            
            # 准备合成的剪辑列表
            clips = [image_clip]
            
            # 处理字幕
            if subtitle_path:
                print("正在解析字幕文件...")
                subtitles = SubtitleParser.parse_srt_file(subtitle_path)
                
                # 过滤字幕，只保留在视频时长范围内的
                filtered_subtitles = []
                for subtitle in subtitles:
                    if subtitle['start'] < final_duration:
                        # 如果字幕结束时间超过视频时长，则截断
                        if subtitle['end'] > final_duration:
                            subtitle['end'] = final_duration
                        filtered_subtitles.append(subtitle)
                
                print(f"解析到 {len(subtitles)} 条字幕，有效字幕 {len(filtered_subtitles)} 条")
                
                if filtered_subtitles:
                    # 设置字幕样式
                    default_style = {
                        'font_size': max(16, min(width, height) // 30),
                        'font_color': 'white',
                        'font_family': 'Arial',
                        'stroke_color': 'black',
                        'stroke_width': 2
                    }
                    
                    if subtitle_style:
                        default_style.update(subtitle_style)
                    
                    # 创建字幕剪辑
                    subtitle_clips = self.create_subtitle_clips(
                        filtered_subtitles, 
                        (width, height), 
                        **default_style
                    )
                    
                    if subtitle_clips:
                        clips.extend(subtitle_clips)
                        print(f"成功创建 {len(subtitle_clips)} 个字幕剪辑")
            
            # 合成所有剪辑
            if len(clips) > 1:
                final_clip = CompositeVideoClip(clips)
            else:
                final_clip = clips[0]
            
            # 添加音频
            final_clip = final_clip.set_audio(audio_clip)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 导出视频
            print("正在生成视频...")
            final_clip.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # 清理资源
            audio_clip.close()
            image_clip.close()
            final_clip.close()
            
            print(f"视频生成完成: {output_path}")
            
        except Exception as e:
            print(f"错误: {str(e)}")
            raise


def main():
    """主函数"""
    if len(sys.argv) < 4:
        print("使用方法:")
        print("python video_merger.py <图片路径> <音频路径> <输出视频路径> [时长(秒)] [帧率] [字幕文件路径]")
        print("\n示例:")
        print("python video_merger.py image.jpg audio.mp3 output.mp4")
        print("python video_merger.py image.jpg audio.mp3 output.mp4 30")
        print("python video_merger.py image.jpg audio.mp3 output.mp4 30 30")
        print("python video_merger.py image.jpg audio.mp3 output.mp4 30 30 subtitles.srt")
        print("\n字幕支持:")
        print("- 支持SRT格式字幕文件")
        print("- 字幕会自动根据视频尺寸调整大小")
        print("- 字幕位置在视频底部居中")
        return
    
    image_path = sys.argv[1]
    audio_path = sys.argv[2]
    output_path = sys.argv[3]
    
    # 可选参数
    duration = None
    fps = 24
    subtitle_path = None
    
    if len(sys.argv) > 4:
        try:
            duration = float(sys.argv[4])
        except ValueError:
            print("警告: 时长参数无效，将使用音频时长")
    
    if len(sys.argv) > 5:
        try:
            fps = int(sys.argv[5])
        except ValueError:
            print("警告: 帧率参数无效，将使用默认值24")
    
    if len(sys.argv) > 6:
        subtitle_path = sys.argv[6]
    
    # 创建视频合成器实例
    merger = VideoMerger()
    
    try:
        if duration is not None:
            merger.merge_with_custom_duration(
                image_path, audio_path, output_path, 
                duration, fps, subtitle_path
            )
        else:
            merger.merge_image_audio(
                image_path, audio_path, output_path, 
                fps, subtitle_path
            )
    except Exception as e:
        print(f"合成失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 