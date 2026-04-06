# Cross-Agent Skills Deployment Guide

> Deploy skills to Claude Code, Codex CLI, and OpenCode from a single source.
> Companion to the [Agent Skills spec](https://agentskills.io/specification) and [authoring best practices](https://agentskills.io/skill-creation/best-practices).
>
> **This guide covers WHERE to put skills and instruction files so every tool finds them.**
> **For HOW to write skill content, use the agentskills.io docs directly — they're excellent.**

Last updated: March 2026 · Maintainer: Veridian Labs

---

## 1. The Core Principle

The Agent Skills spec defines one format. All three tools read the same `SKILL.md` files with the same YAML frontmatter. Nothing about the skill content changes between tools. The only thing that changes is the **filesystem path** where each tool looks for skills.

Deployment is a routing problem, not a rewriting problem.

---

## 2. Directory Locations: The Compatibility Matrix

### Skills (per-repo / project-level)

| Directory                         | Claude Code | Codex | OpenCode |
|-----------------------------------|:-----------:|:-----:|:--------:|
| `.claude/skills/<n>/SKILL.md`  | ✅          | ❌    | ✅       |
| `.agents/skills/<n>/SKILL.md`  | ❌ *        | ✅    | ✅       |
| `.opencode/skills/<n>/SKILL.md`| ❌          | ❌    | ✅       |

### Skills (global / personal)

| Directory                                   | Claude Code | Codex | OpenCode |
|---------------------------------------------|:-----------:|:-----:|:--------:|
| `~/.claude/skills/<n>/SKILL.md`          | ✅          | ❌    | ✅       |
| `~/.codex/skills/<n>/SKILL.md`           | ❌          | ✅    | ❌       |
| `~/.agents/skills/<n>/SKILL.md`          | ❌          | ❌    | ✅       |
| `~/.config/opencode/skills/<n>/SKILL.md` | ❌          | ❌    | ✅       |

### Instruction Files (project-level)

| File                   | Claude Code | Codex | OpenCode |
|------------------------|:-----------:|:-----:|:--------:|
| `CLAUDE.md`            | ✅          | ❌    | ❌       |
| `AGENTS.md`            | ❌ *        | ✅    | ✅       |
| `.opencode/rules/*.md` | ❌          | ❌    | ✅       |

> \* Claude Code reads **neither** `.agents/skills/` **nor** `AGENTS.md`, despite Anthropic creating the spec that defines both conventions. This is a known gap with 3,000+ community upvotes (GitHub issue #31005, open since August 2025). No timeline for resolution as of March 2026.

### Discovery Behavior Notes

- **Codex** walks up from CWD to repo root, scanning `.agents/skills/` at every level.
- **OpenCode** walks up from CWD to git worktree root, scanning `.opencode/`, `.claude/`, and `.agents/` at every level.
- **Claude Code** looks in `.claude/skills/` relative to the project root and `~/.claude/skills/` globally.

---

## 3. Deployment Scenarios

### Scenario 1: Local Dev (All Three Tools on One Machine)

You write the skill once in the spec-standard location. Symlink to cover Claude Code.

**Skills:**

```bash
# Source of truth — the spec-standard location
~/.agents/skills/recursive-librarian/
├── SKILL.md
├── scripts/
│   └── research_assistant/
└── references/
    └── judaica-gaps.md

# Codex finds it automatically — nothing to do
# OpenCode finds it automatically — nothing to do

# Claude Code needs a symlink
ln -s ~/.agents/skills/recursive-librarian ~/.claude/skills/recursive-librarian
```

**Instruction files:**

```bash
# Source of truth
your-project/AGENTS.md

# Claude Code needs a symlink
cd your-project
ln -s AGENTS.md CLAUDE.md
```

That's it. One skill, one instructions file, three tools see everything.

### Scenario 2: Repo-Level (Skills Committed to a Project)

Same symlink pattern, but tracked in git. Your repo layout:

```
your-project/
├── AGENTS.md                                    # source of truth
├── CLAUDE.md -> AGENTS.md                       # symlink for Claude Code
├── .agents/
│   └── skills/
│       └── recursive-librarian/
│           ├── SKILL.md
│           ├── scripts/
│           │   └── research_assistant/
│           └── references/
│               └── judaica-gaps.md
├── .claude/
│   └── skills/
│       └── recursive-librarian -> ../../.agents/skills/recursive-librarian
└── ...
```

**Setup script** (for first-time clone or CI environments where symlinks may not survive):

```bash
#!/bin/bash
# setup-agent-skills.sh — run from repo root after clone

# Skills: symlink .agents/skills/* into .claude/skills/
SKILLS_SRC=".agents/skills"
CLAUDE_DST=".claude/skills"

mkdir -p "$CLAUDE_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
  skill_name=$(basename "$skill_dir")
  if [ ! -e "$CLAUDE_DST/$skill_name" ]; then
    ln -s "../../$SKILLS_SRC/$skill_name" "$CLAUDE_DST/$skill_name"
    echo "Linked skill: $skill_name"
  fi
done

# Instructions: symlink AGENTS.md to CLAUDE.md
if [ -f "AGENTS.md" ] && [ ! -e "CLAUDE.md" ]; then
  ln -s AGENTS.md CLAUDE.md
  echo "Linked: AGENTS.md -> CLAUDE.md"
fi

echo "Done. All agent tools should now discover skills and instructions."
```

**Makefile alternative** (if you prefer copy over symlink):

```makefile
.PHONY: setup-agents
setup-agents:
	@mkdir -p .claude/skills
	@for dir in .agents/skills/*/; do \
		name=$$(basename "$$dir"); \
		cp -r "$$dir" ".claude/skills/$$name" 2>/dev/null || true; \
	done
	@cp AGENTS.md CLAUDE.md 2>/dev/null || true
	@echo "Agent skills synced."
```

**Git hook alternative** (auto-sync on checkout):

```bash
# .git/hooks/post-checkout
#!/bin/bash
./setup-agent-skills.sh
```

### Scenario 3: Docker Containers (Control Plane)

No symlinks needed. Mount the same source directory to the correct path per agent:

```bash
# Same skills directory, different mount point per container
docker run \
  -v ./skills:/workspace/.claude/skills:ro \
  -v ./AGENTS.md:/workspace/CLAUDE.md:ro \
  -v ./AGENTS.md:/workspace/AGENTS.md:ro \
  claude-code-container

docker run \
  -v ./skills:/workspace/.agents/skills:ro \
  -v ./AGENTS.md:/workspace/AGENTS.md:ro \
  codex-container

docker run \
  -v ./skills:/workspace/.agents/skills:ro \
  -v ./AGENTS.md:/workspace/AGENTS.md:ro \
  opencode-container
```

**Docker Compose equivalent:**

```yaml
services:
  claude-code:
    volumes:
      - ./skills:/workspace/.claude/skills:ro
      - ./AGENTS.md:/workspace/CLAUDE.md:ro
      - ./AGENTS.md:/workspace/AGENTS.md:ro

  codex:
    volumes:
      - ./skills:/workspace/.agents/skills:ro
      - ./AGENTS.md:/workspace/AGENTS.md:ro

  opencode:
    volumes:
      - ./skills:/workspace/.agents/skills:ro
      - ./AGENTS.md:/workspace/AGENTS.md:ro
```

One source directory, one instruction file, three mount configurations. The skill files are never copied or modified.

### Scenario 4: Global Skills (Personal Toolbox)

For skills you want available across all projects regardless of which tool you're using:

```bash
#!/bin/bash
# install-global-skill.sh <skill-directory>
# Installs a skill globally for all three tools

SKILL_DIR="$1"
SKILL_NAME=$(basename "$SKILL_DIR")

# Source of truth
mkdir -p ~/.agents/skills
cp -r "$SKILL_DIR" ~/.agents/skills/"$SKILL_NAME"

# Claude Code
mkdir -p ~/.claude/skills
ln -s ~/.agents/skills/"$SKILL_NAME" ~/.claude/skills/"$SKILL_NAME"

# Codex
mkdir -p ~/.codex/skills
ln -s ~/.agents/skills/"$SKILL_NAME" ~/.codex/skills/"$SKILL_NAME"

# OpenCode finds ~/.agents/skills/ natively — nothing to do

echo "Installed $SKILL_NAME globally for Claude Code, Codex, and OpenCode."
```

---

## 4. What's Portable vs. Tool-Specific

### Spec-Standard Frontmatter (Portable — All Tools)

```yaml
---
name: my-skill
description: What it does and when to use it.
license: MIT
compatibility: Requires git and python3
metadata:
  author: veridian-labs
  version: "1.0"
allowed-tools: Bash(git:*) Read Write    # Spec field, but experimental — support varies
---
```

All fields above are defined in the agentskills.io spec. Unknown fields are silently ignored by all tools, which means you can safely include tool-specific fields alongside these.

### Tool-Specific Extensions

**Claude Code** (extra frontmatter fields — ignored by other tools):

```yaml
context: fork          # Run in isolated subagent (fork | inject)
agent: Explore         # Subagent type (Explore | Plan | custom)
model: sonnet          # Override model (sonnet | opus)
```

Plus: `$ARGUMENTS` injection, lifecycle hooks, plugin packaging, parallel subagents.

**Codex:** No extra SKILL.md fields. `$skill-installer` for installing skills, `[[skills.config]]` in `~/.codex/config.toml` to disable specific skills. Optionally, `agents/openai.yaml` can disable implicit invocation per skill — but the default (`true`) is what you want, so skip this file unless you have a reason to force explicit-only triggering.

**OpenCode** (configured in `opencode.json`, not in SKILL.md):

```json
{
  "permission": {
    "skill": {
      "*": "allow",
      "internal-*": "deny"
    }
  }
}
```

Plus: per-agent permissions, tool disabling, wildcard pattern matching.

### Feature Compatibility Matrix

| Feature                    | Claude Code | Codex | OpenCode | In Spec? |
|----------------------------|:-----------:|:-----:|:--------:|:--------:|
| `name` + `description`    | ✅          | ✅    | ✅       | ✅       |
| `license`                 | ✅          | ✅    | ✅       | ✅       |
| `metadata`                | ✅          | ✅    | ✅       | ✅       |
| `compatibility`           | ✅          | ✅    | ✅       | ✅       |
| `allowed-tools`           | ✅          | ⚠️     | ⚠️       | ✅ *     |
| `scripts/` directory      | ✅          | ✅    | ✅       | ✅       |
| `references/` directory   | ✅          | ✅    | ✅       | ✅       |
| `assets/` directory       | ✅          | ✅    | ✅       | ✅       |
| Progressive disclosure     | ✅          | ✅    | ✅       | ✅       |
| `context: fork`           | ✅          | ❌    | ❌       | ❌       |
| `agent:` field            | ✅          | ❌    | ❌       | ❌       |
| `model:` override         | ✅          | ❌    | ❌       | ❌       |
| `$ARGUMENTS` injection    | ✅          | ❌    | ❌       | ❌       |
| Permission controls        | ❌          | ❌    | ✅       | ❌       |

> \* `allowed-tools` is in the spec but marked experimental. Support varies by implementation.
> ⚠️ = field is recognized per spec but behavior may differ from Claude Code's implementation.

---

## 5. Gotchas and Edge Cases

### Symlinks on Windows
Git on Windows doesn't preserve symlinks by default. Use the copy approach (Makefile or setup script) instead. Or set `git config core.symlinks true` if your Windows environment supports it.

### Editing the Wrong File
If you symlink `CLAUDE.md -> AGENTS.md` and then edit `CLAUDE.md` directly in an editor that resolves symlinks, you'll actually edit `AGENTS.md` (which is what you want). But some editors create a new file instead of following the symlink. If changes aren't showing up, check whether the symlink is still intact.

### Skill Name Collisions
If skills at different directory levels share the same name, behavior varies:
- **Claude Code:** Higher-priority locations win (enterprise > personal > project).
- **Codex:** Both appear in skill selectors — no merge.
- **OpenCode:** Names must be unique across all locations.

Safest approach: keep names unique globally.

### .gitignore Considerations
If you symlink `.claude/skills/` entries, decide whether to gitignore them:

```gitignore
# Option A: Track symlinks in git (works on Mac/Linux)
# Don't ignore anything — symlinks are committed

# Option B: Ignore .claude/ entirely, recreate via setup script
.claude/skills/
CLAUDE.md
```

Option B is cleaner for teams with mixed OS environments.

---

## 6. Distribution Options

| Method                          | Scope          | Works With                    |
|---------------------------------|----------------|-------------------------------|
| Git repo + `npx skills add`    | Community      | Claude Code, Codex, OpenCode  |
| Claude Code plugin marketplace | Claude Code    | Claude Code only              |
| `$skill-installer` in Codex    | Codex          | Codex only                    |
| Manual copy to skill dirs      | Any            | All tools                     |
| Docker volume mount             | Control plane  | All tools (per mount config)  |

The `npx skills add` CLI (from Vercel's skills.sh) auto-detects installed agents and routes skills to the correct directories. It supports `--agent` flags to target specific tools:

```bash
npx skills add your-org/your-skills --skill recursive-librarian -a claude-code -a codex
```

---

## 7. Deployment Checklist

```
□ Source of truth is .agents/skills/ (spec standard)
□ AGENTS.md is the source instruction file
□ Symlinks or copies exist for Claude Code:
    □ .claude/skills/<n> -> .agents/skills/<n>
    □ CLAUDE.md -> AGENTS.md
□ Setup script or Makefile target creates symlinks on fresh clone
□ .gitignore strategy decided (track symlinks vs. regenerate)
□ Docker mounts configured per agent tool (if using containers)
□ Skill discovered by at least 2 tools (manual smoke test)
□ Global install script available for personal toolbox skills
```

---

## 8. Reference: Repo Layout (Complete)

```
your-project/
├── AGENTS.md                                         # Instructions — source of truth
├── CLAUDE.md -> AGENTS.md                            # Symlink for Claude Code
├── setup-agent-skills.sh                             # Setup script for fresh clones
│
├── .agents/                                          # Spec-standard location
│   └── skills/
│       ├── recursive-librarian/
│       │   ├── SKILL.md
│       │   ├── scripts/
│       │   │   └── research_assistant/
│       │   │       ├── cli.py
│       │   │       ├── requirements.txt
│       │   │       ├── apis/
│       │   │       └── core/
│       │   └── references/
│       │       └── judaica-gaps.md
│       └── another-skill/
│           └── SKILL.md
│
├── .claude/                                          # Claude Code compatibility
│   └── skills/
│       ├── recursive-librarian -> ../../.agents/skills/recursive-librarian
│       └── another-skill -> ../../.agents/skills/another-skill
│
└── .opencode/                                        # OpenCode-specific rules (optional)
    └── rules/
        └── project-conventions.md
```

---

## 9. Further Reading

- **Skill authoring:** [agentskills.io/specification](https://agentskills.io/specification) — the definitive format spec
- **Best practices:** [agentskills.io/skill-creation/best-practices](https://agentskills.io/skill-creation/best-practices) — how to write effective skill content
- **Description optimization:** [agentskills.io/skill-creation/optimizing-descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) — systematic trigger testing
- **Claude Code skills docs:** [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)
- **Codex skills docs:** [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills/)
- **OpenCode skills docs:** [opencode.ai/docs/skills](https://opencode.ai/docs/skills/)
- **Community issue:** [github.com/anthropics/claude-code/issues/31005](https://github.com/anthropics/claude-code/issues/31005) — `.agents/skills/` + `AGENTS.md` support request