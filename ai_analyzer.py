"""
AI分析模块 - 使用OpenAI API分析文本内容
"""
import json
import time
from typing import List, Dict, Optional
from openai import OpenAI
import tiktoken
from config import (
    get_openai_api_key,
    get_openai_model,
    get_openai_base_url,
    SYSTEM_PROMPT,
    ANALYSIS_PROMPT,
    MAX_TOKENS_PER_CHUNK
)


class AIAnalyzer:
    """AI文本分析器"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化AI分析器
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
        """
        # 动态获取配置（支持运行时设置环境变量）
        self.api_key = api_key or get_openai_api_key()
        self.model = model or get_openai_model()
        
        if not self.api_key:
            raise ValueError("请配置OPENAI_API_KEY（在GUI中输入或在.env文件中设置）")
        
        # 初始化OpenAI客户端
        client_args = {"api_key": self.api_key}
        base_url = get_openai_base_url()
        if base_url:
            client_args["base_url"] = base_url
        
        self.client = OpenAI(**client_args)
        
        # 初始化tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """计算文本的token数"""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str, max_tokens: int = MAX_TOKENS_PER_CHUNK) -> List[str]:
        """
        将长文本分块
        
        Args:
            text: 输入文本
            max_tokens: 每块最大token数
            
        Returns:
            文本块列表
        """
        # 按段落分割
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            test_chunk = current_chunk + "\n\n" + para if current_chunk else para
            
            if self.count_tokens(test_chunk) <= max_tokens:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def analyze_text(self, text: str, retry_count: int = 3) -> Dict:
        """
        分析文本，识别关键点和生成总结
        
        Args:
            text: 要分析的文本
            retry_count: 重试次数
            
        Returns:
            分析结果，包含highlights和summary
        """
        prompt = ANALYSIS_PROMPT.format(text=text)
        
        for attempt in range(retry_count):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                result_text = response.choices[0].message.content
                result = json.loads(result_text)
                
                # 验证结果格式
                if "highlights" not in result:
                    result["highlights"] = []
                
                # 确保每个highlight都有note字段
                for highlight in result["highlights"]:
                    if "note" not in highlight and "reason" in highlight:
                        highlight["note"] = highlight["reason"]
                    elif "note" not in highlight:
                        highlight["note"] = ""
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"JSON解析错误 (尝试 {attempt + 1}/{retry_count}): {e}")
                if attempt == retry_count - 1:
                    return {"highlights": [], "summary": ""}
                time.sleep(1)
                
            except Exception as e:
                print(f"API调用错误 (尝试 {attempt + 1}/{retry_count}): {e}")
                if attempt == retry_count - 1:
                    return {"highlights": [], "summary": ""}
                time.sleep(2)
        
        return {"highlights": [], "summary": ""}
    
    def analyze_document_full(self, text_blocks: List[Dict], progress_callback=None) -> List[Dict]:
        """
        通读全文后分析整个文档（全局视角）
        
        Args:
            text_blocks: 文本块列表（来自PDF）
            progress_callback: 进度回调函数
            
        Returns:
            分析结果，包含需要高亮的内容和对应的文本块
        """
        # 第一步：组合全文
        print("   - 正在提取全文...")
        full_text = "\n\n".join([block["text"] for block in text_blocks if len(block["text"].strip()) > 50])
        
        # 计算token数
        token_count = self.count_tokens(full_text)
        print(f"   - 全文token数: {token_count}")
        
        # 第二步：处理长文本
        if token_count > MAX_TOKENS_PER_CHUNK:
            print(f"   - 文本较长，分段分析（保持上下文）...")
            return self._analyze_long_document(full_text, text_blocks, progress_callback)
        
        # 第三步：一次性分析全文
        print("   - 正在通读全文并识别关键观点...")
        analysis = self.analyze_text(full_text)
        
        # 检查返回的高亮数量
        highlight_count = len(analysis.get("highlights", []))
        summary_count = len(analysis.get("summaries", []))
        print(f"   - AI返回了 {highlight_count} 个高亮观点")
        print(f"   - AI返回了 {summary_count} 个段落总结")
        
        if highlight_count < 15:
            print(f"   ⚠️  警告：高亮数量少于预期（应该有20-30个）")
        if summary_count < 3:
            print(f"   ⚠️  警告：段落总结少于预期（应该有5-10个）")
        
        if progress_callback:
            progress_callback(1, 1)
        
        # 第四步：将高亮内容映射回对应的文本块
        print("   - 正在定位高亮位置...")
        results = self._map_highlights_to_blocks(analysis, text_blocks)
        
        print(f"   - 成功映射 {len(results)} 个高亮到PDF中")
        
        # 保存段落总结以便后续使用
        self._cached_summaries = analysis.get("summaries", [])
        
        return results
    
    def get_cached_summaries(self):
        """获取缓存的段落总结"""
        return getattr(self, '_cached_summaries', [])
    
    def _analyze_long_document(self, full_text: str, text_blocks: List[Dict], progress_callback=None) -> List[Dict]:
        """
        分析长文档（分段但保持全局视角）
        
        Args:
            full_text: 完整文本
            text_blocks: 文本块列表
            progress_callback: 进度回调
            
        Returns:
            分析结果
        """
        # 将文本分成大块（每块约6000 tokens，比单段大得多）
        chunk_size = 6000
        chunks = self.chunk_text(full_text, max_tokens=chunk_size)
        
        print(f"   - 分成{len(chunks)}个大段进行分析...")
        
        all_highlights = []
        
        # 分析每个大段
        for i, chunk in enumerate(chunks):
            print(f"   - 分析第{i+1}/{len(chunks)}段...")
            
            analysis = self.analyze_text(chunk)
            
            if analysis.get("highlights"):
                chunk_highlights = len(analysis["highlights"])
                print(f"     返回 {chunk_highlights} 个观点")
                all_highlights.extend(analysis["highlights"])
            
            if progress_callback:
                progress_callback(i + 1, len(chunks))
            
            # 避免API限流
            time.sleep(0.5)
        
        print(f"   - 总共获得 {len(all_highlights)} 个观点")
        
        # 合并结果并映射到文本块
        combined_analysis = {"highlights": all_highlights}
        results = self._map_highlights_to_blocks(combined_analysis, text_blocks)
        
        return results
    
    def _smart_text_match(self, search_text: str, target_text: str) -> bool:
        """
        智能文本匹配（更宽容的匹配策略）
        
        Args:
            search_text: 要搜索的文本
            target_text: 目标文本
            
        Returns:
            是否匹配
        """
        import string
        
        # 清理函数
        def normalize(text):
            # 移除多余空格
            text = ' '.join(text.split())
            # 转小写
            text = text.lower()
            return text
        
        # 策略1: 直接匹配
        if search_text in target_text:
            return True
        
        # 策略2: 清理后匹配
        norm_search = normalize(search_text)
        norm_target = normalize(target_text)
        if norm_search in norm_target:
            return True
        
        # 策略3: 移除标点后匹配
        no_punct_search = search_text.translate(str.maketrans('', '', string.punctuation))
        no_punct_target = target_text.translate(str.maketrans('', '', string.punctuation))
        if normalize(no_punct_search) in normalize(no_punct_target):
            return True
        
        # 策略4: 前70%匹配
        if len(search_text) > 40:
            partial = search_text[:int(len(search_text) * 0.7)]
            if normalize(partial) in norm_target:
                return True
        
        # 策略5: 前50%匹配
        if len(search_text) > 30:
            partial = search_text[:int(len(search_text) * 0.5)]
            if normalize(partial) in norm_target:
                return True
        
        # 策略6: 单词级别匹配（前10个单词）
        words = search_text.split()
        if len(words) > 10:
            partial = ' '.join(words[:10])
            if normalize(partial) in norm_target:
                return True
        
        return False
    
    def _map_highlights_to_blocks(self, analysis: Dict, text_blocks: List[Dict]) -> List[Dict]:
        """
        将高亮内容映射到对应的文本块和页码（使用智能匹配）
        
        Args:
            analysis: AI分析结果
            text_blocks: 文本块列表
            
        Returns:
            包含位置信息的结果列表
        """
        results = []
        unmatched = []
        
        for highlight_item in analysis.get("highlights", []):
            highlight_text = highlight_item.get("text", "")
            
            if not highlight_text:
                continue
            
            # 在文本块中查找这段文字
            found = False
            best_match = None
            best_match_score = 0
            
            for block in text_blocks:
                block_text = block["text"]
                
                # 使用智能匹配
                if self._smart_text_match(highlight_text, block_text):
                    # 计算匹配度（简单的基于长度）
                    match_score = len(highlight_text)
                    if match_score > best_match_score:
                        best_match = block
                        best_match_score = match_score
                    found = True
            
            if found and best_match:
                results.append({
                    "block": best_match,
                    "analysis": {
                        "highlights": [highlight_item]
                    }
                })
            else:
                # 记录未匹配的文本
                unmatched.append(highlight_text[:80])
        
        # 显示未匹配的统计
        if unmatched:
            print(f"   ⚠️  有 {len(unmatched)} 个高亮未能精确定位（将尝试模糊匹配）")
            # 只显示前3个
            for text in unmatched[:3]:
                print(f"      - {text}...")
        
        return results
    
    def analyze_document(self, text_blocks: List[Dict], progress_callback=None) -> List[Dict]:
        """
        分析整个文档（使用全文分析策略）
        
        Args:
            text_blocks: 文本块列表（来自PDF）
            progress_callback: 进度回调函数
            
        Returns:
            每个文本块的分析结果
        """
        # 使用新的全文分析方法
        return self.analyze_document_full(text_blocks, progress_callback)

