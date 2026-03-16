<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:00d4a8,100:0095ff&height=200&section=header&text=BioTrack&fontSize=72&fontColor=ffffff&fontAlignY=38&desc=Biological+Sample+Management+System+for+Biobanks&descAlignY=58&descSize=16&animation=fadeIn" width="100%"/>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Space+Mono&size=16&pause=1000&color=00D4A8&center=true&vCenter=true&width=600&lines=Biological+sample+traceability;Donor+→+Sample+→+Research+Project;Built+with+SQLAlchemy+%2B+Docker;CFGS+DAM+·+Data+Access+2025–2026" alt="Typing animation" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Ubuntu-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Status-In%20development-FFB400?style=for-the-badge"/>
</p>

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

| Module | Description | Priority |
|--------|-------------|----------|
| 🧑‍🔬 **Donors** | Register, edit and deactivate donors with a unique anonymized code | 🔴 High |
| 🧫 **Samples** | Track plasma, DNA, tissue... with type and container | 🔴 High |
| 📊 **Quality Control** | 1:1 report per sample — purity, concentration, result | 🔴 High |
| 📋 **Protocols** | N:M assignment of handling protocols per sample | 🟡 Medium |
| 🔭 **Research Projects** | N:M assignment with consumed quantity and status | 🔴 High |
| 🌡️ **Temperature Log** | Historical freezer readings per sample | 🔴 High |

---

## 🛠️ Tech Stack

```python
stack = {
    "language":  "Python 3.x",
    "ORM":       "SQLAlchemy",   # ✅ confirmed
    "database":  "PostgreSQL",   # ✅ in Docker (Ubuntu)
    "container": "Docker",       # ✅ confirmed
    "UI":        "⏳ TBD",
}
```

<details>
<summary><b>📦 Docker Infrastructure</b></summary>

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
│           BioTrack          │
└─────────────────────────────┘
```

</details>

---

## 🗃️ Data Model

<details>
<summary><b>View table schema</b></summary>

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

---

## 📋 User Stories

<details>
<summary><b>View full backlog (6 stories)</b></summary>

| ID | Story | Priority |
|----|-------|----------|
| US-01 | As a technician, I want to **register a donor** with a unique anonymized code | 🔴 High |
| US-02 | As a technician, I want to **register a sample** linked to a donor and container | 🔴 High |
| US-03 | As a QC technician, I want to **register the quality report** for a sample | 🔴 High |
| US-04 | As a technician, I want to **assign handling protocols** to each sample | 🟡 Medium |
| US-05 | As a researcher, I want to **assign samples to projects** with quantity and date | 🔴 High |
| US-06 | As a technician, I want to **log temperature readings** from the freezer | 🔴 High |

</details>

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0095ff,100:00d4a8&height=100&section=footer&animation=fadeIn" width="100%"/>
</p>

<p align="center">
  <sub>CFGS DAM · Data Access · 2025–2026 &nbsp;·&nbsp; Built with 🧬 &amp; SQLAlchemy</sub>
</p>
