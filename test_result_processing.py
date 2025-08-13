"""
测试MCP结果处理功能
"""

import asyncio
from llm.llm_chat_with_tools.tools.result_processor import process_mcp_result, ProcessingMode


async def test_result_processing():
    """测试结果处理功能"""
    
    # 模拟学生成绩查询的JSON结果
    test_json_result = """
    {
        "class_name": "class_1",
        "chinese_avg": 85.67,
        "math_avg": 78.92,
        "english_avg": 82.45,
        "student_count": 25,
        "total_avg": 82.35,
        "details": {
            "highest_score": {"chinese": 98, "math": 95, "english": 94},
            "lowest_score": {"chinese": 72, "math": 65, "english": 71}
        }
    }
    """
    
    print("=== 测试MCP结果处理功能 ===\n")
    
    # 测试不同的处理模式
    modes = ["raw", "summary", "formatted", "structured"]
    
    for mode in modes:
        print(f"--- {mode.upper()} 模式 ---")
        try:
            processed = await process_mcp_result(
                tool_name="query_student_avg_grade",
                result=test_json_result,
                mode=mode
            )
            print(f"处理结果:\n{processed}\n")
        except Exception as e:
            print(f"处理出错: {e}\n")
        
        print("-" * 50 + "\n")


async def test_text_processing():
    """测试文本结果处理"""
    
    test_text_result = """
    班级成绩统计报告
    
    班级名称：三年级一班
    学生总数：25人
    
    各科平均分：
    语文：85.67分
    数学：78.92分
    英语：82.45分
    
    总平均分：82.35分
    
    成绩分析：
    该班级在语文科目表现最好，数学成绩相对较弱，需要加强数学教学。
    整体成绩处于中等偏上水平，建议继续保持并提升薄弱科目。
    """
    
    print("=== 测试文本结果处理功能 ===\n")
    
    modes = ["summary", "formatted", "structured"]
    
    for mode in modes:
        print(f"--- {mode.upper()} 模式 ---")
        try:
            processed = await process_mcp_result(
                tool_name="class_report_generator",
                result=test_text_result,
                mode=mode
            )
            print(f"处理结果:\n{processed}\n")
        except Exception as e:
            print(f"处理出错: {e}\n")
        
        print("-" * 50 + "\n")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_result_processing())
    asyncio.run(test_text_processing())