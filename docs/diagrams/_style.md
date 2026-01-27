# Mermaid Style Tokens

Style version: v1

Use this file as the single source of truth for Mermaid diagram styling.

## Flowchart Block (classDef)

Copy this block **verbatim** into every flowchart diagram:

```
%% Style: docs/diagrams/_style.md (v1)
classDef user fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;
classDef cli fill:#F1F5F9,stroke:#94A3B8,stroke-width:1px,rx:8,ry:8,color:#0F172A;
classDef service fill:#E0F2FE,stroke:#7DD3FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
classDef pipeline fill:#E0E7FF,stroke:#A5B4FC,stroke-width:1px,rx:8,ry:8,color:#0F172A;
classDef core fill:#ECFCCB,stroke:#A3E635,stroke-width:1px,rx:8,ry:8,color:#0F172A;
classDef infra fill:#FFE4E6,stroke:#FDA4AF,stroke-width:1px,rx:8,ry:8,color:#0F172A;
classDef config fill:#F5F3FF,stroke:#C4B5FD,stroke-width:1px,rx:8,ry:8,color:#0F172A;
classDef external fill:#FFF7ED,stroke:#FDBA74,stroke-width:1px,rx:8,ry:8,color:#0F172A;
classDef note fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1px,rx:8,ry:8,color:#0F172A;
```

## Sequence Diagram Init Block

Use this init block at the top of every sequence diagram:

```
%%{init: {'theme':'base','themeVariables':{'fontFamily':'Inter, ui-sans-serif, system-ui','lineColor':'#94A3B8','primaryBorderColor':'#CBD5E1','primaryTextColor':'#0F172A','actorTextColor':'#0F172A','actorBorderColor':'#CBD5E1','actorBkg':'#F8FAFC','noteBkg':'#F8FAFC','noteBorderColor':'#CBD5E1'}}}%%
%% Style: docs/diagrams/_style.md (v1)
```

## Usage Rules

- Keep IDs simple; use quoted labels for readable names.
- Use `<br/>` for line breaks (not `\n`).
- Flowcharts should prefer Left → Right direction.
- Dotted edges are only for support relationships (e.g., config).
