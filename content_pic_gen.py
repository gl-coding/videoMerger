#!/usr/bin/env python3
"""
图片背景生成器
将输入图片居中放置在指定尺寸的黑色背景上
"""

import os
import sys
import argparse
from PIL import Image, ImageDraw
import requests
from urllib.parse import urlparse
import tempfile

class ContentPicGenerator:
    def __init__(self, bg_width=1024, bg_height=573, bg_color=(0, 0, 0)):
        """
        初始化图片生成器
        
        Args:
            bg_width: 背景宽度，默认1024
            bg_height: 背景高度，默认573
            bg_color: 背景颜色，默认黑色(0,0,0)
        """
        self.bg_width = bg_width
        self.bg_height = bg_height
        self.bg_color = bg_color
    
    def is_url(self, path):
        """判断是否为URL"""
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def download_image(self, url, timeout=30):
        """
        从URL下载图片
        
        Args:
            url: 图片URL
            timeout: 超时时间
            
        Returns:
            临时文件路径
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # 创建临时文件
            suffix = os.path.splitext(urlparse(url).path)[1] or '.jpg'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            
            # 下载图片
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            raise Exception(f"下载图片失败: {str(e)}")
    
    def load_image(self, image_path):
        """
        加载图片
        
        Args:
            image_path: 图片路径或URL
            
        Returns:
            PIL Image对象
        """
        temp_file = None
        
        try:
            # 如果是URL，先下载
            if self.is_url(image_path):
                print(f"正在下载图片: {image_path}")
                temp_file = self.download_image(image_path)
                actual_path = temp_file
            else:
                actual_path = image_path
            
            # 检查文件是否存在
            if not os.path.exists(actual_path):
                raise FileNotFoundError(f"图片文件不存在: {actual_path}")
            
            # 加载图片
            image = Image.open(actual_path)
            
            # 转换为RGB模式（处理RGBA、P等模式）
            if image.mode != 'RGB':
                # 如果有透明通道，先创建白色背景
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'RGBA':
                        background.paste(image, mask=image.split()[-1])
                    else:
                        background.paste(image, mask=image.split()[-1])
                    image = background
                else:
                    image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            raise Exception(f"加载图片失败: {str(e)}")
        
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def calculate_fit_size(self, img_width, img_height, max_width, max_height):
        """
        计算图片适应尺寸（保持宽高比）
        
        Args:
            img_width: 原图宽度
            img_height: 原图高度
            max_width: 最大宽度
            max_height: 最大高度
            
        Returns:
            (新宽度, 新高度)
        """
        # 计算缩放比例
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        
        # 选择较小的比例以确保图片完全适应
        scale_ratio = min(width_ratio, height_ratio)
        
        # 计算新尺寸
        new_width = int(img_width * scale_ratio)
        new_height = int(img_height * scale_ratio)
        
        return new_width, new_height
    
    def generate(self, image_path, output_path=None, fit_mode='fit', padding=20):
        """
        生成居中图片
        
        Args:
            image_path: 输入图片路径或URL
            output_path: 输出路径，默认为 centered_图片名
            fit_mode: 适应模式 ('fit': 完全适应, 'fill': 填充满, 'stretch': 拉伸)
            padding: 内边距
            
        Returns:
            输出文件路径
        """
        try:
            # 加载原图
            print(f"加载图片: {image_path}")
            original_image = self.load_image(image_path)
            orig_width, orig_height = original_image.size
            
            print(f"原图尺寸: {orig_width}x{orig_height}")
            print(f"目标背景: {self.bg_width}x{self.bg_height}")
            
            # 创建黑色背景
            background = Image.new('RGB', (self.bg_width, self.bg_height), self.bg_color)
            
            # 计算可用空间（减去内边距）
            available_width = self.bg_width - 2 * padding
            available_height = self.bg_height - 2 * padding
            
            # 根据适应模式处理图片
            if fit_mode == 'fit':
                # 完全适应：保持宽高比，确保图片完全显示
                new_width, new_height = self.calculate_fit_size(
                    orig_width, orig_height, available_width, available_height
                )
                resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
            elif fit_mode == 'fill':
                # 填充满：保持宽高比，可能裁剪图片
                width_ratio = available_width / orig_width
                height_ratio = available_height / orig_height
                scale_ratio = max(width_ratio, height_ratio)  # 选择较大的比例
                
                new_width = int(orig_width * scale_ratio)
                new_height = int(orig_height * scale_ratio)
                resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 如果超出边界，需要裁剪
                if new_width > available_width or new_height > available_height:
                    left = (new_width - available_width) // 2
                    top = (new_height - available_height) // 2
                    right = left + available_width
                    bottom = top + available_height
                    resized_image = resized_image.crop((left, top, right, bottom))
                    new_width, new_height = available_width, available_height
                    
            elif fit_mode == 'stretch':
                # 拉伸：直接拉伸到目标尺寸
                new_width, new_height = available_width, available_height
                resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            else:
                raise ValueError(f"不支持的适应模式: {fit_mode}")
            
            print(f"调整后尺寸: {new_width}x{new_height}")
            
            # 计算居中位置
            x = (self.bg_width - new_width) // 2
            y = (self.bg_height - new_height) // 2
            
            print(f"居中位置: ({x}, {y})")
            
            # 将图片粘贴到背景上
            background.paste(resized_image, (x, y))
            
            # 生成输出文件名
            if output_path is None:
                if self.is_url(image_path):
                    filename = f"centered_{os.path.basename(urlparse(image_path).path)}"
                    if not filename or filename == "centered_":
                        filename = "centered_image.jpg"
                else:
                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    ext = os.path.splitext(image_path)[1] or '.jpg'
                    filename = f"centered_{base_name}{ext}"
                
                output_path = os.path.join(os.getcwd(), filename)
            
            # 保存图片
            background.save(output_path, 'JPEG', quality=95)
            
            print(f"✓ 图片已保存: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"✗ 生成失败: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='图片背景生成器 - 将图片居中放置在黑色背景上')
    parser.add_argument('image_path', help='输入图片路径或URL')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-w', '--width', type=int, default=1024, help='背景宽度 (默认: 1024)')
    parser.add_argument('--height', type=int, default=573, help='背景高度 (默认: 571)')
    parser.add_argument('--fit-mode', choices=['fit', 'fill', 'stretch'], default='fit',
                       help='适应模式: fit=完全适应, fill=填充满, stretch=拉伸 (默认: fit)')
    parser.add_argument('--padding', type=int, default=20, help='内边距 (默认: 20)')
    parser.add_argument('--bg-color', default='black', help='背景颜色 (默认: black)')
    
    args = parser.parse_args()
    
    # 解析背景颜色
    if args.bg_color.lower() == 'black':
        bg_color = (0, 0, 0)
    elif args.bg_color.lower() == 'white':
        bg_color = (255, 255, 255)
    elif args.bg_color.startswith('#'):
        # 十六进制颜色
        hex_color = args.bg_color[1:]
        bg_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        # 尝试解析为RGB
        try:
            bg_color = tuple(map(int, args.bg_color.split(',')))
        except:
            print(f"无法解析背景颜色: {args.bg_color}")
            sys.exit(1)
    
    try:
        # 创建生成器
        generator = ContentPicGenerator(
            bg_width=args.width,
            bg_height=args.height,
            bg_color=bg_color
        )
        
        # 生成图片
        output_path = generator.generate(
            image_path=args.image_path,
            output_path=args.output,
            fit_mode=args.fit_mode,
            padding=args.padding
        )
        
        print(f"\n🎉 处理完成!")
        print(f"输出文件: {output_path}")
        
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 