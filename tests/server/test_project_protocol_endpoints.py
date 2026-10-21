"""Tests for the project and protocol resource endpoints."""

import unittest
from unittest.mock import MagicMock

from server.controllers.project_controller import ProjectController
from server.controllers.protocol_controller import ProtocolController
from server.services.project_service import ProjectService
from server.services.protocol_service import ProtocolService
from shared.errors import ServiceValidationError


class ProjectServiceTests(unittest.TestCase):
    def test_create_project_success(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = ProjectService(uow)
        service.project_repository = MagicMock()
        service.project_repository.get_by_name.return_value = None
        created = service.create_project({"project_name": "Cancer Study", "start_date": "2024-01-01"})
        self.assertEqual(created.project_name, "Cancer Study")

    def test_create_project_missing_name_raises(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = ProjectService(uow)
        with self.assertRaises(ServiceValidationError):
            service.create_project({"start_date": "2024-01-01"})


class ProtocolServiceTests(unittest.TestCase):
    def test_create_protocol_success(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = ProtocolService(uow)
        service.protocol_repository = MagicMock()
        service.protocol_repository.get_by_code.return_value = None
        created = service.create_protocol({"code": "PROTO-001", "name": "DNA extraction"})
        self.assertEqual(created.code, "PROTO-001")

    def test_create_protocol_invalid_payload_raises(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = ProtocolService(uow)
        with self.assertRaises(ServiceValidationError):
            service.create_protocol({"code": "PROTO-001"})


class ProjectControllerTests(unittest.TestCase):
    def test_list_projects_calls_service(self):
        service = MagicMock()
        service.list_projects.return_value = []
        controller = ProjectController(service)
        self.assertEqual(controller.list_projects({}), [])


class ProtocolControllerTests(unittest.TestCase):
    def test_get_protocol_uses_path_parameter(self):
        service = MagicMock()
        dto = MagicMock()
        dto.id = 1
        dto.code = "PROTO-001"
        dto.name = "DNA extraction"
        dto.description = None
        dto.reviewed_by = None
        dto.last_update = None
        service.get_protocol.return_value = dto
        controller = ProtocolController(service)
        payload = controller.get_protocol({}, {"code": "PROTO-001"})
        self.assertEqual(payload["code"], "PROTO-001")


if __name__ == "__main__":
    unittest.main()
