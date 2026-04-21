from typing import Literal

from pydantic import BaseModel


ValidationLevel = Literal["error", "warning", "info"]


class ValidationIssue(BaseModel):
    level: ValidationLevel
    code: str
    message: str


class ValidationReport(BaseModel):
    issues: list[ValidationIssue]

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def infos(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == "info"]

    @property
    def can_export(self) -> bool:
        return not self.errors
