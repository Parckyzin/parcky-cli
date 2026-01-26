# Diagrams: Architecture and Workflows

This document provides Mermaid diagrams for architecture and CLI workflows.

## Architecture Overview (Layers and Dependencies)

```mermaid
flowchart LR
%% ========= Nodes =========
    CLI["cli/<br/>(Typer + Rich)"]
    Services["services/<br/>Use cases"]
    Pipelines["pipelines/<br/>Context builder"]
    Core["core/<br/>Domain + interfaces"]
    Infra["infrastructure<br/>Integrations"]
    Config["config<br/>settings + cache + prompts"]

    subgraph External Systems
        AI["AI Providers"]
        GH["GitHub"]
        GIT["Git"]
    end

%% ========= Main flow =========
    CLI --> Services
    Services --> Pipelines
    Pipelines --> Core
    Services --> Core
    Services --> Infra
    Infra --> Core

%% ========= Support =========
    Config -.-> CLI
    Config -.-> Services
    Config -.-> Pipelines
    Config -.-> Infra

%% ========= External =========
    Infra --> AI
    Infra --> GH
    Infra --> GIT

%% ========= Styling =========
    classDef layer fill:#0b0f19,stroke:#3b4252,stroke-width:1px,color:#e5e9f0,rx:10,ry:10;
    classDef domain fill:#0b0f19,stroke:#88c0d0,stroke-width:1px,color:#e5e9f0,rx:10,ry:10;
    classDef infra fill:#0b0f19,stroke:#a3be8c,stroke-width:1px,color:#e5e9f0,rx:10,ry:10;
    classDef support fill:#0b0f19,stroke:#b48ead,stroke-width:1px,color:#e5e9f0,rx:10,ry:10;
    classDef external fill:#0b0f19,stroke:#d08770,stroke-width:1px,color:#e5e9f0,rx:10,ry:10;

    class CLI,Services,Pipelines layer;
    class Core domain;
    class Infra infra;
    class Config support;
    class AI,GH,GIT external;


```

## High-Level Workflows (per command)

### smart-commit

```mermaid
flowchart LR
    A["User runs smart-commit"] --> B["CLI collects flags + confirms"]
    B --> C["SmartCommitService"]
    C --> D["GitRepository: staged diff"]
    C --> E["Pipelines: build commit context<br/>(truncation + notes)"]
    C --> F["AIService: generate commit msg"]
    F --> G["CLI preview + confirm"]
    G --> H["GitRepository: commit + optional push"]

```

### smart-commit-all

```mermaid
flowchart
    A["User runs smart-commit"] --> B["CLI collects flags + confirms"]
    B --> C["SmartCommitService"]
    C --> D["GitRepository: staged diff"]
    C --> E["Pipelines: build commit context<br/>(truncation + notes)"]
    C --> F["AIService: generate commit msg"]
    F --> G["CLI preview + confirm"]
    G --> H["GitRepository: commit + optional push"]

```

### create-pr

```mermaid
flowchart LR
    A["User runs create-pr"] --> B["CLI collects flags"]
    B --> C["CreatePRService"]
    C --> D["GitRepository: branch info<br/>(commits, stats, patches)"]
    C --> E["Pipelines: build PRContext<br/>(truncation + notes)"]
    C --> F["AIService: generate PR title/body"]
    F --> G["CLI preview + confirm"]
    G --> H["GitHub PR service (gh)"]

```

### config (provider/model/settings)

```mermaid
flowchart LR
    A["User runs config"] --> B["CLI loads config + sources"]
    B --> C["Render table + prompts"]
    C --> D["Provider selector"]
    C --> E["Model selector<br/>(change provider optional)"]
    C --> F["Edit numeric settings"]
    D --> G["config/writer persists"]
    E --> G
    F --> G

```

## Detailed Sequence: smart-commit

```mermaid
sequenceDiagram
  actor U as User
  participant CLI as cli/
  participant SVC as SmartCommitService
  participant GIT as GitRepository
  participant PIPE as pipelines/
  participant AI as AIService

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
sequenceDiagram
  actor U as User
  participant CLI as cli/
  participant SVC as SmartCommitAllService
  participant GIT as GitRepository
  participant PIPE as pipelines/
  participant AI as AIService

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
