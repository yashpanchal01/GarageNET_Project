## Core rules

* When sizing tasks for an AI agent, keep the context size under ~100k tokens, because crossing this threshold pushes the LLM into the "dumb zone" where its reasoning degrades quadratically.
* When starting a new development session or moving to a new task, clear the context completely, because the LLM performs best from a clean slate and context compacting creates confusing historical "sediment."
* When given a new client brief or idea, invoke a "grill me" prompt, because you must reach a shared design concept and alignment with the AI before generating specifications or code.
* When the AI generates a Product Requirements Document (PRD) after an alignment session, skip manually reviewing it, because the shared understanding is already established and LLMs summarize dependably well.
* When breaking a PRD down into actionable tasks, split them into vertical slices (tracer bullets), because horizontal layering prevents the AI from testing the entire integrated flow until the very end.
* When scheduling tasks for AI agents, format them as a Kanban board with blocking relationships, because this enables Directed Acyclic Graph (DAG) parallelization across multiple independent agents.
* When writing code with an agent, enforce a Test-Driven Development (TDD) red-green-refactor loop, because AI will cheat on tests to match its own flawed logic if it writes the implementation first.
* When structuring the codebase architecture, build "deep modules" (small interfaces hiding large internal functionality), because they are easier to wrap in single test boundaries for the AI to navigate.
* When running automated code reviews, push coding standards directly to the reviewer agent via the prompt, because reviewer agents need strict, explicit boundaries to evaluate the implementation agent's work.
* When a PRD has been fully implemented, delete or close the planning documents, because stale documentation ("doc rot") will negatively influence future AI sessions.

## Do / Don't

| Do | Don't |
| --- | --- |
| Clear the context to a zero-state for new tasks. | Compact the context to save token space. |
| Engage in a deep Q&A ("Grill me") to establish a shared design concept. | Rely on the "specs-to-code" loop where you only edit the spec document. |
| Force tasks into vertical slices (tracer bullets). | Structure phases horizontally (e.g., Schema first -> API second -> Frontend last). |
| Map out blocking relationships on a Kanban board. | Feed the AI a single, linear multi-phase loop. |
| Rely on TDD to write a failing test before implementation. | Let the AI write the implementation and tests simultaneously. |
| Architect "deep modules" with large internal logic. | Architect "shallow modules" with many small, highly-coupled files. |
| Use human QA to enforce taste, design, and usability. | Automate final QA and initial design decisions completely. |
| Close and discard PRD documents once implemented. | Keep old PRDs in the repository for future reference. |

## Decision checklist

* Does this task fit well within the ~100k token "smart zone"?
* Have I completed a deep Q&A session with the AI to establish a shared "design concept"?
* Are the planned tasks structured as vertical slices (tracer bullets) crossing all necessary architectural layers?
* Do the tasks specify strict blocking relationships to allow for parallel agent execution?
* Does the target architecture utilize "deep modules" with clear, testable boundaries?
* Are the local feedback loops (tests, type checking) robust enough for an agent to code against blindly?
* Is the implementation step structured to write a failing test first (TDD)?

## Exact specifics

* **Dumb zone threshold:** `100k` tokens (or roughly 40% of the context window).
* **Grill me skill template:** `Interview me relentlessly about every aspect of this plan until we reach a shared understanding Walk down each branch of the design tree resolving dependencies one by one For each question provide your recommended answer Ask the questions one at a time`
* **PRD generation skill:** `write a PRD`
* **Task splitting template:** `break a PRD into independently grabbable issues using vertical slices traceable it's written as local markdown files`
* **Codebase architecture skill:** `improve codebase architecture`
* **Concision prompt (deprecated but noted):** `when talking to me sacrifice grammar for the sake of concision`
* **CLI agent tool:** `claude code`
* **Claude code flag:** permission mode set to accept edits.
* **Shell scripts used for execution:** `once.sh`, `ralph_once.sh`
* **Feedback loop commands:** `npm run test`, `npm run type-check`, `npx vitest`
* **Agent Orchestration Library:** `Sand Castle` (TypeScript library defining `planner`, `implementer`, and `merger` loop logic).
* **Model selection:** `Sonnet` for implementation tasks, `Opus` for review tasks.