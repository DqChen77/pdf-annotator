#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF智能标注工具 - 图形界面版本
适用于Windows系统的友好界面
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import json

# 导入核心功能
from pdf_reader import PDFReader
from ai_analyzer import AIAnalyzer
from pdf_annotator import annotate_from_analysis


class PDFAnnotatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF智能标注工具 - AI助手")
        self.root.geometry("800x700")
        
        # 设置图标（如果有的话）
        try:
            # self.root.iconbitmap('icon.ico')
            pass
        except:
            pass
        
        # 变量
        self.pdf_path = tk.StringVar()
        self.api_key = tk.StringVar()
        self.api_base_url = tk.StringVar(value="https://api.zhizengzeng.com/v1")
        self.model = tk.StringVar(value="gpt-4o")
        self.output_path = tk.StringVar()
        self.is_processing = False
        
        # 标注设置变量
        self.highlight_count_min = tk.IntVar(value=20)
        self.highlight_count_max = tk.IntVar(value=30)
        self.summary_count_min = tk.IntVar(value=5)
        self.summary_count_max = tk.IntVar(value=10)
        self.summary_word_min = tk.IntVar(value=40)
        self.summary_word_max = tk.IntVar(value=80)
        self.term_level = tk.StringVar(value="moderate")
        
        # 颜色设置（RGB 0-255格式，方便GUI显示）
        self.highlight_color = [255, 255, 0]  # 黄色
        self.term_color = [128, 204, 255]  # 浅蓝色
        self.summary_color = [255, 179, 179]  # 淡红色
        
        # 加载配置
        self.load_config()
        
        # 创建界面
        self.create_widgets()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_config(self):
        """加载配置文件"""
        config_file = Path("gui_config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # API配置
                    self.api_key.set(config.get('api_key', ''))
                    self.api_base_url.set(config.get('api_base_url', 'https://api.zhizengzeng.com/v1'))
                    self.model.set(config.get('model', 'gpt-4o'))
                    
                    # 标注设置
                    self.highlight_count_min.set(config.get('highlight_count_min', 20))
                    self.highlight_count_max.set(config.get('highlight_count_max', 30))
                    self.summary_count_min.set(config.get('summary_count_min', 5))
                    self.summary_count_max.set(config.get('summary_count_max', 10))
                    self.summary_word_min.set(config.get('summary_word_min', 40))
                    self.summary_word_max.set(config.get('summary_word_max', 80))
                    self.term_level.set(config.get('term_level', 'moderate'))
                    
                    # 颜色配置
                    self.highlight_color = config.get('highlight_color', [255, 255, 0])
                    self.term_color = config.get('term_color', [128, 204, 255])
                    self.summary_color = config.get('summary_color', [255, 179, 179])
            except:
                pass
    
    def save_config(self):
        """保存配置文件"""
        config = {
            # API配置
            'api_key': self.api_key.get(),
            'api_base_url': self.api_base_url.get(),
            'model': self.model.get(),
            
            # 标注设置
            'highlight_count_min': self.highlight_count_min.get(),
            'highlight_count_max': self.highlight_count_max.get(),
            'summary_count_min': self.summary_count_min.get(),
            'summary_count_max': self.summary_count_max.get(),
            'summary_word_min': self.summary_word_min.get(),
            'summary_word_max': self.summary_word_max.get(),
            'term_level': self.term_level.get(),
            
            # 颜色配置
            'highlight_color': self.highlight_color,
            'term_color': self.term_color,
            'summary_color': self.summary_color
        }
        try:
            # 保存 JSON 配置文件
            with open("gui_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            # 同时保存 .env 文件（确保配置被加载）
            with open(".env", 'w', encoding='utf-8') as f:
                f.write(f"OPENAI_API_KEY={self.api_key.get()}\n")
                if self.api_base_url.get():
                    f.write(f"OPENAI_BASE_URL={self.api_base_url.get()}\n")
                f.write(f"OPENAI_MODEL={self.model.get()}\n")
            
            self.log("✅ 配置已保存")
        except Exception as e:
            self.log(f"⚠️ 保存配置时出错: {str(e)}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="📚 PDF智能标注工具",
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="使用AI自动识别并标注论文中的关键观点",
            font=("Arial", 10)
        )
        subtitle_label.pack()
        
        # 主要内容区域
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. PDF文件选择
        pdf_frame = ttk.LabelFrame(main_frame, text="1️⃣ 选择PDF文件", padding="10")
        pdf_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(pdf_frame, textvariable=self.pdf_path, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(pdf_frame, text="浏览...", command=self.browse_pdf).pack(side=tk.LEFT)
        
        # 2. API配置
        api_frame = ttk.LabelFrame(main_frame, text="2️⃣ API配置", padding="10")
        api_frame.pack(fill=tk.X, pady=5)
        
        # API密钥
        ttk.Label(api_frame, text="API密钥:").grid(row=0, column=0, sticky=tk.W, pady=2)
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key, width=50, show="*")
        api_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        # 显示/隐藏密钥按钮
        self.show_key = False
        def toggle_key():
            self.show_key = not self.show_key
            api_entry.config(show="" if self.show_key else "*")
            toggle_btn.config(text="隐藏" if self.show_key else "显示")
        
        toggle_btn = ttk.Button(api_frame, text="显示", command=toggle_key, width=6)
        toggle_btn.grid(row=0, column=2, pady=2, padx=2)
        
        # API地址
        ttk.Label(api_frame, text="API地址:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(api_frame, textvariable=self.api_base_url, width=50).grid(
            row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # 模型选择
        ttk.Label(api_frame, text="AI模型:").grid(row=2, column=0, sticky=tk.W, pady=2)
        model_combo = ttk.Combobox(
            api_frame, 
            textvariable=self.model,
            values=["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            width=20
        )
        model_combo.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        
        # 帮助文本
        help_text = ttk.Label(
            api_frame,
            text="💡 提示：首次使用需要配置API密钥，之后会自动保存",
            font=("Arial", 9),
            foreground="gray"
        )
        help_text.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # 3. 输出设置
        output_frame = ttk.LabelFrame(main_frame, text="3️⃣ 输出文件（可选）", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(output_frame, textvariable=self.output_path, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_frame, text="浏览...", command=self.browse_output).pack(side=tk.LEFT)
        
        ttk.Label(
            output_frame,
            text="留空则自动生成 原文件名_annotated.pdf",
            font=("Arial", 9),
            foreground="gray"
        ).pack(side=tk.LEFT, padx=10)
        
        # 4. 开始按钮
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(
            button_frame,
            text="🚀 开始标注",
            command=self.start_processing,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹ 停止",
            command=self.stop_processing,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="⚙️ 标注设置",
            command=self.open_settings,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="💾 保存配置",
            command=self.save_config,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
        
        # 5. 进度显示
        progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 进度条
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(fill=tk.X, pady=5)
        
        # 日志输出
        self.log_text = scrolledtext.ScrolledText(
            progress_frame,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(
            status_frame,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=2)
    
    def browse_pdf(self):
        """浏览选择PDF文件"""
        filename = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if filename:
            self.pdf_path.set(filename)
            # 自动设置输出路径
            if not self.output_path.get():
                base = Path(filename).stem
                output = str(Path(filename).parent / f"{base}_annotated.pdf")
                self.output_path.set(output)
    
    def browse_output(self):
        """浏览选择输出文件"""
        filename = filedialog.asksaveasfilename(
            title="保存为",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def set_status(self, message):
        """设置状态栏"""
        self.status_label.config(text=message)
        self.root.update()
    
    def validate_inputs(self):
        """验证输入"""
        if not self.pdf_path.get():
            messagebox.showerror("错误", "请选择PDF文件！")
            return False
        
        if not os.path.exists(self.pdf_path.get()):
            messagebox.showerror("错误", "PDF文件不存在！")
            return False
        
        if not self.api_key.get():
            messagebox.showerror("错误", "请输入API密钥！")
            return False
        
        return True
    
    def start_processing(self):
        """开始处理"""
        if not self.validate_inputs():
            return
        
        if self.is_processing:
            messagebox.showwarning("警告", "正在处理中，请稍候...")
            return
        
        # 保存配置
        self.save_config()
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 设置UI状态
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start()
        
        # 在新线程中处理
        thread = threading.Thread(target=self.process_pdf, daemon=True)
        thread.start()
    
    def stop_processing(self):
        """停止处理"""
        self.is_processing = False
        self.set_status("正在停止...")
    
    def process_pdf(self):
        """处理PDF文件"""
        try:
            input_pdf = self.pdf_path.get()
            output_pdf = self.output_path.get()
            
            if not output_pdf:
                base = Path(input_pdf).stem
                output_pdf = str(Path(input_pdf).parent / f"{base}_annotated.pdf")
            
            self.log(f"📚 正在处理: {os.path.basename(input_pdf)}")
            self.log(f"📝 输出文件: {os.path.basename(output_pdf)}")
            self.log("-" * 60)
            
            # 步骤1: 读取PDF
            self.set_status("正在读取PDF...")
            self.log("\n1️⃣ 正在读取PDF文件...")
            
            with PDFReader(input_pdf) as reader:
                page_count = reader.get_page_count()
                self.log(f"   - 总页数: {page_count}")
                
                text_blocks = reader.extract_all_text()
                self.log(f"   - 提取到 {len(text_blocks)} 个文本块")
            
            if not self.is_processing:
                self.log("\n❌ 用户取消")
                return
            
            # 步骤2: AI分析
            self.set_status("正在使用AI分析...")
            self.log("\n2️⃣ 正在使用AI分析内容...")
            
            # 设置环境变量（确保配置可用）
            os.environ['OPENAI_API_KEY'] = self.api_key.get()
            if self.api_base_url.get():
                os.environ['OPENAI_BASE_URL'] = self.api_base_url.get()
            os.environ['OPENAI_MODEL'] = self.model.get()
            
            # 动态更新config中的颜色配置
            import config
            config.HIGHLIGHT_COLOR = tuple(c/255 for c in self.highlight_color)  # 转换为0-1范围
            config.TERM_HIGHLIGHT_COLOR = tuple(c/255 for c in self.term_color)
            config.SUMMARY_HIGHLIGHT_COLOR = tuple(c/255 for c in self.summary_color)
            
            # 生成自定义提示词
            from config import get_dynamic_analysis_prompt
            custom_prompt = get_dynamic_analysis_prompt(
                highlight_min=self.highlight_count_min.get(),
                highlight_max=self.highlight_count_max.get(),
                summary_min=self.summary_count_min.get(),
                summary_max=self.summary_count_max.get(),
                summary_word_min=self.summary_word_min.get(),
                summary_word_max=self.summary_word_max.get(),
                term_level=self.term_level.get()
            )
            
            self.log(f"   - 使用模型: {self.model.get()}")
            self.log(f"   - 关键观点数量: {self.highlight_count_min.get()}-{self.highlight_count_max.get()}个")
            self.log(f"   - 段落总结数量: {self.summary_count_min.get()}-{self.summary_count_max.get()}个")
            self.log(f"   - 总结字数范围: {self.summary_word_min.get()}-{self.summary_word_max.get()}字")
            self.log(f"   - 术语标注级别: {self.term_level.get()}")
            
            # 直接传入配置参数，更可靠
            analyzer = AIAnalyzer(
                api_key=self.api_key.get(),
                model=self.model.get()
            )
            
            analysis_results = analyzer.analyze_document(text_blocks, custom_prompt=custom_prompt)
            
            if not self.is_processing:
                self.log("\n❌ 用户取消")
                return
            
            total_highlights = sum(len(r["analysis"].get("highlights", [])) 
                                  for r in analysis_results)
            self.log(f"   - 完成分析，识别到 {len(analysis_results)} 个重要片段")
            self.log(f"   - 共标记 {total_highlights} 个关键观点")
            
            summaries = analyzer.get_cached_summaries()
            if summaries:
                self.log(f"   - 获取到 {len(summaries)} 个段落总结")
            
            # 步骤3: 标注PDF
            self.set_status("正在生成标注PDF...")
            self.log("\n3️⃣ 正在生成标注PDF...")
            
            annotate_from_analysis(input_pdf, output_pdf, analysis_results, summaries)
            
            self.log("\n" + "=" * 60)
            self.log("✅ 处理完成！")
            self.log(f"📄 已生成标注PDF: {output_pdf}")
            self.log("=" * 60)
            
            self.set_status("完成！")
            
            # 显示完成对话框
            result = messagebox.askyesno(
                "完成",
                f"PDF标注完成！\n\n输出文件:\n{output_pdf}\n\n是否打开文件所在文件夹？"
            )
            
            if result:
                # 打开文件所在文件夹
                import subprocess
                if sys.platform == 'win32':
                    subprocess.run(['explorer', '/select,', output_pdf])
                elif sys.platform == 'darwin':
                    subprocess.run(['open', '-R', output_pdf])
                else:
                    subprocess.run(['xdg-open', os.path.dirname(output_pdf)])
        
        except Exception as e:
            self.log(f"\n❌ 错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("错误", f"处理失败:\n{str(e)}")
            self.set_status("错误")
        
        finally:
            # 恢复UI状态
            self.is_processing = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.progress.stop()
    
    def open_settings(self):
        """打开设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("标注设置")
        settings_window.geometry("600x650")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 创建notebook（标签页）
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 数量设置标签页
        count_frame = ttk.Frame(notebook, padding="20")
        notebook.add(count_frame, text="📊 数量设置")
        
        # 关键观点数量
        ttk.Label(count_frame, text="关键观点高亮数量", font=("Arial", 11, "bold")).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(count_frame, text="最小数量:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(count_frame, from_=10, to=50, textvariable=self.highlight_count_min, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(count_frame, text="个").grid(row=1, column=2, sticky=tk.W)
        
        ttk.Label(count_frame, text="最大数量:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(count_frame, from_=10, to=50, textvariable=self.highlight_count_max, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=5)
        ttk.Label(count_frame, text="个").grid(row=2, column=2, sticky=tk.W)
        
        ttk.Separator(count_frame, orient='horizontal').grid(
            row=3, column=0, columnspan=3, sticky='ew', pady=15)
        
        # 段落总结数量
        ttk.Label(count_frame, text="段落总结数量", font=("Arial", 11, "bold")).grid(
            row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(count_frame, text="最小数量:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(count_frame, from_=3, to=20, textvariable=self.summary_count_min, width=10).grid(
            row=5, column=1, sticky=tk.W, padx=5)
        ttk.Label(count_frame, text="个").grid(row=5, column=2, sticky=tk.W)
        
        ttk.Label(count_frame, text="最大数量:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(count_frame, from_=3, to=20, textvariable=self.summary_count_max, width=10).grid(
            row=6, column=1, sticky=tk.W, padx=5)
        ttk.Label(count_frame, text="个").grid(row=6, column=2, sticky=tk.W)
        
        ttk.Separator(count_frame, orient='horizontal').grid(
            row=7, column=0, columnspan=3, sticky='ew', pady=15)
        
        # 总结字数
        ttk.Label(count_frame, text="段落总结字数", font=("Arial", 11, "bold")).grid(
            row=8, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(count_frame, text="最小字数:").grid(row=9, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(count_frame, from_=20, to=100, textvariable=self.summary_word_min, width=10).grid(
            row=9, column=1, sticky=tk.W, padx=5)
        ttk.Label(count_frame, text="字").grid(row=9, column=2, sticky=tk.W)
        
        ttk.Label(count_frame, text="最大字数:").grid(row=10, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(count_frame, from_=20, to=150, textvariable=self.summary_word_max, width=10).grid(
            row=10, column=1, sticky=tk.W, padx=5)
        ttk.Label(count_frame, text="字").grid(row=10, column=2, sticky=tk.W)
        
        ttk.Separator(count_frame, orient='horizontal').grid(
            row=11, column=0, columnspan=3, sticky='ew', pady=15)
        
        # 术语标注积极程度
        ttk.Label(count_frame, text="术语标注积极程度", font=("Arial", 11, "bold")).grid(
            row=12, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        term_levels = [
            ("保守 - 只标注核心专业术语", "conservative"),
            ("适中 - 标注专业术语和较难词汇 (推荐)", "moderate"),
            ("积极 - 标注所有可能困难的词汇", "aggressive")
        ]
        
        for i, (text, value) in enumerate(term_levels):
            ttk.Radiobutton(
                count_frame, 
                text=text, 
                variable=self.term_level, 
                value=value
            ).grid(row=13+i, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        # 2. 颜色设置标签页
        color_frame = ttk.Frame(notebook, padding="20")
        notebook.add(color_frame, text="🎨 颜色设置")
        
        def choose_color(color_type):
            """选择颜色"""
            from tkinter import colorchooser
            if color_type == "highlight":
                current = self.highlight_color
            elif color_type == "term":
                current = self.term_color
            else:
                current = self.summary_color
            
            # 转换为十六进制
            current_hex = f"#{current[0]:02x}{current[1]:02x}{current[2]:02x}"
            color = colorchooser.askcolor(initialcolor=current_hex, title="选择颜色")
            
            if color[0]:  # 如果用户选择了颜色
                rgb = [int(c) for c in color[0]]
                if color_type == "highlight":
                    self.highlight_color = rgb
                    highlight_preview.config(bg=color[1])
                elif color_type == "term":
                    self.term_color = rgb
                    term_preview.config(bg=color[1])
                else:
                    self.summary_color = rgb
                    summary_preview.config(bg=color[1])
        
        # 关键观点颜色
        ttk.Label(color_frame, text="关键观点高亮颜色", font=("Arial", 11, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        highlight_frame = ttk.Frame(color_frame)
        highlight_frame.grid(row=1, column=0, sticky=tk.W, pady=10)
        
        highlight_preview = tk.Label(
            highlight_frame, 
            text="  预览  ", 
            bg=f"#{self.highlight_color[0]:02x}{self.highlight_color[1]:02x}{self.highlight_color[2]:02x}",
            width=15,
            relief=tk.RAISED
        )
        highlight_preview.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            highlight_frame, 
            text="选择颜色", 
            command=lambda: choose_color("highlight")
        ).pack(side=tk.LEFT)
        
        # 术语高亮颜色
        ttk.Label(color_frame, text="术语高亮颜色", font=("Arial", 11, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=(15, 5))
        
        term_frame = ttk.Frame(color_frame)
        term_frame.grid(row=3, column=0, sticky=tk.W, pady=10)
        
        term_preview = tk.Label(
            term_frame, 
            text="  预览  ", 
            bg=f"#{self.term_color[0]:02x}{self.term_color[1]:02x}{self.term_color[2]:02x}",
            width=15,
            relief=tk.RAISED
        )
        term_preview.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            term_frame, 
            text="选择颜色", 
            command=lambda: choose_color("term")
        ).pack(side=tk.LEFT)
        
        # 段落总结颜色
        ttk.Label(color_frame, text="段落总结高亮颜色", font=("Arial", 11, "bold")).grid(
            row=4, column=0, sticky=tk.W, pady=(15, 5))
        
        summary_frame = ttk.Frame(color_frame)
        summary_frame.grid(row=5, column=0, sticky=tk.W, pady=10)
        
        summary_preview = tk.Label(
            summary_frame, 
            text="  预览  ", 
            bg=f"#{self.summary_color[0]:02x}{self.summary_color[1]:02x}{self.summary_color[2]:02x}",
            width=15,
            relief=tk.RAISED
        )
        summary_preview.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            summary_frame, 
            text="选择颜色", 
            command=lambda: choose_color("summary")
        ).pack(side=tk.LEFT)
        
        # 重置为默认颜色
        def reset_colors():
            self.highlight_color = [255, 255, 0]
            self.term_color = [128, 204, 255]
            self.summary_color = [255, 179, 179]
            highlight_preview.config(bg="#ffff00")
            term_preview.config(bg="#80ccff")
            summary_preview.config(bg="#ffb3b3")
        
        ttk.Button(
            color_frame,
            text="🔄 恢复默认颜色",
            command=reset_colors
        ).grid(row=6, column=0, pady=20)
        
        # 底部按钮
        button_frame = ttk.Frame(settings_window, padding="10")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        def save_and_close():
            self.save_config()
            messagebox.showinfo("保存成功", "设置已保存！", parent=settings_window)
            settings_window.destroy()
        
        ttk.Button(
            button_frame,
            text="✅ 保存设置",
            command=save_and_close,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="❌ 取消",
            command=settings_window.destroy,
            width=20
        ).pack(side=tk.RIGHT, padx=5)
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_processing:
            result = messagebox.askyesnocancel(
                "确认退出",
                "正在处理中，确定要退出吗？"
            )
            if not result:
                return
        
        self.save_config()
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = PDFAnnotatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

