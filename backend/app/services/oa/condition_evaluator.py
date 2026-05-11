"""
工作流条件表达式求值器

支持：
- 简单三段式: "field op value" (如 "amount > 1000")
- JSON结构: {"op": "AND/OR/NOT", "conditions": [...]}
- 支持的运算符: ==, !=, >, <, >=, <=, in, not_in, contains
"""
import json
from typing import Any, Dict, Union


class ConditionEvaluator:
    """
    工作流条件表达式求值器

    支持：
    - 简单三段式: "field op value"
    - JSON结构: {"op": "AND/OR", "conditions": [...]}
    - 支持的运算符: ==, !=, >, <, >=, <=, in, not_in, contains
    """

    SUPPORTED_OPS = {"==", "!=", ">", "<", ">=", "<=", "in", "not_in", "contains"}

    def evaluate(
        self,
        expression: Union[str, Dict, None],
        context: Dict[str, Any]
    ) -> bool:
        """
        求值入口

        Args:
            expression: 条件表达式（字符串或JSON对象或None）
            context: 变量上下文（form_data 等）

        Returns:
            True 表示条件成立，False 表示条件不成立
            expression 为 None 时返回 True（无条件，默认通过）
        """
        if expression is None:
            return True

        # 尝试解析为JSON
        if isinstance(expression, str):
            try:
                parsed = json.loads(expression)
                return self._evaluate_node(parsed, context)
            except (json.JSONDecodeError, ValueError):
                # 退回到简单三段式解析
                return self._evaluate_simple(expression, context)

        if isinstance(expression, dict):
            return self._evaluate_node(expression, context)

        return True

    def _evaluate_node(self, node: Dict, context: Dict) -> bool:
        """递归求值JSON节点"""
        op = node.get("op", "").upper()

        if op == "AND":
            return all(
                self._evaluate_node(c, context)
                for c in node.get("conditions", [])
            )
        elif op == "OR":
            return any(
                self._evaluate_node(c, context)
                for c in node.get("conditions", [])
            )
        elif op == "NOT":
            conditions = node.get("conditions", [])
            return not self._evaluate_node(conditions[0], context) if conditions else True
        else:
            # 叶子条件节点：{"field": "x", "operator": ">", "value": 100}
            return self._evaluate_leaf(node, context)

    def _evaluate_leaf(self, node: Dict, context: Dict) -> bool:
        """求值叶子条件"""
        field = node.get("field", "")
        operator = node.get("operator", "==")
        expected = node.get("value")

        actual = self._get_field_value(field, context)

        return self._compare(actual, operator, expected)

    def _evaluate_simple(self, expression: str, context: Dict) -> bool:
        """
        解析简单三段式表达式: "field op value"

        支持: amount > 1000, status == "pending"
        """
        try:
            parts = expression.strip().split(None, 2)  # 最多分3段
            if len(parts) != 3:
                return True  # 无法解析，默认通过

            field, operator, raw_value = parts

            # 解析值（去除引号，尝试类型转换）
            value = self._parse_value(raw_value)
            actual = self._get_field_value(field, context)

            return self._compare(actual, operator, value)
        except Exception:
            return True  # 解析异常，默认通过

    def _get_field_value(self, field: str, context: Dict) -> Any:
        """
        从 context 中获取字段值，支持点号路径: "form.amount"
        """
        parts = field.split(".")
        val = context
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                return None
        return val

    def _parse_value(self, raw: str) -> Any:
        """将字符串值解析为适当类型"""
        raw = raw.strip()
        # 去除引号
        if (raw.startswith('"') and raw.endswith('"')) or \
           (raw.startswith("'") and raw.endswith("'")):
            return raw[1:-1]
        # 尝试数字
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        # 布尔值
        if raw.lower() == "true":
            return True
        if raw.lower() == "false":
            return False
        return raw

    def _compare(self, actual: Any, operator: str, expected: Any) -> bool:
        """执行比较运算"""
        try:
            if operator == "==":
                return str(actual) == str(expected) if isinstance(expected, str) else actual == expected
            elif operator == "!=":
                return actual != expected
            elif operator == ">":
                return float(actual or 0) > float(expected)
            elif operator == "<":
                return float(actual or 0) < float(expected)
            elif operator == ">=":
                return float(actual or 0) >= float(expected)
            elif operator == "<=":
                return float(actual or 0) <= float(expected)
            elif operator == "in":
                return actual in (expected if isinstance(expected, list) else [expected])
            elif operator == "not_in":
                return actual not in (expected if isinstance(expected, list) else [expected])
            elif operator == "contains":
                return str(expected) in str(actual or "")
        except (TypeError, ValueError):
            pass
        return True
