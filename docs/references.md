# References and Inspiration

Repository-State Agent Workflow is an original synthesis focused on repository-backed continuity and bounded agent sessions. The references below motivate the problem, the surrounding ecosystem, and evaluation practice; they do not by themselves prove RSAW's effectiveness.

## Repository instructions and agent workflow

- [AGENTS.md](https://agents.md/) — an open convention for repository-level coding-agent instructions.
- [agentsmd/agents.md](https://github.com/agentsmd/agents.md) — specification, examples, and ecosystem references.
- [mattpocock/skills](https://github.com/mattpocock/skills) — small, adaptable, composable engineering skills.
- [OpenAI Codex](https://openai.com/index/introducing-codex/) — repository-oriented coding-agent execution and scoped `AGENTS.md` instructions.

## Long context and repository-level software work

- Nelson F. Liu et al., [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172), 2023. The paper studies how model performance changes with relevant-information position and longer context.
- Carlos E. Jimenez et al., [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770), ICLR 2024. SWE-bench frames repository-level issue resolution as a task requiring codebase understanding, execution, and multi-file reasoning.

## Durable engineering state

RSAW also builds on established software-engineering practices:

- version control as durable history;
- issue/task specifications as bounded contracts;
- architecture decision records;
- staged testing and independent review;
- immutable or append-only experimental evidence.

## Distinctive contribution

The workflow combines these practices into an explicit continuity architecture:

- stable policy;
- bounded active working memory;
- one active task contract;
- fresh role-separated sessions;
- progressive disclosure;
- evidence-gated closure;
- deterministic context-footprint and handoff checks.
