# CLAUDE.md

Instructions for working with me on this project. Read and follow these every session.

## Context

- This is a **Python Spotify data pipeline** (repo: Music-Analytics). It fetches, normalizes, and analyzes Spotify Web API data. It's a solo learning + portfolio project.
- My background: **Java / C++ with solid DSA**, but **new to Python and new to API development**. Treat me as a strong programmer who is a beginner in _this_ stack.
- Environment: macOS, VS Code, Python 3.11.5 in a virtual environment, secrets in `.env` via `python-dotenv`.

## Communication Style

- **Do not give me code unless I explicitly ask for it.** Default to **pseudocode, procedures, and logic flow.** Explain the _steps_ and the _why_, and let me write the actual code.
- Example: if I'm making my first Spotify API call, walk me through the procedure (get a token, build the request, send it, read the response) — don't hand me a finished script.
- When I do ask for code, keep it minimal and targeted.
- Bridge from my background when it helps: relate Python concepts to Java/C++ equivalents (e.g. dict as HashMap, `None` vs `null`, f-strings, dynamic typing).
- **Reason step-by-step and explain your logic.** I learn by understanding the reasoning, not by copying output.

## Verify, Don't Speculate

- When uncertain about facts, current info, or technical details, **search the web and check official documentation** instead of guessing or hedging.
- For any specific API or library, **do not assume you know it** — check the current docs for the relevant feature. This especially applies to the **Spotify Web API**, whose access rules have changed repeatedly (endpoints and fields have been removed or restricted). Verify against current Spotify docs before recommending an endpoint.

## Design Principles

1. **Don't overengineer** — simple beats complex.
2. **No fallbacks** — one correct path, no alternatives.
3. **One way** — one way to do a thing, not many.
4. **Clarity over compatibility** — clear code beats backward compatibility.
5. **Throw errors** — fail fast when preconditions aren't met.
6. **No backups** — trust the primary mechanism.
7. **Separation of concerns** — each function has a single responsibility.

## Development Methodology

1. **Surgical changes only** — minimal, focused fixes.
2. **Evidence-based debugging** — add minimal, targeted logging.
3. **Fix root causes** — address the underlying issue, not the symptom.
4. **Collaborative process** — work with me to find the most efficient solution.
5. **Reason step-by-step** — explain your logic as you go.
6. **Security-aware at every stage** — flag security concerns proactively (e.g. warn me about storing API keys / client secrets securely, keeping them out of source control).

## Security Baseline

- Never commit secrets. Keep API keys and client secrets in `.env`; ensure `.gitignore` covers it (verify the `.gitignore` is at the **repo root**, not in a subfolder).
- If credentials are ever exposed, treat them as compromised: rotate them and correct the git state.
- Flag any code or suggestion that would leak secrets (logging them, hardcoding them, putting them in URLs).
