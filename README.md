<div align="center">

[![BioTrack Header](https://capsule-render.vercel.app/api?type=waving&color=0:00d4a8,100:0095ff&height=200&section=header&text=BioTrack&fontSize=72&fontColor=ffffff&fontAlignY=38&desc=Biological+Sample+Management+System+for+Biobanks&descAlignY=58&descSize=16&animation=fadeIn)](https://github.com/Arnaudevv/Biotrack)

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Space+Mono&size=16&pause=1000&color=00D4A8&center=true&vCenter=true&width=600&lines=Biological+sample+traceability;Donor+%E2%86%92+Sample+%E2%86%92+Research+Project;Built+with+SQLAlchemy+%2B+Docker;CFGS+DAM+%C2%B7+Data+Access+2025%E2%80%932026)](https://github.com/Arnaudevv/Biotrack)

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Ubuntu-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Rich](https://img.shields.io/badge/UI-Rich_Terminal-00D4A8?style=for-the-badge)](https://github.com/Textualize/rich)
[![Status](https://img.shields.io/badge/Status-In%20development-FFB400?style=for-the-badge)](https://github.com/Arnaudevv/Biotrack)

</div>

---

## 📑 Table of Contents

- [What is BioTrack?](#-what-is-biotrack)
- [Main Flow](#-main-flow)
- [Features](#-features)
- [Tech Stack](#️-tech-stack)
- [Data Model](#️-data-model)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Running the Application](#-running-the-application)
- [UI Guide](#-ui-guide)
- [Relationship Demonstrations](#-relationship-demonstrations)
- [User Stories](#-user-stories)

---

## 🔬 What is BioTrack?

BioTrack is a **desktop application** for managing the basic lifecycle of biological samples in a biobank. It belongs to the **LIMS** *(Laboratory Information Management Systems)* domain, reduced to its minimum functional expression.

> No automation. No complex logic. Just **create · query · edit** — with full traceability from donor to research project.

---

## 🧬 Main Flow

```
🧑‍⚕️ Donor  ──►  🧪 Sample  ──►  ✅ Quality  ──►  📋 Protocol  ──►  🔭 Project  ──►  🌡️ Temperature
```

---

## ✨ Features

| Module                  | Description                                                        | Priority |
| ----------------------- | ------------------------------------------------------------------ | -------- |
| 🧑‍🔬 **Donors**          | Register, edit and deactivate donors with a unique anonymized code | 🔴 High   |
| 🧫 **Samples**           | Track plasma, DNA, tissue... with type and container               | 🔴 High   |
| 📊 **Quality Control**   | 1:1 report per sample — purity, concentration, result              | 🔴 High   |
| 📋 **Protocols**         | N:M assignment of handling protocols per sample                    | 🟡 Medium |
| 🔭 **Research Projects** | N:M assignment with consumed quantity and status                   | 🔴 High   |
| 🌡️ **Temperature Log**  | Historical freezer readings per sample                             | 🔴 High   |

---

## 🛠️ Tech Stack

```python
stack = {
    "language":  "Python 3.x",
    "ORM":       "SQLAlchemy 2.0",   # ✅ confirmed
    "database":  "PostgreSQL",        # ✅ in Docker (Ubuntu)
    "container": "Docker",            # ✅ confirmed
    "UI":        "Rich (terminal)",   # ✅ console-based CLI
    "migrations":"Alembic",           # ✅ confirmed
}
```

**📦 Docker Infrastructure**

```
┌─────────────────────────────┐
│        Docker (Ubuntu)      │
│  ┌─────────────────────┐    │
│  │      PostgreSQL     │    │
│  └──────────┬──────────┘    │
└─────────────┼───────────────┘
              │ SQLAlchemy ORM
┌─────────────┴───────────────┐
│       Python Application    │
│   BioTrack · Rich CLI UI    │
└─────────────────────────────┘
```

---

## 🗃️ Data Model

<details>
<summary><strong>View full table schema</strong></summary>

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     patient     │   │   sample_type   │   │    container    │
│─────────────────│   │─────────────────│   │─────────────────│
│ id              │   │ id              │   │ id              │
│ code            │   │ type_name       │   │ code            │
│ name            │   └────────┬────────┘   │ type_name       │
│ last_name       │            │            └────────┬────────┘
│ birth_date      │            │                     │
│ active          │            │                     │
│ registration_   │            │                     │
│   date          │            │                     │
└────────┬────────┘            │                     │
         │                     │                     │
         └──────────────┬──────┘─────────────────────┘
                        ▼
             ┌─────────────────────┐
             │       sample        │
             │─────────────────────│
             │ id                  ├──────────────────────────────────┐
             │ code                │                                  │
             │ volume              ├────────────────────┐             │
             │ extraction_date     │                    │             │
             │ status              │                    │             │
             │ id_patient          │                    │             │
             │ id_sample_type      │                    │             │
             │ id_container        │                    │             │
             └──────────┬──────────┘                    │             │
                        │                               │             │
         ┌──────────────┼──────────────┐                │             │
         ▼              ▼              ▼                 ▼             ▼
┌────────────────┐ ┌──────────────┐ ┌────────────────────┐  ┌─────────────────┐
│quality_control │ │log_temperatu-│ │  sample_protocol   │  │research_project_│
│────────────────│ │re            │ │────────────────────│  │samples          │
│ id             │ │──────────────│ │ id_protocol        │  │─────────────────│
│ purity         │ │ id_log       │ │ id_sample          │  │ sample_assign_  │
│ concentration  │ │ reading_date │ └─────────┬──────────┘  │   date          │
│ result         │ │ temperature  │           │             │ id_sample       │
│ id_sample      │ │ id_sample    │           ▼             │ id_project      │
└────────────────┘ └──────────────┘  ┌────────────────┐    └────────┬────────┘
                                     │    protocol    │             │
                                     │────────────────│             ▼
                                     │ id             │    ┌────────────────────┐
                                     │ code           │    │  research_project  │
                                     │ name           │    │────────────────────│
                                     │ description    │    │ id                 │
                                     │ protocol_file  │    │ project_name       │
                                     │ file_name      │    │ start_date         │
                                     │ creation_date  │    │ description        │
                                     │ last_review_   │    └────────┬───────────┘
                                     │   date         │             │
                                     │ reviewed_by_id │    ┌────────┴───────────┐
                                     └───────┬────────┘    │   project_team     │
                                             │             │────────────────────│
                                             │             │ id_project         │
                                             │             │ id_staff           │
                                             │             │ role               │
                                             │             └────────┬───────────┘
                                             │                      │
                                             └──────────┬───────────┘
                                                        ▼
                                               ┌────────────────┐
                                               │     staff      │
                                               │────────────────│
                                               │ id             │
                                               │ code           │
                                               │ name           │
                                               │ lastname       │
                                               │ role           │
                                               │ active         │
                                               └────────────────┘
```

</details>

**Relationship summary:**

| Relationship | Entities | Type | Association table |
|---|---|---|---|
| Patient → Samples | `patient` → `sample` | **1 : N** | — |
| Sample → Quality Control | `sample` → `quality_control` | **1 : 1** | — |
| Sample → Temperature Log | `sample` → `log_temperature` | **1 : N** | — |
| Sample ↔ Protocol | `sample` ↔ `protocol` | **N : M** | `sample_protocol` |
| Sample ↔ Research Project | `sample` ↔ `research_project` | **N : M + attr** | `research_project_samples` (`sample_assignment_date`) |
| Staff ↔ Research Project | `staff` ↔ `research_project` | **N : M + attr** | `project_team` (`role`) |
| Protocol → Staff (reviewer) | `protocol` → `staff` | **N : 1** | — |

---

## 📁 Project Structure

```
Biotrack/
├── src/
│   └── domain/
│       ├── models.py                         # SQLAlchemy ORM models
│       ├── config.py                         # DB connection URL loader
│       └── repositories/
│           ├── base_repository.py            # Generic CRUD base class
│           ├── unit_of_work.py               # Unit of Work pattern
│           ├── patient_repository.py
│           ├── sample_repository.py
│           ├── staff_repository.py
│           ├── research_project_repository.py
│           ├── protocol_repository.py
│           └── quality_control_repository.py
├── alembic/                                  # Database migration scripts
│   └── versions/
├── data/                                     # Seed / fixture data
├── notebooks/                                # Jupyter exploration notebooks
├── cli_app.py                                # ← Entry point (Rich terminal UI)
├── alembic.ini                               # Alembic configuration
├── pyproject.toml
├── requirements.txt
├── .env                                      # Local environment variables (not committed)
└── README.md
```

---

## 🧰 Prerequisites

Before running BioTrack, make sure you have the following installed:

| Tool | Minimum version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Runtime |
| **pip** | bundled with Python | Package installer |
| **Docker Desktop** | latest | Runs PostgreSQL |
| **PowerShell** | 5.1+ / PS Core 7+ | **Recommended terminal** |

> **⚠️ Terminal compatibility** — the CLI is designed for **Windows PowerShell** or **PowerShell Core**.  
> Git Bash users can launch the app with `winpty python cli_app.py`, but Rich's color rendering, box-drawing characters, and interactive prompts **will not display correctly** in that environment. Use PowerShell for the full visual experience.

---

## 📦 Installation

### 1 · Clone the repository

```powershell
git clone https://github.com/Arnaudevv/Biotrack.git
cd Biotrack
```

### 2 · Create and activate a virtual environment *(recommended)*

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> If PowerShell blocks script execution, run this first (once per machine):
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3 · Install dependencies

```powershell
pip install -r requirements.txt
pip install rich
```

> `rich` is the terminal UI library used by `cli_app.py`. Install it separately if it is not yet included in `requirements.txt`.

### 4 · Start the PostgreSQL database with Docker

```powershell
docker compose up -d
```

> If your project uses a plain `docker run` instead of Compose, check the `.env` file for the correct port and credentials and adapt accordingly.

### 5 · Run database migrations

```powershell
alembic upgrade head
```

---

## ⚙️ Configuration

BioTrack supports **three runtime environments**, each backed by a different database engine. The active environment is controlled entirely through a `.env` file at the project root, which is read by `src/domain/config.py` via `python-dotenv`.

> **`.env` is never committed to version control.** Add it to `.gitignore` if it is not already there.

### Environment reference

| Variable | Required in | Description |
|---|---|---|
| `ENVIRONMENT` | always | Active environment: `development`, `testing`, or `production` |
| `DB_FILENAME_DEVELOPMENT` | `development` | SQLite filename for the development database |
| `DB_FILENAME_TEST` | `testing` | SQLite filename for the test database |
| `DB_URL_PRODUCTION` | `production` | Full PostgreSQL connection string |

### How it works

`config.py` reads `ENVIRONMENT` and then picks the corresponding variable to build the SQLAlchemy database URL:

- **`development` / `testing`** — uses **SQLite**. You only provide the `.db` filename (e.g. `biotrack.db`). `config.py` resolves the full file path automatically and creates or updates the database file on first run. No Docker or PostgreSQL needed.
- **`production`** — uses **PostgreSQL**. You provide the full connection string in `DB_URL_PRODUCTION`. This is the environment intended for a Docker-hosted database.

### `.env` template

Copy the block below, paste it into a new `.env` file at the project root, and fill in the values that match your setup:

```dotenv
# ── Active environment ──────────────────────────────────────────
# Choose one: development | testing | production
ENVIRONMENT=development

# ── SQLite (development) ────────────────────────────────────────
# Filename only — config.py resolves the full path automatically.
DB_FILENAME_DEVELOPMENT=biotrack.db

# ── SQLite (testing) ────────────────────────────────────────────
# Kept separate so test runs never touch development data.
DB_FILENAME_TEST=biotrack_test.db

# ── PostgreSQL (production) ─────────────────────────────────────
# Full connection URL. Only used when ENVIRONMENT=production.
# Format: postgresql://user:password@host:port/database
DB_URL_PRODUCTION=postgresql://admin:admin123@localhost:5432/biotrack
```

### Typical setup per environment

**Local development (default)**

```dotenv
ENVIRONMENT=development
DB_FILENAME_DEVELOPMENT=biotrack.db
```

No Docker required. The SQLite file is created automatically on first run.

**Running tests**

```dotenv
ENVIRONMENT=testing
DB_FILENAME_TEST=biotrack_test.db
```

Test runs use an isolated database so they never affect development data.

**Production / Docker**

```dotenv
ENVIRONMENT=production
DB_URL_PRODUCTION=postgresql://admin:admin123@localhost:5432/biotrack
```

Make sure the Docker container is running (`docker compose up -d`) before launching the app.

---

## 🚀 Running the Application

### ✅ PowerShell (recommended)

Open PowerShell, navigate to the project root, and run:

```powershell
python cli_app.py
```

The terminal will clear and display the BioTrack main menu with full color, Unicode box-drawing characters, and interactive prompts rendered correctly by the Rich library.

---

### ⚠️ Git Bash (limited support)

Git Bash can launch the app, but the visual output will be degraded — panels, colored tables, and prompt widgets will not render as intended because Git Bash does not fully emulate a Windows console:

```bash
winpty python cli_app.py
```

Use this only for quick debugging. For normal use, switch to PowerShell.

---

## 🖥️ UI Guide

BioTrack's interface is built entirely with the **[Rich](https://github.com/Textualize/rich)** library. Navigation is done by typing the number of the desired option and pressing `Enter`. There are no mouse interactions.

### Main menu

When you launch the app you are presented with the main menu:

```
╭──────────────────────────────────────────────╮
│       BIOTRACK CLINICAL SYSTEM               │
│       ❖ Main Menu ❖                          │
╰──────────────────────────────────────────────╯

 [1]  🧑‍🔬  Patient Manager
 [2]  🧪   Sample Manager
 [3]  👥   Staff Manager
 [4]  🔭   Research Project Manager
 [5]  📋   Protocol Manager
 [6]  🌡️   Temperature Log Manager
 [0]  🚪   Exit
```

Select a number to enter the corresponding submenu.

---

### Submenus — one per repository

Each module has its own submenu following the same structure. Below is a reference for each.

#### 🧑‍🔬 Patient Manager

```
 [1]  🗃️  List all patients
 [2]  ➕  Add new patient
 [3]  ✏️   Update patient details
 [4]  ❌  Delete patient
 [5]  🔍  Search patient by code
 [6]  🟢  View active patients only          (custom filter)
 [7]  🧪  View patient's samples             (1:N relationship)
 [0]  🔙  Back to main menu
```

When creating a patient you will be asked for: unique code (e.g. `PAT-001`), first name, last name, birth date (`YYYY-MM-DD`), a clinical note, and active status.

#### 🧪 Sample Manager

```
 [1]  🧪  List all samples
 [2]  ➕  Add new sample                     (selects patient, type, container)
 [3]  ✏️   Update sample details
 [4]  ❌  Delete sample
 [5]  🔍  Search sample by code
 [6]  🩺  View full sample details           (eager-loads all relationships)
 [7]  🎚️  Filter samples by status           (custom filter)
 [8]  📅  Filter samples by extraction date  (custom filter)
 [9]  🛡️  Manage quality control             (1:1 relationship)
 [0]  🔙  Back to main menu
```

When creating a sample, the UI first lists available **patients**, **sample types**, and **containers** so you can select the related entity by ID before filling in the sample-specific fields.

Option **[6] View full sample details** displays all four relationship levels in a single panel (see [Relationship Demonstrations](#-relationship-demonstrations)).

#### 👥 Staff Manager

```
 [1]  👥  List all staff members
 [2]  ➕  Add new staff member
 [3]  ✏️   Update staff details
 [4]  ❌  Delete staff member
 [5]  🔍  Search staff by code
 [6]  💼  Assign staff to research project   (N:M with role attribute)
 [7]  📜  View staff member's project roles  (reads N:M attributes)
 [0]  🔙  Back to main menu
```

#### 🔭 Research Project Manager

```
 [1]  📋  List all research projects
 [2]  ➕  Create new project
 [3]  ✏️   Update project details
 [4]  ❌  Delete project
 [5]  🔍  Search project by name
 [6]  🧪  Assign sample to project           (N:M with date attribute)
 [7]  👥  View project team                  (N:M with role attribute)
 [0]  🔙  Back to main menu
```

#### 📋 Protocol Manager

```
 [1]  📋  List all protocols
 [2]  ➕  Create new protocol
 [3]  ✏️   Update protocol
 [4]  ❌  Delete protocol
 [5]  🔍  Search protocol by code
 [6]  🧫  Assign protocol to sample          (N:M relationship)
 [0]  🔙  Back to main menu
```

#### 🌡️ Temperature Log Manager

```
 [1]  🌡️  List all temperature logs
 [2]  ➕  Add new reading                    (selects sample by code)
 [3]  ✏️   Update reading
 [4]  ❌  Delete reading
 [5]  🔍  Filter logs by sample code         (custom filter)
 [0]  🔙  Back to main menu
```

---

### General interaction patterns

| Action | What to type |
|---|---|
| Select menu option | Number shown in brackets, then `Enter` |
| Confirm a destructive action | `y` + `Enter` (or `n` to cancel) |
| Accept default value | Press `Enter` without typing |
| Enter a date | Format `YYYY-MM-DD` (e.g. `2024-03-15`) |
| Cancel and go back | Choose option `[0]` from any submenu |

After every action a message confirms success or describes the error. Press `Enter` to return to the submenu.

---

## 🔗 Relationship Demonstrations

The UI explicitly surfaces every relationship type defined in the schema.

### 1 : 1 — Sample ↔ Quality Control

Accessed via **Sample Manager → [9] Manage quality control**.  
The app looks up the single QC record linked to a sample. If one exists, it offers Edit or Delete. If none exists, it offers to create one inline. A sample can have at most one QC record — the uniqueness is enforced at the database level.

```
Quality Control Record Exists for Sample 'SMP-001':
  Result:        APPROVED
  Purity:        98.5%
  Concentration: 142.3 ng/μL
```

### 1 : N — Patient → Samples

Accessed via **Patient Manager → [7] View patient's samples**.  
The repository uses eager loading (`get_with_samples`) to fetch the patient and all their associated samples in a single query. Results are displayed in a Rich table.

```
Patient: John Doe (PAT-001)

┌─────────────┬─────────────┬───────────┬─────────────────┐
│ Sample Code │ Volume (mL) │ Status    │ Extraction Date │
├─────────────┼─────────────┼───────────┼─────────────────┤
│ SMP-001     │ 5.00        │ ANALYZED  │ 2024-01-10      │
│ SMP-007     │ 2.50        │ PENDING   │ 2024-03-22      │
└─────────────┴─────────────┴───────────┴─────────────────┘
```

### N : M — Sample ↔ Protocol

Accessed via **Protocol Manager → [6] Assign protocol to sample**.  
Multiple protocols can be assigned to the same sample, and the same protocol can be applied to many samples. The association table `sample_protocol` links them without extra attributes.

The assigned protocols appear in the "Full sample details" panel (option [6] in Sample Manager) under the **N:M Relationships** section.

### N : M with attributes — Sample ↔ Research Project

Accessed via **Research Project Manager → [6] Assign sample to project**.  
The `research_project_samples` association table carries an extra field: `sample_assignment_date`. When assigning a sample, the user enters this date explicitly. The app reads it back and displays it alongside the project name in the full sample details view.

```
📊 N:M WITH ATTRIBUTES (Research Projects)
  • Oncology Study Alpha  (Assigned on: 2024-02-14)
  • Genome Mapping Beta   (Assigned on: 2024-04-01)
```

### N : M with attributes — Staff ↔ Research Project

Accessed via **Staff Manager → [6] Assign staff to research project**.  
The `project_team` table links staff members to projects and stores their **role** on that project (e.g. `principal_investigator`, `analyst`). This is visible in **Staff Manager → [7] View staff member's project roles**.

```
┌──────────────────────┬──────────────────────────┬─────────────────────┐
│ Research Project     │ Assigned Role             │ Last Update         │
├──────────────────────┼──────────────────────────┼─────────────────────┤
│ Oncology Study Alpha │ PRINCIPAL INVESTIGATOR    │ 2024-02-01 09:15    │
│ Genome Mapping Beta  │ ANALYST                   │ 2024-04-03 14:22    │
└──────────────────────┴──────────────────────────┴─────────────────────┘
```

### All relationships at once — Full sample details

**Sample Manager → [6] View full sample details** calls `repo.get_full(code)` which eager-loads all related objects. The output panel shows all four relationship levels for a single sample:

```
╔══════════════════════════════════════════════════════╗
║    FULL DOMAIN GRAPH MAP: SMP-001                   ║
╠══════════════════════════════════════════════════════╣
║ 🔬 SAMPLE CORE PROPERTIES                          ║
║   Code: SMP-001 | Volume: 5.00 mL                  ║
║   Extraction Date: 2024-01-10 | Status: ANALYZED   ║
║                                                      ║
║ 🧑 1:N RELATIONSHIP (Patient)                       ║
║   Patient: John Doe (PAT-001)                       ║
║                                                      ║
║ 🛡️ 1:1 RELATIONSHIP (Quality Control)               ║
║   Result: APPROVED                                   ║
║   Purity: 98.5% | Concentration: 142.3 ng/μL       ║
║                                                      ║
║ 🧬 N:M RELATIONSHIP (Protocols Applied)             ║
║   Standard Extraction (PROT-01), Cold Chain (PROT-03)║
║                                                      ║
║ 📊 N:M WITH ATTRIBUTES (Research Projects)          ║
║   • Oncology Study Alpha (Assigned on: 2024-02-14)  ║
╚══════════════════════════════════════════════════════╝
```

---

## 📋 User Stories

<details>
<summary><strong>View full backlog (6 stories)</strong></summary>

| ID    | Story                                                                            | Priority |
| ----- | -------------------------------------------------------------------------------- | -------- |
| US-01 | As a technician, I want to **register a donor** with a unique anonymized code    | 🔴 High   |
| US-02 | As a technician, I want to **register a sample** linked to a donor and container | 🔴 High   |
| US-03 | As a QC technician, I want to **register the quality report** for a sample       | 🔴 High   |
| US-04 | As a technician, I want to **assign handling protocols** to each sample          | 🟡 Medium |
| US-05 | As a researcher, I want to **assign samples to projects** with quantity and date | 🔴 High   |
| US-06 | As a technician, I want to **log temperature readings** from the freezer         | 🔴 High   |

</details>

---

<div align="center">

[![Footer](https://capsule-render.vercel.app/api?type=waving&color=0:0095ff,100:00d4a8&height=100&section=footer&animation=fadeIn)](https://github.com/Arnaudevv/Biotrack)

CFGS DAM · Data Access · 2025–2026 · Built with 🧬 & SQLAlchemy

</div>