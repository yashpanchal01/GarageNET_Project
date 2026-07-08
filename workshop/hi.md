## Core rules

* When starting a new task or session, clear your context completely to a zero-state, because compacting leaves confusing history ("sediment") and you perform best from a clean slate.

* When sizing tasks, keep the scope under 100k tokens, because adding more tokens pushes you into the "dumb zone" where your reasoning degrades quadratically.

* When receiving a new client brief or idea, run the 'grill me' skill to interrogate the user, because you must align with the human to reach a shared "design concept" before generating any specifications.

* When an ongoing session requires running deep code changes or explorations to answer a question, execute a handoff document and spin up a fresh agent context, because prototyping in a heavily strained context window exhausts the token limit.

* When faced with complex stateful logic or visual variations, build a throwaway interactive prototype, because you must look at running code or toggle variations to uncover unknown design issues.

* When prompt instructions contain large blocks of supporting data or references, wrap that data in explicit XML tags, because isolating reference data prevents it from competing with primary command directives.

* When generating issue backlogs, apply the `ready for agent` triage label to the items, because these tasks must be structured for immediate pick-up by an automated agent loop without requiring additional human intervention.

* When you generate a Product Requirements Document (PRD) after a grilling session, do not ask the user to manually review it, because the shared understanding is already established and you are reliable at summarizing.

* When breaking down a PRD into actionable tasks, split the work into vertical slices (tracer bullets) that cross all architectural layers, because horizontal layering prevents you from testing the integrated flow until the final phase.

* When organizing tasks for execution, structure them as a Kanban board with clear blocking relationships, because this allows multiple agents to work on independent tasks in parallel as a Directed Acyclic Graph.

* When writing implementation code, strictly follow a red-green-refactor Test-Driven Development (TDD) loop, because you must prove the test fails before writing the implementation to prevent testing hallucinations.

* When designing codebase architecture, build "deep modules" with simple interfaces and large internal logic, because they allow you to test a large chunk of functionality inside a single, reliable test boundary.

* When evaluating code changes, deploy parallel sub-agents to check the diff across two separate axes—codebase standards and the feature spec—because focusing only on one axis misses style or structural discrepancies.

* When a PRD or planning document has been fully implemented, close or delete it, because keeping outdated documentation in the repository causes "doc rot" and will negatively influence your future context.

## Do / Don't

| Do | Don't | 
| ----- | ----- | 
| Clear your context entirely to reset to a zero-state. | Compact your context to save token space. | 
| Isolate long documentation blocks using XML wrapper tags. | Mix reference data loosely next to primary instructions. | 
| Handoff to a fresh agent window when prototyping features. | Accumulate experimental code iteration on top of a planning context. | 
| Mark generated issues as `ready for agent` immediately. | Default new backlog issues to a `needs triage` state. | 
| Create simple interactive scripts to test complex state machines. | Guess how state combinations resolve on paper without code execution. | 
| Generate distinct UI options with an embedded switch mechanism. | Deliver a single layout design without testing alternatives. | 
| Break plans into vertical slices (tracer bullets). | Structure implementation in horizontal layers (e.g., Schema first, API second, UI last). | 
| Direct parallel sub-agents to audit style rules and specs concurrently. | Run single-pass reviews that ignore architectural consistency. | 

## Decision checklist

* Does this planned task fit comfortably within my \~100k token "smart zone"?
* Is my context window getting congested, requiring me to hand off this execution spike to a fresh agent?
* Are there unknown state interactions or UI paths that require building a throwaway terminal app or frontend variation?
* Did I isolate all large pieces of reference documentation inside XML container tags?
* Are the markdown issues generated from the plan marked with the `ready for agent` label?
* Have I completed a relentless Q&A session with the user to establish a shared "design concept"?
* Are my resulting implementation tasks structured as vertical slices (tracer bullets) from UI to database?
* Are task dependencies explicitly mapped out so other agents can execute non-blocking tasks in parallel?
* Am I targeting "deep modules" with clear, testable boundaries for this implementation?
* Are the local feedback loops (tests, type checking) robust enough for me to code against blindly?
* Am I writing a failing test first (TDD) before implementing the feature code?

## Exact specifics

* **Smart zone token limit:** `100k` tokens
* **CLI Agent Tool:** `claude code`
* **Agent Permissions:** Run with permission mode set to accept edits.
* **Agent Orchestration Library:** `Sand Castle` (TypeScript library defining `planner`, `implementer`, and `merger` loop logic).
* **Model Selection:** `Sonnet` for implementation tasks, `Opus` for automated review tasks.
* **Feedback loop commands:** `npm run test`, `npm run type-check`, `npx vitest`
* **Execution Shell Scripts:** `once.sh`, `ralph_once.sh`
* **Prompt/Skill — Grill me:** `Interview me relentlessly about every aspect of this plan until we reach a shared understanding Walk down each branch of the design tree resolving dependencies one by one For each question provide your recommended answer Ask the questions one at a time`
* **Prompt/Skill — Grill with Docs:** `/grill-with-docs` (Isolate documentation arrays within `<supporting_info>` tags).
* **Prompt/Skill — Handoff:** `/handoff` (Saves context map using `make temp -t handoff`, reads file target before execution to avoid write errors, and explicitly details intent/vibe for the next window).
* **Prompt/Skill — Prototype:** `/prototype` (Deploys interactive terminal loops or interactive frontend route variants with toggle buttons for testing visual/logic trees).
* **Prompt/Skill — Write PRD:** `/to-PRD` (Applies `ready for agent` label automatically).
* **Prompt/Skill — Task splitting:** `/to-issues` (Generates standalone local markdown issue targets applying the `ready for agent` label).
* **Prompt/Skill — Architecture:** `improve codebase architecture`
* **Prompt/Skill — Review (In Development):** `/review` (Spawns twin sub-agents evaluating against *standards* and *spec* boundaries simultaneously).
* **Prompt/Skill — Writing (In Development):** `/writing-fragments`, `/writing-beats`, `/writing-shape`
* **Prompt/Config — Concision (place in claude.md):** `when talking to me sacrifice grammar for the sake of concision`