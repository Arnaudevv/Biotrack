# =============================================================================
# BIOTRACK BACK OFFICE TERMINAL SYSTEM (CLI)
# =============================================================================
# This application represents the UI layer for the BioTrack clinical system.
# It uses the Repository Pattern and Unit of Work (UoW) to access persistence
# while demonstrating 1:1, 1:N, N:M, and N:M with attributes relationships.
#
# Requirements:
# - Run 'pip install rich' before launching (required for visual UI formatting)
# =============================================================================

import os
import sys
from datetime import datetime, date
from decimal import Decimal

# Import Rich components for a stunning professional terminal UI
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
    from rich.align import Align
    from rich import box
except ImportError:
    print("\n[!] Error: The 'rich' library is required to run this application.")
    print("Please install it manually by running:")
    print("    pip install rich\n")
    sys.exit(1)

# Import internal domain modules
from src.domain.config import DB_URL
from src.domain.repositories.unit_of_work import UnitOfWorkFactory
from src.domain.repositories.patient_repository import PatientRepository
from src.domain.repositories.staff_repository import StaffRepository
from src.domain.repositories.research_project_repository import ResearchProjectRepository
from src.domain.repositories.sample_repository import SampleRepository
from src.domain.repositories.protocol_repository import ProtocolRepository
from src.domain.repositories.quality_control_repository import QualityControlRepository
from src.domain.repositories.base_repository import BaseRepository

from src.domain.models import (
    Patient, Staff, ResearchProject, Sample, Protocol,
    QualityControl, ProjectTeam, ResearchProjectSamples, Container, SampleType
)

# Global rich console helper
console = Console()
uow_factory = UnitOfWorkFactory(DB_URL)


# =============================================================================
# GENERAL UTILITIES
# =============================================================================

def clear_screen():
    """Clears the console screen for a clean, application-like experience."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner(title: str):
    """Displays a stylized header banner on top of submenus."""
    console.print(Panel(
        Align.center(f"[bold cyan]BIOTRACK CLINICAL SYSTEM[/bold cyan] \n[bold white]❖ {title} ❖[/bold white]"),
        box=box.ROUNDED,
        style="cyan"
    ))
    console.print()


def press_any_key():
    """Prompts the user to continue after an action or error."""
    console.print("\n[dim]Press [bold yellow]Enter[/bold yellow] to return to the menu...[/dim]")
    input()


def parse_date(date_str: str) -> date:
    """Parses date from YYYY-MM-DD string, returning a date object or raising ValueError."""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Must be YYYY-MM-DD.")


# =============================================================================
# 1. PATIENT SUBMENU (Demonstrates 1:N relationship with Samples)
# =============================================================================

def patient_menu():
    while True:
        clear_screen()
        show_banner("Patient Repository Manager")
        console.print("[1] 🗃️  List All Patients")
        console.print("[2] ➕ Add New Patient")
        console.print("[3] ✏️  Update Patient Details")
        console.print("[4] ❌ Delete Patient")
        console.print("[5] 🔍 Search Patient by Code")
        console.print("[6] 🟢 View Active Patients Only [dim](Custom Query)[/dim]")
        console.print("[7] 🧪 View Patient's Samples [dim](1:N Relationship)[/dim]")
        console.print("[0] 🔙 Back to Main Menu")
        console.print()

        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "7", "0"])

        if choice == "1":
            list_patients()
        elif choice == "2":
            create_patient()
        elif choice == "3":
            update_patient()
        elif choice == "4":
            delete_patient()
        elif choice == "5":
            search_patient()
        elif choice == "6":
            list_active_patients()
        elif choice == "7":
            view_patient_samples()
        elif choice == "0":
            break


def list_patients(active_only=False):
    clear_screen()
    show_banner("Patients List")
    
    with uow_factory.create() as uow:
        repo = PatientRepository(uow.session)
        patients = repo.get_active() if active_only else repo.get_all()
        
        if not patients:
            console.print("[bold yellow]No patients found in the database.[/bold yellow]")
            press_any_key()
            return
        
        table = Table(box=box.DOUBLE_EDGE, header_style="bold magenta")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Code", style="cyan bold")
        table.add_column("Full Name", style="white")
        table.add_column("Birth Date", style="green")
        table.add_column("Active", justify="center")
        table.add_column("Test Info", style="yellow")
        table.add_column("Last Update", style="dim")
        
        for p in patients:
            active_str = "🟢 Yes" if p.active else "🔴 No"
            table.add_row(
                str(p.id),
                p.code,
                f"{p.name} {p.lastname}",
                p.birth_date.strftime("%Y-%m-%d"),
                active_str,
                p.test,
                p.last_update.strftime("%Y-%m-%d %H:%M") if p.last_update else "N/A"
            )
            
        console.print(table)
    press_any_key()


def create_patient():
    clear_screen()
    show_banner("Create Patient")
    
    code = Prompt.ask("[bold white]Patient Unique Code[/bold white] (e.g. PAT-001)")
    name = Prompt.ask("[bold white]First Name[/bold white]")
    lastname = Prompt.ask("[bold white]Last Name[/bold white]")
    
    birth_str = Prompt.ask("[bold white]Birth Date[/bold white] (YYYY-MM-DD)")
    try:
        birth_date = parse_date(birth_str)
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        press_any_key()
        return

    test = Prompt.ask("[bold white]Test / Clinical Note[/bold white]", default="Routine checkup")
    active = Confirm.ask("[bold white]Is Patient Active?[/bold white]", default=True)

    with uow_factory.create() as uow:
        repo = PatientRepository(uow.session)
        
        # Check uniqueness
        if repo.get_by_code(code):
            console.print(f"[bold red]Error: A patient with code '{code}' already exists.[/bold red]")
            press_any_key()
            return
            
        new_patient = Patient(
            code=code,
            name=name,
            lastname=lastname,
            birth_date=birth_date,
            active=active,
            test=test
        )
        repo.save(new_patient)
        console.print(f"\n[bold green]Success: Patient '{name} {lastname}' created successfully![/bold green]")
    press_any_key()


def update_patient():
    clear_screen()
    show_banner("Update Patient")
    
    code = Prompt.ask("[bold white]Enter Code of the Patient to update[/bold white]")
    
    with uow_factory.create() as uow:
        repo = PatientRepository(uow.session)
        patient = repo.get_by_code(code)
        
        if not patient:
            console.print(f"[bold red]Error: Patient with code '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        console.print(f"\nEditing: [cyan]{patient.name} {patient.lastname}[/cyan] (Current test: {patient.test})\n")
        
        new_name = Prompt.ask("New First Name (Leave empty to keep current)", default=patient.name)
        new_lastname = Prompt.ask("New Last Name (Leave empty to keep current)", default=patient.lastname)
        
        birth_str = Prompt.ask("New Birth Date (YYYY-MM-DD, Leave empty to keep current)", default=patient.birth_date.strftime("%Y-%m-%d"))
        try:
            new_birth = parse_date(birth_str)
        except ValueError as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            press_any_key()
            return

        new_test = Prompt.ask("New Test / Clinical Note", default=patient.test)
        new_active = Confirm.ask("Is Patient Active?", default=patient.active)

        patient.name = new_name
        patient.lastname = new_lastname
        patient.birth_date = new_birth
        patient.test = new_test
        patient.active = new_active
        
        repo.save(patient)
        console.print(f"\n[bold green]Success: Patient '{code}' updated successfully![/bold green]")
    press_any_key()


def delete_patient():
    clear_screen()
    show_banner("Delete Patient")
    
    code = Prompt.ask("[bold red]Enter Code of the Patient to delete[/bold red]")
    
    with uow_factory.create() as uow:
        repo = PatientRepository(uow.session)
        patient = repo.get_by_code(code)
        
        if not patient:
            console.print(f"[bold red]Error: Patient with code '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        confirm = Confirm.ask(f"[bold red]Are you sure you want to permanently delete {patient.name} {patient.lastname}?[/bold red]")
        if confirm:
            repo.delete(patient)
            console.print(f"[bold green]Success: Patient '{code}' deleted successfully![/bold green]")
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            
    press_any_key()


def search_patient():
    clear_screen()
    show_banner("Search Patient")
    
    code = Prompt.ask("[bold white]Enter unique Patient Code[/bold white]")
    
    with uow_factory.create() as uow:
        repo = PatientRepository(uow.session)
        patient = repo.get_by_code(code)
        
        if not patient:
            console.print(f"[bold red]Patient with code '{code}' not found.[/bold red]")
        else:
            console.print(Panel(
                f"[bold cyan]Patient ID:[/bold cyan] {patient.id}\n"
                f"[bold cyan]Code:[/bold cyan] {patient.code}\n"
                f"[bold cyan]Name:[/bold cyan] {patient.name} {patient.lastname}\n"
                f"[bold cyan]Birth Date:[/bold cyan] {patient.birth_date}\n"
                f"[bold cyan]Active Status:[/bold cyan] {'🟢 Active' if patient.active else '🔴 Inactive'}\n"
                f"[bold cyan]Test Note:[/bold cyan] {patient.test}\n"
                f"[bold cyan]Registration Date:[/bold cyan] {patient.registration_date}",
                title=f"Details for {patient.code}",
                expand=False
            ))
    press_any_key()


def list_active_patients():
    list_patients(active_only=True)


def view_patient_samples():
    """Displays samples belonging to a patient (demonstrates 1:N relationship)."""
    clear_screen()
    show_banner("View Patient's Samples (1:N)")
    
    code = Prompt.ask("[bold white]Enter unique Patient Code[/bold white]")
    
    with uow_factory.create() as uow:
        repo = PatientRepository(uow.session)
        patient = repo.get_with_samples(code)  # Eager loading 1:N relationship
        
        if not patient:
            console.print(f"[bold red]Error: Patient '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        console.print(f"[bold cyan]Patient:[/bold cyan] {patient.name} {patient.lastname} [dim]({patient.code})[/dim]")
        
        if not patient.samples:
            console.print(f"[bold yellow]This patient does not have any samples registered.[/bold yellow]")
        else:
            table = Table(box=box.MINIMAL_DOUBLE_HEAD, header_style="bold green")
            table.add_column("Sample Code", style="bold cyan")
            table.add_column("Volume (mL)", style="white")
            table.add_column("Status", style="yellow")
            table.add_column("Extraction Date", style="green")
            
            for s in patient.samples:
                table.add_row(
                    s.code,
                    f"{s.volume:.2f}",
                    s.status.upper(),
                    s.extraction_date.strftime("%Y-%m-%d")
                )
            console.print(table)
            
    press_any_key()


# =============================================================================
# 2. SAMPLE SUBMENU (1:1 QC, N:M Protocols, N:M with attributes Projects)
# =============================================================================

def sample_menu():
    while True:
        clear_screen()
        show_banner("Sample Repository Manager")
        console.print("[1] 🧪 List All Samples")
        console.print("[2] ➕ Add New Sample [dim](1:N Patient assignment)[/dim]")
        console.print("[3] ✏️  Update Sample Details")
        console.print("[4] ❌ Delete Sample")
        console.print("[5] 🔍 Search Sample by Code")
        console.print("[6] 🩺 View FULL Sample Details [dim](Eager Load 1:1 QC, N:M, N:M-Attr)[/dim]")
        console.print("[7] 🎚️  Filter Samples by Status [dim](Custom Query)[/dim]")
        console.print("[8] 📅 Filter Samples by Extraction Date [dim](Custom Query)[/dim]")
        console.print("[9] 🛡️  Manage Quality Control (1:1 Relation)")
        console.print("[0] 🔙 Back to Main Menu")
        console.print()

        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])

        if choice == "1":
            list_samples()
        elif choice == "2":
            create_sample()
        elif choice == "3":
            update_sample()
        elif choice == "4":
            delete_sample()
        elif choice == "5":
            search_sample()
        elif choice == "6":
            view_full_sample()
        elif choice == "7":
            filter_samples_status()
        elif choice == "8":
            filter_samples_date()
        elif choice == "9":
            manage_quality_control()
        elif choice == "0":
            break


def list_samples(status_filter=None, date_range=None):
    clear_screen()
    show_banner("Samples List")
    
    with uow_factory.create() as uow:
        repo = SampleRepository(uow.session)
        
        if status_filter:
            samples = repo.get_by_status(status_filter)
        elif date_range:
            samples = repo.get_by_extraction_date_range(date_range[0], date_range[1])
        else:
            samples = repo.get_all()
            
        if not samples:
            console.print("[bold yellow]No samples matched the selection criteria.[/bold yellow]")
            press_any_key()
            return
            
        table = Table(box=box.DOUBLE_EDGE, header_style="bold cyan")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Code", style="cyan bold")
        table.add_column("Patient Code", style="white")
        table.add_column("Volume (mL)", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Type", style="green")
        table.add_column("Container", style="yellow")
        table.add_column("Extraction Date", style="green")
        table.add_column("Last Update", style="dim")
        
        for s in samples:
            # Safely fetch related attributes
            patient_code = s.patient.code if s.patient else "N/A"
            type_name = s.sample_type.type_name if s.sample_type else "N/A"
            container_code = s.container.code if s.container else "N/A"
            
            table.add_row(
                str(s.id),
                s.code,
                patient_code,
                f"{s.volume:.2f}",
                s.status.upper(),
                type_name,
                container_code,
                s.extraction_date.strftime("%Y-%m-%d"),
                s.last_update.strftime("%Y-%m-%d %H:%M") if s.last_update else "N/A"
            )
        console.print(table)
    press_any_key()


def create_sample():
    clear_screen()
    show_banner("Create Sample")
    
    with uow_factory.create() as uow:
        patient_repo = PatientRepository(uow.session)
        sample_repo = SampleRepository(uow.session)
        container_repo = BaseRepository(uow.session, Container)
        type_repo = BaseRepository(uow.session, SampleType)
        
        # 1. Select Patient (Shows 1:N selection in UI)
        pat_code = Prompt.ask("[bold white]Associate Patient Code[/bold white]")
        patient = patient_repo.get_by_code(pat_code)
        if not patient:
            console.print(f"[bold red]Error: Patient '{pat_code}' does not exist! Create them first.[/bold red]")
            press_any_key()
            return
            
        # 2. Select Sample Type
        types = type_repo.get_all()
        if not types:
            console.print("[bold red]Error: No Sample Types configured in system. Please configure them first.[/bold red]")
            press_any_key()
            return
        
        console.print("\n[bold cyan]Available Sample Types:[/bold cyan]")
        for t in types:
            console.print(f"  [{t.id}] {t.type_name}")
        type_id = IntPrompt.ask("Select Sample Type ID", choices=[str(t.id) for t in types])
        
        # 3. Select Container
        containers = container_repo.get_all()
        if not containers:
            console.print("[bold red]Error: No Containers configured. Please configure them first.[/bold red]")
            press_any_key()
            return
            
        console.print("\n[bold cyan]Available Containers:[/bold cyan]")
        for c in containers:
            console.print(f"  [{c.id}] {c.code} ({c.type_name})")
        container_id = IntPrompt.ask("Select Container ID", choices=[str(c.id) for c in containers])
        
        # 4. Fill local fields
        code = Prompt.ask("\nSample Unique Code (e.g. SMP-001)")
        if sample_repo.get_by_code(code):
            console.print(f"[bold red]Error: A sample with code '{code}' already exists.[/bold red]")
            press_any_key()
            return
            
        volume = FloatPrompt.ask("Volume (mL)")
        if volume <= 0:
            console.print("[bold red]Error: Volume must be positive.[/bold red]")
            press_any_key()
            return
            
        status = Prompt.ask("Status", choices=['pending','in_process','analyzed','rejected','archived'], default='pending')
        
        ext_date_str = Prompt.ask("Extraction Date (YYYY-MM-DD)", default=date.today().strftime("%Y-%m-%d"))
        try:
            ext_date = parse_date(ext_date_str)
        except ValueError as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            press_any_key()
            return

        new_sample = Sample(
            code=code,
            volume=volume,
            extraction_date=ext_date,
            status=status,
            id_patient=patient.id,
            id_sample_type=type_id,
            id_container=container_id
        )
        
        sample_repo.save(new_sample)
        console.print(f"\n[bold green]Success: Sample '{code}' created and linked to Patient '{patient.code}' successfully![/bold green]")
        
    press_any_key()


def update_sample():
    clear_screen()
    show_banner("Update Sample")
    
    code = Prompt.ask("[bold white]Enter Code of the Sample to update[/bold white]")
    
    with uow_factory.create() as uow:
        repo = SampleRepository(uow.session)
        sample = repo.get_by_code(code)
        
        if not sample:
            console.print(f"[bold red]Error: Sample '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        console.print(f"\nEditing Sample: [cyan]{sample.code}[/cyan] (Current Volume: {sample.volume} mL, Status: {sample.status})\n")
        
        new_vol = FloatPrompt.ask("New Volume (mL)", default=float(sample.volume))
        if new_vol <= 0:
            console.print("[bold red]Error: Volume must be positive.[/bold red]")
            press_any_key()
            return
            
        new_status = Prompt.ask("New Status", choices=['pending','in_process','analyzed','rejected','archived'], default=sample.status)
        
        ext_date_str = Prompt.ask("New Extraction Date (YYYY-MM-DD)", default=sample.extraction_date.strftime("%Y-%m-%d"))
        try:
            new_date = parse_date(ext_date_str)
        except ValueError as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            press_any_key()
            return

        sample.volume = new_vol
        sample.status = new_status
        sample.extraction_date = new_date
        
        repo.save(sample)
        console.print(f"\n[bold green]Success: Sample '{code}' updated successfully![/bold green]")
    press_any_key()


def delete_sample():
    clear_screen()
    show_banner("Delete Sample")
    
    code = Prompt.ask("[bold red]Enter Code of the Sample to delete[/bold red]")
    
    with uow_factory.create() as uow:
        repo = SampleRepository(uow.session)
        sample = repo.get_by_code(code)
        
        if not sample:
            console.print(f"[bold red]Error: Sample '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        confirm = Confirm.ask(f"[bold red]Are you sure you want to permanently delete Sample {sample.code}?[/bold red]")
        if confirm:
            repo.delete(sample)
            console.print(f"[bold green]Success: Sample '{code}' deleted successfully![/bold green]")
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            
    press_any_key()


def search_sample():
    clear_screen()
    show_banner("Search Sample")
    
    code = Prompt.ask("[bold white]Enter Sample Code[/bold white]")
    
    with uow_factory.create() as uow:
        repo = SampleRepository(uow.session)
        sample = repo.get_by_code(code)
        
        if not sample:
            console.print(f"[bold red]Sample with code '{code}' not found.[/bold red]")
        else:
            console.print(Panel(
                f"[bold cyan]Sample ID:[/bold cyan] {sample.id}\n"
                f"[bold cyan]Code:[/bold cyan] {sample.code}\n"
                f"[bold cyan]Patient Name:[/bold cyan] {sample.patient.name} {sample.patient.lastname} [dim]({sample.patient.code})[/dim]\n"
                f"[bold cyan]Volume:[/bold cyan] {sample.volume} mL\n"
                f"[bold cyan]Status:[/bold cyan] {sample.status.upper()}\n"
                f"[bold cyan]Type:[/bold cyan] {sample.sample_type.type_name}\n"
                f"[bold cyan]Container Code:[/bold cyan] {sample.container.code}\n"
                f"[bold cyan]Extraction Date:[/bold cyan] {sample.extraction_date}",
                title=f"Details for Sample {sample.code}",
                expand=False
            ))
    press_any_key()


def view_full_sample():
    """Eager loads all relational tables to demonstrate all levels of relationships in detail."""
    clear_screen()
    show_banner("Eager Loaded Full Sample Details")
    
    code = Prompt.ask("[bold white]Enter Sample Code[/bold white]")
    
    with uow_factory.create() as uow:
        repo = SampleRepository(uow.session)
        sample = repo.get_full(code)  # Custom eager loading method
        
        if not sample:
            console.print(f"[bold red]Error: Sample '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        # 1:1 QC Detail (Without comments since QualityControl model does not have them)
        qc = sample.quality_control
        qc_details = "❌ No Quality Control record registered yet"
        if qc:
            status_color = "green" if qc.result == "approved" else "red" if qc.result == "rejected" else "yellow"
            qc_details = (
                f"Result: [{status_color}]{qc.result.upper()}[/{status_color}]\n"
                f"Purity: {qc.purity}% | Concentration: {qc.concentration} ng/μL"
            )
            
        # N:M Protocols Applied
        protocols = sample.protocols
        protocol_list = ", ".join([f"[cyan]{p.name}[/cyan] ({p.code})" for p in protocols]) if protocols else "No protocols applied"

        # N:M with attributes Research Projects
        # Let's query the specific association records to read the attribute (sample_assignment_date)
        assoc_stmt = uow.session.query(ResearchProjectSamples).filter_by(id_sample=sample.id).all()
        project_details = []
        for assoc in assoc_stmt:
            # Load project details
            proj = uow.session.get(ResearchProject, assoc.id_project)
            if proj:
                project_details.append(f"• [cyan]{proj.project_name}[/cyan] (Assigned on: [green]{assoc.sample_assignment_date}[/green])")
        project_str = "\n".join(project_details) if project_details else "Not associated with any research projects"

        # Build massive structured output card
        console.print(Panel(
            f"[bold yellow]🔬 SAMPLE CORE PROPERTIES[/bold yellow]\n"
            f"  Code: {sample.code} | Volume: {sample.volume} mL\n"
            f"  Extraction Date: {sample.extraction_date} | Status: {sample.status.upper()}\n\n"
            f"[bold yellow]🧑 1:N RELATIONSHIP (Patient)[/bold yellow]\n"
            f"  Patient: {sample.patient.name} {sample.patient.lastname} [cyan]({sample.patient.code})[/cyan]\n\n"
            f"[bold yellow]🛡️  1:1 RELATIONSHIP (Quality Control)[/bold yellow]\n"
            f"  {qc_details}\n\n"
            f"[bold yellow]🧬 N:M RELATIONSHIP (Protocols Applied)[/bold yellow]\n"
            f"  {protocol_list}\n\n"
            f"[bold yellow]📊 N:M WITH ATTRIBUTES RELATIONSHIP (Research Projects)[/bold yellow]\n"
            f"  {project_str}",
            title=f"FULL DOMAIN GRAPH MAP: {sample.code}",
            expand=False,
            box=box.DOUBLE
        ))
        
    press_any_key()


def filter_samples_status():
    status = Prompt.ask("Status", choices=['pending','in_process','analyzed','rejected','archived'])
    list_samples(status_filter=status)


def filter_samples_date():
    start_str = Prompt.ask("Start Date (YYYY-MM-DD)")
    end_str = Prompt.ask("End Date (YYYY-MM-DD)")
    try:
        start = parse_date(start_str)
        end = parse_date(end_str)
        list_samples(date_range=(start, end))
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        press_any_key()


def manage_quality_control():
    """Manages the 1:1 relationship with Quality Control (without comments attribute)."""
    clear_screen()
    show_banner("Quality Control (1:1 Manager)")
    
    sample_code = Prompt.ask("[bold white]Enter Sample Code to view/manage QC[/bold white]")
    
    with uow_factory.create() as uow:
        sample_repo = SampleRepository(uow.session)
        qc_repo = QualityControlRepository(uow.session)
        
        sample = sample_repo.get_by_code(sample_code)
        if not sample:
            console.print(f"[bold red]Error: Sample '{sample_code}' not found.[/bold red]")
            press_any_key()
            return
            
        qc = qc_repo.get_by_sample_code(sample_code)
        
        if qc:
            console.print(f"\n[cyan]Quality Control Record Exists for Sample '{sample_code}':[/cyan]")
            console.print(f"  Result: [bold]{qc.result.upper()}[/bold]")
            console.print(f"  Purity: {qc.purity}%")
            console.print(f"  Concentration: {qc.concentration} ng/μL\n")
            
            action = Prompt.ask("Do you want to [E]dit it, [D]elete it, or [B]ack?", choices=["E", "D", "B"], default="B")
            
            if action == "E":
                new_res = Prompt.ask("Result", choices=['approved', 'rejected', 'pending_review'], default=qc.result)
                new_pur = FloatPrompt.ask("Purity (%)", default=float(qc.purity) if qc.purity else 0.0)
                new_con = FloatPrompt.ask("Concentration (ng/uL)", default=float(qc.concentration) if qc.concentration else 0.0)
                
                qc.result = new_res
                qc.purity = new_pur
                qc.concentration = new_con
                qc_repo.save(qc)
                console.print("[bold green]Success: Quality Control updated successfully![/bold green]")
                
            elif action == "D":
                if Confirm.ask("[bold red]Are you sure you want to delete this Quality Control record?[/bold red]"):
                    qc_repo.delete(qc)
                    console.print("[bold green]Success: Quality Control record deleted successfully![/bold green]")
        else:
            console.print(f"\n[bold yellow]No Quality Control record exists for sample '{sample_code}'.[/bold yellow]")
            create_qc = Confirm.ask("Do you want to create one now?")
            
            if create_qc:
                result = Prompt.ask("Result", choices=['approved', 'rejected', 'pending_review'], default='pending_review')
                purity = FloatPrompt.ask("Purity (%)")
                concentration = FloatPrompt.ask("Concentration (ng/uL)")
                
                new_qc = QualityControl(
                    id_sample=sample.id,
                    result=result,
                    purity=purity,
                    concentration=concentration
                )
                qc_repo.save(new_qc)
                console.print(f"[bold green]Success: Quality Control record linked to sample '{sample_code}'![/bold green]")
                
    press_any_key()


# =============================================================================
# 3. STAFF SUBMENU (N:M with attributes via ProjectTeam roles)
# =============================================================================

def staff_menu():
    while True:
        clear_screen()
        show_banner("Staff Repository Manager")
        console.print("[1] 👥 List All Staff Members")
        console.print("[2] ➕ Add New Staff Member")
        console.print("[3] ✏️  Update Staff Details")
        console.print("[4] ❌ Delete Staff Member")
        console.print("[5] 🔍 Search Staff by Code")
        console.print("[6] 💼 Assign Staff to Research Project [dim](N:M with Role Attribute)[/dim]")
        console.print("[7] 📜 View Staff Member's Project Team Roles")
        console.print("[0] 🔙 Back to Main Menu")
        console.print()

        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "7", "0"])

        if choice == "1":
            list_staff()
        elif choice == "2":
            create_staff()
        elif choice == "3":
            update_staff()
        elif choice == "4":
            delete_staff()
        elif choice == "5":
            search_staff()
        elif choice == "6":
            assign_staff_project()
        elif choice == "7":
            view_staff_assignments()
        elif choice == "0":
            break


def list_staff():
    clear_screen()
    show_banner("Staff Members List")
    
    with uow_factory.create() as uow:
        repo = StaffRepository(uow.session)
        members = repo.get_all()
        
        if not members:
            console.print("[bold yellow]No staff members registered.[/bold yellow]")
            press_any_key()
            return
            
        table = Table(box=box.DOUBLE_EDGE, header_style="bold magenta")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Code", style="cyan bold")
        table.add_column("Full Name", style="white")
        table.add_column("Role / Title", style="yellow")
        table.add_column("Last Update", style="dim")
        
        for m in members:
            table.add_row(
                str(m.id),
                m.code,
                f"{m.name} {m.lastname}",
                m.role.replace("_", " ").upper(),
                m.last_update.strftime("%Y-%m-%d %H:%M") if m.last_update else "N/A"
            )
        console.print(table)
    press_any_key()


def create_staff():
    clear_screen()
    show_banner("Create Staff Member")
    
    code = Prompt.ask("[bold white]Staff Unique Code[/bold white] (e.g. S001)")
    name = Prompt.ask("[bold white]First Name[/bold white]")
    lastname = Prompt.ask("[bold white]Last Name[/bold white]")
    
    role = Prompt.ask(
        "[bold white]Staff Role[/bold white]",
        choices=['researcher', 'analyst', 'technician', 'manager', 'administrator'],
        default='analyst'
    )

    with uow_factory.create() as uow:
        repo = StaffRepository(uow.session)
        
        if repo.get_by_code(code):
            console.print(f"[bold red]Error: Staff with code '{code}' already exists.[/bold red]")
            press_any_key()
            return
            
        new_staff = Staff(
            code=code,
            name=name,
            lastname=lastname,
            role=role
        )
        repo.save(new_staff)
        console.print(f"\n[bold green]Success: Staff member '{name} {lastname}' created successfully![/bold green]")
    press_any_key()


def update_staff():
    clear_screen()
    show_banner("Update Staff Details")
    
    code = Prompt.ask("[bold white]Enter Code of the Staff Member to update[/bold white]")
    
    with uow_factory.create() as uow:
        repo = StaffRepository(uow.session)
        staff = repo.get_by_code(code)
        
        if not staff:
            console.print(f"[bold red]Error: Staff member '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        console.print(f"\nEditing: [cyan]{staff.name} {staff.lastname}[/cyan]\n")
        
        new_name = Prompt.ask("First Name", default=staff.name)
        new_lastname = Prompt.ask("Last Name", default=staff.lastname)
        
        new_role = Prompt.ask(
            "New Role",
            choices=['researcher', 'analyst', 'technician', 'manager', 'administrator'],
            default=staff.role
        )

        staff.name = new_name
        staff.lastname = new_lastname
        staff.role = new_role
        
        repo.save(staff)
        console.print(f"\n[bold green]Success: Staff '{code}' updated successfully![/bold green]")
    press_any_key()


def delete_staff():
    clear_screen()
    show_banner("Delete Staff Member")
    
    code = Prompt.ask("[bold red]Enter Code of the Staff Member to delete[/bold red]")
    
    with uow_factory.create() as uow:
        repo = StaffRepository(uow.session)
        staff = repo.get_by_code(code)
        
        if not staff:
            console.print(f"[bold red]Error: Staff member '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        confirm = Confirm.ask(f"[bold red]Are you sure you want to permanently delete {staff.name} {staff.lastname}?[/bold red]")
        if confirm:
            repo.delete(staff)
            console.print(f"[bold green]Success: Staff member '{code}' deleted successfully![/bold green]")
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            
    press_any_key()


def search_staff():
    clear_screen()
    show_banner("Search Staff Member")
    
    code = Prompt.ask("[bold white]Enter Staff Code[/bold white]")
    
    with uow_factory.create() as uow:
        repo = StaffRepository(uow.session)
        staff = repo.get_by_code(code)
        
        if not staff:
            console.print(f"[bold red]Staff member with code '{code}' not found.[/bold red]")
        else:
            console.print(Panel(
                f"[bold cyan]Staff ID:[/bold cyan] {staff.id}\n"
                f"[bold cyan]Code:[/bold cyan] {staff.code}\n"
                f"[bold cyan]Full Name:[/bold cyan] {staff.name} {staff.lastname}\n"
                f"[bold cyan]Role:[/bold cyan] {staff.role.replace('_', ' ').upper()}",
                title=f"Details for {staff.code}",
                expand=False
            ))
    press_any_key()


def assign_staff_project():
    """Assigns staff to a project (demonstrates N:M relationship with attributes: role)."""
    clear_screen()
    show_banner("Assign Staff to Research Project (N:M with Attributes)")
    
    staff_code = Prompt.ask("[bold white]Enter Staff Code[/bold white]")
    proj_name = Prompt.ask("[bold white]Enter exact Research Project Name[/bold white]")
    
    role = Prompt.ask(
        "[bold white]Enter Team Role[/bold white]",
        choices=['principal_investigator', 'co_investigator', 'analyst', 'technician', 'assistant'],
        default='analyst'
    )
    
    with uow_factory.create() as uow:
        repo = StaffRepository(uow.session)
        try:
            repo.add_to_research_project(staff_code, proj_name, role)
            console.print(f"\n[bold green]Success: Staff member [{staff_code}] successfully added to project '{proj_name}' as '{role}'![/bold green]")
        except ValueError as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]")
            
    press_any_key()


def view_staff_assignments():
    """Queries team roles for a staff member (demonstrates reading N:M with attributes)."""
    clear_screen()
    show_banner("View Staff Assignments & Roles (N:M Attributes)")
    
    staff_code = Prompt.ask("[bold white]Enter Staff Code[/bold white]")
    
    with uow_factory.create() as uow:
        repo = StaffRepository(uow.session)
        assignments = repo.get_research_project_with_roles(staff_code)
        
        if not assignments:
            console.print(f"[bold yellow]Staff member '{staff_code}' has no research project assignments.[/bold yellow]")
        else:
            table = Table(box=box.DOUBLE_EDGE, header_style="bold cyan")
            table.add_column("Research Project Name", style="white")
            table.add_column("Assigned Role", style="yellow bold")
            table.add_column("Last Update", style="dim")
            
            for assoc in assignments:
                # assoc.project is linked back via overlaps relationship in ProjectTeam model
                table.add_row(
                    assoc.project.project_name,
                    assoc.role.replace("_", " ").upper(),
                    assoc.last_update.strftime("%Y-%m-%d %H:%M")
                )
            console.print(table)
            
    press_any_key()


# =============================================================================
# 4. RESEARCH PROJECT SUBMENU (N:M with attributes date, N:M team list)
# =============================================================================

def project_menu():
    while True:
        clear_screen()
        show_banner("Research Project Repository Manager")
        console.print("[1] 📁 List All Research Projects")
        console.print("[2] ➕ Add New Research Project")
        console.print("[3] ✏️  Update Research Project")
        console.print("[4] ❌ Delete Research Project")
        console.print("[5] 🔍 Search Research Project by Name [dim](Custom Query)[/dim]")
        console.print("[6] 🧪 Link Sample to Project [dim](N:M with assignment date attribute)[/dim]")
        console.print("[7] 🗺️  View Research Project Details [dim](Shows Team and Sample relationships)[/dim]")
        console.print("[0] 🔙 Back to Main Menu")
        console.print()

        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "7", "0"])

        if choice == "1":
            list_projects()
        elif choice == "2":
            create_project()
        elif choice == "3":
            update_project()
        elif choice == "4":
            delete_project()
        elif choice == "5":
            search_project_name()
        elif choice == "6":
            link_sample_project()
        elif choice == "7":
            view_project_details()
        elif choice == "0":
            break


def list_projects():
    clear_screen()
    show_banner("Research Projects List")
    
    with uow_factory.create() as uow:
        repo = ResearchProjectRepository(uow.session)
        projects = repo.get_all()
        
        if not projects:
            console.print("[bold yellow]No research projects configured.[/bold yellow]")
            press_any_key()
            return
            
        table = Table(box=box.DOUBLE_EDGE, header_style="bold magenta")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Project Name", style="white bold")
        table.add_column("Start Date", style="green")
        table.add_column("Description", style="dim")
        table.add_column("Last Update", style="dim")
        
        for p in projects:
            table.add_row(
                str(p.id),
                p.project_name,
                p.start_date.strftime("%Y-%m-%d"),
                p.description[:50] + "..." if p.description and len(p.description) > 50 else p.description or "",
                p.last_update.strftime("%Y-%m-%d %H:%M") if p.last_update else "N/A"
            )
        console.print(table)
    press_any_key()


def create_project():
    clear_screen()
    show_banner("Create Research Project")
    
    name = Prompt.ask("[bold white]Project Name[/bold white]")
    start_str = Prompt.ask("[bold white]Start Date[/bold white] (YYYY-MM-DD)", default=date.today().strftime("%Y-%m-%d"))
    try:
        start_date = parse_date(start_str)
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        press_any_key()
        return
        
    description = Prompt.ask("[bold white]Project Description[/bold white]", default="")

    with uow_factory.create() as uow:
        repo = ResearchProjectRepository(uow.session)
        
        if repo.get_by_name(name):
            console.print(f"[bold red]Error: A project named '{name}' already exists.[/bold red]")
            press_any_key()
            return
            
        new_project = ResearchProject(
            project_name=name,
            start_date=start_date,
            description=description if description else None
        )
        repo.save(new_project)
        console.print(f"\n[bold green]Success: Research Project '{name}' created successfully![/bold green]")
    press_any_key()


def update_project():
    clear_screen()
    show_banner("Update Research Project")
    
    proj_id = IntPrompt.ask("[bold white]Enter Project ID to update[/bold white]")
    
    with uow_factory.create() as uow:
        repo = ResearchProjectRepository(uow.session)
        project = repo.get_by_id(proj_id)
        
        if not project:
            console.print(f"[bold red]Error: Research Project with ID {proj_id} not found.[/bold red]")
            press_any_key()
            return
            
        console.print(f"\nEditing: [cyan]{project.project_name}[/cyan] (Start Date: {project.start_date})\n")
        
        new_name = Prompt.ask("Project Name", default=project.project_name)
        start_str = Prompt.ask("Start Date (YYYY-MM-DD)", default=project.start_date.strftime("%Y-%m-%d"))
        try:
            new_start = parse_date(start_str)
        except ValueError as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            press_any_key()
            return
            
        new_desc = Prompt.ask("Description", default=project.description or "")

        project.project_name = new_name
        project.start_date = new_start
        project.description = new_desc if new_desc else None
        
        repo.save(project)
        console.print(f"\n[bold green]Success: Research Project ID {proj_id} updated successfully![/bold green]")
    press_any_key()


def delete_project():
    clear_screen()
    show_banner("Delete Research Project")
    
    proj_id = IntPrompt.ask("[bold red]Enter Project ID to delete[/bold red]")
    
    with uow_factory.create() as uow:
        repo = ResearchProjectRepository(uow.session)
        project = repo.get_by_id(proj_id)
        
        if not project:
            console.print(f"[bold red]Error: Research Project ID {proj_id} not found.[/bold red]")
            press_any_key()
            return
            
        confirm = Confirm.ask(f"[bold red]Are you sure you want to permanently delete Research Project '{project.project_name}'?[/bold red]")
        if confirm:
            repo.delete(project)
            console.print(f"[bold green]Success: Research Project '{project.project_name}' deleted successfully![/bold green]")
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            
    press_any_key()


def search_project_name():
    clear_screen()
    show_banner("Search Research Project by Name")
    
    name = Prompt.ask("[bold white]Enter Project Name[/bold white]")
    
    with uow_factory.create() as uow:
        repo = ResearchProjectRepository(uow.session)
        project = repo.get_by_name(name)
        
        if not project:
            console.print(f"[bold red]Research Project '{name}' not found.[/bold red]")
        else:
            console.print(Panel(
                f"[bold cyan]Project ID:[/bold cyan] {project.id}\n"
                f"[bold cyan]Project Name:[/bold cyan] {project.project_name}\n"
                f"[bold cyan]Start Date:[/bold cyan] {project.start_date}\n"
                f"[bold cyan]Description:[/bold cyan] {project.description or 'No description provided.'}",
                title=f"Details for Project {project.id}",
                expand=False
            ))
    press_any_key()


def link_sample_project():
    """Assigns sample to a research project (demonstrates N:M with attributes: sample_assignment_date)."""
    clear_screen()
    show_banner("Link Sample to Research Project (N:M with Attributes)")
    
    sample_code = Prompt.ask("[bold white]Enter unique Sample Code[/bold white]")
    proj_id = IntPrompt.ask("[bold white]Enter target Project ID[/bold white]")
    
    with uow_factory.create() as uow:
        sample_repo = SampleRepository(uow.session)
        project_repo = ResearchProjectRepository(uow.session)
        
        sample = sample_repo.get_by_code(sample_code)
        project = project_repo.get_by_id(proj_id)
        
        if not sample:
            console.print(f"[bold red]Error: Sample '{sample_code}' does not exist![/bold red]")
            press_any_key()
            return
            
        if not project:
            console.print(f"[bold red]Error: Research Project ID {proj_id} not found![/bold red]")
            press_any_key()
            return
            
        # Check if already linked
        existing = uow.session.query(ResearchProjectSamples).filter_by(id_sample=sample.id, id_project=project.id).first()
        if existing:
            console.print("[bold yellow]This sample is already associated with the project.[/bold yellow]")
            press_any_key()
            return
            
        # Save N:M assignment with attributes
        assignment = ResearchProjectSamples(
            id_sample=sample.id,
            id_project=project.id,
            sample_assignment_date=date.today()
        )
        uow.session.add(assignment)
        
        console.print(f"\n[bold green]Success: Sample '{sample.code}' linked to project '{project.project_name}' starting on {date.today()}![/bold green]")
        
    press_any_key()


def view_project_details():
    """Demonstrates N:M relationship maps (both Project Team roles and Samples associated)."""
    clear_screen()
    show_banner("Research Project Full Graph Map")
    
    proj_id = IntPrompt.ask("[bold white]Enter Research Project ID[/bold white]")
    
    with uow_factory.create() as uow:
        repo = ResearchProjectRepository(uow.session)
        # Eager load relationships using get_with_team
        project = repo.get_with_team(proj_id)
        
        if not project:
            console.print(f"[bold red]Error: Research Project ID {proj_id} not found.[/bold red]")
            press_any_key()
            return
            
        # Query ProjectTeam table directly to fetch specific team role attributes
        team_assignments = uow.session.query(ProjectTeam).filter_by(id_project=project.id).all()
        team_list = []
        for assoc in team_assignments:
            member = assoc.staff
            team_list.append(f"• [cyan]{member.name} {member.lastname}[/cyan] [bold yellow]({assoc.role.replace('_', ' ').upper()})[/bold yellow]")
            
        team_str = "\n  ".join(team_list) if team_list else "No staff assigned yet."

        # Fetch sample associations with their specific assignment dates
        sample_assignments = uow.session.query(ResearchProjectSamples).filter_by(id_project=project.id).all()
        samples_list = []
        for assoc in sample_assignments:
            sample = uow.session.get(Sample, assoc.id_sample)
            if sample:
                samples_list.append(f"• [cyan]{sample.code}[/cyan] (Assigned: [green]{assoc.sample_assignment_date}[/green] | Status: {sample.status.upper()})")
                
        samples_str = "\n  ".join(samples_list) if samples_list else "No samples associated yet."

        # Print layout panel
        console.print(Panel(
            f"[bold cyan]Project Details[/bold cyan]\n"
            f"  ID: {project.id} | Name: {project.project_name}\n"
            f"  Start Date: {project.start_date}\n"
            f"  Description: {project.description or 'N/A'}\n\n"
            f"[bold yellow]👥 PROJECT TEAM & ROLES (N:M with Roles)[/bold yellow]\n"
            f"  {team_str}\n\n"
            f"[bold yellow]🧪 SAMPLES ASSIGNED (N:M with Assignment Dates)[/bold yellow]\n"
            f"  {samples_str}",
            title=f"Domain Detail for Project: {project.project_name}",
            expand=False,
            box=box.DOUBLE
        ))
        
    press_any_key()


# =============================================================================
# 5. PROTOCOL SUBMENU (N:M relationship without attributes, matching Protocol DB columns)
# =============================================================================

def protocol_menu():
    while True:
        clear_screen()
        show_banner("Protocol Repository Manager")
        console.print("[1] 🧬 List All Protocols")
        console.print("[2] ➕ Add New Protocol")
        console.print("[3] ✏️  Update Protocol Details")
        console.print("[4] ❌ Delete Protocol")
        console.print("[5] 🔍 Search Protocol by Keyword [dim](Custom Query)[/dim]")
        console.print("[6] 🔗 Apply Protocol to Sample [dim](N:M Relationship creation)[/dim]")
        console.print("[7] 🧪 View Protocol Details [dim](Lists all applied samples)[/dim]")
        console.print("[0] 🔙 Back to Main Menu")
        console.print()

        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "7", "0"])

        if choice == "1":
            list_protocols()
        elif choice == "2":
            create_protocol()
        elif choice == "3":
            update_protocol()
        elif choice == "4":
            delete_protocol()
        elif choice == "5":
            search_protocol_keyword()
        elif choice == "6":
            apply_protocol_to_sample()
        elif choice == "7":
            view_protocol_samples()
        elif choice == "0":
            break


def list_protocols():
    clear_screen()
    show_banner("Protocols List")
    
    with uow_factory.create() as uow:
        repo = ProtocolRepository(uow.session)
        protocols = repo.get_all()
        
        if not protocols:
            console.print("[bold yellow]No protocols registered in the database.[/bold yellow]")
            press_any_key()
            return
            
        table = Table(box=box.DOUBLE_EDGE, header_style="bold magenta")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Code", style="cyan bold")
        table.add_column("Name", style="white")
        table.add_column("Description", style="dim")
        table.add_column("Reviewed By", style="yellow")
        table.add_column("Last Update", style="dim")
        
        for prt in protocols:
            reviewer = prt.staff.code if prt.staff else "🔴 UNREVIEWED"
            table.add_row(
                str(prt.id),
                prt.code,
                prt.name,
                prt.description[:50] + "..." if prt.description and len(prt.description) > 50 else prt.description or "",
                reviewer,
                prt.last_update.strftime("%Y-%m-%d %H:%M") if prt.last_update else "N/A"
            )
        console.print(table)
    press_any_key()


def create_protocol():
    clear_screen()
    show_banner("Create Protocol")
    
    code = Prompt.ask("[bold white]Protocol Code[/bold white] (e.g. PROT-001)")
    name = Prompt.ask("[bold white]Protocol Name[/bold white]")
    description = Prompt.ask("[bold white]Protocol Description[/bold white]", default="")
    
    with uow_factory.create() as uow:
        repo = ProtocolRepository(uow.session)
        staff_repo = StaffRepository(uow.session)
        
        if repo.get_by_code(code):
            console.print(f"[bold red]Error: Protocol with code '{code}' already exists.[/bold red]")
            press_any_key()
            return
            
        # Optional reviewer selection
        rev_code = Prompt.ask("[bold white]Enter Reviewer Staff Code (Optional)[/bold white]", default="")
        reviewer_id = None
        if rev_code.strip():
            staff = staff_repo.get_by_code(rev_code)
            if not staff:
                console.print(f"[bold yellow]Warning: Staff reviewer '{rev_code}' not found. Leaving unreviewed.[/bold yellow]")
            else:
                reviewer_id = staff.id
                
        new_protocol = Protocol(
            code=code,
            name=name,
            description=description if description else None,
            reviewed_by_id=reviewer_id
        )
        repo.save(new_protocol)
        console.print(f"\n[bold green]Success: Protocol '{name}' created successfully![/bold green]")
    press_any_key()


def update_protocol():
    clear_screen()
    show_banner("Update Protocol Details")
    
    code = Prompt.ask("[bold white]Enter Code of the Protocol to update[/bold white]")
    
    with uow_factory.create() as uow:
        repo = ProtocolRepository(uow.session)
        staff_repo = StaffRepository(uow.session)
        protocol = repo.get_by_code(code)
        
        if not protocol:
            console.print(f"[bold red]Error: Protocol '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        console.print(f"\nEditing: [cyan]{protocol.name}[/cyan]\n")
        
        new_name = Prompt.ask("Protocol Name", default=protocol.name)
        new_desc = Prompt.ask("Description", default=protocol.description or "")
        
        rev_code = Prompt.ask("New Reviewer Staff Code (Optional, leave blank to clear/keep)", default=protocol.staff.code if protocol.staff else "")
        if rev_code.strip():
            staff = staff_repo.get_by_code(rev_code)
            if staff:
                protocol.reviewed_by_id = staff.id
        elif rev_code.strip() == "" and protocol.reviewed_by_id:
            clear_rev = Confirm.ask("Do you want to clear the reviewer?")
            if clear_rev:
                protocol.reviewed_by_id = None

        protocol.name = new_name
        protocol.description = new_desc if new_desc else None
        
        repo.save(protocol)
        console.print(f"\n[bold green]Success: Protocol '{code}' updated successfully![/bold green]")
    press_any_key()


def delete_protocol():
    clear_screen()
    show_banner("Delete Protocol")
    
    code = Prompt.ask("[bold red]Enter Code of the Protocol to delete[/bold red]")
    
    with uow_factory.create() as uow:
        repo = ProtocolRepository(uow.session)
        protocol = repo.get_by_code(code)
        
        if not protocol:
            console.print(f"[bold red]Error: Protocol '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        confirm = Confirm.ask(f"[bold red]Are you sure you want to permanently delete Protocol '{protocol.name}'?[/bold red]")
        if confirm:
            repo.delete(protocol)
            console.print(f"[bold green]Success: Protocol '{code}' deleted successfully![/bold green]")
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            
    press_any_key()


def search_protocol_keyword():
    clear_screen()
    show_banner("Search Protocol by Name Keyword")
    
    keyword = Prompt.ask("[bold white]Enter search keyword[/bold white]")
    
    with uow_factory.create() as uow:
        repo = ProtocolRepository(uow.session)
        results = repo.search_by_name(keyword)
        
        if not results:
            console.print(f"[bold yellow]No protocols contain the keyword '{keyword}'.[/bold yellow]")
        else:
            table = Table(box=box.DOUBLE_EDGE, header_style="bold green")
            table.add_column("Code", style="cyan bold")
            table.add_column("Name", style="white")
            table.add_column("Reviewer", style="yellow")
            
            for p in results:
                reviewer = p.staff.code if p.staff else "UNREVIEWED"
                table.add_row(p.code, p.name, reviewer)
            console.print(table)
            
    press_any_key()


def apply_protocol_to_sample():
    """Links a protocol to a sample (demonstrates adding to a secondary N:M mapping)."""
    clear_screen()
    show_banner("Apply Protocol to Sample (N:M)")
    
    protocol_code = Prompt.ask("[bold white]Enter Protocol Code[/bold white]")
    sample_code = Prompt.ask("[bold white]Enter Sample Code[/bold white]")
    
    with uow_factory.create() as uow:
        prot_repo = ProtocolRepository(uow.session)
        sample_repo = SampleRepository(uow.session)
        
        protocol = prot_repo.get_by_code(protocol_code)
        sample = sample_repo.get_by_code(sample_code)
        
        if not protocol:
            console.print(f"[bold red]Error: Protocol '{protocol_code}' not found![/bold red]")
            press_any_key()
            return
            
        if not sample:
            console.print(f"[bold red]Error: Sample '{sample_code}' not found![/bold red]")
            press_any_key()
            return
            
        # Check if already applied
        if protocol in sample.protocols:
            console.print("[bold yellow]This protocol is already applied to this sample.[/bold yellow]")
            press_any_key()
            return
            
        # Since it is a standard secondary mapping, we append directly to the relationship list
        sample.protocols.append(protocol)
        sample_repo.save(sample)
        
        console.print(f"\n[bold green]Success: Protocol '{protocol.name}' successfully applied to Sample '{sample.code}'![/bold green]")
        
    press_any_key()


def view_protocol_samples():
    """Lists all samples using this protocol (demonstrates reading N:M relationships)."""
    clear_screen()
    show_banner("View Protocol Applied Samples (N:M)")
    
    code = Prompt.ask("[bold white]Enter Protocol Code[/bold white]")
    
    with uow_factory.create() as uow:
        repo = ProtocolRepository(uow.session)
        protocol = repo.get_with_samples(code)  # eager loaded N:M samples
        
        if not protocol:
            console.print(f"[bold red]Error: Protocol '{code}' not found.[/bold red]")
            press_any_key()
            return
            
        console.print(f"[bold cyan]Protocol:[/bold cyan] {protocol.name} [dim]({protocol.code})[/dim]")
        
        if not protocol.samples:
            console.print(f"[bold yellow]This protocol has not been applied to any samples yet.[/bold yellow]")
        else:
            table = Table(box=box.DOUBLE_EDGE, header_style="bold yellow")
            table.add_column("Sample Code", style="bold cyan")
            table.add_column("Patient Associated", style="white")
            table.add_column("Status", style="green")
            
            for s in protocol.samples:
                table.add_row(
                    s.code,
                    f"{s.patient.name} {s.patient.lastname}" if s.patient else "N/A",
                    s.status.upper()
                )
            console.print(table)
            
    press_any_key()


# =============================================================================
# 6. CONTAINER & SAMPLE TYPE ADMINISTRATIVE UTILITIES
# =============================================================================

def admin_menu():
    while True:
        clear_screen()
        show_banner("Container & Sample Type Admin")
        console.print("[1] 📦 List All Containers")
        console.print("[2] ➕ Add New Container")
        console.print("[3] 🧪 List All Sample Types")
        console.print("[4] ➕ Add New Sample Type")
        console.print("[0] 🔙 Back to Main Menu")
        console.print()

        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]", choices=["1", "2", "3", "4", "0"])

        if choice == "1":
            list_containers()
        elif choice == "2":
            create_container()
        elif choice == "3":
            list_sample_types()
        elif choice == "4":
            create_sample_type()
        elif choice == "0":
            break


def list_containers():
    clear_screen()
    show_banner("Containers List")
    
    with uow_factory.create() as uow:
        repo = BaseRepository(uow.session, Container)
        containers = repo.get_all()
        
        if not containers:
            console.print("[bold yellow]No containers registered.[/bold yellow]")
            press_any_key()
            return
            
        table = Table(box=box.DOUBLE_EDGE, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Code (Unique)", style="bold cyan")
        table.add_column("Type Name", style="white")
        table.add_column("Last Update", style="dim")
        
        for c in containers:
            table.add_row(str(c.id), c.code, c.type_name, c.last_update.strftime("%Y-%m-%d %H:%M"))
        console.print(table)
    press_any_key()


def create_container():
    clear_screen()
    show_banner("Create Container")
    
    code = Prompt.ask("Container Code (e.g. CNT-001)")
    type_name = Prompt.ask("Container Type (e.g. Cryotube 2mL)")
    
    with uow_factory.create() as uow:
        repo = BaseRepository(uow.session, Container)
        
        # Check unique constraints
        existing = uow.session.query(Container).filter((Container.code == code) | (Container.type_name == type_name)).first()
        if existing:
            console.print("[bold red]Error: A container with this code or type name already exists.[/bold red]")
            press_any_key()
            return
            
        new_container = Container(code=code, type_name=type_name)
        repo.save(new_container)
        console.print(f"[bold green]Success: Container '{code}' created successfully![/bold green]")
        
    press_any_key()


def list_sample_types():
    clear_screen()
    show_banner("Sample Types List")
    
    with uow_factory.create() as uow:
        repo = BaseRepository(uow.session, SampleType)
        types = repo.get_all()
        
        if not types:
            console.print("[bold yellow]No sample types registered.[/bold yellow]")
            press_any_key()
            return
            
        table = Table(box=box.DOUBLE_EDGE, header_style="bold green")
        table.add_column("ID", style="dim")
        table.add_column("Type Name", style="white bold")
        table.add_column("Last Update", style="dim")
        
        for t in types:
            table.add_row(str(t.id), t.type_name, t.last_update.strftime("%Y-%m-%d %H:%M"))
        console.print(table)
    press_any_key()


def create_sample_type():
    clear_screen()
    show_banner("Create Sample Type")
    
    type_name = Prompt.ask("Sample Type Name (e.g. Serum, Plasma, Whole Blood)")
    
    with uow_factory.create() as uow:
        repo = BaseRepository(uow.session, SampleType)
        
        existing = uow.session.query(SampleType).filter_by(type_name=type_name).first()
        if existing:
            console.print(f"[bold red]Error: Sample Type '{type_name}' already exists.[/bold red]")
            press_any_key()
            return
            
        new_type = SampleType(type_name=type_name)
        repo.save(new_type)
        console.print(f"[bold green]Success: Sample Type '{type_name}' created successfully![/bold green]")
        
    press_any_key()


# =============================================================================
# MAIN APPLICATION LOOP
# =============================================================================

def main():
    while True:
        clear_screen()
        # Main styled terminal dashboard
        console.print(Panel(
            Align.center(
                "[bold cyan]🧬 BIOTRACK BACK OFFICE CLINICAL PORTAL 🧬[/bold cyan]\n"
                "[italic dim]Robust Layered UI utilizing UoW & Repository Patterns[/italic dim]\n\n"
                "[bold white]Select a Repository Module below to manage data & relationships:[/bold white]"
            ),
            box=box.DOUBLE,
            style="cyan",
            expand=False
        ))
        console.print()
        
        console.print("  [bold yellow][1][/bold yellow] 👤 Patient Manager        [dim]— [1:N] Patients ↔ Samples relationship[/dim]")
        console.print("  [bold yellow][2][/bold yellow] 🧪 Sample Manager         [dim]— [1:1] QC, [N:M] Protocols, [N:M-Attr] Projects[/dim]")
        console.print("  [bold yellow][3][/bold yellow] 👥 Staff Manager          [dim]— [N:M-Attr] Staff Assignments & Roles[/dim]")
        console.print("  [bold yellow][4][/bold yellow] 📁 Research Projects      [dim]— [N:M-Attr] Samples & Project Team Graph[/dim]")
        console.print("  [bold yellow][5][/bold yellow] 🧬 Protocol Manager       [dim]— [N:M] Protocols ↔ Samples association[/dim]")
        console.print("  [bold yellow][6][/bold yellow] ⚙️  Admin Utilities        [dim]— Manage Containers & Sample Types[/dim]")
        console.print("  [bold yellow][0][/bold yellow] 🚪 Exit Application")
        console.print()

        choice = Prompt.ask("[bold yellow]Choose option[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "0"])

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
            clear_screen()
            console.print(Panel(
                Align.center("[bold green]Thank you for using BioTrack! Exiting systems...[/bold green]\n[dim]All transactions closed successfully.[/dim]"),
                box=box.ROUNDED,
                style="green"
            ))
            break


if __name__ == "__main__":
    main()
