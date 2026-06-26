# Agents — Claude Code Skills & Plugins

A personal collection of Claude Code skills and plugins. Everything here is either a standalone skill or a packaged plugin that extends Claude Code's capabilities.

---

## Repository Structure

```
agents/
├── skills/          # Standalone skills (individual SKILL.md files)
└── plugins/         # Plugin-packaged skills (grouped by plugin source)
    ├── superpowers/
    ├── terraform-provider-development/
    ├── notion-workspace/
    ├── frontend-design/
    ├── tanstack-query/
    └── claude-code-setup/
```

---

## Skills

Standalone skills installed via `~/.claude/skills/` or the built-in marketplace.

| Skill | Description |
|-------|-------------|
| `api-designer` | REST API design with OpenAPI, pagination, error handling, and versioning patterns |
| `backend-patterns` | Backend architecture patterns for scalable services |
| `database-optimizer` | Query optimization, indexing strategies, PostgreSQL/MySQL tuning |
| `find-skills` | Discover and install new Claude Code skills |
| `fine-tuning-expert` | LLM fine-tuning: dataset prep, LoRA/PEFT, hyperparameter tuning, evaluation |
| `frontend-patterns` | Frontend architecture and component patterns |
| `java-architect` | Spring Boot, JPA, Spring Security, reactive WebFlux patterns |
| `microservices-architect` | Microservices decomposition, communication, data, and observability patterns |
| `nestjs-best-practices` | NestJS best practices for enterprise TypeScript backends |
| `nestjs-expert` | NestJS modules, controllers, services, DTOs, guards, and interceptors |
| `next-best-practices` | Next.js App Router, RSC boundaries, data patterns, metadata, error handling |
| `nextjs-developer` | Next.js app router, server components, server actions, data fetching, deployment |
| `playwright-expert` | Playwright testing: page object model, selectors, API mocking, flaky test debugging |
| `prisma-cli` | Prisma CLI commands reference |
| `prisma-client-api` | Prisma Client API usage patterns |
| `prisma-database-setup` | Prisma database setup and configuration |
| `prisma-driver-adapter-implementation` | Prisma driver adapter implementation guide |
| `prisma-postgres` | Prisma with PostgreSQL patterns |
| `prisma-postgres-setup` | Setting up Prisma with PostgreSQL |
| `prisma-upgrade-v7` | Guide for upgrading to Prisma v7 |
| `react-expert` | React hooks, state management, performance, React 19, server components, testing |
| `run-loop` | Run prompts or slash commands on a recurring interval |
| `spring-boot-engineer` | Spring Boot with security, data, web, testing, and cloud patterns |
| `supabase` | Supabase: database, auth, Edge Functions, Realtime, Storage, RLS |
| `supabase-postgres-best-practices` | PostgreSQL best practices for Supabase projects |
| `terraform-engineer` | Terraform best practices, module patterns, providers, state management, testing |

---

## Plugins

Plugin-packaged skills installed via the Claude Code plugin marketplace.

### `superpowers` — `plugins/superpowers/`

Core workflow skills for structured development. Install with:
```bash
claude plugin install superpowers@claude-plugins-official
```

| Skill | Description |
|-------|-------------|
| `brainstorming` | Collaborative design exploration before any implementation |
| `dispatching-parallel-agents` | Dispatch multiple subagents to work in parallel |
| `executing-plans` | Execute implementation plans step by step |
| `finishing-a-development-branch` | Structured options for merge, PR, or cleanup when work is complete |
| `receiving-code-review` | Process and respond to code review feedback |
| `requesting-code-review` | Request structured code review from peers or agents |
| `subagent-driven-development` | Execute plans with independent tasks via subagents |
| `systematic-debugging` | Structured debugging process for bugs and test failures |
| `test-driven-development` | TDD workflow before writing implementation code |
| `using-git-worktrees` | Isolate feature work using git worktrees |
| `using-superpowers` | Introduction to the superpowers skill system |
| `verification-before-completion` | Verify work meets requirements before marking done |
| `writing-plans` | Create detailed implementation plans from specs |
| `writing-skills` | Create, edit, and verify Claude Code skills |

### `terraform-provider-development` — `plugins/terraform-provider-development/`

HashiCorp Terraform provider development skills. Install with:
```bash
claude plugin install terraform-provider-development@hashicorp
```

| Skill | Description |
|-------|-------------|
| `new-terraform-provider` | Scaffold a new Terraform provider from scratch |
| `provider-actions` | Implement provider CRUD actions |
| `provider-docs` | Write provider documentation |
| `provider-resources` | Define Terraform resources and data sources |
| `provider-test-patterns` | Testing patterns for Terraform providers |
| `run-acceptance-tests` | Run provider acceptance tests |

### `notion-workspace` — `plugins/notion-workspace/`

Notion-integrated skills for knowledge management. Install with:
```bash
claude plugin install notion-workspace-plugin@notion-plugin-marketplace
```

| Skill | Description |
|-------|-------------|
| `knowledge-capture` | Capture and structure knowledge in Notion |
| `meeting-intelligence` | Extract action items and insights from meetings |
| `research-documentation` | Document research findings in Notion |
| `spec-to-implementation` | Turn Notion specs into implementation tasks |

### `frontend-design` — `plugins/frontend-design/`

Guidance for distinctive, intentional visual design. Install with:
```bash
claude plugin install frontend-design@claude-plugins-official
```

| Skill | Description |
|-------|-------------|
| `frontend-design` | Aesthetic direction, typography, and design choices for new UI |

### `tanstack-query` — `plugins/tanstack-query/`

TanStack Query patterns and best practices. Install with:
```bash
claude plugin install tanstack-query@tanstack-skills
```

### `claude-code-setup` — `plugins/claude-code-setup/`

Claude Code configuration and automation. Install with:
```bash
claude plugin install claude-code-setup@claude-plugins-official
```

| Skill | Description |
|-------|-------------|
| `claude-automation-recommender` | Recommends Claude Code automation configurations |

---

## MCP Plugins

These are Model Context Protocol servers that give Claude access to external tools and services. They are configured in Claude's settings (not stored as files in this repo).

| Plugin | Source | Tools |
|--------|--------|-------|
| **Context7** | `context7@claude-plugins-official` | Live library documentation lookup |
| **Gmail** | claude.ai integration | Read/search threads, manage labels, create drafts |
| **Google Calendar** | claude.ai integration | List/create/update/delete events, suggest times |
| **Google Drive** | claude.ai integration | Search, read, create, copy files |
| **HubSpot** | claude.ai integration | CRM objects, campaigns, analytics, landing pages |
| **Nimble** | claude.ai integration | Authentication workflows |
| **Notion** | claude.ai integration | Pages, databases, comments, search |
| **Supabase** | claude.ai integration | SQL execution, migrations, Edge Functions, logs |
| **Vercel** | claude.ai integration | Deployments, projects, logs, runtime errors |
| **n8n** | claude.ai integration | Workflow automation |

To configure MCP plugins, use:
```bash
claude mcp add <plugin-name>
```

---

## Installing Skills & Plugins on a New Machine

### Prerequisites

1. Install [Claude Code](https://claude.ai/code):
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. Log in:
   ```bash
   claude login
   ```

### Installing Standalone Skills

Copy the skills from this repo into your Claude skills directory:

```bash
# Clone this repo
git clone git@github.com:apettiigrew/agents.git
cd agents

# Copy all standalone skills
cp -r skills/* ~/.claude/skills/
```

### Installing Plugin Skills

Plugin skills must be installed via the Claude Code plugin system. Run these commands:

```bash
# Core workflow (superpowers)
claude plugin install superpowers@claude-plugins-official

# HashiCorp Terraform provider development
claude plugin install terraform-provider-development@hashicorp

# Notion workspace (requires Notion MCP connection)
claude plugin install notion-workspace-plugin@notion-plugin-marketplace

# Frontend design guidance
claude plugin install frontend-design@claude-plugins-official

# TanStack Query patterns
claude plugin install tanstack-query@tanstack-skills

# Claude Code setup & automation
claude plugin install claude-code-setup@claude-plugins-official

# Context7 live documentation (MCP server)
claude plugin install context7@claude-plugins-official
```

### Configuring MCP Servers (claude.ai integrations)

The following MCP plugins are managed through your Claude account at [claude.ai](https://claude.ai):

- Gmail, Google Calendar, Google Drive — connect via Google account in Claude settings
- HubSpot, Vercel, Notion, Supabase, n8n, Nimble — connect via their respective OAuth flows in Claude settings

To re-enable after logging into a new machine, sign in at claude.ai and reconnect each integration under **Settings > Integrations**.

### Full Setup Script

```bash
#!/bin/bash
# Clone repo and install all skills
git clone git@github.com:apettiigrew/agents.git
cd agents

# Standalone skills
cp -r skills/* ~/.claude/skills/

# Plugin skills
claude plugin install superpowers@claude-plugins-official
claude plugin install terraform-provider-development@hashicorp
claude plugin install notion-workspace-plugin@notion-plugin-marketplace
claude plugin install frontend-design@claude-plugins-official
claude plugin install tanstack-query@tanstack-skills
claude plugin install claude-code-setup@claude-plugins-official
claude plugin install context7@claude-plugins-official

echo "Done! Restart Claude Code to activate all skills."
```
