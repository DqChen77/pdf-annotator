"""
PDF读取和文本提取模块
"""
import fitz  # PyMuPDF
from typing import List, Dict, Tuple


class PDFReader:
    """PDF读取器"""
    
    def __init__(self, pdf_path: str):
        """
        初始化PDF读取器
        
        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def get_page_count(self) -> int:
        """获取页数"""
        return len(self.doc)
    
    def extract_text_by_page(self, page_num: int) -> str:
        """
        提取指定页的文本
        
        Args:
            page_num: 页码（从0开始）
            
        Returns:
            页面文本内容
        """
        if page_num >= len(self.doc):
            return ""
        
        page = self.doc[page_num]
        return page.get_text()
    
    def extract_text_blocks(self, page_num: int) -> List[Dict]:
        """
        提取页面的文本块（包含位置信息）
        
        Args:
            page_num: 页码（从0开始）
            
        Returns:
            文本块列表，每个块包含文本和位置信息
        """
        if page_num >= len(self.doc):
            return []
        
        page = self.doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        text_blocks = []
        for block in blocks:
            if block.get("type") == 0:  # 文本块
                block_text = ""
                block_bbox = block["bbox"]
                
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span.get("text", "")
                    block_text += "\n"
                
                if block_text.strip():
                    text_blocks.append({
                        "text": block_text.strip(),
                        "bbox": block_bbox,  # (x0, y0, x1, y1)
                        "page": page_num
                    })
        
        return text_blocks
    
    def search_text_in_page(self, page_num: int, search_text: str) -> List[Tuple[float, float, float, float]]:
        """
        在指定页面搜索文本，返回所有匹配位置
        
        Args:
            page_num: 页码
            search_text: 要搜索的文本
            
        Returns:
            匹配位置的边界框列表 [(x0, y0, x1, y1), ...]
        """
        if page_num >= len(self.doc):
            return []
        
        page = self.doc[page_num]
        # 搜索文本，返回矩形区域
        rects = page.search_for(search_text)
        return [tuple(rect) for rect in rects]
    
    def extract_all_text(self) -> List[Dict]:
        """
        提取所有页面的文本块
        
        Returns:
            所有文本块列表
        """
        all_blocks = []
        for page_num in range(len(self.doc)):
            blocks = self.extract_text_blocks(page_num)
            all_blocks.extend(blocks)
        
        return all_blocks
    
    def close(self):
        """关闭PDF文档"""
        if self.doc:
            self.doc.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

