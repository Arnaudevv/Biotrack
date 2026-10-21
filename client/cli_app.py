"""Interactive terminal client for the BioTrack TCP server."""

from __future__ import annotations

import sys
from datetime import date, datetime
from typing import Any, Iterable

try:
    from rich.console import Console
except ImportError:  # pragma: no cover - optional CLI dependency
    Console = None

from client import api_client as api


def _print(message: str) -> None:
    if Console is not None:
        Console().print(message)
    else:
        print(message)


def clear_screen() -> None:
    """Clear the terminal screen when supported."""
    if sys.platform.startswith("win"):
        try:
            import os
            os.system("cls")
        except OSError:
            pass
    else:
        try:
            import os
            os.system("clear")
        except OSError:
            pass


def show_banner() -> None:
    """Display a small banner in the terminal."""
    title = "BioTrack CLI"
    if Console is None:
        print(title)
        return
    Console().print("[bold cyan]BioTrack[/bold cyan] [white]TCP client[/white]")


def press_any_key() -> None:
    """Pause the CLI until the user presses Enter."""
    input("Press Enter to continue... ")


def validate_required(value: str | None, label: str) -> str:
    """Require a non-empty value from the user."""
    if value is None or value.strip() == "":
        raise ValueError(f"{label} is required")
    return value.strip()


def parse_date(value: str | None) -> date:
    """Parse an ISO date string to a date object."""
    if value is None or value.strip() == "":
        raise ValueError("Date is required")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("Use YYYY-MM-DD format") from exc


def _table(rows: Iterable[dict[str, Any]], columns: list[str]) -> str:
    values = []
    for row in rows:
        values.append([str(row.get(column, "")) for column in columns])

    widths = [len(column) for column in columns]
    for row in values:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    header = " | ".join(column.ljust(widths[i]) for i, column in enumerate(columns))
    sep = "-+-".join("-" * widths[i] for i in range(len(columns)))
    lines = [header, sep]
    for row in values:
        lines.append(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)


def _print_rows(title: str, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    rows = list(rows)
    if not rows:
        _print(f"{title}: no records found.")
        return
    _print(f"\n{title}\n")
    _print(_table(rows, columns))


def _prompt_bool(prompt: str) -> bool:
    while True:
        value = input(f"{prompt} [y/N]: ").strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"", "n", "no"}:
            return False
        print("Please answer yes or no.")


def _print_choices(label: str, values: list[str]) -> None:
    """Display a list of valid options to guide the user."""
    if not values:
        print(f"{label}: no options available yet.")
        return
    print(f"{label}: {', '.join(values)}")


def _get_sample_types() -> list[str]:
    try:
        payload = api.list_sample_types()
        if isinstance(payload, dict):
            payload = payload.get("items", []) if isinstance(payload.get("items"), list) else []
        return [str(item.get("type_name", "")).strip() for item in payload if item.get("type_name")]
    except Exception:
        return []


def _get_container_codes() -> list[str]:
    try:
        payload = api.list_containers()
        if isinstance(payload, dict):
            payload = payload.get("items", []) if isinstance(payload.get("items"), list) else []
        return [str(item.get("code", "")).strip() for item in payload if item.get("code")]
    except Exception:
        return []


def list_patients(active_only: bool = False) -> None:
    """List patient records."""
    try:
        payload = api.list_patients(active_only=active_only)
        rows = [{
            "id": item.get("id", ""),
            "code": item.get("code", ""),
            "name": f"{item.get('name', '')} {item.get('lastname', '')}".strip(),
            "birth_date": item.get("birth_date", ""),
            "active": "🟢" if item.get("active") else "🔴",
            "test": item.get("test", ""),
            "registration_date": item.get("registration_date", ""),
        } for item in payload]
        _print_rows("Patients", rows, ["id", "code", "name", "birth_date", "active", "test", "registration_date"])
    except Exception as exc:
        _print(f"Error: {exc}")


def create_patient() -> None:
    """Create a patient via the API."""
    try:
        code = validate_required(input("Patient code: ").strip(), "Patient code")
        name = validate_required(input("Name: ").strip(), "Name")
        lastname = validate_required(input("Lastname: ").strip(), "Lastname")
        birth_date = parse_date(input("Birth date (YYYY-MM-DD): ")).isoformat()
        test = input("Clinical test / note (optional): ").strip() or "Routine checkup"
        active = _prompt_bool("Active patient?")
        response = api.create_patient({
            "code": code,
            "name": name,
            "lastname": lastname,
            "birth_date": birth_date,
            "test": test,
            "active": active,
        })
        _print(f"Created patient: {response}")
    except Exception as exc:
        _print(f"Error: {exc}")


def search_patient() -> None:
    """Search a patient by code."""
    code = input("Patient code: ").strip()
    if not code:
        _print("Patient code is required.")
        return
    try:
        patient = api.get_patient(code)
        _print(patient)
    except Exception as exc:
        _print(f"Error: {exc}")


def view_patient_samples() -> None:
    code = input("Patient code: ").strip()
    if not code:
        _print("Patient code is required.")
        return
    try:
        samples = api.list_patient_samples(code)
        rows = [{
            "code": item.get("code", ""),
            "volume": item.get("volume", ""),
            "status": item.get("status", ""),
            "extraction_date": item.get("extraction_date", ""),
        } for item in samples]
        _print_rows(f"Samples for patient {code}", rows, ["code", "volume", "status", "extraction_date"])
    except Exception as exc:
        _print(f"Error: {exc}")


def list_samples() -> None:
    """List sample records."""
    status = input("Filter by status (blank = all): ").strip() or None
    try:
        payload = api.list_samples(status)
        rows = [{
            "id": item.get("id", ""),
            "code": item.get("code", ""),
            "patient_code": item.get("patient_code", ""),
            "volume": item.get("volume", ""),
            "status": item.get("status", ""),
            "sample_type": item.get("sample_type", ""),
            "container_code": item.get("container_code", ""),
            "extraction_date": item.get("extraction_date", ""),
        } for item in payload]
        _print_rows("Samples", rows, ["id", "code", "patient_code", "volume", "status", "sample_type", "container_code", "extraction_date"])
    except Exception as exc:
        _print(f"Error: {exc}")


def create_sample() -> None:
    """Create a sample via the API."""
    try:
        sample_types = _get_sample_types()
        container_codes = _get_container_codes()

        _print("Create a sample: values are entered as text and volume is in millilitres (mL).")
        if sample_types:
            _print_choices("Available sample types", sample_types)
        else:
            _print("No sample types available yet. Create one in Administration > Create sample type first.")
        if container_codes:
            _print_choices("Available container codes", container_codes)
        else:
            _print("No containers available yet. Create one in Administration > Create container first.")

        code = validate_required(input("Sample code: ").strip(), "Sample code")
        volume_input = input("Volume in mL (example: 2.5): ").strip()
        try:
            volume = float(volume_input)
        except ValueError as exc:
            raise ValueError("Volume must be a number in mL (example: 2.5)") from exc
        if volume <= 0:
            raise ValueError("Volume must be greater than 0 mL")

        extraction_date = parse_date(input("Extraction date (YYYY-MM-DD): ")).isoformat()
        patient_code = validate_required(input("Patient code: ").strip(), "Patient code")
        sample_type = validate_required(input("Sample type: ").strip(), "Sample type")
        container_code = validate_required(input("Container code: ").strip(), "Container code")
        status_options = ["pending", "in_process", "analyzed", "rejected", "archived"]
        _print_choices("Allowed statuses", status_options)
        status = input("Status [pending]: ").strip() or "pending"
        if status not in status_options:
            raise ValueError(f"Status must be one of: {', '.join(status_options)}")

        response = api.create_sample({
            "code": code,
            "volume": str(volume),
            "extraction_date": extraction_date,
            "patient_code": patient_code,
            "sample_type": sample_type,
            "container_code": container_code,
            "status": status,
        })
        _print(f"Created sample: {response}")
    except Exception as exc:
        _print(f"Error: {exc}")


def list_staff() -> None:
    """List staff."""
    try:
        payload = api.list_staff()
        rows = [{
            "id": item.get("id", ""),
            "code": item.get("code", ""),
            "name": f"{item.get('name', '')} {item.get('lastname', '')}".strip(),
            "role": item.get("role", ""),
        } for item in payload]
        _print_rows("Staff", rows, ["id", "code", "name", "role"])
    except Exception as exc:
        _print(f"Error: {exc}")


def create_staff() -> None:
    """Create staff member."""
    try:
        code = validate_required(input("Staff code: ").strip(), "Staff code")
        name = validate_required(input("Name: ").strip(), "Name")
        lastname = validate_required(input("Lastname: ").strip(), "Lastname")
        role = validate_required(input("Role: ").strip(), "Role")
        active = _prompt_bool("Active staff?")
        response = api.create_staff({
            "code": code,
            "name": name,
            "lastname": lastname,
            "role": role,
            "active": active,
        })
        _print(f"Created staff: {response}")
    except Exception as exc:
        _print(f"Error: {exc}")


def list_projects() -> None:
    """List projects."""
    try:
        payload = api.list_projects()
        rows = [{
            "id": item.get("id", ""),
            "project_name": item.get("project_name", ""),
            "start_date": item.get("start_date", ""),
            "description": (item.get("description", "") or "")[:50],
        } for item in payload]
        _print_rows("Projects", rows, ["id", "project_name", "start_date", "description"])
    except Exception as exc:
        _print(f"Error: {exc}")


def create_project() -> None:
    """Create a project."""
    try:
        project_name = validate_required(input("Project name: ").strip(), "Project name")
        start_date = parse_date(input("Start date (YYYY-MM-DD): ")).isoformat()
        description = input("Description (optional): ").strip()
        response = api.create_project({
            "project_name": project_name,
            "start_date": start_date,
            "description": description,
        })
        _print(f"Created project: {response}")
    except Exception as exc:
        _print(f"Error: {exc}")


def list_protocols() -> None:
    """List protocols."""
    try:
        payload = api.list_protocols()
        rows = [{
            "id": item.get("id", ""),
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "reviewed_by": item.get("reviewed_by", "UNREVIEWED"),
            "description": (item.get("description", "") or "")[:40],
        } for item in payload]
        _print_rows("Protocols", rows, ["id", "code", "name", "reviewed_by", "description"])
    except Exception as exc:
        _print(f"Error: {exc}")


def create_protocol() -> None:
    """Create a protocol."""
    try:
        code = validate_required(input("Protocol code: ").strip(), "Protocol code")
        name = validate_required(input("Protocol name: ").strip(), "Protocol name")
        description = input("Description (optional): ").strip()
        reviewer = input("Reviewed by staff code (optional): ").strip() or None
        payload = {"code": code, "name": name, "description": description}
        if reviewer:
            payload["reviewed_by"] = reviewer
        response = api.create_protocol(payload)
        _print(f"Created protocol: {response}")
    except Exception as exc:
        _print(f"Error: {exc}")


def list_containers() -> None:
    """List containers."""
    try:
        payload = api.list_containers()
        rows = [{"id": item.get("id", ""), "code": item.get("code", ""), "type_name": item.get("type_name", "")} for item in payload]
        _print_rows("Containers", rows, ["id", "code", "type_name"])
    except Exception as exc:
        _print(f"Error: {exc}")


def create_container() -> None:
    try:
        code = validate_required(input("Container code: ").strip(), "Container code")
        type_name = validate_required(input("Type name: ").strip(), "Type name")
        _print("Tip: container codes usually identify the physical storage unit. Example: C-001, Freezer-A1")
        response = api.create_container({"code": code, "type_name": type_name})
        _print(f"Created container: {response}")
    except Exception as exc:
        _print(f"Error: {exc}")


def list_sample_types() -> None:
    try:
        payload = api.list_sample_types()
        rows = [{"id": item.get("id", ""), "type_name": item.get("type_name", "")} for item in payload]
        _print_rows("Sample types", rows, ["id", "type_name"])
    except Exception as exc:
        _print(f"Error: {exc}")


def create_sample_type() -> None:
    try:
        existing = _get_sample_types()
        if existing:
            _print_choices("Current sample types", existing)
        type_name = validate_required(input("Sample type name: ").strip(), "Sample type name")
        response = api.create_sample_type({"type_name": type_name})
        _print(f"Created sample type: {response}")
    except Exception as exc:
        _print(f"Error: {exc}")


def patient_menu() -> None:
    while True:
        print("\n-- Patients --")
        print("1. List patients")
        print("2. Create patient")
        print("3. Search patient")
        print("4. View patient samples")
        print("0. Back")
        choice = input("Select: ").strip()
        if choice == "1":
            list_patients()
        elif choice == "2":
            create_patient()
        elif choice == "3":
            search_patient()
        elif choice == "4":
            view_patient_samples()
        elif choice == "0":
            return
        else:
            print("Invalid option")
        press_any_key()


def sample_menu() -> None:
    while True:
        print("\n-- Samples --")
        print("1. List samples")
        print("2. Create sample")
        print("0. Back")
        choice = input("Select: ").strip()
        if choice == "1":
            list_samples()
        elif choice == "2":
            create_sample()
        elif choice == "0":
            return
        else:
            print("Invalid option")
        press_any_key()


def staff_menu() -> None:
    while True:
        print("\n-- Staff --")
        print("1. List staff")
        print("2. Create staff")
        print("0. Back")
        choice = input("Select: ").strip()
        if choice == "1":
            list_staff()
        elif choice == "2":
            create_staff()
        elif choice == "0":
            return
        else:
            print("Invalid option")
        press_any_key()


def project_menu() -> None:
    while True:
        print("\n-- Projects --")
        print("1. List projects")
        print("2. Create project")
        print("0. Back")
        choice = input("Select: ").strip()
        if choice == "1":
            list_projects()
        elif choice == "2":
            create_project()
        elif choice == "0":
            return
        else:
            print("Invalid option")
        press_any_key()


def protocol_menu() -> None:
    while True:
        print("\n-- Protocols --")
        print("1. List protocols")
        print("2. Create protocol")
        print("0. Back")
        choice = input("Select: ").strip()
        if choice == "1":
            list_protocols()
        elif choice == "2":
            create_protocol()
        elif choice == "0":
            return
        else:
            print("Invalid option")
        press_any_key()


def admin_menu() -> None:
    while True:
        print("\n-- Administration --")
        print("1. List containers")
        print("2. Create container")
        print("3. List sample types")
        print("4. Create sample type")
        print("0. Back")
        choice = input("Select: ").strip()
        if choice == "1":
            list_containers()
        elif choice == "2":
            create_container()
        elif choice == "3":
            list_sample_types()
        elif choice == "4":
            create_sample_type()
        elif choice == "0":
            return
        else:
            print("Invalid option")
        press_any_key()


def main() -> None:
    """Start the client terminal application."""
    show_banner()
    try:
        response = api.ping()
        _print(response)
    except Exception as exc:  # pragma: no cover - network errors are handled at runtime
        _print(f"Cannot reach the server: {exc}")

    while True:
        print("\nMain menu")
        print("1. Patients")
        print("2. Samples")
        print("3. Staff")
        print("4. Projects")
        print("5. Protocols")
        print("6. Administration")
        print("0. Exit")
        choice = input("Select: ").strip()
        if choice == "1":
            patient_menu()
        elif choice == "2":
            sample_menu()
        elif choice == "3":
            staff_menu()
        elif choice == "4":
            project_menu()
        elif choice == "5":
            protocol_menu()
        elif choice == "6":
            admin_menu()
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()
    sys.exit(0)
