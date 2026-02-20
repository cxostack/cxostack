# CxO Project File Convention
> How CTO and CMO outputs connect within a project

projects/{slug}/
├── spec.md                  # CTO — what we're building and why
├── RESEARCH.md              # CTO — market + technical research
│                              CMO reads this before writing GTM
├── architecture.md          # CTO — technical design
├── DECISIONS.md             # CTO — every technical/product decision
├── phase-plan.md            # CTO/Planner — phased task breakdown
│
├── GTM.md                   # CMO — go-to-market strategy
├── CONTENT-PLAN.md          # CMO — content calendar + templates
├── MARKETING-DECISIONS.md   # CMO — every marketing decision
│
├── CROSSTEAM.md             # Any CxO — flags for other CxOs to read
│                              e.g. CMO finds competitor feature gap → flags CTO
│                              e.g. CTO picks slow stack → flags CMO to set expectations
│
├── phases/
│   └── phase-{n}.md         # QA bug reports per phase
│
├── usecases/
│   └── {usecase}.md         # Dev context files
│
└── campaigns/
    └── {goal}-{date}.md     # CMO campaign plans


~/.cxostack/                    # Persistent across ALL projects
├── founder-profile.md       # Shared by all CxOs — read first always
├── cto-memory.md            # Tech preferences, stack defaults, past projects
└── cmo-memory.md            # Channel history, brand voice, audience knowledge
