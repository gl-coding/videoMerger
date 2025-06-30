# 视频合成器 (VideoMerger)

一个简单易用的Python工具，用于将静态图片和音频文件合成为视频文件。

## 功能特点

- 🎬 将静态图片与音频合成为MP4视频
- 🎵 支持多种音频格式（MP3, WAV, AAC, M4A, OGG, FLAC）
- 🖼️ 支持多种图片格式（JPG, PNG, BMP, GIF, TIFF）
- 📝 **支持SRT字幕文件嵌入**
- ⏱️ 可自定义视频时长和帧率
- 🎨 可自定义字幕样式（字体、颜色、大小、描边）
- 🔧 简单的命令行界面和Python API
- ✅ 完整的错误处理和文件验证

## 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install moviepy==1.0.3 pillow==10.0.0
```

## 使用方法

### 命令行使用

#### 基本用法
```bash
python video_merger.py <图片路径> <音频路径> <输出视频路径>
```

#### 指定视频时长
```bash
python video_merger.py <图片路径> <音频路径> <输出视频路径> <时长(秒)>
```

#### 指定时长和帧率
```bash
python video_merger.py <图片路径> <音频路径> <输出视频路径> <时长(秒)> <帧率>
```

#### 添加字幕
```bash
python video_merger.py <图片路径> <音频路径> <输出视频路径> <时长(秒)> <帧率> <字幕文件路径>
```

### 示例

```bash
# 使用音频的完整时长
python video_merger.py image.jpg audio.mp3 output.mp4

# 生成30秒的视频
python video_merger.py image.jpg audio.mp3 output.mp4 30

# 生成30秒、30fps的视频
python video_merger.py image.jpg audio.mp3 output.mp4 30 30

# 生成带字幕的视频
python video_merger.py image.jpg audio.mp3 output.mp4 30 30 subtitles.srt
```

### Python API 使用

```python
from video_merger import VideoMerger

# 创建合成器实例
merger = VideoMerger()

# 基本合成（使用音频完整时长）
merger.merge_image_audio("image.jpg", "audio.mp3", "output.mp4")

# 自定义时长合成
merger.merge_with_custom_duration(
    "image.jpg", 
    "audio.mp3", 
    "output.mp4", 
    duration=30,  # 30秒
    fps=30        # 30帧每秒
)

# 带字幕的视频合成
merger.merge_image_audio(
    "image.jpg", 
    "audio.mp3", 
    "output.mp4",
    subtitle_path="subtitles.srt"
)

# 自定义字幕样式
custom_style = {
    'font_size': 32,
    'font_color': 'yellow',
    'stroke_color': 'black',
    'stroke_width': 2
}

merger.merge_image_audio(
    "image.jpg", 
    "audio.mp3", 
    "output.mp4",
    subtitle_path="subtitles.srt",
    subtitle_style=custom_style
)
```

## 支持的文件格式

### 图片格式
- JPG/JPEG
- PNG
- BMP
- GIF
- TIFF

### 音频格式
- MP3
- WAV
- AAC
- M4A
- OGG
- FLAC

### 字幕格式
- SRT（SubRip字幕文件）

## 输出格式

- 视频编码：H.264 (libx264)
- 音频编码：AAC
- 容器格式：MP4

## 注意事项

1. **系统要求**：需要安装FFmpeg（moviepy依赖）
2. **内存使用**：处理大图片时可能占用较多内存
3. **处理时间**：视频时长越长，处理时间越久
4. **文件路径**：确保输入文件路径正确且文件存在
5. **字体要求**：字幕功能需要系统安装相应字体

### 字体和ImageMagick问题解决

如果遇到字幕显示问题，可能是字体或ImageMagick配置问题：

**1. 诊断问题：**
```bash
# 诊断字体问题
python font_helper.py diagnose

# 检查ImageMagick配置
python imagemagick_fix.py check
```

**2. 解决ImageMagick问题：**
```bash
# 自动修复ImageMagick配置
python imagemagick_fix.py fix

# 或分步执行：
python imagemagick_fix.py install    # 安装ImageMagick
python imagemagick_fix.py configure  # 配置MoviePy
python imagemagick_fix.py test       # 测试功能
```

**3. 解决字体问题：**
```bash
# 列出可用字体
python font_helper.py list

# 安装默认字体（Linux）
python font_helper.py install
```

**常见安装命令：**

*ImageMagick:*
- macOS: `brew install imagemagick`
- Ubuntu/Debian: `sudo apt-get install imagemagick`
- CentOS/RHEL: `sudo yum install ImageMagick`

*字体:*
- Ubuntu/Debian: `sudo apt-get install fonts-dejavu-core fonts-liberation fonts-noto-cjk`
- CentOS/RHEL: `sudo yum install dejavu-sans-fonts liberation-fonts`
- macOS: 通常已包含所需字体
- Windows: 通常已包含所需字体

## 错误处理

程序包含完整的错误处理机制：

- 文件存在性检查
- 文件格式验证
- 处理过程异常捕获
- 资源自动清理

## 项目结构

```
videoMerger/
├── video_merger.py        # 主要的合成器类和命令行工具（支持字幕）
├── test.py               # Whisper语音识别和SRT字幕生成工具
├── example.py            # 基本使用示例
├── subtitle_example.py   # 字幕功能演示示例
├── font_helper.py        # 字体问题诊断和解决工具
├── imagemagick_fix.py    # ImageMagick配置修复工具
├── test_subtitle_fix.py  # 字幕功能测试脚本
├── requirements.txt      # 依赖包列表
└── README.md            # 项目说明
```

## 许可证

本项目使用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！ # videoMerger


# 基本下载
python download_wavs.py 4

# 列出文件（显示ID、原名、URL）
python download_wavs.py 4 -l

# 下载到指定目录
python download_wavs.py 4 -d /path/to/download

# 下载后删除服务器文件
python download_wavs.py 4 --delete-after-download

# 仅删除文件夹中所有文件
python download_wavs.py 4 --delete-only

# 删除指定ID的文件
python download_wavs.py 4 --delete-file-id 123