# Setup questions

Used by the `nogamy-project-setup` skill. One at a time, in order, with options where listed. The target is the file and section the answer is written to: `PROJECT.md` (identity, environment names, people) or `_context/platform.md` (§n, the technical profile).
A question already answered by a document is not asked: the answer is shown with its source.

## A. The project → `PROJECT.md` → Identity, People and roles; `platform.md` §1

| # | Question | Options / notes |
|---|---|---|
| A0 | Client name, and a short project id (kebab-case, e.g. `acme-hr`)? Which client words must never leave the project (org name, Git org, system and product names)? | → `PROJECT.md` → `Client`, `Project id`, `Never in feedback` |
| A1 | What is built, for whom, and what is the first scope? | free text, 2–3 lines |
| A2 | Does it replace an existing system? Which? | none · a BI tool · an older DWH · reports and Excel |
| A3 | Who fills each role: architect, data engineer, systems analyst, BI developer, client contact? Who decides architecture? Who approves core updates? | roles → `PROJECT.md` → People and roles; e-mail and access → `_context/people-and-access.md` (never a phone) |
| A4 | In which language are business descriptions, synonyms and rules written? | Hebrew (default) · English · other |
| A5 | Does the client have standards we must follow (naming, security, Git, deployment)? Where are they? | documents → `_private/raw/reference/` |
| A6 | Usage telemetry for this project: on, anonymous, or off? | on (default) · anonymous · off → `PROJECT.md` → `Telemetry` (`nogamy/docs/telemetry.md`) |

## B. The stack → §2

| # | Question | Options / notes |
|---|---|---|
| B1 | Which data platform: database or warehouse engine, and which version or tier? | Fabric · SQL Server / Azure SQL · Snowflake · Databricks · PostgreSQL · BigQuery · Oracle · other → `PROJECT.md` → `Platform`. A platform with a core pack (`nogamy/packs/`) → offer `nogamy-add-pack`. A core reference (`references/<platform>.md`) → note it in §2 |
| B2 | Is it case sensitive, in names and in data? | yes · no · not known → verify in the docs |
| B3 | Which tool brings data from the sources (ingestion / ETL)? | |
| B4 | What orders and schedules the runs? | the ETL tool itself · a scheduler · an orchestration tool |
| B5 | Where is the business logic written? | SQL views and procedures in the database (method default) · a transformation tool · inside the ETL tool |
| B6 | Which BI tool, and does it have a semantic layer saved as text? | |
| B7 | Where is the official documentation? Can the AI tool reach it (web, a docs connector / MCP)? | sets how `nogamy-platform-watch` verifies facts |
| B8 | Is the architecture decided, by whom, and where is it written? | decided → `architecture.md` · open → `open-questions.md`, owner = architect |

## C. Environments → §3

| # | Question | Options / notes |
|---|---|---|
| C1 | Which environments exist, and what is each called (workspace / database / server)? | DEV / TEST / PROD · DEV / PROD · only PROD · other → names in `PROJECT.md` → Environments |
| C2 | Which data is in DEV and in TEST? | real · masked · test data |
| C3 | Who can change each environment? | roles per environment |
| C4 | Do the environments share resources (one server, one capacity)? | affects when heavy runs are allowed |

## D. Code and Git → §4

| # | Question | Options / notes |
|---|---|---|
| D1 | Where does the code live? | the client's Git · Nogamy's Git · no Git yet (then: local repo, and who backs it up) |
| D2 | Which provider, and what is the repo address? | GitHub · Azure DevOps · GitLab · Bitbucket · other |
| D3 | How is the repo reached? Any network limit? | open · VPN · IP allow list · client machine only |
| D4 | Is the main branch protected? Who approves a PR? Are there automatic checks (CI)? | |
| D5 | Does the platform sync with Git by itself, and is that usable here? | yes, used · exists but blocked (why) · no |
| D6 | If not: how does a definition get from the tool into a file, and from a file back into the tool? | export / import · an API · copy by hand · the repo is written first and the tool is filled from it |
| D7 | What can be kept as text: database objects, ETL items, the BI model, reports? | per kind: yes (format) · no |
| D8 | What cannot be kept in Git (connections, permissions, schedules, secrets), and where is each recorded instead? | |
| D9 | Who commits, who pushes, who opens the PR? | default: the AI commits only when asked and never pushes; a person pushes and opens the PR |
| D10 | Is anything forbidden from leaving the client's network (code, metadata, documents)? | decides what an AI tool may be shown at all |

## E. Promotion between environments → §5, §6

For each hop (to DEV, DEV → TEST, TEST → PROD):

| # | Question | Options / notes |
|---|---|---|
| E1 | How does a change reach this environment? | **manual**: a person runs the scripts in order · **platform tool**: the platform's deployment feature · **CI/CD**: a pipeline or runner from the main branch · not decided |
| E2 | What starts it, and who? | automatic after a merge · a deliberate click · a request to another team |
| E3 | From where is it deployed? | the main branch only (method default) · a release branch or tag · the previous environment |

Once for the project:

| # | Question | Options / notes |
|---|---|---|
| E4 | How do database changes move? | numbered migrations + object files (method default) · a state-compare tool · the platform's deployment · scripts by hand with no log (then: add the log) |
| E5 | How do ETL items and the BI model move? | export / import · the platform's deployment · CI/CD · rebuilt by hand |
| E6 | Where do values that differ per environment live (servers, IDs, paths)? | a parameter file · a variable set · a config table · typed into the items today (then: an open question, it must change) |
| E7 | How do config rows and grants reach an environment? | default: `scripts/seed/`, `scripts/grants/`, after the migrations |
| E8 | What is backed up before a risky PROD change, and how is a deploy rolled back? | |
| E9 | Is there a release window, a freeze, or an approval outside the team? | |
| E10 | Who checks an environment after a deploy, and with what? | default: the test document in `qa/deploy/`, filled per environment |

## F. Data sensitivity → §8

| # | Question | Options / notes |
|---|---|---|
| F1 | Is there personal or otherwise sensitive data in scope? | none · personal · financial · medical · classified |
| F2 | May an AI tool see data values at all? | no values, structure and counts only (method default) · values of non-sensitive columns · test data only |
| F3 | Which rules apply (regulation, the client's security policy)? | documents → `_private/raw/reference/` |

## G. The AI → §7

| # | Question | Options / notes |
|---|---|---|
| G1 | Which AI tools are approved for this project? By whom? | a coding agent with repo access · a chat tool only · none yet (then: who approves) |
| G2 | What can the AI run by itself in DEV? | **L0** nothing, a person runs and pastes · **L1** SQL read · **L2** SQL write · **L3** also publish and run ETL items |
| G3 | As which identity does it connect, with which role? | its own account (preferred) · the developer's account |
| G4 | What is the exact command or tool for running a query? For running an ETL item? | becomes an entry in `tools/README.md` |
| G5 | Is any approval pending (information security, licences)? What works until then? | usually: L0 until approved |
| G6 | May the AI reach the internet and the official docs from this environment? | |

## H. Method and working style → `nogamy-method`, `working-agreement.md`

| # | Question | Options / notes |
|---|---|---|
| H1 | Does the project follow Nogamy's base method as is? Known deviations? | each deviation → `_context/architecture.md` → Deviations from the base, with reason and who decided; a rule that binds the agents also → `PROJECT.md` → Project rules |
| H2 | Layers and schemas: the method's, or the client's own? | `BRONZE / SILVER / GOLD / MNG` (default) · other names · fewer layers |
| H3 | Is there a naming convention of the client to adopt? | none · yes (document) → `nogamy-naming`, source column **C** |
| H4 | How does the project lead want to work with the AI: plan approval, depth of explanation, format of deliverables? | differences from the defaults → `working-agreement.md` |
| H5 | How often should platform facts be re-checked? | daily (fast-moving cloud platform) · weekly · monthly |
