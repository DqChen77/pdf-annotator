"""
PDF标注模块 - 在PDF上添加高亮和注释
"""
import fitz  # PyMuPDF
from typing import List, Dict, Tuple
from config import HIGHLIGHT_COLOR, NOTE_COLOR


class PDFAnnotator:
    """PDF标注器"""
    
    def __init__(self, input_pdf_path: str):
        """
        初始化PDF标注器
        
        Args:
            input_pdf_path: 输入PDF文件路径
        """
        self.input_path = input_pdf_path
        self.doc = fitz.open(input_pdf_path)
    
    def _smart_search_text(self, page, text: str):
        """
        智能文本搜索，尝试多种匹配策略
        
        Args:
            page: PDF页面对象
            text: 要搜索的文本
            
        Returns:
            找到的矩形列表，如果未找到返回None
        """
        # 策略1: 精确匹配
        instances = page.search_for(text)
        if instances:
            return instances
        
        # 策略2: 清理空格后匹配
        clean_text = ' '.join(text.split())
        instances = page.search_for(clean_text)
        if instances:
            return instances
        
        # 策略3: 移除标点符号后匹配
        import string
        no_punct = text.translate(str.maketrans('', '', string.punctuation))
        no_punct_clean = ' '.join(no_punct.split())
        instances = page.search_for(no_punct_clean)
        if instances:
            return instances
        
        # 策略4: 尝试前70%的内容
        if len(text) > 40:
            partial = text[:int(len(text) * 0.7)]
            instances = page.search_for(partial)
            if instances:
                return instances
            
            # 清理后再试
            partial_clean = ' '.join(partial.split())
            instances = page.search_for(partial_clean)
            if instances:
                return instances
        
        # 策略5: 尝试前50%的内容
        if len(text) > 30:
            partial = text[:int(len(text) * 0.5)]
            instances = page.search_for(partial)
            if instances:
                return instances
        
        # 策略6: 尝试前30个单词
        words = text.split()
        if len(words) > 10:
            partial = ' '.join(words[:min(10, len(words))])
            instances = page.search_for(partial)
            if instances:
                return instances
        
        return None
    
    def add_highlight_with_popup(self, page_num: int, text: str, note: str = "", 
                                 color: Tuple[float, float, float] = HIGHLIGHT_COLOR) -> bool:
        """
        在指定页面高亮文本，并添加弹出式注释（不遮挡文字）
        支持跨行文本的完整高亮和智能文本匹配
        
        Args:
            page_num: 页码（从0开始）
            text: 要高亮的文本
            note: 注释内容（点击高亮时弹出）
            color: 高亮颜色 (R, G, B) 范围0-1
            
        Returns:
            是否成功添加高亮和注释
        """
        if page_num >= len(self.doc):
            return False
        
        page = self.doc[page_num]
        
        # 使用智能搜索
        text_instances = self._smart_search_text(page, text)
        
        if not text_instances:
            return False
        
        # text_instances是一个矩形列表，对于跨行文本会有多个矩形
        # 需要为每个矩形都添加高亮（这样整个句子都会被高亮）
        
        # 如果只有一个矩形（单行文本）
        if len(text_instances) == 1:
            rect = text_instances[0]
            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(stroke=color)
            
            # 添加弹出式注释
            if note:
                highlight.set_info(content=note, title="AI标注")
                highlight.set_flags(fitz.PDF_ANNOT_IS_PRINT)
            
            highlight.update()
        
        # 如果有多个矩形（跨行文本）
        else:
            # 为所有矩形添加高亮（使用add_highlight_annot的列表形式）
            # 注意：传入矩形列表会自动创建一个连续的高亮
            highlight = page.add_highlight_annot(text_instances)
            highlight.set_colors(stroke=color)
            
            # 添加弹出式注释
            if note:
                highlight.set_info(content=note, title="AI标注")
                highlight.set_flags(fitz.PDF_ANNOT_IS_PRINT)
            
            highlight.update()
        
        return True
    
    def add_text_annotation(self, page_num: int, x: float, y: float, text: str, 
                           color: Tuple[float, float, float] = NOTE_COLOR) -> bool:
        """
        在指定位置添加文本注释
        
        Args:
            page_num: 页码
            x, y: 注释位置坐标
            text: 注释内容
            color: 注释颜色
            
        Returns:
            是否成功添加注释
        """
        if page_num >= len(self.doc):
            return False
        
        page = self.doc[page_num]
        
        # 创建注释框的位置（右上角）
        rect = fitz.Rect(x, y, x + 20, y + 20)
        
        # 添加文本注释
        annot = page.add_text_annot(rect.tl, text)
        annot.set_colors(stroke=color)
        annot.update()
        
        return True
    
    def add_sticky_note(self, page_num: int, bbox: Tuple[float, float, float, float], 
                       text: str) -> bool:
        """
        在文本块附近添加便签式注释
        
        Args:
            page_num: 页码
            bbox: 文本块边界框 (x0, y0, x1, y1)
            text: 注释内容
            
        Returns:
            是否成功添加注释
        """
        if page_num >= len(self.doc):
            return False
        
        page = self.doc[page_num]
        
        # 在文本块右侧添加注释
        x = bbox[2] + 10  # 右边界 + 10像素
        y = bbox[1]  # 顶部边界
        
        # 确保坐标在页面范围内
        page_rect = page.rect
        if x > page_rect.width - 30:
            x = bbox[0] - 30  # 如果右侧空间不够，放在左侧
        
        return self.add_text_annotation(page_num, x, y, text)
    
    def add_paragraph_summary(self, page_num: int, bbox: tuple, summary_text: str) -> bool:
        """
        在段落开头添加小型总结文本框（不遮挡内容）
        
        Args:
            page_num: 页码
            bbox: 段落边界框 (x0, y0, x1, y1)
            summary_text: 总结内容
            
        Returns:
            是否成功添加总结
        """
        if page_num >= len(self.doc):
            return False
        
        page = self.doc[page_num]
        page_rect = page.rect
        
        # 在段落左侧创建小文本框
        x0 = max(10, bbox[0] - 5)  # 略微向左
        y0 = bbox[1] - 2  # 段落顶部
        x1 = min(bbox[0] + 120, page_rect.width - 10)  # 小文本框宽度
        y1 = y0 + 30  # 固定高度
        
        # 确保不超出页面
        if y1 > page_rect.height - 10:
            y0 = page_rect.height - 40
            y1 = page_rect.height - 10
        
        rect = fitz.Rect(x0, y0, x1, y1)
        
        # 添加自由文本注释（半透明背景）
        try:
            annot = page.add_freetext_annot(
                rect,
                f"📋 {summary_text}",
                fontsize=7,
                text_color=(0.2, 0.2, 0.2),
                fill_color=(0.95, 0.95, 1.0)  # 淡蓝色背景
            )
            annot.set_border(width=0.5, dashes=[1, 1])
            annot.set_opacity(0.9)  # 90%不透明度
            annot.update()
            return True
        except Exception as e:
            # 如果添加失败，静默处理
            return False
    
    def add_margin_note(self, page_num: int, y_position: float, text: str, 
                       max_width: int = 150) -> bool:
        """
        在页面边距添加注释文本框
        
        Args:
            page_num: 页码
            y_position: 垂直位置
            text: 注释内容
            max_width: 文本框最大宽度
            
        Returns:
            是否成功添加注释
        """
        if page_num >= len(self.doc):
            return False
        
        page = self.doc[page_num]
        page_rect = page.rect
        
        # 在右侧边距创建文本框
        margin_x = page_rect.width - max_width - 20
        rect = fitz.Rect(margin_x, y_position, page_rect.width - 20, y_position + 100)
        
        # 添加自由文本注释
        annot = page.add_freetext_annot(
            rect,
            text,
            fontsize=8,
            text_color=(0, 0, 0),
            fill_color=(1, 1, 0.8)  # 淡黄色背景
        )
        annot.set_border(width=1, dashes=[2])
        annot.update()
        
        return True
    
    def save(self, output_path: str):
        """
        保存标注后的PDF
        
        Args:
            output_path: 输出文件路径
        """
        self.doc.save(output_path, garbage=4, deflate=True, clean=True)
        print(f"已保存标注PDF到: {output_path}")
    
    def close(self):
        """关闭PDF文档"""
        if self.doc:
            self.doc.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def annotate_from_analysis(input_pdf: str, output_pdf: str, analysis_results: List[Dict], 
                          all_summaries: List[Dict] = None):
    """
    根据AI分析结果标注PDF（高亮+弹出注释+段落总结）
    
    Args:
        input_pdf: 输入PDF路径
        output_pdf: 输出PDF路径
        analysis_results: AI分析结果列表（包含高亮）
        all_summaries: 段落总结列表
    """
    highlight_count = 0
    failed_count = 0
    summary_count = 0
    
    with PDFAnnotator(input_pdf) as annotator:
        # 第一步：添加高亮和弹出注释
        for result in analysis_results:
            block = result["block"]
            analysis = result["analysis"]
            page_num = block["page"]
            
            # 添加高亮和弹出注释
            for highlight_item in analysis.get("highlights", []):
                highlight_text = highlight_item.get("text", "")
                note_text = highlight_item.get("note", highlight_item.get("reason", ""))
                
                if highlight_text:
                    success = annotator.add_highlight_with_popup(
                        page_num, 
                        highlight_text, 
                        note_text
                    )
                    
                    if success:
                        highlight_count += 1
                    else:
                        failed_count += 1
        
        # 第二步：添加段落总结
        if all_summaries:
            print(f"   - 正在添加段落总结...")
            
            # 重新读取文本块用于定位段落
            from pdf_reader import PDFReader
            with PDFReader(input_pdf) as reader:
                text_blocks = reader.extract_all_text()
            
            for summary_item in all_summaries:
                paragraph_start = summary_item.get("paragraph_start", "")
                summary_text = summary_item.get("summary", "")
                
                if not paragraph_start or not summary_text:
                    continue
                
                # 在文本块中查找匹配的段落
                clean_start = ' '.join(paragraph_start.split())
                
                for block in text_blocks:
                    block_text = block["text"]
                    clean_block_start = ' '.join(block_text[:100].split())
                    
                    # 检查是否匹配
                    if clean_start in clean_block_start or paragraph_start[:50] in block_text[:100]:
                        # 在这个段落开头添加总结
                        success = annotator.add_paragraph_summary(
                            block["page"],
                            block["bbox"],
                            summary_text
                        )
                        
                        if success:
                            summary_count += 1
                        break
        
        # 保存结果
        annotator.save(output_pdf)
    
    print(f"   - ✅ 成功添加 {highlight_count} 个高亮注释")
    if summary_count > 0:
        print(f"   - ✅ 成功添加 {summary_count} 个段落总结")
    if failed_count > 0:
        print(f"   - ⚠️  有 {failed_count} 个标注匹配失败")

