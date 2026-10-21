from __future__ import annotations

from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional


def _to_json_value(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value):
        return dto_to_dict(value)
    if isinstance(value, list):
        return [_to_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_json_value(item) for key, item in value.items()}
    if hasattr(value, "__dict__"):
        return dto_to_dict(value)
    return value


def dto_to_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        payload = {}
        for field_name, field_value in asdict(value, dict_factory=dict).items():
            payload[field_name] = _to_json_value(field_value)
        return payload
    if isinstance(value, dict):
        return {str(key): _to_json_value(item) for key, item in value.items()}
    if hasattr(value, "__dict__"):
        return {key: _to_json_value(item) for key, item in vars(value).items()}
    return value


def dto_from_dict(data_class: type, payload: dict[str, Any] | None):
    if payload is None:
        return None
    if not isinstance(payload, dict):
        return payload
    values = {}
    for field_name, field_type in getattr(data_class, "__annotations__", {}).items():
        if field_name in payload:
            value = payload[field_name]
            if value is None:
                values[field_name] = None
            elif field_type is datetime:
                values[field_name] = datetime.fromisoformat(value)
            elif field_type is date:
                values[field_name] = date.fromisoformat(value)
            elif field_type is Decimal:
                values[field_name] = Decimal(str(value))
            elif hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                item_type = field_type.__args__[0] if field_type.__args__ else str
                values[field_name] = [dto_from_dict(item_type, item) if isinstance(item, dict) else item for item in value]
            elif getattr(field_type, "__module__", None) == "dataclasses":
                values[field_name] = dto_from_dict(field_type, value)
            else:
                values[field_name] = value
    return data_class(**values)


@dataclass
class PatientDTO:
    id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    lastname: Optional[str] = None
    birth_date: Optional[date] = None
    active: bool = True
    test: str = "Routine checkup"
    registration_date: Optional[datetime] = None


@dataclass
class SampleDTO:
    id: Optional[int] = None
    code: Optional[str] = None
    volume: Optional[Decimal] = None
    extraction_date: Optional[date] = None
    status: str = "pending"
    patient_code: Optional[str] = None
    sample_type: Optional[str] = None
    container_code: Optional[str] = None


@dataclass
class StaffDTO:
    id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    lastname: Optional[str] = None
    role: Optional[str] = None
    active: bool = True


@dataclass
class ProjectDTO:
    id: Optional[int] = None
    project_name: Optional[str] = None
    start_date: Optional[date] = None
    description: Optional[str] = None


@dataclass
class ProtocolDTO:
    id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    reviewed_by: Optional[str] = None
    last_update: Optional[datetime] = None


@dataclass
class ContainerDTO:
    id: Optional[int] = None
    code: Optional[str] = None
    type_name: Optional[str] = None
    last_update: Optional[datetime] = None


@dataclass
class SampleTypeDTO:
    id: Optional[int] = None
    type_name: Optional[str] = None
    last_update: Optional[datetime] = None


@dataclass
class QualityControlDTO:
    sample_code: Optional[str] = None
    purity: Optional[Decimal] = None
    concentration: Optional[Decimal] = None
    result: Optional[str] = None
