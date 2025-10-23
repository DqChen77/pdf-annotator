"""
PDF标注模块 - 在PDF上添加高亮和注释
"""
import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional
from config import HIGHLIGHT_COLOR, TERM_HIGHLIGHT_COLOR, SUMMARY_HIGHLIGHT_COLOR, NOTE_COLOR


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
    
    def _get_first_occurrence_rects(self, instances):
        """
        从矩形列表中提取第一次出现的所有矩形（支持跨行）
        
        Args:
            instances: 矩形列表（可能包含多次出现）
            
        Returns:
            第一次出现的所有矩形（连续的矩形被认为是同一次出现）
        """
        if not instances:
            return None
        
        if len(instances) == 1:
            return instances
        
        # 按照y坐标（从上到下）和x坐标（从左到右）排序
        sorted_instances = sorted(instances, key=lambda r: (r.y0, r.x0))
        
        # 第一次出现的矩形集合
        first_occurrence = [sorted_instances[0]]
        
        # 检查后续矩形是否与第一个矩形连续（跨行判断）
        for i in range(1, len(sorted_instances)):
            prev_rect = first_occurrence[-1]
            curr_rect = sorted_instances[i]
            
            # 判断是否连续：
            # 1. 同一行：y坐标接近，x坐标递增
            # 2. 下一行：y坐标递增，且y差距不太大（换行）
            y_diff = abs(curr_rect.y0 - prev_rect.y0)
            is_same_line = y_diff < 5  # 同一行的容差
            is_next_line = 5 <= y_diff <= 30  # 换行的y差距范围
            
            if is_same_line or is_next_line:
                # 检查x坐标是否合理（下一行应该在左边开始，或者同行在右边）
                if is_next_line and curr_rect.x0 < prev_rect.x1 + 100:
                    # 换行，且新行起始位置合理
                    first_occurrence.append(curr_rect)
                elif is_same_line and curr_rect.x0 >= prev_rect.x0:
                    # 同一行，且在右边
                    first_occurrence.append(curr_rect)
                else:
                    # 不连续，说明是新的出现
                    break
            else:
                # y差距太大，说明是新的出现
                break
        
        return first_occurrence
    
    def _smart_search_text(self, page, text: str, first_only: bool = False):
        """
        智能文本搜索，尝试多种匹配策略
        
        Args:
            page: PDF页面对象
            text: 要搜索的文本
            first_only: 是否只返回第一次出现（用于术语标注去重）
            
        Returns:
            找到的矩形列表，如果未找到返回None
        """
        # 策略1: 精确匹配
        instances = page.search_for(text)
        if instances:
            return self._get_first_occurrence_rects(instances) if first_only else instances
        
        # 策略2: 清理空格后匹配
        clean_text = ' '.join(text.split())
        instances = page.search_for(clean_text)
        if instances:
            return self._get_first_occurrence_rects(instances) if first_only else instances
        
        # 策略3: 移除标点符号后匹配
        import string
        no_punct = text.translate(str.maketrans('', '', string.punctuation))
        no_punct_clean = ' '.join(no_punct.split())
        instances = page.search_for(no_punct_clean)
        if instances:
            return self._get_first_occurrence_rects(instances) if first_only else instances
        
        # 策略4: 尝试前70%的内容
        if len(text) > 40:
            partial = text[:int(len(text) * 0.7)]
            instances = page.search_for(partial)
            if instances:
                return self._get_first_occurrence_rects(instances) if first_only else instances
            
            # 清理后再试
            partial_clean = ' '.join(partial.split())
            instances = page.search_for(partial_clean)
            if instances:
                return self._get_first_occurrence_rects(instances) if first_only else instances
        
        # 策略5: 尝试前50%的内容
        if len(text) > 30:
            partial = text[:int(len(text) * 0.5)]
            instances = page.search_for(partial)
            if instances:
                return self._get_first_occurrence_rects(instances) if first_only else instances
        
        # 策略6: 尝试前30个单词
        words = text.split()
        if len(words) > 10:
            partial = ' '.join(words[:min(10, len(words))])
            instances = page.search_for(partial)
            if instances:
                return self._get_first_occurrence_rects(instances) if first_only else instances
        
        return None
    
    def add_highlight_with_popup(self, page_num: int, text: str, note: str = "", 
                                 color: Tuple[float, float, float] = HIGHLIGHT_COLOR,
                                 first_only: bool = False) -> bool:
        """
        在指定页面高亮文本，并添加弹出式注释（不遮挡文字）
        支持跨行文本的完整高亮和智能文本匹配
        
        Args:
            page_num: 页码（从0开始）
            text: 要高亮的文本
            note: 注释内容（点击高亮时弹出）
            color: 高亮颜色 (R, G, B) 范围0-1
            first_only: 是否仅高亮第一次出现（用于术语去重）
            
        Returns:
            是否成功添加高亮和注释
        """
        if page_num >= len(self.doc):
            return False
        
        page = self.doc[page_num]
        
        # 使用智能搜索
        text_instances = self._smart_search_text(page, text, first_only=first_only)
        
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
    
    def add_paragraph_summary(self, page_num: int, paragraph_text: str, summary_text: str) -> bool:
        """
        在段落第一句话的第一个字符上添加红色高亮，悬停显示详细段落大意
        
        Args:
            page_num: 页码
            paragraph_text: 完整段落文本
            summary_text: 段落总结内容（详细版）
            
        Returns:
            是否成功添加总结
        """
        if page_num >= len(self.doc):
            return False
        
        page = self.doc[page_num]
        
        # 提取第一句话
        first_sentence = self._extract_first_sentence(paragraph_text)
        
        if not first_sentence or len(first_sentence) < 5:
            first_sentence = paragraph_text[:50].strip()
        
        # 搜索第一句话的第一个词（用于定位）
        first_words = ' '.join(first_sentence.split()[:3])  # 前3个词
        
        if not first_words:
            return False
        
        # 在页面中搜索第一个词的位置
        text_instances = self._smart_search_text(page, first_words, first_only=True)
        
        if not text_instances:
            # 如果找不到，尝试只用第一个词
            first_word = first_sentence.split()[0] if first_sentence.split() else ""
            if first_word:
                text_instances = self._smart_search_text(page, first_word, first_only=True)
        
        if not text_instances:
            return False
        
        # 获取第一个词的矩形位置
        first_rect = text_instances[0]
        
        try:
            # 使用高亮注释（红色高亮）
            annot = page.add_highlight_annot([first_rect])
            
            # 设置红色高亮
            annot.set_colors(stroke=(1.0, 0.3, 0.3))  # 红色
            annot.set_info(title="📋 段落大意", content=summary_text)
            annot.set_opacity(0.5)  # 高亮透明度
            annot.update()
            
            return True
        except Exception as e:
            return False
    
    def _extract_first_sentence(self, text: str) -> str:
        """
        提取文本的第一句话
        
        Args:
            text: 完整文本
            
        Returns:
            第一句话
        """
        import re
        
        # 查找第一个句子结束符（. ! ?）后跟空格或换行
        # 但要排除缩写（如 Dr. Mr. U.S.）
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text, maxsplit=1)
        
        if len(sentences) > 0:
            first_sentence = sentences[0].strip()
            # 如果第一句太长（超过200字符），截断
            if len(first_sentence) > 200:
                first_sentence = first_sentence[:200].strip()
            return first_sentence
        
        return text[:100].strip()
    
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
    根据AI分析结果标注PDF（双色高亮+弹出注释+段落总结）
    
    Args:
        input_pdf: 输入PDF路径
        output_pdf: 输出PDF路径
        analysis_results: AI分析结果列表（包含高亮和术语）
        all_summaries: 段落总结列表
    """
    insight_count = 0  # 黄色观点高亮
    term_count = 0     # 蓝色术语高亮
    failed_count = 0
    summary_count = 0
    annotated_terms = set()  # 追踪已标注的术语，防止重复
    
    with PDFAnnotator(input_pdf) as annotator:
        # 第一步：添加高亮和弹出注释（支持双色）
        for result in analysis_results:
            block = result["block"]
            analysis = result["analysis"]
            page_num = block["page"]
            
            # 添加高亮和弹出注释
            for highlight_item in analysis.get("highlights", []):
                highlight_text = highlight_item.get("text", "")
                note_text = highlight_item.get("note", highlight_item.get("reason", ""))
                highlight_type = highlight_item.get("type", "insight")  # 默认为观点
                
                if not highlight_text:
                    continue
                
                # 对于术语，进行二次去重检查（防止AI或映射层遗漏）
                if highlight_type == "term":
                    term_key = highlight_text.lower().strip()
                    
                    # 检查是否已标注过完全相同的术语
                    if term_key in annotated_terms:
                        continue
                    
                    # 检查包含关系（避免 "oxytocin" 和 "oxytocin levels" 同时出现）
                    should_skip = False
                    for annotated in list(annotated_terms):
                        if term_key in annotated or annotated in term_key:
                            # 存在包含关系，保留更长的版本
                            if len(term_key) > len(annotated):
                                # 新术语更长，移除旧的（虽然已经标注了，但记录下来避免后续重复）
                                annotated_terms.discard(annotated)
                            else:
                                # 旧术语更长或相等，跳过新术语
                                should_skip = True
                                break
                    
                    if should_skip:
                        continue
                    
                    # 记录这个术语
                    annotated_terms.add(term_key)
                
                # 根据类型选择颜色和标注策略
                if highlight_type == "term":
                    color = TERM_HIGHLIGHT_COLOR  # 蓝色：术语
                    first_only = True             # 术语：只标注第一次出现，但支持跨行
                else:
                    color = HIGHLIGHT_COLOR       # 黄色：观点
                    first_only = False            # 观点：标注所有出现（通常只有一次）
                
                # first_only=True 会使用 _get_first_occurrence_rects 提取第一次出现的所有矩形
                # 这样既避免了重复标注，又能完整高亮跨行的术语
                success = annotator.add_highlight_with_popup(
                    page_num, 
                    highlight_text, 
                    note_text,
                    color=color,
                    first_only=first_only
                )
                
                if success:
                    if highlight_type == "term":
                        term_count += 1
                    else:
                        insight_count += 1
                else:
                    failed_count += 1
        
        # 第二步：添加段落总结（在第一个字符添加红色popup图标）
        if all_summaries:
            print(f"   - 正在添加段落总结图标...")
            
            # 重新读取文本块用于定位段落
            from pdf_reader import PDFReader
            with PDFReader(input_pdf) as reader:
                text_blocks = reader.extract_all_text()
            
            unmatched_summaries = []
            
            for summary_item in all_summaries:
                paragraph_start = summary_item.get("paragraph_start", "")
                summary_text = summary_item.get("summary", "")
                
                if not paragraph_start or not summary_text:
                    continue
                
                # 在文本块中查找匹配的段落（更智能的匹配）
                clean_start = ' '.join(paragraph_start.split()).lower()
                matched = False
                
                for block in text_blocks:
                    block_text = block["text"]
                    clean_block = ' '.join(block_text.split()).lower()
                    
                    # 多种匹配策略
                    # 策略1: 前20个字符匹配
                    if clean_start[:20] in clean_block[:150]:
                        success = annotator.add_paragraph_summary(
                            block["page"],
                            block_text,  # 传递完整段落文本
                            summary_text
                        )
                        if success:
                            summary_count += 1
                            matched = True
                        break
                    
                    # 策略2: 前10个字符匹配（更宽松）
                    if clean_start[:10] in clean_block[:100]:
                        success = annotator.add_paragraph_summary(
                            block["page"],
                            block_text,  # 传递完整段落文本
                            summary_text
                        )
                        if success:
                            summary_count += 1
                            matched = True
                        break
                
                if not matched:
                    unmatched_summaries.append(paragraph_start[:30])
            
            if unmatched_summaries:
                print(f"   ⚠️  有 {len(unmatched_summaries)} 个段落总结未能定位")
                for text in unmatched_summaries[:3]:
                    print(f"      - {text}...")
        
        # 保存结果
        annotator.save(output_pdf)
    
    print(f"   - ✅ 成功添加 {insight_count} 个观点高亮（黄色）")
    print(f"   - ✅ 成功添加 {term_count} 个术语高亮（蓝色）")
    if summary_count > 0:
        print(f"   - ✅ 成功添加 {summary_count} 个段落总结（红色💬图标，悬停查看详细内容）")
    if failed_count > 0:
        print(f"   - ⚠️  有 {failed_count} 个标注匹配失败")

