# AGENTS.md : Core Behavioral & Clean Code Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

Code is clean if it can be understood easily – by everyone on the team. Clean code can be read and enhanced by a developer other than its original author.

## 0. Global Directives

- **Output Language**: All responses must be in Korean. Retain original terminology (e.g., technical jargon, proper nouns) when translation would lead to awkward phrasing or a loss of technical clarity.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.
- Always find root cause. Always look for the root cause of a problem.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.
- Keep it simple stupid. Simpler is always better. Reduce complexity as much as possible.
- Keep configurable data at high levels and prevent over-configurability.

## 3. Surgical Changes & The Boy Scout Rule

**Touch only what you must. Clean up only your own mess.**

- Apply the Boy Scout rule (leave the campground cleaner than you found it) only within the radius of the code you have modified.

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.
- The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. General Design Rules

- Follow standard conventions.
- Prefer polymorphism to if/else or switch/case.
- Separate multi-threading code.
- Use dependency injection.
- Follow Law of Demeter. A class should know only its direct dependencies.

## 6. Understandability & Naming

- Be consistent. If you do something a certain way, do all similar things in the same way.
- Use explanatory variables.
- Encapsulate boundary conditions. Put the processing for them in one place.
- Prefer dedicated value objects to primitive type.
- Avoid logical dependency. Don't write methods which works correctly depending on something else in the same class.
- Avoid negative conditionals.
- Choose descriptive and unambiguous names, make meaningful distinction, use pronounceable and searchable names.
- Replace magic numbers with named constants.
- Avoid encodings. Don't append prefixes or type information.

## 7. Functions Rules

- Small and do one thing.
- Use descriptive names.
- Prefer fewer arguments.
- Have no side effects.
- Don't use flag arguments. Split method into several independent methods that can be called from the client without the flag.

## 8. Objects and Data Structures

- Hide internal structure and prefer data structures.
- Avoid hybrids structures (half object and half data).
- Should be small, do one thing, with a small number of instance variables.
- Base class should know nothing about their derivatives.
- Better to have many functions than to pass some code into a function to select a behavior.
- Prefer non-static methods to static methods.

## 9. Source Code Structure

- Separate concepts vertically. Related code should appear vertically dense.
- Declare variables close to their usage.
- Dependent and similar functions should be close, placed in the downward direction.
- Keep lines short.
- Don't use horizontal alignment.
- Use white space to associate related things and disassociate weakly related.
- Don't break indentation.

## 10. Comments Rules

- Always try to explain yourself in code.
- Don't be redundant or add obvious noise.
- Don't use closing brace comments.
- Don't comment out code. Just remove.
- Use as explanation of intent, clarification of code, or warning of consequences.

## 11. Tests & Code Smells

- Tests must be: Readable, Fast, Independent, Repeatable, with one assert per test.
- Code smells to prevent:
    - Rigidity (difficult to change).
    - Fragility (breaks in many places).
    - Immobility (cannot reuse).
    - Needless Complexity and Needless Repetition.
    - Opacity (hard to understand).

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.