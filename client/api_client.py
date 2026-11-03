"""High-level API client for the BioTrack TCP server."""

from __future__ import annotations

from client.connection import send_request
from shared.protocol import percent_encode


def ping() -> dict:
    """Check that the server is reachable."""
    return send_request("GET", "/ping")


def list_patients(active_only: bool = False) -> list[dict] | dict:
    """List all patients or only those matching the active filter."""
    path = "/patients?active=true" if active_only else "/patients"
    return send_request("GET", path)


def get_patient(code: str) -> dict:
    """Fetch a single patient."""
    return send_request("GET", f"/patients/{code}")


def create_patient(payload: dict) -> dict:
    """Create a patient."""
    return send_request("POST", "/patients", payload)


def update_patient(code: str, payload: dict) -> dict:
    """Update a patient."""
    return send_request("PATCH", f"/patients/{code}", payload)


def delete_patient(code: str) -> dict:
    """Delete a patient."""
    return send_request("DELETE", f"/patients/{code}")


def list_patient_samples(code: str) -> list[dict] | dict:
    """List samples for a patient."""
    return send_request("GET", f"/patients/{code}/samples")


def list_samples(status: str | None = None) -> list[dict] | dict:
    """List all samples or filter them by status."""
    path = "/samples"
    if status:
        path = f"/samples?status={status}"
    return send_request("GET", path)


def list_samples_by_date(start_date: str, end_date: str) -> list[dict] | dict:
    """List samples extracted in an inclusive date range."""
    return send_request("GET", f"/samples?start_date={start_date}&end_date={end_date}")


def get_sample(code: str) -> dict:
    """Fetch a sample."""
    return send_request("GET", f"/samples/{code}")


def get_full_sample(code: str) -> dict:
    """Fetch the full sample graph."""
    return send_request("GET", f"/samples/{code}/full")


def create_sample(payload: dict) -> dict:
    """Create a sample."""
    return send_request("POST", "/samples", payload)


def update_sample(code: str, payload: dict) -> dict:
    """Update a sample."""
    return send_request("PATCH", f"/samples/{code}", payload)


def delete_sample(code: str) -> dict:
    """Delete a sample."""
    return send_request("DELETE", f"/samples/{code}")


def get_quality_control(code: str) -> dict:
    """Read the quality control for a sample."""
    return send_request("GET", f"/samples/{code}/quality-control")


def set_quality_control(code: str, payload: dict) -> dict:
    """Create or update quality control for a sample."""
    return send_request("PUT", f"/samples/{code}/quality-control", payload)


def delete_quality_control(code: str) -> dict:
    """Delete the quality control for a sample."""
    return send_request("DELETE", f"/samples/{code}/quality-control")


def apply_protocol_to_sample(code: str, protocol_code: str) -> dict:
    """Apply a protocol to a sample."""
    return send_request("POST", f"/samples/{code}/protocols", {"protocol_code": protocol_code})


def remove_protocol_from_sample(code: str, protocol_code: str) -> dict:
    return send_request("DELETE", f"/samples/{code}/protocols/{protocol_code}")


def list_container_samples(code: str) -> list[dict] | dict:
    return send_request("GET", f"/containers/{code}/samples")


def list_sample_type_samples(type_name: str) -> list[dict] | dict:
    return send_request("GET", f"/sample-types/{percent_encode(type_name)}/samples")


def list_staff() -> list[dict] | dict:
    """Retrieve all staff records."""
    return send_request("GET", "/staff")


def get_staff(code: str) -> dict:
    """Retrieve an individual staff record."""
    return send_request("GET", f"/staff/{code}")


def create_staff(payload: dict) -> dict:
    """Create a staff record."""
    return send_request("POST", "/staff", payload)


def update_staff(code: str, payload: dict) -> dict:
    """Update a staff record."""
    return send_request("PATCH", f"/staff/{code}", payload)


def delete_staff(code: str) -> dict:
    """Delete a staff record."""
    return send_request("DELETE", f"/staff/{code}")


def list_staff_assignments(code: str) -> list[dict] | dict:
    """List project assignments for a staff member."""
    return send_request("GET", f"/staff/{code}/assignments")


def list_staff_protocols(code: str) -> list[dict] | dict:
    return send_request("GET", f"/staff/{code}/protocols")


def list_containers() -> list[dict] | dict:
    """Retrieve all containers."""
    return send_request("GET", "/containers")


def create_container(payload: dict) -> dict:
    """Create a container record."""
    return send_request("POST", "/containers", payload)


def get_container(code: str) -> dict:
    return send_request("GET", f"/containers/{code}")


def update_container(code: str, payload: dict) -> dict:
    return send_request("PATCH", f"/containers/{code}", payload)


def delete_container(code: str) -> dict:
    return send_request("DELETE", f"/containers/{code}")


def list_sample_types() -> list[dict] | dict:
    """Retrieve all sample types."""
    return send_request("GET", "/sample-types")


def create_sample_type(payload: dict) -> dict:
    """Create a sample type."""
    return send_request("POST", "/sample-types", payload)


def get_sample_type(type_name: str) -> dict:
    return send_request("GET", f"/sample-types/{percent_encode(type_name)}")


def update_sample_type(type_name: str, payload: dict) -> dict:
    return send_request("PATCH", f"/sample-types/{percent_encode(type_name)}", payload)


def delete_sample_type(type_name: str) -> dict:
    return send_request("DELETE", f"/sample-types/{percent_encode(type_name)}")


def list_projects(name: str | None = None) -> list[dict] | dict:
    """Retrieve all projects."""
    return send_request("GET", f"/projects?name={percent_encode(name)}" if name else "/projects")


def get_project(project_id: int) -> dict:
    """Fetch a project."""
    return send_request("GET", f"/projects/{project_id}")


def get_project_details(project_id: int) -> dict:
    """Fetch a project including team roles and sample assignment dates."""
    return send_request("GET", f"/projects/{project_id}/details")


def create_project(payload: dict) -> dict:
    """Create a research project."""
    return send_request("POST", "/projects", payload)


def update_project(project_id: int, payload: dict) -> dict:
    """Update a project."""
    return send_request("PATCH", f"/projects/{project_id}", payload)


def delete_project(project_id: int) -> dict:
    """Delete a project."""
    return send_request("DELETE", f"/projects/{project_id}")


def link_sample_to_project(
    project_id: int, sample_code: str, assignment_date: str | None = None
) -> dict:
    """Link a sample to a project."""
    payload = {"sample_code": sample_code}
    if assignment_date is not None:
        payload["sample_assignment_date"] = assignment_date
    return send_request("POST", f"/projects/{project_id}/samples", payload)


def list_project_samples(project_id: int) -> list[dict] | dict:
    return send_request("GET", f"/projects/{project_id}/samples")


def update_project_sample(project_id: int, sample_code: str, assignment_date: str) -> dict:
    return send_request(
        "PATCH", f"/projects/{project_id}/samples/{sample_code}",
        {"sample_assignment_date": assignment_date},
    )


def remove_sample_from_project(project_id: int, sample_code: str) -> dict:
    return send_request("DELETE", f"/projects/{project_id}/samples/{sample_code}")


def add_team_member(project_id: int, staff_code: str, role: str) -> dict:
    """Add a staff member to a project."""
    return send_request("POST", f"/projects/{project_id}/team", {"staff_code": staff_code, "role": role})


def list_project_team(project_id: int) -> list[dict] | dict:
    return send_request("GET", f"/projects/{project_id}/team")


def update_team_member(project_id: int, staff_code: str, role: str) -> dict:
    return send_request("PATCH", f"/projects/{project_id}/team/{staff_code}", {"role": role})


def remove_team_member(project_id: int, staff_code: str) -> dict:
    return send_request("DELETE", f"/projects/{project_id}/team/{staff_code}")


def list_protocols(keyword: str | None = None) -> list[dict] | dict:
    """Retrieve all protocols."""
    return send_request("GET", f"/protocols?keyword={percent_encode(keyword)}" if keyword else "/protocols")


def get_protocol(code: str) -> dict:
    """Retrieve a protocol."""
    return send_request("GET", f"/protocols/{code}")


def create_protocol(payload: dict) -> dict:
    """Create a protocol."""
    return send_request("POST", "/protocols", payload)


def update_protocol(code: str, payload: dict) -> dict:
    """Update a protocol."""
    return send_request("PATCH", f"/protocols/{code}", payload)


def delete_protocol(code: str) -> dict:
    """Delete a protocol."""
    return send_request("DELETE", f"/protocols/{code}")


def list_protocol_samples(code: str) -> list[dict] | dict:
    """List samples linked to a protocol."""
    return send_request("GET", f"/protocols/{code}/samples")
