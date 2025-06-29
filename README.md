# 视频合成器 (VideoMerger)

一个简单易用的Python工具，用于将静态图片和音频文件合成为视频文件。

## 功能特点

- 🎬 将静态图片与音频合成为MP4视频
- 🎵 支持多种音频格式（MP3, WAV, AAC, M4A, OGG, FLAC）
- 🖼️ 支持多种图片格式（JPG, PNG, BMP, GIF, TIFF）
- ⏱️ 可自定义视频时长和帧率
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

### 示例

```bash
# 使用音频的完整时长
python video_merger.py image.jpg audio.mp3 output.mp4

# 生成30秒的视频
python video_merger.py image.jpg audio.mp3 output.mp4 30

# 生成30秒、30fps的视频
python video_merger.py image.jpg audio.mp3 output.mp4 30 30
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

## 输出格式

- 视频编码：H.264 (libx264)
- 音频编码：AAC
- 容器格式：MP4

## 注意事项

1. **系统要求**：需要安装FFmpeg（moviepy依赖）
2. **内存使用**：处理大图片时可能占用较多内存
3. **处理时间**：视频时长越长，处理时间越久
4. **文件路径**：确保输入文件路径正确且文件存在

## 错误处理

程序包含完整的错误处理机制：

- 文件存在性检查
- 文件格式验证
- 处理过程异常捕获
- 资源自动清理

## 项目结构

```
videoMerger/
├── video_merger.py     # 主要的合成器类和命令行工具
├── example.py          # 使用示例
├── requirements.txt    # 依赖包列表
└── README.md          # 项目说明
```

## 许可证

本项目使用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！ # videoMerger
