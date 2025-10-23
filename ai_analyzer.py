"""
AI分析模块 - 使用OpenAI API分析文本内容
"""
import json
import time
from typing import List, Dict, Optional
from openai import OpenAI
import tiktoken
from datetime import datetime
import os
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
    
    def _save_ai_response_log(self, result_text: str, result: Dict):
        """
        保存AI响应到日志文件
        
        Args:
            result_text: AI返回的原始JSON文本
            result: 解析后的字典
        """
        try:
            # 创建logs目录
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 生成日志文件名（带时间戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"ai_response_{timestamp}.json")
            
            # 检测重复术语
            term_texts = [t.get('text', '').lower().strip() for t in result.get('terms', [])]
            duplicates = {}
            for t in term_texts:
                if term_texts.count(t) > 1:
                    duplicates[t] = term_texts.count(t)
            
            # 准备日志内容
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "raw_response": result_text,
                "parsed_result": result,
                "statistics": {
                    "highlights_count": len(result.get("highlights", [])),
                    "terms_count": len(result.get("terms", [])),
                    "unique_terms_count": len(set(term_texts)),
                    "duplicates": duplicates,
                    "summaries_count": len(result.get("summaries", []))
                },
                "all_term_texts": [t.get('text', '') for t in result.get('terms', [])]
            }
            
            # 保存到文件
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            print(f"   📝 AI响应已保存到: {log_file}")
            
        except Exception as e:
            print(f"   ⚠️  保存日志失败: {e}")
    
    def analyze_text(self, text: str, retry_count: int = 3, custom_prompt: Optional[str] = None) -> Dict:
        """
        分析文本，识别关键点和生成总结
        
        Args:
            text: 要分析的文本
            retry_count: 重试次数
            custom_prompt: 自定义提示词模板（可选）
            
        Returns:
            分析结果，包含highlights和summary
        """
        prompt_template = custom_prompt if custom_prompt else ANALYSIS_PROMPT
        prompt = prompt_template.format(text=text)
        
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
                
                # 打印原始响应（截断显示）
                print(f"\n   📋 AI原始响应（前500字符）:")
                print(f"   {result_text[:500]}...")
                
                result = json.loads(result_text)
                
                # 保存完整响应到日志文件
                self._save_ai_response_log(result_text, result)
                
                # 打印详细统计
                print(f"\n   📊 AI返回内容统计:")
                print(f"   - highlights: {len(result.get('highlights', []))} 个")
                print(f"   - terms: {len(result.get('terms', []))} 个")
                print(f"   - summaries: {len(result.get('summaries', []))} 个")
                
                # 检测重复术语
                if result.get('terms'):
                    print(f"\n   📝 前10个术语示例:")
                    for i, term in enumerate(result['terms'][:10], 1):
                        print(f"      {i}. {term.get('text', 'N/A')}")
                    
                    # 检查重复
                    term_texts = [t.get('text', '').lower().strip() for t in result['terms']]
                    duplicates = [t for t in set(term_texts) if term_texts.count(t) > 1]
                    if duplicates:
                        print(f"\n   ⚠️⚠️⚠️  检测到重复术语！AI在充数！")
                        print(f"   重复的术语: {', '.join(duplicates[:5])}")
                        if len(duplicates) > 5:
                            print(f"   还有 {len(duplicates)-5} 个重复术语...")
                    
                    # 后10个术语（检查是否在凑数）
                    if len(result['terms']) > 10:
                        print(f"\n   📝 后10个术语示例（检查质量）:")
                        for i, term in enumerate(result['terms'][-10:], len(result['terms'])-9):
                            print(f"      {i}. {term.get('text', 'N/A')}")
                
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
    
    def analyze_document_full(self, text_blocks: List[Dict], progress_callback=None, custom_prompt: Optional[str] = None) -> List[Dict]:
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
        analysis = self.analyze_text(full_text, custom_prompt=custom_prompt)
        
        # 立即对术语进行去重（在映射前）
        original_term_count = len(analysis.get("terms", []))
        if "terms" in analysis:
            analysis["terms"] = self._deduplicate_terms(analysis["terms"])
        
        # 检查返回的高亮数量
        highlight_count = len(analysis.get("highlights", []))
        term_count = len(analysis.get("terms", []))
        summary_count = len(analysis.get("summaries", []))
        print(f"   - AI返回了 {highlight_count} 个高亮观点")
        print(f"   - AI返回了 {original_term_count} 个专业术语（含重复）")
        if original_term_count != term_count:
            print(f"   - 去重后保留 {term_count} 个唯一术语")
        else:
            print(f"   - 无重复术语")
        print(f"   - AI返回了 {summary_count} 个段落总结")
        
        if highlight_count < 15:
            print(f"   ⚠️  警告：高亮数量少于预期（应该有20-30个）")
        if term_count < 30:
            print(f"   ⚠️  提示：术语数量较少（去重后{term_count}个），可能需要更全面的标注")
        if summary_count < 3:
            print(f"   ⚠️  警告：段落总结少于预期（应该有5-10个）")
        
        if progress_callback:
            progress_callback(1, 1)
        
        # 第四步：将高亮内容映射回对应的文本块
        print("   - 正在定位高亮位置...")
        results = self._map_highlights_to_blocks(analysis, text_blocks)
        
        # 第五步：将术语映射回对应的文本块
        print("   - 正在定位术语位置...")
        term_results = self._map_terms_to_blocks(analysis, text_blocks)
        
        # 合并结果
        all_results = results + term_results
        
        print(f"   - 成功映射 {len(results)} 个观点高亮到PDF中")
        print(f"   - 成功映射 {len(term_results)} 个术语高亮到PDF中")
        
        # 保存段落总结以便后续使用
        self._cached_summaries = analysis.get("summaries", [])
        
        return all_results
    
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
    
    def _deduplicate_terms(self, terms: List[Dict]) -> List[Dict]:
        """
        智能去重术语列表（处理完全重复和包含关系）- 增强版
        
        Args:
            terms: 术语列表
            
        Returns:
            去重后的术语列表
        """
        if not terms:
            return []
        
        unique_terms = []
        seen_keys = set()
        seen_texts = []
        
        for term in terms:
            term_text = term.get("text", "").strip()
            if not term_text:
                continue
            
            # 标准化：小写 + 移除多余空格
            term_key = ' '.join(term_text.lower().split())
            
            # 检查是否完全重复
            if term_key in seen_keys:
                continue
            
            # 检查包含关系（更严格）
            should_skip = False
            term_to_replace = None
            
            # 分词比较（处理 "nucleus accumbens" 这类多词术语）
            term_words = set(term_key.split())
            
            for i, seen_text in enumerate(seen_texts):
                seen_key = ' '.join(seen_text.lower().split())
                seen_words = set(seen_key.split())
                
                # 完全相同（经过标准化后）
                if term_key == seen_key:
                    should_skip = True
                    break
                
                # 多词术语的完全包含（如 "nucleus accumbens" vs "nucleus")
                # 如果新术语的所有词都在旧术语中，且词序相同
                if term_key in seen_key and len(term_words) < len(seen_words):
                    # 新术语是子集，保留旧的
                    should_skip = True
                    break
                elif seen_key in term_key and len(seen_words) < len(term_words):
                    # 旧术语是子集，保留新的
                    term_to_replace = i
                    break
                
                # 处理相同核心词的不同形式
                # 如 "nucleus accumbens" 的各种出现
                if len(term_words) >= 2 and len(seen_words) >= 2:
                    # 检查主要词是否相同（取最长的两个词）
                    term_main = sorted(term_words, key=len, reverse=True)[:2]
                    seen_main = sorted(seen_words, key=len, reverse=True)[:2]
                    if set(term_main) == set(seen_main):
                        # 认为是同一术语，保留更长/更完整的版本
                        if len(term_key) > len(seen_key):
                            term_to_replace = i
                        else:
                            should_skip = True
                        break
            
            if should_skip:
                continue
            
            # 如果需要替换旧术语
            if term_to_replace is not None:
                old_text = seen_texts[term_to_replace]
                old_key = ' '.join(old_text.lower().split())
                # 移除旧的
                seen_keys.discard(old_key)
                seen_texts.pop(term_to_replace)
                unique_terms.pop(term_to_replace)
            
            # 添加新术语
            seen_keys.add(term_key)
            seen_texts.append(term_text)
            unique_terms.append(term)
        
        return unique_terms
    
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
                # 标记为观点高亮（黄色）
                highlight_item["type"] = "insight"
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
    
    def _map_terms_to_blocks(self, analysis: Dict, text_blocks: List[Dict]) -> List[Dict]:
        """
        将术语映射到对应的文本块和页码（每个术语只标注第一次出现，智能去重）
        
        Args:
            analysis: AI分析结果
            text_blocks: 文本块列表
            
        Returns:
            包含位置信息的结果列表
        """
        results = []
        unmatched = []
        seen_terms = set()  # 用于去重，记录已标注的术语
        seen_term_list = []  # 保存完整的术语文本，用于包含关系检查
        
        for term_item in analysis.get("terms", []):
            term_text = term_item.get("text", "")
            
            if not term_text:
                continue
            
            # 去重：将术语转为小写作为唯一标识
            term_key = term_text.lower().strip()
            
            # 智能去重：检查是否与已有术语冲突
            should_skip = False
            term_to_remove = None
            
            # 如果完全相同，跳过
            if term_key in seen_terms:
                should_skip = True
            else:
                # 检查包含关系
                for seen_term in seen_term_list:
                    seen_key = seen_term.lower().strip()
                    
                    # 如果新术语是已有术语的子串（如 "oxytocin" vs "oxytocin levels"）
                    # 保留更长的版本
                    if term_key in seen_key:
                        # 新术语是子串，跳过新术语
                        should_skip = True
                        break
                    elif seen_key in term_key:
                        # 已有术语是新术语的子串，移除旧的，添加新的
                        term_to_remove = seen_term
                        break
            
            if should_skip:
                continue
            
            # 如果需要移除旧术语
            if term_to_remove:
                old_key = term_to_remove.lower().strip()
                if old_key in seen_terms:
                    seen_terms.remove(old_key)
                if term_to_remove in seen_term_list:
                    seen_term_list.remove(term_to_remove)
                # 从results中移除对应的结果
                results = [r for r in results 
                          if r["analysis"]["highlights"][0]["text"].lower().strip() != old_key]
            
            # 在文本块中查找这个术语（找第一次出现）
            found = False
            best_match = None
            best_match_score = 0
            earliest_page = float('inf')
            
            for block in text_blocks:
                block_text = block["text"]
                page_num = block.get("page", 0)
                
                # 术语通常较短，使用更精确的匹配
                if self._smart_text_match(term_text, block_text):
                    # 优先选择更早出现的页面
                    if page_num < earliest_page:
                        best_match = block
                        best_match_score = len(term_text)
                        earliest_page = page_num
                        found = True
                    elif page_num == earliest_page and len(term_text) > best_match_score:
                        # 同一页面，选择更长的匹配
                        best_match = block
                        best_match_score = len(term_text)
            
            if found and best_match:
                # 标记为已处理
                seen_terms.add(term_key)
                seen_term_list.append(term_text)
                
                # 构建术语的注释内容（中文翻译 + 解释）
                translation = term_item.get("translation", "")
                note = term_item.get("note", "")
                
                full_note = f"【术语】{translation}"
                if note:
                    full_note += f"\n{note}"
                
                # 标记为术语高亮（蓝色）
                term_highlight = {
                    "text": term_text,
                    "note": full_note,
                    "type": "term"
                }
                
                results.append({
                    "block": best_match,
                    "analysis": {
                        "highlights": [term_highlight]
                    }
                })
            else:
                # 记录未匹配的术语
                unmatched.append(term_text[:50])
        
        # 显示统计
        if unmatched:
            print(f"   ⚠️  有 {len(unmatched)} 个术语未能定位")
            # 只显示前3个
            for text in unmatched[:3]:
                print(f"      - {text}")
        
        return results
    
    def analyze_document(self, text_blocks: List[Dict], progress_callback=None, custom_prompt: Optional[str] = None) -> List[Dict]:
        """
        分析整个文档（使用全文分析策略）
        
        Args:
            text_blocks: 文本块列表（来自PDF）
            progress_callback: 进度回调函数
            custom_prompt: 自定义提示词模板（可选）
            
        Returns:
            每个文本块的分析结果
        """
        # 使用新的全文分析方法
        return self.analyze_document_full(text_blocks, progress_callback, custom_prompt)

