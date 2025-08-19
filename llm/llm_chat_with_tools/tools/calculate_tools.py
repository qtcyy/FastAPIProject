import math
import statistics
import ast
import operator
import re
from typing import Any, Dict, List, Union
from langchain.tools import tool


class SafeMathEvaluator:
    """安全的数学表达式计算器"""

    # 允许的操作符
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # 允许的数学函数
    ALLOWED_FUNCTIONS = {
        # 基本数学函数
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        # 数学库函数
        "sqrt": math.sqrt,
        "pow": pow,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        # 三角函数
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        # 角度转换
        "degrees": math.degrees,
        "radians": math.radians,
        # 其他数学函数
        "ceil": math.ceil,
        "floor": math.floor,
        "fabs": math.fabs,
        "factorial": math.factorial,
        "gcd": math.gcd,
        "lcm": (
            math.lcm
            if hasattr(math, "lcm")
            else lambda a, b: abs(a * b) // math.gcd(a, b)
        ),
        # 统计函数
        "mean": statistics.mean,
        "median": statistics.median,
        "mode": statistics.mode,
        "stdev": statistics.stdev,
        "variance": statistics.variance,
        "harmonic_mean": statistics.harmonic_mean,
        "geometric_mean": (
            statistics.geometric_mean
            if hasattr(statistics, "geometric_mean")
            else lambda x: math.exp(statistics.mean(math.log(i) for i in x))
        ),
    }

    # 允许的常量
    ALLOWED_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
        "nan": math.nan,
    }

    def __init__(self):
        self.allowed_names = {**self.ALLOWED_FUNCTIONS, **self.ALLOWED_CONSTANTS}

    def evaluate(self, expression: str) -> Any:
        """安全地计算数学表达式"""
        try:
            # 预处理表达式
            expression = self._preprocess_expression(expression)

            # 解析AST
            tree = ast.parse(expression, mode="eval")

            # 计算结果
            result = self._eval_node(tree.body)

            return result
        except Exception as e:
            raise ValueError(f"计算错误: {str(e)}")

    def _preprocess_expression(self, expression: str) -> str:
        """预处理表达式"""
        # 移除空白字符
        expression = expression.strip()

        # 替换常见的数学符号
        replacements = {
            "×": "*",
            "÷": "/",
            "^": "**",
            "√": "sqrt",
        }

        for old, new in replacements.items():
            expression = expression.replace(old, new)

        return expression

    def _eval_node(self, node) -> Any:
        """递归计算AST节点"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"不支持的操作符: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"不支持的一元操作符: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Name):
            if node.id in self.allowed_names:
                return self.allowed_names[node.id]
            else:
                raise ValueError(f"未知的名称: {node.id}")
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"不支持的函数: {func_name}")

            func = self.ALLOWED_FUNCTIONS[func_name]
            args = [self._eval_node(arg) for arg in node.args]

            return func(*args)
        elif isinstance(node, ast.List):
            return [self._eval_node(item) for item in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(item) for item in node.elts)
        else:
            raise ValueError(f"不支持的节点类型: {type(node).__name__}")


# 全局计算器实例
calculator = SafeMathEvaluator()


@tool
async def calculate_tools(expression: str) -> str:
    """
    强化的数学计算工具，支持复杂的数学表达式、统计函数和科学计算

    支持的功能：
    - 基本运算：+, -, *, /, //, %, ** (幂运算)
    - 数学函数：sqrt, exp, log, log10, log2, abs, round, min, max, sum
    - 三角函数：sin, cos, tan, asin, acos, atan, atan2, sinh, cosh, tanh
    - 统计函数：mean, median, mode, stdev, variance, harmonic_mean, geometric_mean
    - 其他函数：ceil, floor, factorial, gcd, lcm, degrees, radians
    - 数学常量：pi, e, tau, inf, nan
    - 列表操作：支持对数组进行统计计算

    示例：
    - 基本计算: "2 + 3 * 4"
    - 科学计算: "sqrt(25) + log(e)"
    - 三角函数: "sin(pi/2) + cos(0)"
    - 统计计算: "mean([1, 2, 3, 4, 5])"
    - 复合表达式: "sqrt(pow(3, 2) + pow(4, 2))"

    Args:
        expression: 数学表达式字符串

    Returns:
        计算结果的字符串表示
    """
    try:
        result = calculator.evaluate(expression)

        # 格式化结果
        if isinstance(result, float):
            # 对于浮点数，如果接近整数则显示为整数
            if abs(result - round(result)) < 1e-10:
                result = int(round(result))
            else:
                # 限制小数位数以提高可读性
                result = round(result, 10)

        return f"🧮 **计算结果**\n\n表达式: `{expression}`\n结果: **{result}**"

    except Exception as e:
        return f"❌ **计算错误**\n\n表达式: `{expression}`\n错误: {str(e)}\n\n💡 **提示**: 请检查表达式语法，确保使用支持的函数和操作符。"


@tool
async def advanced_math(operation: str, data: List[float], **kwargs) -> str:
    """
    高级数学运算工具，用于复杂的数据分析和统计计算

    支持的操作：
    - descriptive: 描述性统计
    - distribution: 分布分析
    - correlation: 相关性分析
    - regression: 简单线性回归
    - probability: 概率计算

    Args:
        operation: 操作类型
        data: 数据列表
        **kwargs: 额外参数

    Returns:
        分析结果的字符串表示
    """
    try:
        if operation == "descriptive":
            return _descriptive_statistics(data)
        elif operation == "distribution":
            return _distribution_analysis(data)
        elif operation == "probability":
            return _probability_calculations(data, **kwargs)
        else:
            return f"❌ 不支持的操作类型: {operation}"

    except Exception as e:
        return f"❌ **计算错误**: {str(e)}"


def _descriptive_statistics(data: List[float]) -> str:
    """计算描述性统计"""
    if not data:
        return "❌ 数据为空"

    n = len(data)
    mean_val = statistics.mean(data)
    median_val = statistics.median(data)

    # 计算其他统计量
    min_val = min(data)
    max_val = max(data)
    range_val = max_val - min_val

    try:
        stdev_val = statistics.stdev(data) if n > 1 else 0
        variance_val = statistics.variance(data) if n > 1 else 0
    except:
        stdev_val = 0
        variance_val = 0

    # 计算四分位数
    sorted_data = sorted(data)
    q1 = statistics.median(sorted_data[: n // 2])
    q3 = statistics.median(sorted_data[(n + 1) // 2 :])
    iqr = q3 - q1

    result = f"""📊 **描述性统计分析**

📈 **基本统计**
- 样本数量: {n}
- 平均值: {mean_val:.4f}
- 中位数: {median_val:.4f}
- 最小值: {min_val:.4f}
- 最大值: {max_val:.4f}
- 极差: {range_val:.4f}

📐 **变异性指标**
- 标准差: {stdev_val:.4f}
- 方差: {variance_val:.4f}
- 变异系数: {(stdev_val/mean_val*100):.2f}% (如果均值非零)

📏 **分位数**
- 第一四分位数 (Q1): {q1:.4f}
- 第三四分位数 (Q3): {q3:.4f}
- 四分位距 (IQR): {iqr:.4f}
"""

    return result


def _distribution_analysis(data: List[float]) -> str:
    """分布分析"""
    if not data:
        return "❌ 数据为空"

    n = len(data)
    mean_val = statistics.mean(data)

    try:
        stdev_val = statistics.stdev(data) if n > 1 else 0
    except:
        stdev_val = 0

    # 计算偏度和峰度的近似值
    if stdev_val > 0:
        # 简化的偏度计算
        centered = [(x - mean_val) for x in data]
        skewness = sum(x**3 for x in centered) / (n * stdev_val**3) if n > 2 else 0

        # 简化的峰度计算
        kurtosis = sum(x**4 for x in centered) / (n * stdev_val**4) - 3 if n > 3 else 0
    else:
        skewness = 0
        kurtosis = 0

    result = f"""📈 **分布分析**

📊 **分布特征**
- 样本数量: {n}
- 均值: {mean_val:.4f}
- 标准差: {stdev_val:.4f}

📐 **形状指标**
- 偏度: {skewness:.4f} ({'右偏' if skewness > 0 else '左偏' if skewness < 0 else '对称'})
- 峰度: {kurtosis:.4f} ({'尖峰' if kurtosis > 0 else '平峰' if kurtosis < 0 else '正态峰'})

💡 **解释**
- 偏度 > 0: 右偏分布（尾部向右延伸）
- 偏度 < 0: 左偏分布（尾部向左延伸）
- 峰度 > 0: 比正态分布更尖锐
- 峰度 < 0: 比正态分布更平缓
"""

    return result


def _probability_calculations(data: List[float], **kwargs) -> str:
    """概率计算"""
    prob_type = kwargs.get("type", "basic")

    if prob_type == "normal":
        mean_val = statistics.mean(data)
        stdev_val = statistics.stdev(data) if len(data) > 1 else 0

        return f"""🎲 **正态分布概率**

📊 **参数估计**
- 均值 (μ): {mean_val:.4f}
- 标准差 (σ): {stdev_val:.4f}

📈 **标准化**
- Z分数计算: Z = (X - {mean_val:.4f}) / {stdev_val:.4f}

💡 **应用**: 可用于计算特定值的概率密度和累积概率
"""

    return "🎲 **基本概率信息**\n请指定概率类型进行详细计算"
