"""
测试增强的计算工具功能
"""

import asyncio
from llm.llm_chat_with_tools.tools.calculate_tools import calculate_tools, advanced_math


async def test_basic_calculations():
    """测试基本数学计算"""
    print("=== 基本数学计算测试 ===\n")
    
    test_cases = [
        "2 + 3 * 4",  # 基本运算
        "sqrt(25) + log(e)",  # 科学函数
        "sin(pi/2) + cos(0)",  # 三角函数
        "mean([1, 2, 3, 4, 5])",  # 统计函数
        "sqrt(pow(3, 2) + pow(4, 2))",  # 复合表达式
        "factorial(5)",  # 阶乘
        "gcd(48, 18)",  # 最大公约数
        "degrees(pi/4)",  # 角度转换
        "round(3.14159, 2)",  # 四舍五入
        "stdev([1, 2, 3, 4, 5])",  # 标准差
    ]
    
    for i, expression in enumerate(test_cases, 1):
        print(f"测试 {i}: {expression}")
        try:
            result = await calculate_tools(expression)
            print(f"结果:\n{result}\n")
        except Exception as e:
            print(f"错误: {e}\n")
        
        print("-" * 50 + "\n")


async def test_advanced_statistics():
    """测试高级统计功能"""
    print("=== 高级统计分析测试 ===\n")
    
    # 测试数据
    test_data = [12.5, 15.2, 18.1, 14.7, 16.3, 13.9, 17.8, 15.5, 16.9, 14.2]
    
    # 测试描述性统计
    print("1. 描述性统计分析")
    try:
        result = await advanced_math("descriptive", test_data)
        print(f"结果:\n{result}\n")
    except Exception as e:
        print(f"错误: {e}\n")
    
    print("-" * 50 + "\n")
    
    # 测试分布分析
    print("2. 分布分析")
    try:
        result = await advanced_math("distribution", test_data)
        print(f"结果:\n{result}\n")
    except Exception as e:
        print(f"错误: {e}\n")
    
    print("-" * 50 + "\n")
    
    # 测试概率计算
    print("3. 概率计算")
    try:
        result = await advanced_math("probability", test_data, type="normal")
        print(f"结果:\n{result}\n")
    except Exception as e:
        print(f"错误: {e}\n")


async def test_complex_expressions():
    """测试复杂数学表达式"""
    print("=== 复杂表达式测试 ===\n")
    
    complex_cases = [
        # 物理公式
        "sqrt(2 * 9.8 * 10)",  # 自由落体速度
        "0.5 * 70 * pow(20, 2)",  # 动能计算
        
        # 金融计算
        "1000 * pow(1.05, 10)",  # 复利计算
        
        # 几何计算
        "pi * pow(5, 2)",  # 圆面积
        "4 * pi * pow(3, 2)",  # 球表面积
        
        # 统计分析
        "variance([85, 90, 78, 92, 88, 95, 82])",  # 成绩方差
        "median([1, 3, 5, 7, 9, 11, 13])",  # 中位数
    ]
    
    for i, expression in enumerate(complex_cases, 1):
        print(f"复杂计算 {i}: {expression}")
        try:
            result = await calculate_tools(expression)
            print(f"结果:\n{result}\n")
        except Exception as e:
            print(f"错误: {e}\n")
        
        print("-" * 50 + "\n")


async def test_error_handling():
    """测试错误处理"""
    print("=== 错误处理测试 ===\n")
    
    error_cases = [
        "1/0",  # 除零错误
        "sqrt(-1)",  # 数学域错误
        "unknown_function(5)",  # 未知函数
        "2 + + 3",  # 语法错误
        "eval('print(hello)')",  # 不安全函数
    ]
    
    for i, expression in enumerate(error_cases, 1):
        print(f"错误测试 {i}: {expression}")
        try:
            result = await calculate_tools(expression)
            print(f"结果:\n{result}\n")
        except Exception as e:
            print(f"异常: {e}\n")
        
        print("-" * 30 + "\n")


async def main():
    """运行所有测试"""
    print("🧮 增强计算工具测试开始\n")
    print("=" * 60 + "\n")
    
    await test_basic_calculations()
    await test_advanced_statistics()
    await test_complex_expressions()
    await test_error_handling()
    
    print("=" * 60)
    print("🎉 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())