# Diagrams: Architecture and Workflows

This document provides Mermaid diagrams for architecture and CLI workflows.

## Architecture Overview (Layers and Dependencies)

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontFamily':'Inter, ui-sans-serif, system-ui','primaryColor':'#F8FAFC','primaryTextColor':'#0F172A','primaryBorderColor':'#CBD5E1','lineColor':'#94A3B8','clusterBkg':'#F8FAFC','clusterBorder':'#CBD5E1'}}}%%
%% Style: docs/diagrams/_style.md (v1)
flowchart LR
    cli["cli/<br/>(Typer + Rich)<br/>UI only"]
    svc["services/<br/>Use cases"]
    pipe["pipelines/<br/>AI context source of truth"]
    core["core/<br/>Domain models & interfaces"]
    infra["infrastructure/<br/>External integrations"]
    cfg["config/<br/>loader · writer · cache · prompts"]

    subgraph ext["External Systems"]
        ai["AI Providers<br/>(openai · anthropic · gemini · local)"]
        gh["GitHub CLI / API"]
        git["Git"]
    end

    cli --> svc
    cli -.-> infra
    svc --> pipe
    svc --> core
    pipe --> core
    svc --> infra
    infra --> core

    cfg -.-> cli
    cfg -.-> svc
    cfg -.-> pipe
    cfg -.-> infra

    infra --> ai
    infra --> gh
    infra --> git

    rules["Rules:<br/>- No business logic in CLI<br/>- Pipelines = source of truth<br/>- No Rich/Typer in core/services/pipelines"]
    cli --- rules

    classDef user fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef cli fill:#F1F5F9,stroke:#94A3B8,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef service fill:#E0F2FE,stroke:#7DD3FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef pipeline fill:#E0E7FF,stroke:#A5B4FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef core fill:#ECFCCB,stroke:#A3E635,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef infra fill:#FFE4E6,stroke:#FDA4AF,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef config fill:#F5F3FF,stroke:#C4B5FD,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef external fill:#FFF7ED,stroke:#FDBA74,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef note fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;

    class cli cli;
    class svc service;
    class pipe pipeline;
    class core core;
    class infra infra;
    class cfg config;
    class ai,gh,git external;
    class rules note;
```

## High-Level Workflows (per command)

### smart-commit

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontFamily':'Inter, ui-sans-serif, system-ui','primaryColor':'#F8FAFC','primaryTextColor':'#0F172A','primaryBorderColor':'#CBD5E1','lineColor':'#94A3B8'}}}%%
%% Style: docs/diagrams/_style.md (v1)
flowchart LR
    u1["User runs smart-commit"] --> cli1["CLI collects flags + confirms"]
    cli1 --> svc1["SmartCommitService"]
    svc1 --> git1["GitRepository: staged diff"]
    svc1 --> pipe1["Pipelines: build commit context<br/>(truncation + notes)"]
    svc1 --> ai1["AIService: generate commit msg"]
    ai1 --> cli2["CLI preview + confirm"]
    cli2 --> git2["GitRepository: commit + optional push"]

    classDef user fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef cli fill:#F1F5F9,stroke:#94A3B8,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef service fill:#E0F2FE,stroke:#7DD3FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef pipeline fill:#E0E7FF,stroke:#A5B4FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef core fill:#ECFCCB,stroke:#A3E635,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef infra fill:#FFE4E6,stroke:#FDA4AF,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef config fill:#F5F3FF,stroke:#C4B5FD,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef external fill:#FFF7ED,stroke:#FDBA74,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef note fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;

    class u1 user;
    class cli1,cli2 cli;
    class svc1 service;
    class pipe1 pipeline;
    class git1,git2,ai1 infra;
```

### smart-commit-all

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontFamily':'Inter, ui-sans-serif, system-ui','primaryColor':'#F8FAFC','primaryTextColor':'#0F172A','primaryBorderColor':'#CBD5E1','lineColor':'#94A3B8'}}}%%
%% Style: docs/diagrams/_style.md (v1)
flowchart LR
    u2["User runs smart-commit"] --> cli3["CLI collects flags + confirms"]
    cli3 --> svc2["SmartCommitService"]
    svc2 --> git3["GitRepository: staged diff"]
    svc2 --> pipe2["Pipelines: build commit context<br/>(truncation + notes)"]
    svc2 --> ai2["AIService: generate commit msg"]
    ai2 --> cli4["CLI preview + confirm"]
    cli4 --> git4["GitRepository: commit + optional push"]

    classDef user fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef cli fill:#F1F5F9,stroke:#94A3B8,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef service fill:#E0F2FE,stroke:#7DD3FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef pipeline fill:#E0E7FF,stroke:#A5B4FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef core fill:#ECFCCB,stroke:#A3E635,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef infra fill:#FFE4E6,stroke:#FDA4AF,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef config fill:#F5F3FF,stroke:#C4B5FD,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef external fill:#FFF7ED,stroke:#FDBA74,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef note fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;

    class u2 user;
    class cli3,cli4 cli;
    class svc2 service;
    class pipe2 pipeline;
    class git3,git4,ai2 infra;
```

### create-pr

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontFamily':'Inter, ui-sans-serif, system-ui','primaryColor':'#F8FAFC','primaryTextColor':'#0F172A','primaryBorderColor':'#CBD5E1','lineColor':'#94A3B8'}}}%%
%% Style: docs/diagrams/_style.md (v1)
flowchart LR
    u3["User runs create-pr"] --> cli5["CLI collects flags"]
    cli5 --> svc3["CreatePRService"]
    svc3 --> git5["GitRepository: branch info<br/>(commits, stats, patches)"]
    svc3 --> pipe3["Pipelines: build PRContext<br/>(truncation + notes)"]
    svc3 --> ai3["AIService: generate PR title/body"]
    ai3 --> cli6["CLI preview + confirm"]
    cli6 --> gh1["GitHub PR service (gh)"]

    classDef user fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef cli fill:#F1F5F9,stroke:#94A3B8,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef service fill:#E0F2FE,stroke:#7DD3FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef pipeline fill:#E0E7FF,stroke:#A5B4FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef core fill:#ECFCCB,stroke:#A3E635,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef infra fill:#FFE4E6,stroke:#FDA4AF,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef config fill:#F5F3FF,stroke:#C4B5FD,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef external fill:#FFF7ED,stroke:#FDBA74,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef note fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;

    class u3 user;
    class cli5,cli6 cli;
    class svc3 service;
    class pipe3 pipeline;
    class git5,ai3,gh1 infra;
```

### config (provider/model/settings)

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontFamily':'Inter, ui-sans-serif, system-ui','primaryColor':'#F8FAFC','primaryTextColor':'#0F172A','primaryBorderColor':'#CBD5E1','lineColor':'#94A3B8'}}}%%
%% Style: docs/diagrams/_style.md (v1)
flowchart LR
    u4["User runs config"] --> cli7["CLI loads config + sources"]
    cli7 --> ui1["Render table + prompts"]
    ui1 --> prov["Provider selector"]
    ui1 --> mod["Model selector<br/>(change provider optional)"]
    ui1 --> edit["Edit numeric settings"]
    prov -.-> cfgw["config/writer persists"]
    mod -.-> cfgw
    edit -.-> cfgw

    classDef user fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef cli fill:#F1F5F9,stroke:#94A3B8,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef service fill:#E0F2FE,stroke:#7DD3FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef pipeline fill:#E0E7FF,stroke:#A5B4FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef core fill:#ECFCCB,stroke:#A3E635,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef infra fill:#FFE4E6,stroke:#FDA4AF,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef config fill:#F5F3FF,stroke:#C4B5FD,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef external fill:#FFF7ED,stroke:#FDBA74,stroke-width:1px,rx:8,ry:8,color:#0F172A;
    classDef note fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;

    class u4 user;
    class cli7 cli;
    class ui1,prov,mod,edit cli;
    class cfgw config;
```

## Detailed Sequence: smart-commit

```mermaid
%%{init: {
  "theme": "dark",
  "themeVariables": {
    "fontFamily": "Inter, ui-sans-serif, system-ui",
    "lineColor": "#94A3B8",

    "primaryColor": "#0b0f19",
    "secondaryColor": "#0b0f19",
    "tertiaryColor": "#0b0f19",

    "primaryTextColor": "#E5E9F0",
    "secondaryTextColor": "#E5E9F0",
    "tertiaryTextColor": "#E5E9F0",

    "actorBkg": "#F8FAFC",
    "actorBorder": "#CBD5E1",
    "actorTextColor": "#0F172A",

    "noteBkgColor": "#0b0f19",
    "noteTextColor": "#E5E9F0",
    "noteBorderColor": "#3b4252",

    "activationBkgColor": "#0b0f19",
    "activationBorderColor": "#3b4252"
  }
}}%%
%% Style: docs/diagrams/_style.md (v1)
sequenceDiagram
    actor U as "User"
    participant CLI as "cli/"
    participant SVC as "SmartCommitService"
    participant GIT as "GitRepository"
    participant PIPE as "pipelines/"
    participant AI as "AIService"

    U->>CLI: smart-commit
    CLI->>SVC: run command
    SVC->>GIT: get staged diff
    GIT-->>SVC: GitDiff
    SVC->>PIPE: build commit context
    PIPE-->>SVC: context + truncation notes
    SVC->>AI: generate commit message
    AI-->>SVC: commit message
    SVC-->>CLI: result + preview data
    CLI->>U: preview + confirm
    U-->>CLI: confirm
    CLI->>GIT: commit (+ optional push)

```

## Detailed Sequence: smart-commit-all

```mermaid
%%{init: {
  "theme": "dark",
  "themeVariables": {
    "fontFamily": "Inter, ui-sans-serif, system-ui",
    "lineColor": "#94A3B8",

    "primaryColor": "#0b0f19",
    "secondaryColor": "#0b0f19",
    "tertiaryColor": "#0b0f19",

    "primaryTextColor": "#E5E9F0",
    "secondaryTextColor": "#E5E9F0",
    "tertiaryTextColor": "#E5E9F0",

    "actorBkg": "#F8FAFC",
    "actorBorder": "#CBD5E1",
    "actorTextColor": "#0F172A",

    "noteBkgColor": "#0b0f19",
    "noteTextColor": "#E5E9F0",
    "noteBorderColor": "#3b4252",

    "activationBkgColor": "#0b0f19",
    "activationBorderColor": "#3b4252"
  }
}}%%
%% Style: docs/diagrams/_style.md (v1)
sequenceDiagram
    actor U as User
    participant CLI as "cli/"
    participant SVC as "SmartCommitAllService"
    participant GIT as "GitRepository"
    participant PIPE as "pipelines/"
    participant AI as "AIService"

    U->>CLI: smart-commit-all
    CLI->>SVC: run command
    SVC->>GIT: get working diff + staged info
    GIT-->>SVC: files + diff
    SVC->>PIPE: build grouping context
    PIPE-->>SVC: deterministic groups + notes
    SVC->>AI: generate commit messages per group
    AI-->>SVC: messages
    SVC-->>CLI: groups + explain/dry-run
    CLI->>U: render groups + confirm
    U-->>CLI: confirm
    CLI->>GIT: apply commits + optional push

```
