# OpenHands hosting: multi-user vs single-user, licensing, and sandbox/runtime options (state as of 1 Oct 2026)

Method note: docs.openhands.dev, openhands.dev and runtime.all-hands.dev were blocked by this sandbox's egress proxy, so the documentation was read from its source repo (github.com/OpenHands/docs, commit 84ac94d, 2026-10-01). Each docs claim below links the public docs.openhands.dev URL that the .mdx file is published at (Mintlify path = file path). Code was read from shallow clones made on 2026-10-01: OpenHands/OpenHands a8c0558, OpenHands/software-agent-sdk 53a4bc5, OpenHands/enterprise bf4139f, OpenHands/OpenHands-Cloud 5c4729b, OpenHands/sandbox-server 4abe6a4 (2026-09-28), OpenHands/legacy ee9e78b (2026-07-25). OpenHands/runtime-api could not be cloned anonymously (it asked for credentials), so it appears to be private.

**The big change in 2026, which older blog posts and LLM memory will get wrong:** the `OpenHands/OpenHands` repo is no longer the Python monorepo with a React GUI plus an `enterprise/` directory. Since mid-2026 it holds **Agent Canvas**, a TypeScript/React frontend and launcher. Agent execution moved to `OpenHands/software-agent-sdk` (Agent Server, SDK, workspaces), and multi-tenant code moved to the separate `OpenHands/enterprise` and `OpenHands/OpenHands-Cloud` repos. The old monorepo, including the old "Local GUI" and V0 "runtimes", is frozen in `OpenHands/legacy`. Anything about `openhands-ai`, `RUNTIME=docker|remote|daytona|modal|e2b|runloop`, or the in-repo `enterprise/` directory describes the deprecated V0 or V1 Local GUI.

## Q1. Does open-source OpenHands support multiple users, where do the multi-tenant features live, under what license, and can UW run them for free beta users?

### Takeaway
No. Open-source OpenHands (Agent Canvas + Agent Server, MIT) is officially documented as single-user / single-tenant. Its only access control is one shared session API key, with no accounts, no per-user settings or secrets, and no tenant isolation. Accounts, login (Keycloak / GitHub / GitLab / Bitbucket OAuth, SAML), RBAC, organizations and per-user sandboxes live in `OpenHands/enterprise` and `OpenHands/OpenHands-Cloud`. Both are under the **PolyForm Free Trial License 1.0.0**: source-available, not open source, limited to 30 days per calendar year, no redistribution. A university therefore cannot legally run them as a free beta for many users beyond 30 days a year without negotiating a commercial license.

### Cited Findings
**Official single-user statements**
- The FAQ says verbatim: "OpenHands is meant to be run by a single user on their local workstation. It is not appropriate for multi-tenant deployments where multiple users share the same instance. There is no built-in authentication, isolation, or scalability." — [OpenHands FAQ](https://docs.openhands.dev/overview/faqs) (source: [docs repo overview/faqs.mdx](https://github.com/OpenHands/docs/blob/main/overview/faqs.mdx))
- The official Helm chart README says: "Agent Canvas is an **unauthenticated, single-tenant** application. This chart runs exactly that: **one** shared instance where all agents are comingled on the same pod and PVC, with no built-in auth, RBAC for users, or tenant isolation." It also says: "This Helm chart is experimental." — [helm/agent-canvas/README.md](https://github.com/OpenHands/OpenHands/blob/main/helm/agent-canvas/README.md); the same wording is on [Kubernetes (Helm) docs](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/kubernetes)
- The official comparison table ([Enterprise vs. Open Source](https://docs.openhands.dev/enterprise/enterprise-vs-oss)):
  - The Agent Canvas Local and VM backends show "—" for "Authentication & authorization", "Role-based access control" and "Multi-user organizations".
  - "Isolated sandboxes" are "—" for the Local backend and "On Roadmap" for the VM backend.
  - Cloud and Enterprise have all of these; Enterprise RBAC is listed as "✓ Keycloak".
  - "LLM gateway & budgeting" is Enterprise-only ("✓ LiteLLM"), as are SAML and custom runtime images.
  - License row: Open Source / Open Source / Commercial SaaS / Commercial.

**How the open-source Agent Server authenticates**
- Config field `session_api_keys` is documented as: "List of valid session API keys used to authenticate incoming requests. Empty list implies the server will be unsecured. Any key in this list will be accepted…". The listed reason for allowing multiple keys is "to enable key rotation", not per-user identity. — [agent_server/config.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/config.py)
- Public mode works like this: "every `/api/*` call must carry a matching `X-Session-API-Key` header, and the UI requires users to enter the key". A "2 vCPU / 4 GB RAM is plenty for a single user" VM is suggested. — [docs/SELF_HOSTING.md](https://github.com/OpenHands/OpenHands/blob/main/docs/SELF_HOSTING.md)
- Settings are not per user: "Settings, LLM configuration, MCP servers, and automations are all scoped to the active backend". — [Backends docs](https://docs.openhands.dev/openhands/usage/agent-canvas/backends)

**Docs contradiction**
- The SDK architecture page calls `openhands.agent_server` a "Multi-user API server" and lists "Multi-user web apps, SaaS products" as use cases. — [SDK architecture overview](https://docs.openhands.dev/sdk/arch/overview)
- The code (single shared key list, settings per backend) and the FAQ/Helm/comparison docs contradict a literal reading.

**Open proposals to add auth to open-source Canvas (not implemented yet)**
- RFC #17055 (opened 2026-08-31, open) proposes "API-key identity, fixed roles [Read/Run/Admin], scoped service actors… for a single Canvas instance".
  - It explicitly puts these out of scope: "Multi-node tenancy and multi-tenant isolation" and "User accounts, passwords, and SSO/OIDC/SAML".
  - It states the boundary: "OSS owns instance-local roles and actors; enterprise systems may supply organization-scale identity". — [OpenHands#17055](https://github.com/OpenHands/OpenHands/issues/17055)
- Proposal #17635 (opened 2026-09-22, labeled high priority / ready-for-dev):
  - It describes the current model as a "long-lived session API key… stored in plaintext in browser localStorage, where any script on the Canvas origin can read it".
  - It proposes GitHub device-flow login, but **single-owner** per agent-server. — [OpenHands#17635](https://github.com/OpenHands/OpenHands/issues/17635)
- The "Agent Canvas Initiative" issue says open source has "no concept of user identity or authentication, with authorization done through a single shared API key". (Seen in a search-result snippet only; the page was not fetched.) — [OpenHands#14374](https://github.com/OpenHands/OpenHands/issues/14374)

**Where the multi-tenant code lives and its license**
- `OpenHands/enterprise` describes itself as "the source-available, commercially licensed backend codebase for OpenHands Enterprise… with additional enterprise features including authentication, billing, and integrations".
  - It is "licensed under the Polyform Free Trial License. This is **not** an open source license. Usage is limited to 30 days per calendar year without a commercial license."
  - "Contributions from outside, non-OpenHands maintainers are currently not accepted." — [OpenHands/enterprise README](https://github.com/OpenHands/enterprise)
- Its code includes:
  - `server/auth/keycloak_manager.py`, `saas_user_auth.py`, `token_manager.py`
  - `storage/org*.py`, `user_store.py`, `saas_secrets_store.py`, `encrypt_utils.py`, `lite_llm_manager.py`
  - integrations for GitHub, GitLab, Bitbucket (incl. Data Center), Azure DevOps, Jira, Slack and Stripe
  - (observed in [OpenHands/enterprise tree](https://github.com/OpenHands/enterprise/tree/main/server/auth))
- License text (PolyForm Free Trial 1.0.0, © 2026 All Hands AI):
  - "Use of the software for more than 30 days per calendar year is not allowed without a commercial license"
  - "you may not distribute copies of the software"
  - "These terms do not allow you to sublicense or transfer any of your licenses"
  - "Your company" covers the whole organization you work for. — [enterprise/LICENSE](https://github.com/OpenHands/enterprise/blob/main/LICENSE)
- The Helm charts and Replicated installer for self-hosting "OpenHands Cloud" are under the same PolyForm Free Trial license ("This is **NOT** an open source license. Usage is limited to 30 days per calendar year"). These charts "are also used to drive the official, public version of OpenHands Cloud at app.all-hands.dev". — [OpenHands/OpenHands-Cloud README](https://github.com/OpenHands/OpenHands-Cloud)
- Enterprise trial: "Sign up for a free 30-day OpenHands Enterprise trial account" via the Replicated portal. — [Enterprise Quick Start](https://docs.openhands.dev/enterprise/quick-start)
- Organizations (multiple users, shared credits, roles) "is a commercial feature available with an OpenHands Cloud subscription or OpenHands Enterprise". By default conversations are "private to individual members". — [Organizations overview](https://docs.openhands.dev/openhands/usage/cloud/organizations/overview)
- The Helm chart describes OpenHands Enterprise as the paid upgrade path. It adds "Authentication (SSO / SAML / OIDC)", "Role-based access control", "Multi-tenancy so different teams get isolated spaces", and "Isolated agent sandboxes — each agent run gets its own container". — [helm/agent-canvas/README.md](https://github.com/OpenHands/OpenHands/blob/main/helm/agent-canvas/README.md)

**MIT-licensed parts**
- `OpenHands/OpenHands` (Agent Canvas) is MIT: "Copyright © 2025 OpenHands contributors". — [LICENSE](https://github.com/OpenHands/OpenHands/blob/main/LICENSE)
- `OpenHands/software-agent-sdk` is MIT (© 2026). — [LICENSE](https://github.com/OpenHands/software-agent-sdk/blob/main/LICENSE)
- **MIT multi-user scaffolding exists but is incomplete:** `OpenHands/sandbox-server`, described as "the standalone OpenHands API and sandbox control plane… the history-preserving extraction of `openhands/app_server/` from the former `OpenHands/OpenHands` monorepo".
  - It is MIT except any `enterprise/` directory.
  - Its default auth class says: "The default implementation does not support multi tenancy, so user_id is always None".
  - It has pluggable `UserAuth`, user-keyed `SettingsStore` / `SecretsStore`, and sandbox services for Docker, Process, Remote and Kubernetes (agent-sandbox).
  - (Sources: [sandbox-server README](https://github.com/OpenHands/sandbox-server), [default_user_auth.py](https://github.com/OpenHands/sandbox-server/blob/main/openhands/app_server/user_auth/default_user_auth.py), [sandbox/README.md](https://github.com/OpenHands/sandbox-server/blob/main/openhands/app_server/sandbox/README.md))
- History (V0/V1 monorepo, before mid-2026): the same split already existed inside one repo. The root LICENSE said "All content that resides under the enterprise/ directory is licensed under… enterprise/LICENSE" (the same PolyForm Free Trial text), and everything else was MIT. — [OpenHands/legacy](https://github.com/OpenHands/legacy) (snapshot dated 2026-07-25; diff confirms identical license text)

**Pricing**
- No academic, research or nonprofit licensing program was found in the docs, the enterprise repo or the search results. The pricing page (openhands.dev/pricing) was egress-blocked.
- Third-party aggregators say Enterprise has "no per-seat licensing", but this is unconfirmed by a primary source. — [OpenHands Pricing (search snippet)](https://www.openhands.dev/pricing)

### Inferences
- Running OSS Agent Canvas as a shared UW server means every beta user who has the one key shares everything: settings, LLM keys, secrets, conversation history and the host or pod filesystem. In effect every user is an admin of everyone else's agents. This is unacceptable for a "bring your own key" public beta.
- Using the PolyForm-licensed enterprise or OpenHands-Cloud code for a beta lasting more than 30 days a year would require a commercial license from All Hands AI, which must be negotiated. Forking it or redistributing modified copies is not permitted. Unless an academic agreement is obtained, the UW server would have to build its own auth, tenancy and sandbox orchestration, or build on MIT parts only: Agent Canvas, Agent Server, sandbox-server's pluggable `UserAuth` / user-scoped stores, and the k8s agent-sandbox service.
- The MIT `sandbox-server` (a pluggable `UserAuth` interface plus per-user stores plus a per-conversation sandbox service) is the closest open-source starting point for multi-tenancy. Its default is still single-tenant, and the real per-user auth implementation (Keycloak) is in the PolyForm repo.

### Gaps
- Commercial or academic pricing for OpenHands Enterprise / Cloud self-host: openhands.dev/pricing and /enterprise were blocked and no academic program was found. Contacting All Hands AI is needed.
- Whether RFC #17055 or proposal #17635 will land, and when, is unknown. Both are open as of Oct 2026.
- Whether "30 days per calendar year" is counted per installation or per organization is not defined in the license text. The license defines "your company" broadly, which suggests all of UW.

## Q2. Self-hosting: official guidance for running locally and on a server or Kubernetes; resources, Docker-socket security, reverse proxy / TLS

### Takeaway
Local install is `npm i -g @openhands/agent-canvas` (needs Node 24+ and uv), `npx @openhands/agent-canvas`, or the `ghcr.io/openhands/agent-canvas` Docker image (v1.24.0 as of Sep 2026). Server install is a single VM in `--public` mode behind nginx + Let's Encrypt with a firewall, or an experimental single-replica Helm StatefulSet. All official open-source server guidance assumes one trusted user or team. Enterprise has its own Replicated / k0s or Helm installers, with Sysbox sandboxes and published sizing tables (16 vCPU / 64 GB minimum, about 15 concurrent sandboxes).

### Cited Findings
**Local install options (README, Oct 2026)** — [OpenHands README](https://github.com/OpenHands/OpenHands/blob/main/README.md)
- Option 1, "Without a Sandbox": `npm install -g @openhands/agent-canvas && agent-canvas`, with the warning "the agent will have full access to your filesystem!".
- Option 2, "With a Docker Sandbox": `docker run … -p 127.0.0.1:8000:8000 -v $HOME/.openhands:… -v ${PROJECTS_PATH}:/projects ghcr.io/openhands/agent-canvas:1.24.0`. The agent can access only `PROJECTS_PATH`.
- Option 3, "With Multiple Docker Sandboxes": `OH_CONVERSATION_RUNTIME=docker agent-canvas`, so that each new conversation runs "in its own Docker container, with its own Agent Server and tools".
- Option 4: from source with `npm run dev`.

**Network binding and the key**
- "Local (`npx` / `npm run dev`) listeners bind **loopback only** (`127.0.0.1`) so the auto-injected session key is not reachable from other machines". With `--host 0.0.0.0` the key is not injected. — [README](https://github.com/OpenHands/OpenHands/blob/main/README.md)
- The Docker image does not inject the key unless `AGENT_CANVAS_ALLOW_LAN_SESSION_KEY=true` is set. — [README](https://github.com/OpenHands/OpenHands/blob/main/README.md)

**VM self-hosting guide** — [docs/SELF_HOSTING.md](https://github.com/OpenHands/OpenHands/blob/main/docs/SELF_HOSTING.md)
- Steps: provision a VM (Ubuntu 24.04, "2 vCPU / 4 GB RAM is plenty for a single user"); firewall everything except SSH from your IP; `export LOCAL_BACKEND_API_KEY=$(openssl rand -base64 32); npx @openhands/agent-canvas --public`; then optionally nginx + certbot for TLS.
- The ingress at 127.0.0.1:8000 routes `/api/*` and `/sockets` to the agent server (:18000), `/api/automation/*` to the automation backend (:18001), and everything else to the static server (:3001).
- The nginx config must forward WebSocket/SSE headers with `proxy_read_timeout 3600s`.
- Warnings:
  - "The agent server runs **directly on the host** with full access to the machine's filesystem, environment, and network. The firewall… and the `LOCAL_BACKEND_API_KEY` are what stop a stranger from getting that same access."
  - "Treat the VM as you would any machine that holds production credentials."
- Known issue: the bundled OpenVSCode is served under `/vscode` on the same origin, so script on that origin "can read the canvas's `localStorage`, which holds the SESSION API key of _every_ backend registered in that browser". Tracked in [OpenHands#16492](https://github.com/OpenHands/OpenHands/issues/16492).

**Helm chart** — [helm/agent-canvas](https://github.com/OpenHands/OpenHands/tree/main/helm/agent-canvas); [Kubernetes docs](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/kubernetes)
- Chart version 0.1.0, appVersion 1.24.0, Kubernetes ≥1.24.
- Deploys a single-replica StatefulSet with an all-in-one image (frontend + agent-server + automation), a 20Gi RWO PVC for `~/.openhands` and `~/workspace`, an optional Ingress, and optional RBAC (`rbac.enabled`, `rbac.clusterAdmin`).
- "Put it behind an authenticated ingress before exposing it to the internet."
- The pod runs as UID 10001.
- The persisted state on the PVC includes the "auto-generated `OH_SECRET_KEY`, session API key", "encrypted secrets, conversation history", and the automation SQLite DB.

**Remote Modal backend**
- An official guide deploys the Agent Server (`ghcr.io/openhands/agent-server:1.24.0-python`, 2 vCPU / 4 GB) as a Modal app with a Modal Volume for `~/.openhands`.
- Always-on "Costs ~$102/month"; scale-to-zero has "~10-30s cold start".
- Warning: "Anyone with the API key can execute arbitrary code on your Modal container." — [Modal Backend](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/modal)

**Docker socket**
- Option 3 requires "The user starting Canvas must be able to run `docker` commands". — [README](https://github.com/OpenHands/OpenHands/blob/main/README.md)
- The MIT sandbox-server's "Compose setup mounts the Docker socket… so the server can manage sandbox containers". — [sandbox-server README](https://github.com/OpenHands/sandbox-server)
- A user issue states that "mounting the docker socket… is essentially equivalent to granting root control of the host". It was closed as not planned. (The date shown, 2024-11-25, predates the repo transfer.) — [software-agent-sdk#1563](https://github.com/OpenHands/software-agent-sdk/issues/1563)

**Reverse-proxy pitfalls (deprecated Local GUI docs)**
- Each Docker sandbox exposes its ports on "a **randomly assigned host port**", reached via `container_url_pattern` (default `http://localhost:{port}`).
- `AGENT_SERVER_USE_HOST_NETWORK=true` pins ports, but then "Only one sandbox can run at a time".
- "Traefik cannot natively route an arbitrary dynamic port; a regex-based proxy (e.g. nginx) is needed".
- These pages are filed under "Deprecated Projects > Local GUI" in docs.json. — [Docker Sandbox (deprecated Local GUI)](https://docs.openhands.dev/openhands/usage/sandboxes/docker)

**Enterprise resources** — [Enterprise Quick Start](https://docs.openhands.dev/enterprise/quick-start); [Sizing Guide](https://docs.openhands.dev/enterprise/sizing-guide)
- Trial VM: 16 vCPU / 64 GB / 200 GB disk (≤10 ms P99 write latency), Linux x86-64, systemd and root.
- This "comfortably supports about 15 concurrent sandboxes".
- The default sandbox isolation is Sysbox, which "requires **Linux kernel 6.3 or newer**".
- Network: ports 80, 443 and 30000 (admin console), plus outbound access to replicated.app and *.r9.all-hands.dev.
- Per-sandbox planning unit: 0.5 vCPU, 4 GiB RAM, 10 GiB node disk, 10 GiB volume.
- Single VM examples: 5 peak sandboxes (~25 users) → 8 vCPU / 32 GiB; 50 peak sandboxes (~250 users) → 64 vCPU / 256 GiB.
- Helm on existing Kubernetes: separate tainted sandbox node pool (16 vCPU / 64 GiB nodes); 100 peak sandboxes (~500 users) → 1–10 sandbox nodes plus 3 platform nodes and 10 TiB of volumes.

**Deprecation timeline**
- Agent Canvas beta launched 2026-06-03. The `openhands serve` / Docker Local GUI keeps working. The CLI TUI is in maintenance "until October 1, 2026", while headless and ACP modes continue.
- "Local GUI: Support continues until Agent Canvas implements isolated, ephemeral sandboxes". — [OpenHands/docs#657 Agent Canvas transition FAQ](https://github.com/OpenHands/docs/issues/657)
- The docs call the Local GUI "the deprecated Docker-based browser application from the former OpenHands monorepo", with source pinned at OpenHands/legacy. — [Introduction](https://docs.openhands.dev/overview/introduction)

### Inferences
- For deep_reasoner's **localhost option**, the Agent Canvas shape maps well onto the requirement to access local files: loopback bind, an auto-injected key, a Docker mode mounting `PROJECTS_PATH`, and a no-sandbox host mode.
- For the **UW server**, none of the open-source deployment recipes (VM, Helm, Modal) is designed for untrusted strangers. They are designed for one person or one trusted team holding the shared key.
- Any design where the web server can reach the Docker socket gives a server compromise root on the host. On a shared server, sandbox creation should go through an isolated control plane: Kubernetes agent-sandbox with gVisor/Kata, Sysbox, or a remote sandbox provider such as Daytona.

### Gaps
- No official numbers for open-source multi-conversation resource use beyond "2 vCPU / 4 GB … single user".
- Exact launch date of Agent Canvas GA: only the beta date (2026-06-03) is confirmed; the blog "Introducing Agent Canvas" (2026-06-16 per search snippet) was not fetchable.

## Q3. Runtimes / sandboxes as of 2026: what exists in the V1 agent-server/workspace model, how per-user / per-conversation isolation works, network policy, persistence

### Takeaway
"Runtimes" are now "workspaces" (SDK) or "sandboxes" / "backends" (Canvas).

| Open-source option | What runs where | Status / scope |
|---|---|---|
| Host process | Agent Server and tools on the host | No isolation |
| `OH_CONVERSATION_RUNTIME=docker` | One Agent Server container per conversation | |
| `OH_EXECUTION_RUNTIME=docker` | Agent loop and LLM keys on the host; only built-in file/shell tools in an ephemeral container | |
| SDK `DockerWorkspace` | Container | |
| SDK `ApptainerWorkspace` | Apptainer container | |
| SDK `AgentSandboxWorkspace` | Kubernetes pods via kubernetes-sigs/agent-sandbox, with warm pools, pause/resume, gVisor/Kata via RuntimeClass, NetworkPolicy | |
| SDK `APIRemoteWorkspace` | All Hands' hosted, closed Runtime API | |
| SDK `OpenHandsCloudWorkspace` | OpenHands Cloud | |
| Modal | Whole backend on Modal | Deployment recipe, not per-user isolation |

The V0 third-party runtimes (Daytona, Modal, E2B, Runloop) are legacy-only and have no V1 equivalent in the SDK. True per-user isolation (separate sandbox per conversation plus auth) is documented only for Cloud and Enterprise, using Sysbox or Kubernetes plus a closed Runtime API.

### Cited Findings
**Current SDK workspace backends**
- The `openhands.workspace` package "contains workspace implementations… (Docker, Apptainer, cloud, and API-remote)". Subpackages: `docker/`, `apptainer/`, `agent_sandbox/`, `cloud/`, `remote_api/`. — [openhands-workspace](https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-workspace/openhands/workspace)
- A grep of the SDK found no Daytona, E2B, Runloop or Modal sandbox code. The only hits were the words "runloop" and "modal" in unrelated contexts. (Own grep of [software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) at 53a4bc5.)

**Kubernetes `AgentSandboxWorkspace`** — [agent_sandbox README](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-workspace/openhands/workspace/agent_sandbox/README.md)
- "Run the OpenHands agent server inside a Kubernetes pod managed by kubernetes-sigs/agent-sandbox. The pod is claimed from a `SandboxWarmPool`… sub-second starts… native pause/resume… gVisor / Kata isolation is available by setting a `runtimeClass`".
- Configuration is on the cluster side: "Network egress allow-listing belongs in the template's `NetworkPolicy`. Persistent volumes belong in the template's `volumeClaimTemplates`."
- `pause()` means "pod terminated, PVC retained".
- The MIT sandbox-server has a matching `KubernetesSandboxService`. Its docstring: "Each sandbox is a `SandboxClaim`… The per-sandbox session API key is injected as an environment variable on the claim". — [kubernetes_sandbox_service.py](https://github.com/OpenHands/sandbox-server/blob/main/openhands/app_server/sandbox/kubernetes_sandbox_service.py)

**`APIRemoteWorkspace`**
- Docstring: "Remote workspace using OpenHands runtime API. Runtime API: https://runtime.all-hands.dev/".
- Parameters: `runtime_api_url`, `runtime_api_key`, `server_image`, `resource_factor` (1/2/4/8). — [remote_api/workspace.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-workspace/openhands/workspace/remote_api/workspace.py)
- The Runtime API is the Enterprise component for "Sandbox creation, startup, pause, and cleanup". — [Enterprise troubleshooting](https://docs.openhands.dev/enterprise/troubleshooting)
- The `OpenHands/runtime-api` repo was not anonymously clonable, which implies it is private.

**Canvas docker modes**
- Per-conversation Agent Server containers: `OH_CONVERSATION_RUNTIME=docker`. "Each container mounts its conversation's workspace and persisted state… Conversations using the same host workspace still share those files… This setting isolates conversation execution; it does not move the entire Canvas or automation service into a sandbox." — [README](https://github.com/OpenHands/OpenHands/blob/main/README.md)
- The implementation (`agent_server/docker_runtime/`, "Per-conversation Docker runtime support"):
  - mints a per-container `RuntimeIdentity` (conversation_id, api_key, encryption_key, workspace_path)
  - "materializes" secrets before "crossing a runtime boundary"
  - [docker_runtime](https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-agent-server/openhands/agent_server/docker_runtime)
- Tool-only isolation: `OH_EXECUTION_RUNTIME=docker` creates a `DockerExecutionWorkspace` per conversation. The `terminal`, `file_editor`, `grep`, `glob` and `apply_patch` tools run in the container, while "The outer Agent Server continues to run the agent loop and all LLM requests". — [Isolate Tool Execution with Docker](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/docker-execution)
  - Warning: "Tools without a Docker execution adapter continue to run in the outer Agent Server process."
  - The container "Publishes its API only on host loopback", "Receives a generated per-workspace capability instead of the outer server's credentials", "Is removed when its workspace closes", and has no host mounts by default (`OH_EXECUTION_VOLUMES=[]`).

**Canvas isolation-boundary table** — [Agent Canvas architecture](https://docs.openhands.dev/openhands/usage/agent-canvas/architecture)
- Host process = "without container isolation".
- Docker or Kubernetes = "inside the configured container or pod with its mounts and network policy".
- Cloud or Enterprise = "The managed platform creates and operates the conversation sandbox".
- Self-hosted backends may be "in another process, on a VM, in Docker or Kubernetes, or on Modal".
- The open-source "Isolated sandboxes" feature for the VM backend is "On Roadmap". — [Enterprise vs. Open Source](https://docs.openhands.dev/enterprise/enterprise-vs-oss)

**Enterprise isolation model**
- "OpenHands runs each agent session in a sandbox that uses Sysbox for isolation". It is installed via the `sysbox-deploy-k8s` DaemonSet on a dedicated node pool and registers the `sysbox-runc` RuntimeClass. — [Installing Sysbox](https://docs.openhands.dev/enterprise/k8s-install/sysbox)
- Docker-in-sandbox works "without privileged access to your cluster"; it avoids both privileged DinD and host-socket mounting. — [Docker in Sandbox](https://docs.openhands.dev/enterprise/docker-in-sandbox)
- Sandbox grouping: a sandbox can host multiple conversations. Users choose a "Sandbox Grouping Strategy" (No grouping = new sandbox per conversation, Group by newest, LRU, Fewest conversations, Add to any). — [Conversations And Sandboxes](https://docs.openhands.dev/enterprise/conversations-and-sandboxes)
  - "A separate conversation is not a security boundary when it shares a sandbox with another conversation."
  - "Grouping is a placement rule, not a resource scheduler."
- Custom sandbox images can be registered through the Runtime API, "each kept ready in its own warm pool". — [Multiple images & warm pools](https://docs.openhands.dev/enterprise/custom-sandbox-images/multiple-images-warm-pools)

**Legacy runtimes (V0, before mid-2026 / late 2025)**
- Docker (default), OpenHands Remote Runtime (beta), Local, plus "Third-Party Runtimes… when you install the `third_party_runtimes` extra": E2B, Modal, Runloop, Daytona.
- "These third-party runtimes are supported by their respective developers, not by the OpenHands team." — [V0 Runtimes overview](https://docs.openhands.dev/openhands/usage/v0/runtimes/V0_overview)
- The legacy `pyproject.toml` pins optional deps `modal`, `runloop-api-client 0.50.0`, `daytona 0.24.2`, `e2b-code-interpreter ^2.0.0`. — [OpenHands/legacy pyproject.toml](https://github.com/OpenHands/legacy/blob/main/pyproject.toml)
- The V0 Daytona runtime was set via `DAYTONA_API_KEY` and `RUNTIME=daytona`. — [V0 Daytona Runtime](https://docs.openhands.dev/openhands/usage/v0/runtimes/V0_daytona)
- Daytona's announcement (V0 era): "replaces OpenHands' default Docker runtime with Daytona's… isolated, cloud-hosted sandboxes", with "ephemeral environments that are fresh for each session" and preview URLs. — [Daytona blog (search snippet)](https://www.daytona.io/dotfiles/introducing-runtime-for-openhands-secure-ai-code-execution); [OpenHands PR #6863](https://github.com/OpenHands/OpenHands/pull/6863)
- The intermediate "V1 Local GUI" (late 2025 – mid-2026) offered Docker (recommended), Process ("no sandbox isolation") and Remote sandbox providers via the legacy `RUNTIME` env var. It is now under "Deprecated Projects > Local GUI". — [Sandboxes overview (deprecated)](https://docs.openhands.dev/openhands/usage/sandboxes/overview)

**Third-party vendor content (2026)**
- Modal publishes a "Best Code Execution Sandbox for OpenHands in 2026" page. This is marketing and was not fetched. — [modal.com resource](https://modal.com/resources/best-sandbox-openhands)

### Inferences
- A deep_reasoner sub-agent already chooses its own REPL backend (local, RestrictedPython, Daytona). The OpenHands sandbox layer would sit on top of or instead of that. If deep_reasoner uses Daytona for Python execution, the host only orchestrates LLM calls and never runs model code, which is the property the UW server needs.
- The OpenHands tool-only Docker mode (`OH_EXECUTION_RUNTIME`) keeps any custom tool without an adapter running on the host. A custom deep_reasoner REPL tool would not get isolation for free.
- The best MIT-licensed building block for strong multi-user isolation on a UW Kubernetes cluster is kubernetes-sigs/agent-sandbox, with gVisor/Kata, warm pools and NetworkPolicy, used through the SDK's `AgentSandboxWorkspace` or sandbox-server's `KubernetesSandboxService`. The user/auth layer would still need to be built.
- Daytona can no longer be plugged in as an OpenHands "runtime" in V1. It remains usable from inside deep_reasoner itself.

### Gaps
- Whether `OH_CONVERSATION_RUNTIME` and `OH_EXECUTION_RUNTIME` are two coexisting modes or a rename. Both appear in current README/docs and code (`docker_runtime/` and `DockerExecutionWorkspace`); I did not trace the launcher code to confirm.
- No official network-egress policy for open-source Docker modes was found. Default container networking is presumably unrestricted; unconfirmed.
- Runtime API internals and isolation tech (gVisor vs Sysbox) for the hosted Cloud could not be confirmed (private repo; runtime.all-hands.dev blocked).

## Q4. How OpenHands handles bring-your-own LLM keys and git provider tokens (storage, encryption)

### Takeaway
LLM access goes through LiteLLM (`litellm>=1.93.0`), with per-backend "LLM Profiles" (provider, model, base URL, key) set in the UI. Secrets are stored by the Agent Server on disk (`~/.openhands`) and encrypted with Fernet using `OH_SECRET_KEY`; the code calls this "preventing accidental secret disclosure". Without `OH_SECRET_KEY`, secrets are not persisted. Custom secrets and git tokens (e.g. `GITHUB_TOKEN`) are exported as environment variables into the agent's runtime, so the agent and any code it runs can read them. Enterprise stores per-user / per-org secrets in Postgres (Fernet / JWT-service encryption) and runs a LiteLLM proxy for budgets.

### Cited Findings
**LLM settings**
- The SDK depends on `"litellm>=1.93.0"`. — [openhands-sdk/pyproject.toml](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/pyproject.toml)
- The LLM settings page supports "any LLM supported by litellm", custom models via "the specific provider docs on litellm", a `Base URL` field, and "LLM profiles [that] allow you to save multiple LLM configurations and switch between them, even during an active conversation". — [LLM Settings](https://docs.openhands.dev/openhands/usage/settings/llm-settings)

**Secret encryption**
- `OH_SECRET_KEY` is the "Secret key for encrypting sensitive data (LLM API keys, secrets) in stored conversations. **Required for persistence across restarts.**" — [Agent Server README](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/README.md)
- Code warns "OH_SECRET_KEY was not defined. Secrets will not be persisted between restarts". If the env var is absent, the secret key defaults to the session API key. — [config.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/config.py)
- `Cipher` uses `cryptography.fernet.Fernet`. Its docstring: "Simple encryption utility for preventing accidental secret disclosure". Decrypt failures return None. — [cipher.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/utils/cipher.py)
- The Helm chart persists "encrypted secrets" and the auto-generated `OH_SECRET_KEY` on the same PVC. — [Kubernetes docs](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/kubernetes)

**Secrets in the agent environment**
- "All custom secrets are automatically exported as environment variables in the agent's runtime environment". — [Secrets Management](https://docs.openhands.dev/openhands/usage/settings/secrets-settings)
- For ACP agents, "Each credential you enter is saved as a **global secret** whose name is exactly the environment variable the Agent Server exports into the ACP subprocess (e.g. `ANTHROPIC_API_KEY`)". In containers, the start request references secrets as `LookupSecret`, resolved by the agent-server at spawn time. — [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)

**Git provider tokens**
- The Agent Server looks up GitHub tokens from secrets named by the provider token name, `GITHUB_TOKEN`, `GH_TOKEN` or `github`, to call `api.github.com/user/repos`. — [git_provider_service.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/git_provider_service.py)

**Exposure and redaction**
- `_secret_redaction.py` and `_secrets_exposure.py` modules exist in the agent server (names observed; contents not reviewed). — [agent_server directory](https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-agent-server/openhands/agent_server)
- RFC #17055 states its roles would "**not** prevent a Run user from asking an allowed agent to print a credential that the selected server-side profile makes available inside the agent sandbox". — [OpenHands#17055](https://github.com/OpenHands/OpenHands/issues/17055)

**Enterprise**
- `storage/encrypt_utils.py` uses Fernet and a JWT service `encrypt_value`.
- Stores include `saas_secrets_store.py`, `saas_settings_store.py`, `api_key_store.py`, `auth_token_store.py` and `lite_llm_manager.py`.
- `server/constants.py` references `LITELLM_DEFAULT_MODEL` and says "billing margins are now handled internally in litellm". — [OpenHands/enterprise storage](https://github.com/OpenHands/enterprise/tree/main/storage)
- Enterprise lists "LLM gateway & budgeting — ✓ LiteLLM" and "Enforce default LLMs". — [Enterprise vs. Open Source](https://docs.openhands.dev/enterprise/enterprise-vs-oss)
- In Cloud, Organizations "share a pool of credits, use consistent LLM configurations". — [Organizations overview](https://docs.openhands.dev/openhands/usage/cloud/organizations/overview)

### Inferences
- The open-source design puts user keys in the same process or sandbox where model-written code runs (env vars). For a BYOK multi-user server this means:
  - each user's keys must live only in that user's own sandbox;
  - users must accept that their own agent can read their keys;
  - the server-side store must be per-user. The open-source Agent Server store is per-backend, not per-user.
- At-rest encryption is Fernet with a key stored alongside the data (PVC) in Helm deployments. This protects against accidental disclosure, not against host compromise.

### Gaps
- Whether the V1 Agent Server masks secrets in LLM-visible output (the redaction module exists; behavior not verified).
- GitLab / Bitbucket token handling in the open-source Agent Server was not reviewed; only GitHub discovery code was seen.

## Q5. Known institutional / university or third-party multi-user deployments of OpenHands, and lessons learned

### Takeaway
No public university or institutional multi-user deployment of OpenHands was found. The only documented multi-user deployments are All Hands' own OpenHands Cloud (app.all-hands.dev, run from the PolyForm OpenHands-Cloud charts) and commercial Enterprise customers. Community material is mostly single-user hosting guides and hardening advice centered on Docker-socket risk.

### Cited Findings
- The OpenHands-Cloud charts "are also used to drive the official, public version of OpenHands Cloud at app.all-hands.dev". — [OpenHands-Cloud README](https://github.com/OpenHands/OpenHands-Cloud)
- The Helm chart suggests an "internal 'vibecoding' platform" for "a small, trusted group" sharing one deployment, explicitly not for untrusted multi-user use. — [Kubernetes docs](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/kubernetes)
- The Enterprise sizing guide notes "one user can have multiple sandboxes running at one time" and plans capacity on peak concurrent sandboxes, not users. This is a lesson for cost planning. — [Sizing Guide](https://docs.openhands.dev/enterprise/sizing-guide)
- Third-party hardening posts (secondary sources, search snippets only) argue that Docker socket access is "root on the host with extra steps", and that operators should "treat the container as the security boundary, not the UI". — [interconnectd blog](https://interconnectd.com/blog/31/fixing-openhands-hardened-docker-compose-for-production/); [PandaStack](https://www.pandastack.ai/blog/best-openhands-hosting-platforms-2026/)
- A search-result snippet mentions an issue on agent-server containers being unable to resolve `host.docker.internal` in a Docker runtime deployment. The snippet suggested it blocks LAN team-server deployments, but this was not fetched and its status is unconfirmed. — [OpenHands#12229](https://github.com/OpenHands/OpenHands/issues/12229)

### Inferences
- UW would likely be a first mover. Expect to own abuse controls:
  - per-user concurrency caps (the sizing unit is 0.5 vCPU / 4 GiB per sandbox);
  - egress policy, since BYOK keys plus free compute attract crypto-mining or proxy abuse;
  - account gating.
- Cost scales with peak concurrent sandboxes, not registered users.

### Gaps
- No academic deployments, cost reports or abuse post-mortems were found in public sources. The searches returned only unrelated education papers.
- The Enterprise customer list and any academic customers are unknown.

## Q6 (integration path). Can deep_reasoner plug into OpenHands "as a plugin" rather than being rebuilt?

### Takeaway
Yes, most cleanly via the **Agent Client Protocol (ACP)**. Agent Canvas / Agent Server can drive "any stdio ACP server" as a custom agent. The Agent Server spawns it as a subprocess, passes saved secrets as env vars, and Canvas renders the turns. deep_reasoner could therefore expose an ACP adapter and reuse the Canvas UI and backend switching (local vs remote) without being an OpenHands-native agent. This does not solve multi-tenancy (Q1) or sandboxing of its REPL (Q3).

### Cited Findings
- "Instead of Agent Canvas calling an LLM directly, the Agent Server spawns the agent's own CLI as a subprocess and relays each turn to it. The external agent manages its own LLM, tools, and execution." — [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)
- "Custom ACP servers: Any stdio ACP server works: choose **Custom** in Settings → Agent and enter its launch command… Pass credentials by adding the env vars the server reads as global secrets." — [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)
- Built-in presets are Claude Code (`npx -y @agentclientprotocol/claude-agent-acp`), Codex and Gemini CLI. The agent choice "is stored per backend". — [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)
- Isolation caveat: "Concurrent same-provider conversations in one container share a HOME". Per-conversation `acp_isolate_data_dir` exists in the SDK but is not yet exposed by Canvas. — [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)
- Agent Canvas also ships library entrypoints (`@openhands/agent-canvas/conversation`, `/files`, `/terminal`, `/settings`, `/sidebar`, `/browser`) for embedding UI components. — [docs/architecture.md](https://github.com/OpenHands/OpenHands/blob/main/docs/architecture.md); [CHANGELOG.md](https://github.com/OpenHands/OpenHands/blob/main/CHANGELOG.md)
- The repo is labeled "status-beta" and part of the OpenHands incubator program. — [README](https://github.com/OpenHands/OpenHands/blob/main/README.md)

### Inferences
- An ACP adapter gives deep_reasoner the localhost product with little work: Canvas plus Agent Server on loopback with access to local files.
- For the UW server, ACP alone is insufficient: ACP subprocesses run inside whatever Agent Server hosts them. Each user would need their own Agent Server in their own sandbox (pod or VM), plus a separate auth and routing layer, because open-source Canvas has a single shared key.
- deep_reasoner's recursive sub-agents and "namespaces" have no native representation in ACP / Canvas beyond what the adapter streams (e.g., tool calls and plans). The UI fit for nested agent trees is unverified.

### Gaps
- Whether ACP events can carry nested sub-agent structure in a way Canvas renders well. Not tested; the ACP spec was not reviewed here, as it is likely covered by another researcher.
- Library-mode embedding stability and API guarantees are undocumented beyond the export list.
