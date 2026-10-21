"""Application-level router factory for the TCP server."""

from __future__ import annotations

from typing import Any, Callable

from server.controllers.container_controller import ContainerController
from server.controllers.patient_controller import PatientController
from server.controllers.project_controller import ProjectController
from server.controllers.protocol_controller import ProtocolController
from server.controllers.sample_controller import SampleController
from server.controllers.sample_type_controller import SampleTypeController
from server.controllers.staff_controller import StaffController
from server.persistence.config import DB_URL
from server.persistence.repositories.unit_of_work import UnitOfWorkFactory
from server.services.container_service import ContainerService
from server.services.patient_service import PatientService
from server.services.project_service import ProjectService
from server.services.protocol_service import ProtocolService
from server.services.sample_service import SampleService
from server.services.sample_type_service import SampleTypeService
from server.services.staff_service import StaffService
from shared.errors import BadRequestError, ConflictError, NotFoundError
from shared.errors import ServiceValidationError


def _match_path(pattern: str, path: str) -> dict[str, str] | None:
    """Match a route pattern to a request path and return path params."""
    pattern_parts = pattern.strip("/").split("/") if pattern != "/" else []
    path_parts = path.strip("/").split("/") if path != "/" else []
    if len(pattern_parts) != len(path_parts):
        return None
    params: dict[str, str] = {}
    for pattern_part, path_part in zip(pattern_parts, path_parts):
        if pattern_part.startswith("{") and pattern_part.endswith("}"):
            params[pattern_part[1:-1]] = path_part
        elif pattern_part != path_part:
            return None
    return params


def build_router() -> Callable[[dict[str, Any]], dict[str, Any] | list | None]:
    """Build the application router with all documented endpoints."""
    routes: list[tuple[str, str, Callable[..., Any]]] = []
    uow_factory = UnitOfWorkFactory(DB_URL)

    def register(method: str, path: str, handler: Callable[..., Any]) -> None:
        routes.append((method.upper(), path, handler))

    def ping_handler(request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return {"message": "pong"}

    def make_patient_controller():
        uow = uow_factory.create()
        return PatientController(PatientService(uow))

    def make_staff_controller():
        uow = uow_factory.create()
        return StaffController(StaffService(uow))

    def make_container_controller():
        uow = uow_factory.create()
        return ContainerController(ContainerService(uow))

    def make_sample_type_controller():
        uow = uow_factory.create()
        return SampleTypeController(SampleTypeService(uow))

    def make_sample_controller():
        uow = uow_factory.create()
        return SampleController(SampleService(uow))

    def make_project_controller():
        uow = uow_factory.create()
        return ProjectController(ProjectService(uow))

    def make_protocol_controller():
        uow = uow_factory.create()
        return ProtocolController(ProtocolService(uow))

    def patient_list_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_patient_controller()
        return controller.list_patients(request)

    def patient_get_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_patient_controller()
        return controller.get_patient(request, params)

    def patient_create_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_patient_controller()
        return controller.create_patient(request)

    def patient_update_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_patient_controller()
        return controller.update_patient(request, params)

    def patient_delete_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_patient_controller()
        return controller.delete_patient(request, params)

    def patient_samples_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_patient_controller()
        return controller.list_samples(request, params)

    def sample_list_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.list_samples(request)

    def sample_get_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.get_sample(request, params)

    def sample_full_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.get_full_sample(request, params)

    def sample_create_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.create_sample(request)

    def sample_update_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.update_sample(request, params)

    def sample_delete_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.delete_sample(request, params)

    def sample_quality_control_get_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.get_quality_control(request, params)

    def sample_quality_control_put_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.set_quality_control(request, params)

    def sample_protocol_post_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_controller()
        return controller.apply_protocol(request, params)

    def staff_list_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_staff_controller()
        return controller.list_staff(request)

    def staff_get_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_staff_controller()
        return controller.get_staff(request, params)

    def staff_create_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_staff_controller()
        return controller.create_staff(request)

    def staff_update_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_staff_controller()
        return controller.update_staff(request, params)

    def staff_delete_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_staff_controller()
        return controller.delete_staff(request, params)

    def staff_assignments_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_staff_controller()
        return controller.list_assignments(request, params)

    def project_list_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_project_controller()
        return controller.list_projects(request)

    def project_get_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_project_controller()
        return controller.get_project(request, params)

    def project_create_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_project_controller()
        return controller.create_project(request)

    def project_update_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_project_controller()
        return controller.update_project(request, params)

    def project_delete_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_project_controller()
        return controller.delete_project(request, params)

    def project_link_sample_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_project_controller()
        return controller.link_sample_to_project(request, params)

    def project_add_team_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_project_controller()
        return controller.add_team_member(request, params)

    def protocol_list_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_protocol_controller()
        return controller.list_protocols(request)

    def protocol_get_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_protocol_controller()
        return controller.get_protocol(request, params)

    def protocol_create_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_protocol_controller()
        return controller.create_protocol(request)

    def protocol_update_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_protocol_controller()
        return controller.update_protocol(request, params)

    def protocol_delete_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_protocol_controller()
        return controller.delete_protocol(request, params)

    def protocol_samples_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_protocol_controller()
        return controller.list_samples(request, params)

    def container_list_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_container_controller()
        return controller.list_containers(request)

    def container_create_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_container_controller()
        return controller.create_container(request)

    def sample_type_list_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_type_controller()
        return controller.list_sample_types(request)

    def sample_type_create_handler(request: dict[str, Any], params: dict[str, str]):
        controller = make_sample_type_controller()
        return controller.create_sample_type(request)

    register("GET", "/ping", ping_handler)
    register("GET", "/patients", patient_list_handler)
    register("POST", "/patients", patient_create_handler)
    register("GET", "/patients/{code}", patient_get_handler)
    register("PATCH", "/patients/{code}", patient_update_handler)
    register("DELETE", "/patients/{code}", patient_delete_handler)
    register("GET", "/patients/{code}/samples", patient_samples_handler)
    register("GET", "/samples", sample_list_handler)
    register("POST", "/samples", sample_create_handler)
    register("GET", "/samples/{code}", sample_get_handler)
    register("GET", "/samples/{code}/full", sample_full_handler)
    register("PATCH", "/samples/{code}", sample_update_handler)
    register("DELETE", "/samples/{code}", sample_delete_handler)
    register("GET", "/samples/{code}/quality-control", sample_quality_control_get_handler)
    register("PUT", "/samples/{code}/quality-control", sample_quality_control_put_handler)
    register("POST", "/samples/{code}/protocols", sample_protocol_post_handler)
    register("GET", "/staff", staff_list_handler)
    register("POST", "/staff", staff_create_handler)
    register("GET", "/staff/{code}", staff_get_handler)
    register("PATCH", "/staff/{code}", staff_update_handler)
    register("DELETE", "/staff/{code}", staff_delete_handler)
    register("GET", "/staff/{code}/assignments", staff_assignments_handler)
    register("GET", "/projects", project_list_handler)
    register("POST", "/projects", project_create_handler)
    register("GET", "/projects/{id}", project_get_handler)
    register("PATCH", "/projects/{id}", project_update_handler)
    register("DELETE", "/projects/{id}", project_delete_handler)
    register("POST", "/projects/{id}/samples", project_link_sample_handler)
    register("POST", "/projects/{id}/team", project_add_team_handler)
    register("GET", "/protocols", protocol_list_handler)
    register("POST", "/protocols", protocol_create_handler)
    register("GET", "/protocols/{code}", protocol_get_handler)
    register("PATCH", "/protocols/{code}", protocol_update_handler)
    register("DELETE", "/protocols/{code}", protocol_delete_handler)
    register("GET", "/protocols/{code}/samples", protocol_samples_handler)
    register("GET", "/containers", container_list_handler)
    register("POST", "/containers", container_create_handler)
    register("GET", "/sample-types", sample_type_list_handler)
    register("POST", "/sample-types", sample_type_create_handler)

    def router(request: dict[str, Any]) -> dict[str, Any] | list | None:
        method = request.get("method", "GET").upper()
        path = request.get("path", "/")
        params: dict[str, str] | None = None
        matched: tuple[str, str, Callable[..., Any]] | None = None

        for route_method, route_path, handler in routes:
            if route_method != method:
                continue
            params = _match_path(route_path, path)
            if params is not None:
                matched = (route_method, route_path, handler)
                break

        if matched is None:
            for route_method, route_path, _ in routes:
                if route_path == path and route_method != method:
                    raise BadRequestError(f"Method {method} not allowed for {path}")
            for route_method, route_path, _ in routes:
                if _match_path(route_path, path) is not None:
                    raise BadRequestError(f"Method {method} not allowed for {path}")
            raise NotFoundError(f"Route not found: {path}")

        handler = matched[2]
        try:
            return handler(request, params or {})
        except (NotFoundError, ConflictError, ServiceValidationError) as exc:
            raise exc

    return router
