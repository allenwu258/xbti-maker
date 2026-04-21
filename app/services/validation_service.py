from collections import Counter

from app.schemas.test_config import TestConfig
from app.schemas.validation import ValidationIssue, ValidationReport


class ValidationService:
    def validate_config(self, config: TestConfig) -> ValidationReport:
        issues: list[ValidationIssue] = []

        self._check_duplicates("dimension", [item.id for item in config.dimensions], issues)
        self._check_duplicates("question", [item.id for item in config.questions], issues)
        self._check_duplicates("result", [item.id for item in config.results], issues)

        dimension_ids = {item.id for item in config.dimensions}
        group_ids = {item.id for item in config.dimension_groups}
        question_ids = {item.id for item in config.questions}
        result_ids = {item.id for item in config.results}

        if not config.meta.name.strip():
            issues.append(ValidationIssue(level="error", code="missing_name", message="测试名称不能为空。"))

        if len(config.dimensions) < 3:
            issues.append(ValidationIssue(level="error", code="few_dimensions", message="至少需要 3 个维度。"))

        if len([item for item in config.results if item.kind == "standard"]) < 2:
            issues.append(ValidationIssue(level="error", code="few_results", message="至少需要 2 个标准结果。"))

        for dimension in config.dimensions:
            if dimension.group_id not in group_ids:
                issues.append(
                    ValidationIssue(
                        level="error",
                        code="missing_group",
                        message=f"维度 {dimension.id} 引用了不存在的分组 {dimension.group_id}。",
                    )
                )

        scored_question_counts = Counter(
            question.dimension_id for question in config.questions if question.is_scored and question.dimension_id
        )
        for dimension in config.dimensions:
            count = scored_question_counts.get(dimension.id, 0)
            if count == 0:
                issues.append(
                    ValidationIssue(
                        level="error",
                        code="dimension_without_questions",
                        message=f"维度 {dimension.id} 没有计分题覆盖。",
                    )
                )
            elif count < 2:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        code="dimension_low_coverage",
                        message=f"维度 {dimension.id} 只有 {count} 道计分题，建议至少 2 道。",
                    )
                )

        for question in config.questions:
            if question.is_scored:
                if not question.dimension_id:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            code="scored_question_without_dimension",
                            message=f"题目 {question.id} 是计分题，但没有绑定维度。",
                        )
                    )
                elif question.dimension_id not in dimension_ids:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            code="unknown_dimension",
                            message=f"题目 {question.id} 绑定了不存在的维度 {question.dimension_id}。",
                        )
                    )
                for option in question.options:
                    if option.score is None:
                        issues.append(
                            ValidationIssue(
                                level="error",
                                code="missing_option_score",
                                message=f"题目 {question.id} 的选项 {option.id} 缺少分值。",
                            )
                        )

        for result in config.results:
            if result.kind == "standard":
                if len(result.template) != len(config.dimensions):
                    issues.append(
                        ValidationIssue(
                            level="error",
                            code="template_length_mismatch",
                            message=f"结果 {result.id} 的模板长度应为 {len(config.dimensions)}。",
                        )
                    )
            if result.kind == "fallback" and result.template:
                issues.append(
                    ValidationIssue(
                        level="info",
                        code="fallback_template_ignored",
                        message=f"兜底结果 {result.id} 的模板会被忽略。",
                    )
                )

        if config.scoring.fallback_result_id not in result_ids:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="missing_fallback",
                    message=f"兜底结果 {config.scoring.fallback_result_id} 不存在。",
                )
            )

        for rule in config.rules:
            if rule.question_id not in question_ids:
                issues.append(
                    ValidationIssue(
                        level="error",
                        code="rule_unknown_question",
                        message=f"规则 {rule.id} 引用了不存在的题目 {rule.question_id}。",
                    )
                )
            else:
                question = next(item for item in config.questions if item.id == rule.question_id)
                option_ids = {option.id for option in question.options}
                if rule.option_id not in option_ids:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            code="rule_unknown_option",
                            message=f"规则 {rule.id} 引用了不存在的选项 {rule.option_id}。",
                        )
                    )
            if rule.result_id not in result_ids:
                issues.append(
                    ValidationIssue(
                        level="error",
                        code="rule_unknown_result",
                        message=f"规则 {rule.id} 引用了不存在的结果 {rule.result_id}。",
                    )
                )

        return ValidationReport(issues=issues)

    def _check_duplicates(self, label: str, values: list[str], issues: list[ValidationIssue]) -> None:
        counts = Counter(values)
        for value, count in counts.items():
            if count > 1:
                issues.append(
                    ValidationIssue(
                        level="error",
                        code=f"duplicate_{label}_id",
                        message=f"{label} ID {value} 重复。",
                    )
                )
