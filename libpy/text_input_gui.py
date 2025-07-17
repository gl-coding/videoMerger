#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
                            QPushButton, QMessageBox, QFileDialog, QGroupBox,
                            QMenuBar, QAction)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ConfigManager:
    """配置文件管理器"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "output_folder": "./output",
            "window_settings": {
                "width": 600,
                "height": 500,
                "x": 100,
                "y": 100
            },
            "file_names": {
                "title": "result_text_title.txt",
                "subtitle": "result_text_subtitle.txt",
                "content": "result_text_rewrite.txt"
            },
            "ui_settings": {
                "font_size": 10,
                "font_family": "Arial"
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置，确保所有必需的键都存在
                return self.merge_config(self.default_config, config)
            else:
                # 如果配置文件不存在，创建默认配置文件
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """保存配置文件"""
        try:
            config_to_save = config if config else self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def merge_config(self, default, user):
        """合并默认配置和用户配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

class TextInputGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("文本输入工具")
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)  # 增加布局间距
        main_layout.setContentsMargins(20, 20, 20, 20)  # 增加边距
        central_widget.setLayout(main_layout)
        
        # 设置字体
        font_family = self.config_manager.get('ui_settings.font_family', 'Microsoft YaHei')
        font_size = self.config_manager.get('ui_settings.font_size', 13)
        font = QFont(font_family, font_size)
        self.setFont(font)
        
        # 创建输入字段组
        input_group = QGroupBox("文本输入")
        input_group.setFont(QFont(font_family, font_size + 1, QFont.Bold))  # 组标题使用更大字体
        input_layout = QVBoxLayout()
        input_layout.setSpacing(15)  # 增加输入框之间的间距
        input_layout.setContentsMargins(15, 20, 15, 15)  # 增加内边距
        
        # Title字段
        title_layout = QHBoxLayout()
        title_label = QLabel("标题 (Title):")
        title_label.setMinimumWidth(150)  # 增加标签宽度
        title_label.setFont(QFont(font_family, font_size, QFont.Bold))
        self.title_input = QLineEdit()
        self.title_input.setMinimumHeight(35)  # 增加输入框高度
        self.title_input.setFont(QFont(font_family, font_size))
        self.title_input.setPlaceholderText("请输入标题...")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        input_layout.addLayout(title_layout)
        
        # Subtitle字段
        subtitle_layout = QHBoxLayout()
        subtitle_label = QLabel("副标题 (Subtitle):")
        subtitle_label.setMinimumWidth(150)  # 增加标签宽度
        subtitle_label.setFont(QFont(font_family, font_size, QFont.Bold))
        self.subtitle_input = QLineEdit()
        self.subtitle_input.setMinimumHeight(35)  # 增加输入框高度
        self.subtitle_input.setFont(QFont(font_family, font_size))
        self.subtitle_input.setPlaceholderText("请输入副标题...")
        subtitle_layout.addWidget(subtitle_label)
        subtitle_layout.addWidget(self.subtitle_input)
        input_layout.addLayout(subtitle_layout)
        
        # Content字段
        content_label = QLabel("内容 (Content):")
        content_label.setFont(QFont(font_family, font_size, QFont.Bold))
        input_layout.addWidget(content_label)
        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(250)  # 增加文本框高度
        self.content_input.setFont(QFont(font_family, font_size))
        self.content_input.setPlaceholderText("请输入内容...")
        input_layout.addWidget(self.content_input)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # 创建文件夹选择组
        folder_group = QGroupBox("保存设置")
        folder_group.setFont(QFont(font_family, font_size + 1, QFont.Bold))  # 组标题使用更大字体
        folder_layout = QVBoxLayout()
        folder_layout.setContentsMargins(15, 20, 15, 15)  # 增加内边距
        
        folder_select_layout = QHBoxLayout()
        folder_label = QLabel("保存文件夹:")
        folder_label.setFont(QFont(font_family, font_size, QFont.Bold))
        self.folder_path_label = QLabel("未选择文件夹")
        self.folder_path_label.setFont(QFont(font_family, font_size))
        self.folder_path_label.setStyleSheet("color: gray; font-style: italic;")
        self.select_folder_btn = QPushButton("选择文件夹")
        self.select_folder_btn.setFont(QFont(font_family, font_size))
        self.select_folder_btn.setMinimumHeight(35)  # 增加按钮高度
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.select_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        folder_select_layout.addWidget(folder_label)
        folder_select_layout.addWidget(self.folder_path_label, 1)
        folder_select_layout.addWidget(self.select_folder_btn)
        folder_layout.addLayout(folder_select_layout)
        
        folder_group.setLayout(folder_layout)
        main_layout.addWidget(folder_group)
        
        # 创建按钮组
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)  # 增加上边距
        
        self.clear_btn = QPushButton("清空所有")
        self.clear_btn.setFont(QFont(font_family, font_size))
        self.clear_btn.setMinimumHeight(40)  # 增加按钮高度
        self.clear_btn.clicked.connect(self.clear_all)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        self.save_btn = QPushButton("保存文件")
        self.save_btn.setFont(QFont(font_family, font_size, QFont.Bold))
        self.save_btn.setMinimumHeight(40)  # 增加按钮高度
        self.save_btn.clicked.connect(self.save_files)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 30px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 重新加载配置
        reload_config_action = QAction('重新加载配置', self)
        reload_config_action.triggered.connect(self.reload_config)
        file_menu.addAction(reload_config_action)
        
        # 保存配置
        save_config_action = QAction('保存配置', self)
        save_config_action.triggered.connect(self.save_config)
        file_menu.addAction(save_config_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def load_settings(self):
        """从配置文件加载设置"""
        # 设置窗口大小和位置
        width = self.config_manager.get('window_settings.width', 600)
        height = self.config_manager.get('window_settings.height', 500)
        x = self.config_manager.get('window_settings.x', 100)
        y = self.config_manager.get('window_settings.y', 100)
        self.setGeometry(x, y, width, height)
        
        # 设置输出文件夹
        output_folder = self.config_manager.get('output_folder', './output')
        # 转换为绝对路径
        if not os.path.isabs(output_folder):
            output_folder = os.path.abspath(output_folder)
        
        self.output_folder = output_folder
        
        # 创建输出文件夹（如果不存在）
        try:
            os.makedirs(self.output_folder, exist_ok=True)
            self.folder_path_label.setText(f"配置文件夹: {self.output_folder}")
            self.folder_path_label.setStyleSheet("color: blue;")
        except Exception as e:
            self.folder_path_label.setText(f"配置文件夹错误: {self.output_folder}")
            self.folder_path_label.setStyleSheet("color: red;")
            print(f"创建输出文件夹失败: {e}")
    
    def save_settings(self):
        """保存设置到配置文件"""
        # 保存窗口设置
        geometry = self.geometry()
        self.config_manager.set('window_settings.width', geometry.width())
        self.config_manager.set('window_settings.height', geometry.height())
        self.config_manager.set('window_settings.x', geometry.x())
        self.config_manager.set('window_settings.y', geometry.y())
        
        # 保存输出文件夹
        self.config_manager.set('output_folder', self.output_folder)
        
        # 保存配置文件
        self.config_manager.save_config()
    
    def select_folder(self):
        """选择保存文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹", self.output_folder)
        if folder:
            self.output_folder = folder
            self.folder_path_label.setText(f"已选择: {folder}")
            self.folder_path_label.setStyleSheet("color: black;")
    
    def clear_all(self):
        """清空所有输入字段"""
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有输入内容吗？", 
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.title_input.clear()
            self.subtitle_input.clear()
            self.content_input.clear()
    
    def save_files(self):
        """保存文件到指定文件夹"""
        # 获取输入内容
        title = self.title_input.text().strip()
        subtitle = self.subtitle_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        # 检查是否有内容
        if not title and not subtitle and not content:
            QMessageBox.warning(self, "警告", "请至少输入一个字段的内容！")
            return
        
        # 确保输出文件夹存在
        try:
            os.makedirs(self.output_folder, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建保存文件夹: {self.output_folder}\n{str(e)}")
            return
        
        try:
            # 从配置文件获取文件名
            title_filename = self.config_manager.get('file_names.title', 'result_text_title.txt')
            subtitle_filename = self.config_manager.get('file_names.subtitle', 'result_text_subtitle.txt')
            content_filename = self.config_manager.get('file_names.content', 'result_text_rewrite.txt')
            
            # 定义文件名
            files_to_save = [
                (title_filename, title),
                (subtitle_filename, subtitle),
                (content_filename, content)
            ]
            
            saved_files = []
            
            # 保存文件
            for filename, text_content in files_to_save:
                if text_content:  # 只保存非空内容
                    file_path = os.path.join(self.output_folder, filename)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text_content)
                    saved_files.append(filename)
            
            # 显示成功消息
            if saved_files:
                saved_list = "\n".join(saved_files)
                QMessageBox.information(self, "保存成功", 
                                      f"以下文件已保存到:\n{self.output_folder}\n\n{saved_list}")
            else:
                QMessageBox.warning(self, "警告", "没有内容需要保存！")
                
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存文件时发生错误:\n{str(e)}")
    
    def reload_config(self):
        """重新加载配置文件"""
        self.config_manager.config = self.config_manager.load_config()
        self.load_settings()
        QMessageBox.information(self, "配置重载", "配置文件已重新加载！")
    
    def save_config(self):
        """保存当前配置"""
        self.save_settings()
        QMessageBox.information(self, "配置保存", "配置已保存到config.json文件！")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "文本输入工具 v1.0\n\n"
                         "一个简单的文本输入和保存工具\n"
                         "支持配置文件自定义设置\n\n"
                         "配置文件: config.json")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.save_settings()
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("文本输入工具")
    app.setApplicationVersion("1.0")
    
    # 创建主窗口
    window = TextInputGUI()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 