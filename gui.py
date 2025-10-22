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
                    self.api_key.set(config.get('api_key', ''))
                    self.api_base_url.set(config.get('api_base_url', 'https://api.zhizengzeng.com/v1'))
                    self.model.set(config.get('model', 'gpt-4o'))
            except:
                pass
    
    def save_config(self):
        """保存配置文件"""
        config = {
            'api_key': self.api_key.get(),
            'api_base_url': self.api_base_url.get(),
            'model': self.model.get()
        }
        try:
            with open("gui_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except:
            pass
    
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
            
            # 设置环境变量
            os.environ['OPENAI_API_KEY'] = self.api_key.get()
            if self.api_base_url.get():
                os.environ['OPENAI_BASE_URL'] = self.api_base_url.get()
            os.environ['OPENAI_MODEL'] = self.model.get()
            
            analyzer = AIAnalyzer()
            self.log(f"   - 使用模型: {analyzer.model}")
            
            analysis_results = analyzer.analyze_document(text_blocks)
            
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

