"""
MCP工具结果处理器 - 对MCP工具输出进行智能处理和格式化
"""

import json
import re
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class ProcessingMode(Enum):
    """结果处理模式"""
    RAW = "raw"              # 原始输出
    SUMMARY = "summary"      # 智能摘要
    FORMATTED = "formatted"  # 格式化输出
    FILTERED = "filtered"    # 内容过滤
    STRUCTURED = "structured" # 结构化处理


class MCPResultProcessor:
    """MCP工具结果处理器"""
    
    def __init__(self):
        """初始化结果处理器"""
        self.llm = ChatOpenAI(
            model_name="Qwen/Qwen2.5-32B-Instruct",
            temperature=0.3,
            max_tokens=1024,
            base_url="https://api-inference.modelscope.cn/v1",
            api_key="a5a8fdf1-e914-4c1e-ac56-82888ec1be87",
        )
        
        # 摘要提示模板
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的信息摘要专家。请对提供的工具执行结果进行智能摘要。

要求：
1. 提取关键信息和重要数据
2. 保持信息的准确性和完整性
3. 使用简洁清晰的语言
4. 突出重点内容
5. 如果是数据类结果，保留重要的数值信息
6. 如果是文本类结果，提炼核心观点

输出格式：结构化的摘要内容，便于用户快速理解。"""),
            ("human", "工具名称：{tool_name}\n工具结果：{result}\n请生成摘要：")
        ])
        
        # 格式化提示模板
        self.format_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的内容格式化专家。请将工具执行结果格式化为用户友好的展示格式。

要求：
1. 使用清晰的标题和分段
2. 重要信息用适当的标记突出显示
3. 数据用表格或列表形式展示
4. 添加适当的说明文字
5. 确保格式规整、易于阅读
6. 可以使用Markdown格式

输出格式：格式化后的结果内容。"""),
            ("human", "工具名称：{tool_name}\n原始结果：{result}\n请格式化输出：")
        ])

    async def process_result(
        self, 
        tool_name: str, 
        result: str, 
        mode: ProcessingMode = ProcessingMode.FORMATTED,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        处理MCP工具结果
        
        Args:
            tool_name: 工具名称
            result: 工具执行结果
            mode: 处理模式
            options: 处理选项
            
        Returns:
            处理后的结果字符串
        """
        options = options or {}
        
        try:
            if mode == ProcessingMode.RAW:
                return result
            elif mode == ProcessingMode.SUMMARY:
                return await self._summarize_result(tool_name, result, options)
            elif mode == ProcessingMode.FORMATTED:
                return await self._format_result(tool_name, result, options)
            elif mode == ProcessingMode.FILTERED:
                return self._filter_result(result, options)
            elif mode == ProcessingMode.STRUCTURED:
                return self._structure_result(result, options)
            else:
                return result
        except Exception as e:
            print(f"结果处理出错: {e}")
            return f"⚠️ 结果处理出错，返回原始结果：\n{result}"

    async def _summarize_result(self, tool_name: str, result: str, options: Dict[str, Any]) -> str:
        """生成结果摘要"""
        max_length = options.get('max_length', 500)
        
        chain = self.summary_prompt | self.llm | StrOutputParser()
        
        summary = await chain.ainvoke({
            "tool_name": tool_name,
            "result": result
        })
        
        # 长度控制
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
            
        return f"📊 **{tool_name} 结果摘要**\n\n{summary}"

    async def _format_result(self, tool_name: str, result: str, options: Dict[str, Any]) -> str:
        """格式化结果输出"""
        chain = self.format_prompt | self.llm | StrOutputParser()
        
        formatted_result = await chain.ainvoke({
            "tool_name": tool_name,
            "result": result
        })
        
        return formatted_result

    def _filter_result(self, result: str, options: Dict[str, Any]) -> str:
        """过滤结果内容"""
        filters = options.get('filters', [])
        include_patterns = options.get('include_patterns', [])
        exclude_patterns = options.get('exclude_patterns', [])
        
        filtered_result = result
        
        # 包含模式过滤
        if include_patterns:
            lines = filtered_result.split('\n')
            filtered_lines = []
            for line in lines:
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in include_patterns):
                    filtered_lines.append(line)
            filtered_result = '\n'.join(filtered_lines)
        
        # 排除模式过滤
        if exclude_patterns:
            lines = filtered_result.split('\n')
            filtered_lines = []
            for line in lines:
                if not any(re.search(pattern, line, re.IGNORECASE) for pattern in exclude_patterns):
                    filtered_lines.append(line)
            filtered_result = '\n'.join(filtered_lines)
        
        # 特定过滤器
        for filter_name in filters:
            if filter_name == 'remove_empty_lines':
                filtered_result = '\n'.join([line for line in filtered_result.split('\n') if line.strip()])
            elif filter_name == 'remove_duplicates':
                lines = filtered_result.split('\n')
                seen = set()
                unique_lines = []
                for line in lines:
                    if line not in seen:
                        seen.add(line)
                        unique_lines.append(line)
                filtered_result = '\n'.join(unique_lines)
        
        return f"🔍 **过滤后的结果**\n\n{filtered_result}"

    def _structure_result(self, result: str, options: Dict[str, Any]) -> str:
        """结构化处理结果"""
        try:
            # 尝试解析JSON
            if result.strip().startswith('{') or result.strip().startswith('['):
                data = json.loads(result)
                return self._format_json_data(data, options)
            else:
                # 文本结构化
                return self._structure_text(result, options)
        except json.JSONDecodeError:
            return self._structure_text(result, options)

    def _format_json_data(self, data: Any, options: Dict[str, Any]) -> str:
        """格式化JSON数据"""
        formatted_lines = ["📋 **结构化数据**\n"]
        
        def format_value(key: str, value: Any, level: int = 0) -> List[str]:
            indent = "  " * level
            lines = []
            
            if isinstance(value, dict):
                lines.append(f"{indent}**{key}:**")
                for k, v in value.items():
                    lines.extend(format_value(k, v, level + 1))
            elif isinstance(value, list):
                lines.append(f"{indent}**{key}:** ({len(value)} 项)")
                for i, item in enumerate(value[:5]):  # 限制显示前5项
                    if isinstance(item, (dict, list)):
                        lines.extend(format_value(f"项目 {i+1}", item, level + 1))
                    else:
                        lines.append(f"{indent}  - {item}")
                if len(value) > 5:
                    lines.append(f"{indent}  ... (还有 {len(value)-5} 项)")
            else:
                lines.append(f"{indent}**{key}:** {value}")
            
            return lines
        
        if isinstance(data, dict):
            for key, value in data.items():
                formatted_lines.extend(format_value(key, value))
        elif isinstance(data, list):
            formatted_lines.extend(format_value("数据列表", data))
        else:
            formatted_lines.append(f"**值:** {data}")
        
        return "\n".join(formatted_lines)

    def _structure_text(self, result: str, options: Dict[str, Any]) -> str:
        """结构化文本内容"""
        lines = result.split('\n')
        structured_lines = ["📄 **结构化文本**\n"]
        
        current_section = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检测标题行（包含特定标记或全大写）
            if (line.isupper() and len(line) > 3) or \
               any(marker in line for marker in ['===', '---', '###', '**']):
                if current_section:
                    structured_lines.extend(current_section)
                    current_section = []
                structured_lines.append(f"\n### {line}")
            else:
                current_section.append(f"- {line}")
        
        if current_section:
            structured_lines.extend(current_section)
        
        return "\n".join(structured_lines)


# 全局处理器实例
result_processor = MCPResultProcessor()


async def process_mcp_result(
    tool_name: str, 
    result: str, 
    mode: str = "formatted",
    **options
) -> str:
    """
    便捷的MCP结果处理函数
    
    Args:
        tool_name: 工具名称
        result: 工具结果
        mode: 处理模式 (raw/summary/formatted/filtered/structured)
        **options: 处理选项
        
    Returns:
        处理后的结果
    """
    try:
        processing_mode = ProcessingMode(mode)
    except ValueError:
        processing_mode = ProcessingMode.FORMATTED
    
    return await result_processor.process_result(
        tool_name, 
        result, 
        processing_mode, 
        options
    )