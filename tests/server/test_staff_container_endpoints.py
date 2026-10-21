"""Tests for the staff and administration resource endpoints."""

import unittest
from unittest.mock import MagicMock

from server.controllers.container_controller import ContainerController
from server.controllers.staff_controller import StaffController
from server.services.container_service import ContainerService
from server.services.staff_service import StaffService
from shared.errors import ServiceValidationError


class StaffServiceTests(unittest.TestCase):
    def test_create_staff_success(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = StaffService(uow)
        service.staff_repository = MagicMock()
        service.staff_repository.get_by_code.return_value = None
        created = service.create_staff({"code": "ST-001", "name": "Ana", "lastname": "López", "role": "researcher"})
        self.assertEqual(created.code, "ST-001")

    def test_create_staff_invalid_role_raises(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = StaffService(uow)
        with self.assertRaises(ServiceValidationError):
            service.create_staff({"code": "ST-001", "name": "Ana", "lastname": "López", "role": "invalid"})


class ContainerServiceTests(unittest.TestCase):
    def test_create_container_success(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = ContainerService(uow)
        service.container_repository = MagicMock()
        service.container_repository.get_by_code_or_type_name.return_value = None
        created = service.create_container({"code": "CNT-001", "type_name": "Plastic tube"})
        self.assertEqual(created.code, "CNT-001")


class StaffControllerTests(unittest.TestCase):
    def test_list_staff_calls_service(self):
        service = MagicMock()
        service.list_staff.return_value = []
        controller = StaffController(service)
        result = controller.list_staff({})
        self.assertEqual(result, [])


class ContainerControllerTests(unittest.TestCase):
    def test_create_container_requires_body_dict(self):
        service = MagicMock()
        controller = ContainerController(service)
        with self.assertRaises(Exception):
            controller.create_container({"body": "bad"})


if __name__ == "__main__":
    unittest.main()
