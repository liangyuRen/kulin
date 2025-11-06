"""
版本约束解析器 - 支持所有常见版本格式

支持的格式：
- 精确版本: 1.0.0
- 比较操作: >=1.0.0, >1.0, <2.0, <=2.0
- Python风格: ~=1.0.0 (兼容版本), ^1.0.0 (NPM风格)
- Maven风格: [1.0,2.0) (包含下限，不包含上限)
- 范围: >=1.0.0,<2.0.0
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class VersionOperator(Enum):
    """版本操作符枚举"""
    EQ = "=="      # 精确等于
    GE = ">="      # 大于等于
    GT = ">"       # 大于
    LE = "<="      # 小于等于
    LT = "<"       # 小于
    NE = "!="      # 不等于
    COMPATIBLE = "~=" # Python兼容版本
    CARET = "^"    # NPM caret (^1.2.3)
    TILDE = "~"    # NPM tilde (~1.2.3)


@dataclass
class VersionConstraint:
    """单个版本约束"""
    operator: VersionOperator
    version: str

    def __str__(self):
        return f"{self.operator.value}{self.version}"

    def __repr__(self):
        return f"VersionConstraint({self.operator.name}, {self.version!r})"


@dataclass
class VersionRange:
    """版本范围（包含所有约束）"""
    constraints: List[VersionConstraint]
    original_string: str

    def __str__(self):
        return ", ".join(str(c) for c in self.constraints)

    def is_unconstrained(self) -> bool:
        """是否无版本约束"""
        return len(self.constraints) == 0

    def get_min_version(self) -> Optional[str]:
        """获取最小版本"""
        for c in self.constraints:
            if c.operator in [VersionOperator.GE, VersionOperator.GT]:
                return c.version
        return None

    def get_max_version(self) -> Optional[str]:
        """获取最大版本"""
        for c in self.constraints:
            if c.operator in [VersionOperator.LE, VersionOperator.LT]:
                return c.version
        return None

    def get_exact_version(self) -> Optional[str]:
        """获取精确版本"""
        for c in self.constraints:
            if c.operator == VersionOperator.EQ:
                return c.version
        return None


class VersionParser:
    """版本约束解析器 - 所有语言共用"""

    def __init__(self):
        # 各种版本格式的正则表达式
        self.patterns = {
            # Maven范围: [1.0,2.0) 或 (1.0,2.0]
            'maven_range': r'[\[\(](.*?)[,\s]+(.*?)[\]\)]',
            # 操作符+版本: >=1.0.0, ~=1.0
            'operator_version': r'^([=~><!^]+)(.+)$',
            # 简单版本号: 1.0.0
            'simple_version': r'^\d+(\.\d+)*(-[a-zA-Z0-9]+)?(\+.*)?$',
        }

    def parse(self, constraint_str: str) -> VersionRange:
        """
        解析版本约束字符串

        Args:
            constraint_str: 原始约束字符串（如 ">=1.0.0,<2.0.0"）

        Returns:
            VersionRange 对象
        """
        if not constraint_str or constraint_str.strip() == '' or constraint_str.lower() == 'unknown':
            return VersionRange([], constraint_str)

        constraint_str = constraint_str.strip()

        # 尝试Maven范围格式
        maven_match = re.match(self.patterns['maven_range'], constraint_str)
        if maven_match:
            return self._parse_maven_range(maven_match, constraint_str)

        # 尝试多个约束用逗号分隔
        if ',' in constraint_str:
            return self._parse_comma_separated(constraint_str)

        # 尝试单个约束
        return self._parse_single_constraint(constraint_str)

    def _parse_maven_range(self, match, original: str) -> VersionRange:
        """解析Maven范围格式"""
        constraints = []
        lower_bound = match.group(1).strip()
        upper_bound = match.group(2).strip()
        is_lower_inclusive = original.startswith('[')
        is_upper_inclusive = original.endswith(']')

        if lower_bound:
            op = VersionOperator.GE if is_lower_inclusive else VersionOperator.GT
            constraints.append(VersionConstraint(op, lower_bound))

        if upper_bound:
            op = VersionOperator.LE if is_upper_inclusive else VersionOperator.LT
            constraints.append(VersionConstraint(op, upper_bound))

        return VersionRange(constraints, original)

    def _parse_comma_separated(self, constraint_str: str) -> VersionRange:
        """解析逗号分隔的多个约束"""
        constraints = []
        parts = constraint_str.split(',')

        for part in parts:
            part = part.strip()
            if not part:
                continue

            single = self._parse_single_constraint(part)
            constraints.extend(single.constraints)

        return VersionRange(constraints, constraint_str)

    def _parse_single_constraint(self, constraint_str: str) -> VersionRange:
        """解析单个约束"""
        constraint_str = constraint_str.strip()

        if not constraint_str:
            return VersionRange([], constraint_str)

        # 尝试匹配操作符+版本
        match = re.match(self.patterns['operator_version'], constraint_str)
        if match:
            operator_str, version = match.groups()
            version = version.strip()

            # 规范化操作符
            operator = self._normalize_operator(operator_str)
            constraint = VersionConstraint(operator, version)
            return VersionRange([constraint], constraint_str)

        # 如果没有操作符，假设是精确版本
        if re.match(self.patterns['simple_version'], constraint_str):
            constraint = VersionConstraint(VersionOperator.EQ, constraint_str)
            return VersionRange([constraint], constraint_str)

        # 无法识别的格式，返回空约束
        return VersionRange([], constraint_str)

    def _normalize_operator(self, op_str: str) -> VersionOperator:
        """规范化操作符字符串为标准操作符"""
        op_map = {
            '==': VersionOperator.EQ,
            '=': VersionOperator.EQ,
            '>=': VersionOperator.GE,
            '>': VersionOperator.GT,
            '<=': VersionOperator.LE,
            '<': VersionOperator.LT,
            '!=': VersionOperator.NE,
            '~=': VersionOperator.COMPATIBLE,
            '~': VersionOperator.TILDE,
            '^': VersionOperator.CARET,
        }

        return op_map.get(op_str.strip(), VersionOperator.EQ)

    def parse_extras(self, dependency_str: str) -> Tuple[str, List[str], str]:
        """
        解析包含extras的依赖字符串

        格式: package-name[extra1,extra2]>=1.0

        Returns:
            (package_name, extras, constraint_str)
        """
        # 提取extras: package[extra1,extra2]
        match = re.match(r'^([a-zA-Z0-9_\-]+)(?:\[([^\]]+)\])?(.*)$', dependency_str)

        if not match:
            return dependency_str, [], ""

        package_name = match.group(1)
        extras_str = match.group(2) or ""
        constraint_str = match.group(3).strip()

        extras = [e.strip() for e in extras_str.split(',') if e.strip()] if extras_str else []

        return package_name, extras, constraint_str


# 使用示例和测试
if __name__ == "__main__":
    parser = VersionParser()

    # 测试用例
    test_cases = [
        # Python风格
        (">=2.28.0,<3.0.0", "Python范围"),
        ("~=1.4.5", "Python兼容版本"),
        ("requests>=2.28.0", "简单版本范围"),

        # Maven风格
        ("[1.0,2.0)", "Maven半开范围"),
        ("[1.0,2.0]", "Maven闭范围"),
        ("(1.0,2.0)", "Maven开范围"),

        # NPM风格
        ("^1.2.3", "NPM caret"),
        ("~1.2.3", "NPM tilde"),
        ("1.x", "NPM x范围"),

        # 其他
        ("", "空字符串"),
        ("1.0.0", "精确版本"),
        (">=1.0.0", "单个约束"),
    ]

    print("=" * 70)
    print("版本约束解析器测试")
    print("=" * 70)

    for constraint_str, description in test_cases:
        result = parser.parse(constraint_str)
        print(f"\n{description}")
        print(f"  输入: {constraint_str!r}")
        print(f"  输出: {result}")
        print(f"  最小版本: {result.get_min_version()}")
        print(f"  最大版本: {result.get_max_version()}")
        print(f"  精确版本: {result.get_exact_version()}")

    # 测试extras解析
    print("\n" + "=" * 70)
    print("Extras 解析测试")
    print("=" * 70)

    extras_cases = [
        "requests[security]>=2.28.0",
        "django>=3.0",
        "numpy[mkl,openblas]==1.21.0",
    ]

    for case in extras_cases:
        pkg, extras, constraint = parser.parse_extras(case)
        print(f"\n输入: {case}")
        print(f"  包名: {pkg}")
        print(f"  Extras: {extras}")
        print(f"  约束: {constraint}")
