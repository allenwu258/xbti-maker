import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.database import db_session
from app.schemas.test_config import TestConfig


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectRepository:
    def list_projects(self) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
            return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            return dict(row) if row else None

    def create_project(self, name: str, topic: str, description: str, config: TestConfig) -> str:
        project_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())
        timestamp = now_iso()
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO projects (id, name, topic, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, name, topic, description, "draft", timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO test_versions
                    (id, project_id, version_number, config_json, is_current, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (version_id, project_id, 1, config.json(ensure_ascii=False, indent=2), 1, timestamp, timestamp),
            )
        return project_id

    def get_current_version(self, project_id: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute(
                """
                SELECT * FROM test_versions
                WHERE project_id = ? AND is_current = 1
                ORDER BY version_number DESC
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_current_config(self, project_id: str) -> Optional[TestConfig]:
        version = self.get_current_version(project_id)
        if not version:
            return None
        return TestConfig.parse_raw(version["config_json"])

    def save_config(self, project_id: str, config: TestConfig) -> str:
        timestamp = now_iso()
        version_id = str(uuid.uuid4())
        with db_session() as conn:
            current = conn.execute(
                "SELECT MAX(version_number) AS max_version FROM test_versions WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            next_version = int(current["max_version"] or 0) + 1
            conn.execute("UPDATE test_versions SET is_current = 0 WHERE project_id = ?", (project_id,))
            conn.execute(
                """
                INSERT INTO test_versions
                    (id, project_id, version_number, config_json, is_current, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (version_id, project_id, next_version, config.json(ensure_ascii=False, indent=2), 1, timestamp, timestamp),
            )
            conn.execute(
                "UPDATE projects SET name = ?, topic = ?, updated_at = ? WHERE id = ?",
                (config.meta.name, config.meta.subtitle, timestamp, project_id),
            )
        return version_id

    def create_export(self, project_id: str, version_id: str, file_path: str, fmt: str = "html") -> str:
        export_id = str(uuid.uuid4())
        timestamp = now_iso()
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO export_bundles (id, project_id, version_id, file_path, format, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (export_id, project_id, version_id, file_path, fmt, timestamp),
            )
        return export_id

    def get_export(self, export_id: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM export_bundles WHERE id = ?", (export_id,)).fetchone()
            return dict(row) if row else None

    def list_exports(self, project_id: str) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM export_bundles WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def config_json(self, project_id: str) -> str:
        version = self.get_current_version(project_id)
        if not version:
            raise ValueError("project has no current version")
        json.loads(version["config_json"])
        return version["config_json"]
