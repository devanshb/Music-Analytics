# QUESTION_BANK.md — hostile interview questions (living document)

Rules: after every gate, add ≥3 questions a HARSH interviewer would ask about
what was just built, each with an honest drafted answer (bullets fine here —
this is a prep doc, not prose). "I chose X because it's best practice" is a
banned answer shape; every answer names the tradeoff. Status: ☐ drafted only /
☑ Devansh has rehearsed it aloud. Fable review spot-checks answer quality.

## Architecture & data engineering
- ☐ Q01 Why capture-first instead of schema-first? (irrecoverable vs replayable; ADR-001)
- ☐ Q02 Your raw zone is JSONL files on a laptop. Is that a data lake or a folder? (honest: a folder with lake DISCIPLINE — immutability, replayability; name what object storage would add)
- ☐ Q03 At-least-once + idempotent — what duplicate slips through the natural key? (same track restarted twice within the same second from two sources — quantify observed rate after D6)
- ☐ Q04 Why no Airflow/dbt/queue? (right-sizing; what signal would trigger adopting each)
- ☐ Q05 Transaction boundary is one raw file — what happens on a 100MB file? (memory + lock window; mitigation: file rotation policy at harvester)
- ☐ Q06 Watermark is a state file — what if it corrupts? (worst case = refetch overlap ⇒ dedup absorbs; loss impossible because advance-after-write)
- ☐ Q07 Why Docker for Postgres but cron/launchd for scheduling — isn't that inconsistent? (containerize the stateful dependency for reproducibility; scheduling is OS-native by deliberate simplicity — defend or concede)
- ☐ Q08 Your DQ checks THROW and halt the pipeline. Isn't availability worth degraded data? (for a personal warehouse, correctness > availability; name where at scale you'd quarantine instead)

## Timestamps & reconciliation (the D6 gauntlet)
- ☐ Q09 Prove played_at and export ts measure the same event. (you can't by docs — show the measured Δt distribution)
- ☐ Q10 Why ±5s and not ±2 or ±30? (derived from measured distribution + second-precision rounding; show sensitivity check)
- ☐ Q11 Export wins on conflict — when is that wrong? (if export has data gaps the API filled; quantify overlap disagreement rate)
- ☐ Q12 A track played twice back-to-back lands within 5s once — do you destroy a real play? (track_id must ALSO match at same instant from BOTH sources to dedup; walk the truth table)
- ☐ Q13 DST and timezone bugs — where would they bite? (nowhere in storage — UTC everywhere; only the listening clock converts, and it's explicit)
- ☐ Q13b The export carries offline / offline_timestamp / incognito_mode — you dropped them from the plays schema. Why? (OPEN — D5 decision + ADR: capture as export-only nullable columns vs omit; incognito/offline are real behavioral signals but power no v1 metric. Decide when D5 loader is built, do not silently drop.)

## Spotify & external APIs
- ☐ Q14 Spotify could kill recently-played tomorrow. Then what? (raw + lifetime export survive; harvester dies; honest answer includes "the live tail ends" + LB scrobbler alternatives)
- ☐ Q15 You're building on an API that hates you — why not Deezer/Tidal? (my listening lives on Spotify; the data follows the life, not the API)
- ☐ Q16 ISRC is one recording, many releases — how do dedup edition problems interact with MB resolution? (canonical_title lesson + MBID recording-level identity; give the Bowie 4-albums example class)
- ☐ Q17 1 req/s MusicBrainz for 15k tracks — you serialized 4 hours of wall time. Why not ask for more? (community service politeness IS the requirement; batch dump exists at scale — name it)
- ☐ Q18 What % genre coverage did you get and what's IN the unresolved 20%? (real numbers post-G4; characterize the tail — regional, remixes, podcasts-mislabeled)

## Metrics & statistics
- ☐ Q19 Defend 30 minutes as the session gap. (convention + sensitivity analysis; show metric stability at 20/45)
- ☐ Q20 Shannon entropy on multi-genre fractional counts — why fractional and what bias does it introduce? (avoids multi-genre tracks inflating diversity; concede genre taxonomy noise dominates anyway)
- ☐ Q21 Cosine drift on raw play counts overweights heavy weeks — why not normalize differently? (vectors ARE normalized; discuss log-scaling alternative and why rejected/kept)
- ☐ Q22 Your qualified_play treats every API row as qualified — that inflates API-era counts vs export-era. Defend or fix. (honest bias acknowledgment + magnitude estimate; possible correction factor)
- ☐ Q23 Discovery rate confounds new-music-discovery with new-to-warehouse. First weeks are 100% discovery. How handled? (burn-in exclusion window; state it)

## Security & privacy
- ☐ Q24 Tell me about the .env incident like I'm your security lead. (rotation, cached-file purge, gitignore, and the process change that prevents recurrence)
- ☐ Q25 Your GDPR export has your IPs and locations — where does it live and who can read it? (backfill dir, gitignored, disk-encrypted laptop; never leaves machine)
- ☐ Q26 The T5 analyzer: prove my zip never left my browser. (network tab evidence, no upload endpoint exists, static hosting, open source)
- ☐ Q27 OAuth: why is the loopback-literal requirement not just pedantry? (localhost resolution attacks; front/back-channel model)

## LLM layer (T1)
- ☐ Q28 Why is the guardrail the DB role and not the prompt? (prompts are suggestions; GRANT is physics; statement_timeout bounds runaway queries)
- ☐ Q29 Your eval is 15 questions — that's tiny. (it's a regression tripwire, not a benchmark; grows with failures; name the two failure classes it already caught [PENDING])
- ☐ Q30 The narration tripwire only catches digits — what hallucinations slip through? (relative claims like "tripled", entity swaps; mitigation: payload includes precomputed comparatives)
- ☐ Q31 Why not RAG over reviews/wiki for richer narration? (no defensible corpus; unverifiable claims; analytical questions want a database)

## Product judgment
- ☐ Q32 Isn't this just stats.fm? (their product, my pipeline: I own capture, schema, metrics, and — in T5 — the zero-custody privacy stance; also: the point was building it)
- ☐ Q33 You rejected the music-hub idea — steelman it back to me, then kill it again. (rehearse ADR-004 both directions)
- ☐ Q34 Five authorized users forever — why sink months into a platform that capped you? (the cap is why the data moat matters; multi-user was never the value)
- ☐ Q35 What would you cut if you had to ship in 3 days instead of 14? (harvester + raw + minimal loader; everything else is replayable later — the answer IS the thesis)

## Meta
- ☐ Q36 You built this with AI executors. What did YOU do? (architecture, decisions, verification standards, every ADR; the gates exist because I distrust the executors — walk through one gate's evidence live)
- ☐ Q37 Show me a decision the AI got wrong that you caught. (maintain a running list here — mandatory, at least 2 entries by GX: ______ )
