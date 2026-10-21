"""Tests for the patient endpoints and controller behavior."""

import unittest
from unittest.mock import MagicMock

from server.controllers.patient_controller import PatientController
from server.services.patient_service import PatientService
from shared.errors import NotFoundError, ServiceValidationError


class PatientServiceTests(unittest.TestCase):
    def test_create_patient_success(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = PatientService(uow)
        service.patient_repository = MagicMock()
        service.patient_repository.get_by_code.return_value = None
        patient = MagicMock()
        patient.id = 1
        patient.code = "PAT-001"
        patient.name = "Ana"
        patient.lastname = "López"
        patient.birth_date = __import__("datetime").date(1990, 1, 1)
        patient.active = True
        patient.test = "Routine checkup"
        patient.registration_date = __import__("datetime").datetime(2024, 1, 1, 0, 0, 0)
        service._dto_to_model = lambda dto: patient
        result = service.create_patient({
            "code": "PAT-001",
            "name": "Ana",
            "lastname": "López",
            "birth_date": "1990-01-01",
            "active": True,
        })
        self.assertEqual(result.code, "PAT-001")

    def test_create_patient_invalid_body_raises_validation(self):
        uow = MagicMock()
        uow.session = MagicMock()
        service = PatientService(uow)
        with self.assertRaises(ServiceValidationError):
            service.create_patient({"code": "PAT-001", "name": "Ana"})


class PatientControllerTests(unittest.TestCase):
    def test_list_patients_calls_service(self):
        service = MagicMock()
        service.list_patients.return_value = []
        controller = PatientController(service)
        result = controller.list_patients({"query": {}})
        self.assertEqual(result, [])

    def test_get_patient_uses_code_param(self):
        service = MagicMock()
        dto = MagicMock()
        dto.id = 1
        dto.code = "PAT-001"
        dto.name = "Ana"
        dto.lastname = "López"
        dto.birth_date = __import__("datetime").date(1990, 1, 1)
        dto.active = True
        dto.test = "Routine checkup"
        dto.registration_date = __import__("datetime").datetime(2024, 1, 1, 0, 0, 0)
        service.get_patient.return_value = dto
        controller = PatientController(service)
        payload = controller.get_patient({"query": {}}, {"code": "PAT-001"})
        self.assertEqual(payload["code"], "PAT-001")


if __name__ == "__main__":
    unittest.main()
