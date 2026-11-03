"""Interactive terminal client for the BioTrack TCP server."""

from __future__ import annotations

import math
import os
import sys
import textwrap
from datetime import date
from typing import Any, Iterable

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:  # pragma: no cover - optional CLI dependency
    Console = None
    Panel = Table = None

from client import api_client as api

console = Console(no_color=bool(os.environ.get("NO_COLOR"))) if Console is not None else None

_COLUMN_LABELS = {
    "id": "ID",
    "code": "Code",
    "patient_code": "Patient code",
    "sample_type": "Sample type",
    "container_code": "Container code",
    "type_name": "Type name",
    "project_name": "Project name",
    "project_id": "Project ID",
    "staff_code": "Staff code",
    "reviewed_by": "Reviewer",
    "birth_date": "Birth date",
    "registration_date": "Registration date",
    "extraction_date": "Extraction date",
    "sample_assignment_date": "Assignment date",
    "last_update": "Last updated",
    "volume": "Volume (mL)",
    "purity": "Purity (%)",
    "concentration": "Concentration (ng/uL)",
    "status": "Status",
    "role": "Role",
    "name": "Name",
    "lastname": "Last name",
    "description": "Description",
    "active": "Active",
    "test": "Clinical test / note",
}


def _label(value: str) -> str:
    return _COLUMN_LABELS.get(value, value.replace("_", " ").title())


def _display(value: Any, key: str = "") -> str:
    if value is None or value == "":
        return "Not set"
    if key == "active":
        return "Active" if value else "Inactive"
    if key == "role":
        return str(value).replace("_", " ").title()
    if key == "status":
        return str(value).replace("_", " ").title()
    if key.endswith("date") or key in {"registration_date", "last_update"}:
        return str(value)[:10]
    return str(value)


def _print(message: str) -> None:
    if console is not None:
        console.print(message)
    else:
        print(message)


def clear_screen() -> None:
    # Keep output linear and readable for screen readers and redirected output.
    return


def show_banner(title: str = "BioTrack CLI", breadcrumb: str | None = None) -> None:
    """Display a consistent, accessible page heading."""
    path = f"Main menu > {breadcrumb}" if breadcrumb else title
    _print(f"BioTrack CLI | {path}")
    _print("=" * min(max(len(path) + 15, 32), 80))


def _status(kind: str, message: str, hint: str | None = None) -> None:
    suffix = f" Hint: {hint}" if hint else ""
    width = max(40, int(os.environ.get("COLUMNS", "80")))
    _print(textwrap.fill(f"{kind}: {message}{suffix}", width=width))


def _success(message: str) -> None:
    _status("SUCCESS", message)


def _error(exc: Exception, hint: str = "Check the values and try again.") -> None:
    message = str(exc).strip() or "The operation could not be completed."
    _status("ERROR", message, hint)


def _info(message: str) -> None:
    _status("INFO", message)


def _warning(message: str) -> None:
    _status("WARNING", message)


def _menu(title: str, breadcrumb: str, options: list[tuple[str, str, str]]) -> None:
    show_banner(title, breadcrumb)
    _print("")
    for number, label, description in options:
        suffix = f" - {description}" if description else ""
        marker = "[DESTRUCTIVE] " if label.lower().startswith(("delete", "remove", "unlink")) else ""
        width = max(40, int(os.environ.get("COLUMNS", "80")))
        prefix = f"{number}. {marker}{label}"
        _print(textwrap.fill(prefix + suffix, width=width, subsequent_indent="   "))


def _menu_choice(maximum: int) -> str:
    return input(f"Choose an option (0-{maximum}): ").strip()


def _action_heading(breadcrumb: str, title: str, explanation: str) -> None:
    show_banner(title, breadcrumb)
    _info(explanation)


def _run_action(breadcrumb: str, label: str, action) -> None:
    _action_heading(breadcrumb, label, f"Action selected: {label}. Follow the prompts below.")
    action()


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
        values.append([_display(row.get(column), column) for column in columns])

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
        _info(f"No records found in {title}. Use the relevant Add/Create option to create one.")
        return
    _print(f"\n{title} ({len(rows)} record{'s' if len(rows) != 1 else ''})")
    if Table is None or console is None:
        _print(_table(rows, columns))
        return
    table = Table(show_header=True, header_style="bold", expand=True)
    for column in columns:
        table.add_column(_label(column), justify="right" if column in {"id", "project_id"} else "left", overflow="fold")
    for row in rows:
        table.add_row(*[_display(row.get(column), column) for column in columns])
    console.print(table)


def _print_detail(title: str, record: dict[str, Any]) -> None:
    """Render a record as labelled lines instead of a raw dictionary."""
    lines = []
    for key, value in record.items():
        if isinstance(value, list):
            lines.append(f"{_label(key)}:")
            if value:
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append("  - None")
        else:
            lines.append(f"{_label(key)}: {_display(value, key)}")
    if Panel is not None and console is not None:
        console.print(Panel("\n".join(lines), title=title, border_style="cyan"))
    else:
        _print(f"\n{title}")
        _print("-" * min(max(len(title), 24), 80))
        _print("\n".join(lines))


def _prompt_bool(prompt: str) -> bool:
    while True:
        value = input(f"{prompt} [y/N; Enter = No]: ").strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"", "n", "no"}:
            return False
        _warning("Please answer yes or no. Enter y or n.")


def _print_choices(label: str, values: list[str]) -> None:
    """Display a list of valid options to guide the user."""
    if not values:
        _info(f"{label}: no options available yet.")
        return
    _print(f"{label}: {', '.join(values)}")


def _prompt_required(label: str, example: str | None = None) -> str:
    """Prompt repeatedly until the user provides a required value."""
    hint = f" [required; example: {example}]" if example else " [required]"
    while True:
        try:
            return validate_required(input(f"{label}{hint}: "), label)
        except ValueError as exc:
            _error(exc, "A value is required.")


def _prompt_date(label: str) -> str:
    """Prompt repeatedly for a date in the supported ISO format."""
    while True:
        try:
            return parse_date(input(f"{label} [required; format YYYY-MM-DD; example: 2026-05-24]: ")).isoformat()
        except ValueError as exc:
            _error(exc, "Use a real date in YYYY-MM-DD format.")


def _prompt_sample_volume() -> str:
    """Prompt for a positive sample volume in millilitres."""
    while True:
        value = input("Volume [required; mL; example: 2.5]: ").strip()
        try:
            volume = float(value)
        except ValueError:
            _error(ValueError("Volume must be a number in mL"), "Example: 2.5.")
            continue
        if not math.isfinite(volume) or volume <= 0:
            _error(ValueError("Volume must be greater than 0 mL"), "Example: 2.5.")
            continue
        return value


def _prompt_choice(
    label: str,
    options: list[str],
    default: str | None = None,
) -> str:
    """Prompt for one of the displayed options, optionally with a default."""
    _print_choices(f"Allowed {label.lower()} values", options)
    default_hint = f" [default: {default}; Enter = {default}]" if default else " [required]"
    while True:
        value = input(f"{label}{default_hint}: ").strip()
        if not value and default is not None:
            return default
        if value in options:
            return value
        _warning(f"Choose one of: {', '.join(options)}.")


def _get_sample_types() -> list[str]:
    try:
        payload = api.list_sample_types()
        if isinstance(payload, dict):
            payload = payload.get("items", []) if isinstance(payload.get("items"), list) else []
        return [str(item.get("type_name", "")).strip() for item in payload if item.get("type_name")]
    except Exception as exc:
        _error(exc, "Check Administration > List sample types or the server connection.")
        return []


def _get_container_codes() -> list[str]:
    try:
        payload = api.list_containers()
        if isinstance(payload, dict):
            payload = payload.get("items", []) if isinstance(payload.get("items"), list) else []
        return [str(item.get("code", "")).strip() for item in payload if item.get("code")]
    except Exception as exc:
        _error(exc, "Check Administration > List containers or the server connection.")
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
            "active": "Active" if item.get("active") else "Inactive",
            "test": item.get("test", ""),
            "registration_date": item.get("registration_date", ""),
            "last_update": item.get("last_update", ""),
        } for item in payload]
        _print_rows("Patients", rows, ["id", "code", "name", "birth_date", "active", "test", "registration_date", "last_update"])
    except Exception as exc:
        _error(exc)


def create_patient() -> None:
    """Create a patient via the API."""
    try:
        _info("Create a patient. You will enter a unique code, identity details, birth date and activity.")
        code = _prompt_required("Patient code", "PAT-001")
        name = _prompt_required("Name", "Ada")
        lastname = _prompt_required("Lastname", "Lovelace")
        birth_date = _prompt_date("Birth date")
        test = input("Clinical test / note [Routine checkup]: ").strip() or "Routine checkup"
        answer = input("Active patient? [Y/n]: ").strip().lower()
        active = answer not in {"n", "no"}
        response = api.create_patient({
            "code": code,
            "name": name,
            "lastname": lastname,
            "birth_date": birth_date,
            "test": test,
            "active": active,
        })
        _success(f"Patient created: {response.get('code', 'record') if isinstance(response, dict) else response}.")
    except Exception as exc:
        _error(exc)


def search_patient() -> None:
    """Search a patient by code."""
    code = input("Patient code: ").strip()
    if not code:
        _error(ValueError("Patient code is required"), "See Patients > List patients for valid codes.")
        return
    try:
        patient = api.get_patient(code)
        _print_rows("Patient", [patient], ["id", "code", "name", "lastname", "birth_date", "active", "test", "registration_date", "last_update"])
    except Exception as exc:
        _error(exc)


def view_patient_samples() -> None:
    code = input("Patient code: ").strip()
    if not code:
        _error(ValueError("Patient code is required"), "See Patients > List patients for valid codes.")
        return
    try:
        samples = api.list_patient_samples(code)
        rows = [{
            "code": item.get("code", ""),
            "volume": f"{item.get('volume', '')} mL",
            "status": item.get("status", ""),
            "extraction_date": item.get("extraction_date", ""),
        } for item in samples]
        _print_rows(f"Samples for patient {code}", rows, ["code", "volume", "status", "extraction_date"])
    except Exception as exc:
        _error(exc)


def list_samples() -> None:
    """List sample records."""
    try:
        payload = api.list_samples()
        rows = [{
            "id": item.get("id", ""),
            "code": item.get("code", ""),
            "patient_code": item.get("patient_code", ""),
            "volume": f"{item.get('volume', '')} mL",
            "status": item.get("status", ""),
            "sample_type": item.get("sample_type", ""),
            "container_code": item.get("container_code", ""),
            "extraction_date": item.get("extraction_date", ""),
            "last_update": item.get("last_update", ""),
        } for item in payload]
        _print_rows("Samples", rows, ["id", "code", "patient_code", "volume", "status", "sample_type", "container_code", "extraction_date", "last_update"])
    except Exception as exc:
        _error(exc)


def create_sample() -> None:
    """Create a sample via the API."""
    try:
        _info("Create a sample. You will enter a patient code, type, container, volume in mL, status and extraction date.")
        patient_code = _prompt_required("Patient code", "PAT-001")
        try:
            api.get_patient(patient_code)
        except Exception as exc:
            _error(exc, "Check the patient code; see Patients > List patients.")
            return
        sample_types = _get_sample_types()
        container_codes = _get_container_codes()
        if sample_types:
            _print_choices("Available sample types", sample_types)
        else:
            _info(
                "Sample types could not be listed. Enter an existing type, "
                "or create one in Administration > Create sample type."
            )
        if container_codes:
            _print_choices("Available container codes", container_codes)
        else:
            _info(
                "Containers could not be listed. Enter an existing code, "
                "or create one in Administration > Create container."
            )

        sample_type = _prompt_choice("Sample type", sample_types) if sample_types else _prompt_required("Sample type", "Plasma")
        container_code = _prompt_choice("Container code", container_codes) if container_codes else _prompt_required("Container code", "C-001")
        code = _prompt_required("Sample code", "SMP-001")
        volume = _prompt_sample_volume()
        status_options = ["pending", "in_process", "analyzed", "rejected", "archived"]
        status = _prompt_choice("Status", status_options, default="pending")
        extraction_date = _prompt_date("Extraction date")

        response = api.create_sample({
            "code": code,
            "volume": float(volume),
            "extraction_date": extraction_date,
            "patient_code": patient_code,
            "sample_type": sample_type,
            "container_code": container_code,
            "status": status,
        })
        _success(f"Sample created: {response.get('code', 'record') if isinstance(response, dict) else response}.")
    except Exception as exc:
        _error(exc)


def list_staff() -> None:
    """List staff."""
    try:
        payload = api.list_staff()
        rows = [{
            "id": item.get("id", ""),
            "code": item.get("code", ""),
            "name": f"{item.get('name', '')} {item.get('lastname', '')}".strip(),
            "role": str(item.get("role", "")).replace("_", " ").upper(),
            "last_update": item.get("last_update", ""),
        } for item in payload]
        _print_rows("Staff", rows, ["id", "code", "name", "role", "last_update"])
    except Exception as exc:
        _error(exc)


def create_staff() -> None:
    """Create staff member."""
    try:
        _info("Create staff. Allowed roles: researcher, analyst, technician, manager, administrator.")
        code = _prompt_required("Staff code", "STF-001")
        name = _prompt_required("Name", "Ada")
        lastname = _prompt_required("Lastname", "Lovelace")
        role_options = [
            "researcher", "analyst", "technician", "manager", "administrator",
        ]
        role = _prompt_choice("Role", role_options)
        response = api.create_staff({
            "code": code,
            "name": name,
            "lastname": lastname,
            "role": role,
            "active": active,
        })
        _success(f"Staff member created: {response.get('code', 'record') if isinstance(response, dict) else response}.")
    except Exception as exc:
        _error(exc)


def list_projects() -> None:
    """List projects."""
    try:
        payload = api.list_projects()
        rows = [{
            "id": item.get("id", ""),
            "project_name": item.get("project_name", ""),
            "start_date": item.get("start_date", ""),
            "description": (item.get("description", "") or "")[:50],
            "last_update": item.get("last_update", ""),
        } for item in payload]
        _print_rows("Research Projects", rows, ["id", "project_name", "start_date", "description", "last_update"])
    except Exception as exc:
        _error(exc)


def create_project() -> None:
    """Create a project."""
    try:
        project_name = _prompt_required("Project name", "Cancer research study")
        start_date = _prompt_date("Start date")
        description = input("Description (optional): ").strip()
        response = api.create_project({
            "project_name": project_name,
            "start_date": start_date,
            "description": description or None,
        })
        _success(f"Project created: {response.get('id', 'record') if isinstance(response, dict) else response}.")
    except Exception as exc:
        _error(exc)


def list_protocols() -> None:
    """List protocols."""
    try:
        payload = api.list_protocols()
        rows = [{
            "id": item.get("id", ""),
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "reviewed_by": item.get("reviewed_by") or "UNREVIEWED",
            "description": (item.get("description", "") or "")[:40],
            "last_update": item.get("last_update", ""),
        } for item in payload]
        _print_rows("Protocols", rows, ["id", "code", "name", "reviewed_by", "description", "last_update"])
    except Exception as exc:
        _error(exc)


def create_protocol() -> None:
    """Create a protocol."""
    try:
        code = _prompt_required("Protocol code", "PRT-001")
        name = _prompt_required("Protocol name", "DNA extraction")
        description = input("Description (optional): ").strip()
        reviewer = input("Reviewer staff code (optional, e.g. STF-001): ").strip() or None
        payload = {"code": code, "name": name, "description": description or None}
        if reviewer:
            payload["reviewed_by"] = reviewer
        response = api.create_protocol(payload)
        _success(f"Protocol created: {response.get('code', 'record') if isinstance(response, dict) else response}.")
    except Exception as exc:
        _error(exc)


def list_containers() -> None:
    """List containers."""
    try:
        payload = api.list_containers()
        rows = [{"id": item.get("id", ""), "code": item.get("code", ""), "type_name": item.get("type_name", ""), "last_update": item.get("last_update", "")} for item in payload]
        _print_rows("Containers", rows, ["id", "code", "type_name", "last_update"])
    except Exception as exc:
        _error(exc)


def create_container() -> None:
    try:
        _info("Create a container. Use a unique code, for example C-001.")
        code = _prompt_required("Container code", "C-001")
        type_name = _prompt_required("Container type_name", "Freezer -80 C")
        response = api.create_container({"code": code, "type_name": type_name})
        _success(f"Container created: {response.get('code', 'record') if isinstance(response, dict) else response}.")
    except Exception as exc:
        _error(exc)


def manage_container() -> None:
    code = _prompt_required("Container code")
    try:
        _print_detail(f"Container {code}", api.get_container(code))
        if _confirm_delete(f"container {code}"):
            api.delete_container(code)
            _success(f"Container {code} deleted.")
    except Exception as exc:
        _error(exc)


def list_sample_types() -> None:
    try:
        payload = api.list_sample_types()
        rows = [{"id": item.get("id", ""), "type_name": item.get("type_name", ""), "last_update": item.get("last_update", "")} for item in payload]
        _print_rows("Sample types", rows, ["id", "type_name", "last_update"])
    except Exception as exc:
        _error(exc)


def create_sample_type() -> None:
    try:
        existing = _get_sample_types()
        if existing:
            _print_choices("Current sample types", existing)
        _info("Examples of sample types: plasma, serum, tissue, DNA.")
        type_name = _prompt_required("Sample type name", "Plasma")
        response = api.create_sample_type({"type_name": type_name})
        _success(f"Sample type created: {response.get('type_name', 'record') if isinstance(response, dict) else response}.")
    except Exception as exc:
        _error(exc)


def manage_sample_type() -> None:
    type_name = _prompt_required("Sample type name")
    try:
        _print_detail(f"Sample type {type_name}", api.get_sample_type(type_name))
        if _confirm_delete(f"sample type {type_name}"):
            api.delete_sample_type(type_name)
            _success(f"Sample type {type_name} deleted.")
    except Exception as exc:
        _error(exc)


def _confirm_delete(label: str) -> bool:
    confirmed = _prompt_bool(f"Delete {label}? This action may remove associated records")
    if not confirmed:
        _warning("Cancelled. No changes were made.")
    return confirmed


def update_patient() -> None:
    code = _prompt_required("Patient code")
    try:
        current = api.get_patient(code)
        payload = {
            "name": input(f"Name [{current.get('name', '')}]: ").strip() or current.get("name"),
            "lastname": input(f"Lastname [{current.get('lastname', '')}]: ").strip() or current.get("lastname"),
            "birth_date": _prompt_date("Birth date"),
            "test": input(f"Test [{current.get('test', '')}]: ").strip() or current.get("test"),
            "active": _prompt_bool("Active?"),
        }
        api.update_patient(code, payload)
        _success(f"Patient {code} updated.")
    except Exception as exc:
        _error(exc)


def delete_patient() -> None:
    code = _prompt_required("Patient code")
    try:
        samples = api.list_patient_samples(code)
        if samples:
            _warning(f"Patient {code} cannot be deleted because {len(samples)} sample(s) are associated.")
        elif _confirm_delete(f"patient {code}"):
            api.delete_patient(code)
            _success(f"Patient {code} deleted.")
    except Exception as exc:
        _error(exc)


def update_sample() -> None:
    code = _prompt_required("Sample code")
    try:
        api.update_sample(code, {
            "volume": float(_prompt_sample_volume()),
            "status": _prompt_choice("Status", ["pending", "in_process", "analyzed", "rejected", "archived"]),
            "extraction_date": _prompt_date("Extraction date"),
        })
        _success(f"Sample {code} updated.")
    except Exception as exc:
        _error(exc)


def delete_sample() -> None:
    code = _prompt_required("Sample code")
    if _confirm_delete(f"sample {code}"):
        try:
            api.delete_sample(code)
            _success(f"Sample {code} deleted.")
        except Exception as exc:
            _error(exc)


def search_sample() -> None:
    try:
        code = _prompt_required("Sample code", "SMP-001; see Samples > List samples")
        _print_detail(f"Sample {code}", api.get_sample(code))
    except Exception as exc:
        _error(exc)


def view_full_sample() -> None:
    try:
        code = _prompt_required("Sample code", "SMP-001; see Samples > List samples")
        _print_detail(f"Full sample {code}", api.get_full_sample(code))
    except Exception as exc:
        _error(exc)


def filter_samples_status() -> None:
    try:
        payload = api.list_samples(_prompt_choice("Status", ["pending", "in_process", "analyzed", "rejected", "archived"]))
        _print_rows("Samples", payload, ["code", "patient_code", "status", "extraction_date", "last_update"])
    except Exception as exc:
        _error(exc)


def filter_samples_date() -> None:
    try:
        payload = api.list_samples_by_date(_prompt_date("Start date"), _prompt_date("End date"))
        _print_rows("Samples", payload, ["code", "patient_code", "status", "extraction_date", "last_update"])
    except Exception as exc:
        _error(exc)


def manage_quality_control() -> None:
    code = _prompt_required("Sample code")
    try:
        qc = api.get_quality_control(code)
        _print_detail(f"Quality control for sample {code}", qc)
        choice = _prompt_choice("Action", ["edit", "delete", "back"])
        if choice == "edit":
            api.set_quality_control(code, {"result": _prompt_choice("Result", ["approved", "rejected", "pending_review"]), "purity": input("Purity [optional; %; Enter = not set]: ").strip() or None, "concentration": input("Concentration [optional; ng/uL; Enter = not set]: ").strip() or None})
            _success(f"Quality control for sample {code} saved.")
        elif choice == "delete" and _confirm_delete("quality control"):
            api.delete_quality_control(code)
            _success(f"Quality control for sample {code} deleted.")
    except Exception:
        if _prompt_bool("No QC exists. Create it?"):
            try:
                api.set_quality_control(code, {"result": _prompt_choice("Result", ["approved", "rejected", "pending_review"]), "purity": input("Purity [optional; %; Enter = not set]: ").strip() or None, "concentration": input("Concentration [optional; ng/uL; Enter = not set]: ").strip() or None})
                _success(f"Quality control for sample {code} saved.")
            except Exception as exc:
                _error(exc)


def update_staff() -> None:
    code = _prompt_required("Staff code")
    try:
        api.update_staff(code, {"name": _prompt_required("Name"), "lastname": _prompt_required("Lastname"), "role": _prompt_choice("Role", ["researcher", "analyst", "technician", "manager", "administrator"])})
        _success(f"Staff member {code} updated.")
    except Exception as exc:
        _error(exc)


def delete_staff() -> None:
    code = _prompt_required("Staff code")
    if _confirm_delete(f"staff {code}"):
        try:
            api.delete_staff(code)
            _success(f"Staff member {code} deleted.")
        except Exception as exc:
            _error(exc)


def search_staff() -> None:
    try:
        code = _prompt_required("Staff code", "STF-001; see Staff > List staff")
        _print_detail(f"Staff member {code}", api.get_staff(code))
    except Exception as exc:
        _error(exc)


def assign_staff() -> None:
    try:
        project_id = int(input("Project ID: "))
        staff_code = _prompt_required("Staff code", "STF-001; see Staff > List staff")
        api.add_team_member(project_id, staff_code, _prompt_choice("Team role", ["principal_investigator", "co_investigator", "analyst", "technician", "assistant"]))
        _success(f"Staff member {staff_code} assigned to project {project_id}.")
    except Exception as exc:
        _error(exc)


def view_staff_assignments() -> None:
    try:
        code = _prompt_required("Staff code")
        _print_rows("Assignments", api.list_staff_assignments(code), ["project_id", "project_name", "role"])
    except Exception as exc:
        _error(exc)


def view_staff_protocols() -> None:
    try:
        code = _prompt_required("Staff code")
        _print_rows("Reviewed protocols", api.list_staff_protocols(code), ["code", "name", "reviewed_by"])
    except Exception as exc:
        _error(exc)


def update_project() -> None:
    try:
        project_id = int(input("Project ID [required; see Research Projects > List projects]: "))
        api.update_project(project_id, {"project_name": _prompt_required("Project name"), "start_date": _prompt_date("Start date"), "description": input("Description [optional; Enter = empty]: ").strip() or None})
        _success(f"Project {project_id} updated.")
    except Exception as exc:
        _error(exc)


def delete_project() -> None:
    try:
        project_id = int(input("Project ID: "))
        if _confirm_delete(f"project {project_id}"):
            api.delete_project(project_id)
            _success(f"Project {project_id} deleted.")
    except Exception as exc:
        _error(exc)


def search_project() -> None:
    try:
        _print_rows("Projects", api.list_projects(_prompt_required("Project name or keyword", "Cancer")), ["id", "project_name", "start_date", "description"])
    except Exception as exc:
        _error(exc)


def link_sample() -> None:
    try:
        project_id = int(input("Project ID [required; see Research Projects > List projects]: "))
        sample_code = _prompt_required("Sample code", "SMP-001; see Samples > List samples")
        api.link_sample_to_project(project_id, sample_code)
        _success(f"Sample {sample_code} linked to project {project_id}.")
    except Exception as exc:
        _error(exc)


def manage_project_relations() -> None:
    try:
        project_id = int(input("Project ID [required; see Research Projects > List projects]: "))
        _print_rows("Project samples", api.list_project_samples(project_id), ["sample_code", "sample_assignment_date"])
        _print_rows("Project team", api.list_project_team(project_id), ["staff_code", "name", "role"])
    except Exception as exc:
        _error(exc)


def view_project_details() -> None:
    try:
        project_id = int(input("Project ID [required; see Research Projects > List projects]: "))
        _print_detail(f"Project {project_id} details", api.get_project_details(project_id))
    except Exception as exc:
        _error(exc)


def update_protocol() -> None:
    code = _prompt_required("Protocol code")
    try:
        api.update_protocol(code, {"name": _prompt_required("Protocol name", "DNA extraction"), "description": input("Description [optional; Enter = empty]: ").strip() or None, "reviewed_by": input("Reviewer staff code [optional; blank clears; see Staff > List staff]: ").strip() or None})
        _success(f"Protocol {code} updated.")
    except Exception as exc:
        _error(exc)


def delete_protocol() -> None:
    code = _prompt_required("Protocol code")
    if _confirm_delete(f"protocol {code}"):
        try:
            api.delete_protocol(code)
            _success(f"Protocol {code} deleted.")
        except Exception as exc:
            _error(exc)


def search_protocol() -> None:
    try:
        _print_rows("Protocols", api.list_protocols(_prompt_required("Keyword", "DNA")), ["code", "name", "reviewed_by", "description"])
    except Exception as exc:
        _error(exc)


def apply_protocol() -> None:
    try:
        sample_code = _prompt_required("Sample code", "SMP-001; see Samples > List samples")
        protocol_code = _prompt_required("Protocol code", "PRT-001; see Protocols > List protocols")
        api.apply_protocol_to_sample(sample_code, protocol_code)
        _success(f"Protocol {protocol_code} applied to sample {sample_code}.")
    except Exception as exc:
        _error(exc)


def remove_protocol() -> None:
    try:
        sample_code = _prompt_required("Sample code", "SMP-001; see Samples > List samples")
        protocol_code = _prompt_required("Protocol code", "PRT-001; see Protocols > List protocols")
        api.remove_protocol_from_sample(sample_code, protocol_code)
        _success(f"Protocol {protocol_code} removed from sample {sample_code}.")
    except Exception as exc:
        _error(exc)


def view_protocol_details() -> None:
    try:
        code = _prompt_required("Protocol code", "PRT-001; see Protocols > List protocols")
        _print_rows("Applied samples", api.list_protocol_samples(code), ["code", "status", "extraction_date", "patient_code"])
    except Exception as exc:
        _error(exc)


def patient_menu() -> None:
    while True:
        clear_screen()
        _menu("Patients", "Patients", [
            ("1", "List patients", "view all patient records"),
            ("2", "Add patient", "create a new patient"),
            ("3", "Update patient details", "change an existing patient"),
            ("4", "Delete patient", "remove a patient"),
            ("5", "Search patient", "look up by patient code"),
            ("6", "List active patients", "show only active patients"),
            ("7", "View patient samples", "find samples by patient code"),
            ("0", "Back to Main menu", ""),
        ])
        choice = _menu_choice(7)
        actions = {"1": list_patients, "2": create_patient, "3": update_patient, "4": delete_patient, "5": search_patient, "6": lambda: list_patients(True), "7": view_patient_samples}
        if choice == "0":
            return
        if choice in actions:
            _run_action(f"Patients > {choice}", getattr(actions[choice], "__name__", "Selected action").replace("_", " ").title(), actions[choice])
            press_any_key()
        else:
            _warning("Invalid option. Choose a number from 0 to 7.")


def sample_menu() -> None:
    while True:
        clear_screen()
        _menu("Samples", "Samples", [
            ("1", "List samples", "view all sample records"),
            ("2", "Add sample", "create a sample; asks for patient, type, container, volume and status"),
            ("3", "Update sample", "change an existing sample"),
            ("4", "Delete sample", "remove a sample"),
            ("5", "Search sample", "look up by sample code"),
            ("6", "View full sample", "show related QC, protocols and projects"),
            ("7", "Filter by status", "view samples with one status"),
            ("8", "Filter by extraction date", "view samples in a date range"),
            ("9", "Manage quality control", "view, edit or delete QC"),
            ("10", "Apply protocol", "link a protocol to a sample"),
            ("0", "Back to Main menu", ""),
        ])
        choice = _menu_choice(10)
        actions = {"1": list_samples, "2": create_sample, "3": update_sample, "4": delete_sample, "5": search_sample, "6": view_full_sample, "7": filter_samples_status, "8": filter_samples_date, "9": manage_quality_control, "10": apply_protocol}
        if choice == "0":
            return
        if choice in actions:
            _run_action(f"Samples > {choice}", getattr(actions[choice], "__name__", "Selected action").replace("_", " ").title(), actions[choice])
            press_any_key()
        else:
            _warning("Invalid option. Choose a number from 0 to 10.")


def staff_menu() -> None:
    while True:
        clear_screen()
        _menu("Staff", "Staff", [
            ("1", "List staff", "view staff records"),
            ("2", "Add staff member", "create a staff record"),
            ("3", "Update staff details", "change an existing staff record"),
            ("4", "Delete staff member", "remove a staff record"),
            ("5", "Search staff member", "look up by staff code"),
            ("6", "Assign staff to project", "requires project ID and staff code"),
            ("7", "View project assignments", "find projects for a staff code"),
            ("8", "View reviewed protocols", "find protocols reviewed by staff"),
            ("0", "Back to Main menu", ""),
        ])
        choice = _menu_choice(8)
        actions = {"1": list_staff, "2": create_staff, "3": update_staff, "4": delete_staff, "5": search_staff, "6": assign_staff, "7": view_staff_assignments, "8": view_staff_protocols}
        if choice == "0":
            return
        if choice in actions:
            _run_action(f"Staff > {choice}", getattr(actions[choice], "__name__", "Selected action").replace("_", " ").title(), actions[choice])
            press_any_key()
        else:
            _warning("Invalid option. Choose a number from 0 to 8.")


def project_menu() -> None:
    while True:
        clear_screen()
        _menu("Research Projects", "Research Projects", [
            ("1", "List projects", "view project records"),
            ("2", "Add project", "create a research project"),
            ("3", "Update project details", "change an existing project"),
            ("4", "Delete project", "remove a project"),
            ("5", "Search project", "look up by project name"),
            ("6", "Link sample to project", "requires project ID and sample code"),
            ("7", "View project details", "show team and linked samples"),
            ("8", "View project relations", "show samples and team"),
            ("0", "Back to Main menu", ""),
        ])
        choice = _menu_choice(8)
        actions = {"1": list_projects, "2": create_project, "3": update_project, "4": delete_project, "5": search_project, "6": link_sample, "7": view_project_details, "8": manage_project_relations}
        if choice == "0":
            return
        if choice in actions:
            _run_action(f"Research Projects > {choice}", getattr(actions[choice], "__name__", "Selected action").replace("_", " ").title(), actions[choice])
            press_any_key()
        else:
            _warning("Invalid option. Choose a number from 0 to 8.")


def protocol_menu() -> None:
    while True:
        clear_screen()
        _menu("Protocols", "Protocols", [
            ("1", "List protocols", "view protocol records"),
            ("2", "Add protocol", "create a protocol"),
            ("3", "Update protocol details", "change an existing protocol"),
            ("4", "Delete protocol", "remove a protocol"),
            ("5", "Search protocol", "look up by keyword"),
            ("6", "Apply protocol to sample", "requires sample and protocol codes"),
            ("7", "View protocol samples", "show samples using a protocol"),
            ("8", "Remove protocol from sample", "unlink a relationship"),
            ("0", "Back to Main menu", ""),
        ])
        choice = _menu_choice(8)
        actions = {"1": list_protocols, "2": create_protocol, "3": update_protocol, "4": delete_protocol, "5": search_protocol, "6": apply_protocol, "7": view_protocol_details, "8": remove_protocol}
        if choice == "0":
            return
        if choice in actions:
            _run_action(f"Protocols > {choice}", getattr(actions[choice], "__name__", "Selected action").replace("_", " ").title(), actions[choice])
            press_any_key()
        else:
            _warning("Invalid option. Choose a number from 0 to 8.")


def admin_menu() -> None:
    while True:
        _menu("Administration", "Administration", [
            ("1", "List containers", "view storage containers"),
            ("2", "Create container", "create a storage container"),
            ("3", "List sample types", "view sample types"),
            ("4", "Create sample type", "create a sample type"),
            ("5", "Manage container", "view or delete a container"),
            ("6", "Manage sample type", "view or delete a sample type"),
            ("0", "Back to Main menu", ""),
        ])
        choice = _menu_choice(6)
        if choice == "1":
            _run_action("Administration > Containers", "List containers", list_containers)
        elif choice == "2":
            _run_action("Administration > Containers", "Create container", create_container)
        elif choice == "3":
            _run_action("Administration > Sample types", "List sample types", list_sample_types)
        elif choice == "4":
            _run_action("Administration > Sample types", "Create sample type", create_sample_type)
        elif choice == "5":
            _run_action("Administration > Containers", "Manage container", manage_container)
        elif choice == "6":
            _run_action("Administration > Sample types", "Manage sample type", manage_sample_type)
        elif choice == "0":
            return
        else:
            _warning("Invalid option. Choose a number from 0 to 6.")
        press_any_key()


def main() -> None:
    """Start the client terminal application."""
    show_banner()
    _info("Enter the number shown for an action. Enter 0 to exit or return.")
    try:
        response = api.ping()
        _success("Server connection is available.")
    except Exception as exc:  # pragma: no cover - network errors are handled at runtime
        _error(exc, "Check that the BioTrack server is running and the host/port settings are correct.")

    while True:
        _menu("Main menu", "Main menu", [
            ("1", "Patients", "manage patient records"),
            ("2", "Samples", "manage samples and quality control"),
            ("3", "Staff", "manage staff and assignments"),
            ("4", "Research Projects", "manage projects and relationships"),
            ("5", "Protocols", "manage protocols and links"),
            ("6", "Administration", "manage containers and sample types"),
            ("0", "Exit", ""),
        ])
        choice = _menu_choice(6)
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
            _info("Goodbye.")
            break
        else:
            _warning("Invalid option. Choose a number from 0 to 6.")


if __name__ == "__main__":
    main()
    sys.exit(0)
