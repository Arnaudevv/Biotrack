"""HTTP controller for research project resources."""

from __future__ import annotations

from typing import Any

from shared.errors import BadRequestError, ConflictError, ServiceValidationError


class ProjectController:
    """Translate HTTP payloads into ProjectService operations."""

    def __init__(self, service):
        self.service = service

    def list_projects(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query = request.get("query", {})
        name = query.get("name")
        return [self._to_payload(item) for item in self.service.list_projects(name)]

    def get_project(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self._to_payload(self.service.get_project(int(params["id"])))

    def get_project_details(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self.service.get_project_details(int(params["id"]))

    def create_project(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        try:
            created = self.service.create_project(payload)
        except ConflictError:
            raise
        except ServiceValidationError as exc:
            raise ServiceValidationError(str(exc)) from exc
        return self._to_payload(created)

    def update_project(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        return self._to_payload(self.service.update_project(int(params["id"]), payload))

    def delete_project(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.delete_project(int(params["id"]))

    def link_sample_to_project(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        sample_code = payload.get("sample_code") or payload.get("code")
        if not sample_code:
            raise BadRequestError("Missing required field: sample_code")
        return self.service.add_sample_to_project(
            int(params["id"]), sample_code, payload.get("sample_assignment_date")
        )

    def list_samples(self, request: dict[str, Any], params: dict[str, str]) -> list[dict[str, Any]]:
        return self.service.list_project_samples(int(params["id"]))

    def update_sample(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict) or not payload.get("sample_assignment_date"):
            raise BadRequestError("Missing required field: sample_assignment_date")
        return self.service.update_sample_assignment(
            int(params["id"]), params["sample_code"], payload["sample_assignment_date"]
        )

    def unlink_sample(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.remove_sample_from_project(int(params["id"]), params["sample_code"])

    def add_team_member(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        staff_code = payload.get("staff_code") or payload.get("code")
        role = payload.get("role")
        if not staff_code:
            raise BadRequestError("Missing required field: staff_code")
        if not role:
            raise BadRequestError("Missing required field: role")
        return self.service.add_team_member(int(params["id"]), staff_code, role)

    def list_team(self, request: dict[str, Any], params: dict[str, str]) -> list[dict[str, Any]]:
        return self.service.list_project_team(int(params["id"]))

    def update_team_member(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict) or not payload.get("role"):
            raise BadRequestError("Missing required field: role")
        return self.service.update_team_member(int(params["id"]), params["staff_code"], payload["role"])

    def remove_team_member(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.remove_team_member(int(params["id"]), params["staff_code"])

    def _to_payload(self, dto) -> dict[str, Any]:
        return {
            "id": dto.id,
            "project_name": dto.project_name,
            "start_date": dto.start_date.isoformat() if dto.start_date else None,
            "description": dto.description,
            "last_update": dto.last_update.isoformat() if dto.last_update else None,
        }
