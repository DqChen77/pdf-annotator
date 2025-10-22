#!/usr/bin/env python3
"""
PDF智能标注工具 - 主程序
使用AI自动识别论文中的关键观点并添加注释
"""
import os
import sys
import argparse
from tqdm import tqdm
from pdf_reader import PDFReader
from ai_analyzer import AIAnalyzer
from pdf_annotator import annotate_from_analysis


def process_pdf(input_pdf: str, output_pdf: str = None, api_key: str = None, 
                model: str = None, verbose: bool = True):
    """
    处理PDF文件，添加AI标注
    
    Args:
        input_pdf: 输入PDF文件路径
        output_pdf: 输出PDF文件路径（默认为输入文件名_annotated.pdf）
        api_key: OpenAI API密钥
        model: 使用的模型
        verbose: 是否显示详细信息
    """
    # 检查输入文件
    if not os.path.exists(input_pdf):
        print(f"错误: 文件不存在: {input_pdf}")
        return False
    
    # 设置输出文件名
    if not output_pdf:
        base_name = os.path.splitext(input_pdf)[0]
        output_pdf = f"{base_name}_annotated.pdf"
    
    print(f"📚 正在处理: {input_pdf}")
    print(f"📝 输出文件: {output_pdf}")
    print("-" * 60)
    
    try:
        # 步骤1: 读取PDF
        if verbose:
            print("1️⃣ 正在读取PDF文件...")
        
        with PDFReader(input_pdf) as reader:
            page_count = reader.get_page_count()
            print(f"   - 总页数: {page_count}")
            
            # 提取所有文本块
            if verbose:
                print("   - 正在提取文本...")
            text_blocks = reader.extract_all_text()
            print(f"   - 提取到 {len(text_blocks)} 个文本块")
        
        if not text_blocks:
            print("错误: 无法从PDF中提取文本")
            return False
        
        # 步骤2: AI分析
        if verbose:
            print("\n2️⃣ 正在使用AI分析内容...")
        
        analyzer = AIAnalyzer(api_key=api_key, model=model)
        print(f"   - 使用模型: {analyzer.model}")
        
        # 进度条
        pbar = tqdm(total=len(text_blocks), desc="   分析进度", 
                   bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}')
        
        def progress_callback(current, total):
            pbar.update(1)
        
        analysis_results = analyzer.analyze_document(text_blocks, progress_callback)
        pbar.close()
        
        print(f"   - 完成分析，识别到 {len(analysis_results)} 个重要片段")
        
        # 统计高亮数量
        total_highlights = sum(len(r["analysis"].get("highlights", [])) 
                              for r in analysis_results)
        print(f"   - 共标记 {total_highlights} 个关键观点")
        
        # 获取段落总结
        summaries = analyzer.get_cached_summaries()
        if summaries:
            print(f"   - 获取到 {len(summaries)} 个段落总结")
        
        # 步骤3: 标注PDF
        if verbose:
            print("\n3️⃣ 正在生成标注PDF...")
        
        annotate_from_analysis(input_pdf, output_pdf, analysis_results, summaries)
        
        print("\n" + "=" * 60)
        print(f"✅ 处理完成！")
        print(f"📄 已生成标注PDF: {output_pdf}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 处理过程中出现错误: {str(e)}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="PDF智能标注工具 - 使用AI自动识别并标注论文中的关键观点",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基本用法（需要先在.env文件中配置API密钥）
  python main.py paper.pdf
  
  # 指定输出文件名
  python main.py paper.pdf -o annotated_paper.pdf
  
  # 使用命令行指定API密钥
  python main.py paper.pdf --api-key YOUR_API_KEY
  
  # 使用不同的模型
  python main.py paper.pdf --model gpt-3.5-turbo
        """
    )
    
    parser.add_argument("input_pdf", help="输入PDF文件路径")
    parser.add_argument("-o", "--output", help="输出PDF文件路径（默认为输入文件名_annotated.pdf）")
    parser.add_argument("--api-key", help="OpenAI API密钥（覆盖.env配置）")
    parser.add_argument("--model", help="使用的AI模型（默认为gpt-4）")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="显示详细信息")
    parser.add_argument("--quiet", action="store_true", 
                       help="静默模式，只显示错误信息")
    
    args = parser.parse_args()
    
    # 处理PDF
    success = process_pdf(
        input_pdf=args.input_pdf,
        output_pdf=args.output,
        api_key=args.api_key,
        model=args.model,
        verbose=not args.quiet
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

