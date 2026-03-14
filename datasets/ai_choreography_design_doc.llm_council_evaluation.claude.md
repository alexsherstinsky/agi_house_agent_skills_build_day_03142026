# LLM Council Evaluation — MoveFlow: AI Choreography System Design Document

**Source artifact:** `datasets/ai_choreography_design_doc.md`
**Detected artifact type:** code (design doc with embedded code)
**Evaluation date:** 2026-03-14
**LLM backend:** Claude (Opus 4.6, via Claude Code MCP)
**Method:** LLM Council (Zhao et al., 2024) — 5 independent reviewers with democratic aggregation

---

## Reviewer 1: Software Engineer

**Lens:** Correctness, bugs, edge cases, logic errors.

**Step-by-step analysis:**

Looking at the architecture, the data flow is clear: audio in → analysis → prompt → video generation → job store → result. Let me trace edge cases.

1. The BPM mapping table in Section 4.2 has **gaps and overlaps**. What happens when BPM is 95 and energy is "high"? Or BPM is 125 and energy is "low"? The table only covers specific combinations — many real-world inputs will fall through. The "any" row for classical creates ambiguity: does low-energy classical match both the first row and the last row?

2. The `beat_times` field in `MusicFeatures` is computed but **never consumed** by any downstream component. The Prompt Builder doesn't use it. This is dead data in v1.

3. The prompt template says "4K quality" but the goal says "720p or higher." These are inconsistent — asking the video model for 4K while the goal is 720p wastes API cost and latency.

4. The `valence` field is described as a "spectral brightness proxy" — but spectral centroid is not a reliable proxy for emotional valence. This could produce mismatched mood adjectives (e.g., a bright-sounding sad song tagged "euphoric").

**Recommendations:**
- Define the BPM/energy mapping as exhaustive (cover all combinations or add a fallback default). **Important.**
- Remove `beat_times` or document its planned use. **Minor.**
- Align prompt resolution with the stated goal (720p). **Medium.**
- Acknowledge the valence proxy limitation in the doc. **Medium.**

---

## Reviewer 2: Code Reviewer

**Lens:** Readability, maintainability, conventions.

**Step-by-step analysis:**

1. The document structure is **well-organized** — numbered sections, clear separation of concerns, good use of tables and code blocks. The architecture diagram is helpful.

2. The `VideoGenerationClient` Protocol pattern is clean — good use of Python's structural subtyping for the adapter layer. However, `FalAiClient` is missing `__init__` — where does `fal_client` come from? It's referenced but never imported or injected. This will confuse implementers.

3. Section 4.2 mixes **specification with implementation** — the mapping table is clear, but the mood adjective thresholds (< 0.4, 0.4–0.7, > 0.7) are buried in prose rather than expressed as code or a structured table. Inconsistent with how the BPM mapping is presented.

4. The doc says "SSE or WebSocket" for progress polling but doesn't commit to either. This is an implementation decision that affects the frontend architecture — leaving it open at design time creates ambiguity.

**Recommendations:**
- Show how `fal_client` is obtained (DI, import, config). **Important.**
- Present mood adjective mapping as a table like the BPM mapping. **Minor.**
- Decide SSE vs. WebSocket and document the choice. **Medium.**

---

## Reviewer 3: Security Engineer

**Lens:** Vulnerabilities, input validation, injection risks.

**Step-by-step analysis:**

1. **File upload validation** — MIME type and magic bytes are checked. Good. However, there's no mention of **file size limits** at the HTTP layer. The doc says "up to 60 seconds" but audio file size depends on encoding — a 60s WAV at 44.1kHz stereo 16-bit is ~10MB, but a corrupted or malicious file could claim to be audio while being much larger. Need an explicit max upload size (e.g., 50MB hard cap).

2. **Temp file cleanup** — files are stored with UUID names, but there's no mention of **when temp files are deleted**. Without cleanup, this is a disk exhaustion vector.

3. **Job ID enumeration** — UUIDs are good, but the `/api/jobs/{job_id}` endpoint has **no authentication**. Anyone who guesses or intercepts a job ID can access the result URL. For a v1 this may be acceptable, but it should be explicitly acknowledged as a known limitation.

4. **fal.ai API error propagation** — Section 6 says "Propagate error message to frontend." Blindly forwarding third-party error messages can **leak internal details** (API keys in error strings, internal URLs, stack traces). Error messages from fal.ai should be sanitized.

5. **No rate limiting** mentioned. The video generation API likely has cost — an attacker could trigger many expensive API calls.

**Recommendations:**
- Add explicit max upload size at the HTTP layer. **Important.**
- Define temp file cleanup policy. **Important.**
- Sanitize third-party error messages before returning to frontend. **Important.**
- Add rate limiting. **Medium.**
- Acknowledge unauthenticated job access as a known v1 limitation. **Minor.**

---

## Reviewer 4: Performance Engineer

**Lens:** Performance concerns, unnecessary work, scalability.

**Step-by-step analysis:**

1. The 90-second P50 budget is almost entirely consumed by the video generation API. The doc acknowledges this ("bottleneck is the video generation API"). But there's **no breakdown** of the latency budget: how much for upload, analysis (< 5s), prompt building (trivial), video generation (???), and response? Without this, the 90s target is untestable.

2. `librosa` loads the entire audio file into memory and decodes it. For a 60s WAV that's ~10MB of raw samples. This is fine for v1 single-process, but the doc doesn't mention **memory limits per request**. If multiple requests hit concurrently, memory could spike.

3. The genre classifier ("fine-tuned MobileNet on mel spectrograms") is mentioned casually but **not spec'd**. Model loading time, inference time, memory footprint — none of these are addressed. A cold-start model load could blow the 5s analysis budget.

4. The prompt template says "4K quality" — if the video API actually generates at 4K, this is significantly more expensive and slower than 720p. The stated goal is 720p.

**Recommendations:**
- Add a latency budget breakdown. **Important.**
- Spec the genre classifier: model size, load time, inference time. **Important.**
- Align prompt resolution with the 720p goal. **Medium.**
- Document memory expectations per request. **Minor.**

---

## Reviewer 5: QA Engineer

**Lens:** Testability, edge cases, missing test cases.

**Step-by-step analysis:**

1. The `MusicFeatures` dataclass is testable — but what are the **boundary conditions**? What if BPM detection returns 0 or NaN? What if energy or valence is outside [0, 1]? The doc doesn't specify validation on the output of the analysis service.

2. The Prompt Builder mapping table has **untested gaps** (see Software Engineer's analysis). What's the prompt for BPM=100, energy=high, genre=rock? There's no row for that. This will be a source of bugs.

3. **No mention of testing strategy** — no unit test plan, no integration test plan, no contract tests for the fal.ai API. For a system with an external API dependency, **contract testing or mocking strategy** is critical.

4. The error handling table is good but **no mention of retry logic** beyond surfacing a retry option to the user. What about transient fal.ai failures? Automatic retry with backoff?

5. **No monitoring or observability** mentioned — how do we know if the system is meeting the 90s P50 target in production? No logging, metrics, or alerting strategy.

**Recommendations:**
- Add input validation on `MusicFeatures` outputs (bounds checking). **Important.**
- Define a testing strategy section. **Important.**
- Add retry logic for transient API failures. **Medium.**
- Add an observability/monitoring section. **Medium.**

---

## Democratic Aggregation

### Summary Table

| Issue | Consensus | Reviewers | Recommendation |
|---|---|---|---|
| BPM/energy mapping table has gaps — many input combinations have no match | **HIGH** | Software Engineer, Code Reviewer, QA Engineer | Make the mapping exhaustive with a default fallback row |
| No max upload file size at HTTP layer | **HIGH** | Security Engineer, Performance Engineer, QA Engineer | Add explicit size cap (e.g., 50MB) |
| 4K in prompt vs. 720p in goals — inconsistent | **HIGH** | Software Engineer, Performance Engineer, Code Reviewer | Align prompt with stated 720p goal |
| No testing strategy documented | **MEDIUM** | QA Engineer, Code Reviewer | Add a testing section covering unit, integration, and contract tests |
| Genre classifier not spec'd (load time, memory, inference) | **MEDIUM** | Performance Engineer, Software Engineer | Spec the model or defer genre classification to v2 |
| Temp file cleanup policy missing | **MEDIUM** | Security Engineer, Performance Engineer | Define TTL or post-processing cleanup |
| No latency budget breakdown | **MEDIUM** | Performance Engineer, QA Engineer | Break down the 90s P50 across pipeline stages |
| `fal_client` origin not shown — unclear how it's injected | **MEDIUM** | Code Reviewer, Software Engineer | Show import or DI pattern |
| Third-party error messages propagated unsanitized | **LOWER** | Security Engineer | Sanitize before returning to frontend |
| No rate limiting | **LOWER** | Security Engineer | Add rate limiting for v1 or document as known gap |
| No observability/monitoring section | **LOWER** | QA Engineer | Add logging, metrics, alerting plan |
| `beat_times` computed but unused | **LOWER** | Software Engineer | Remove or document planned use |
| Valence proxy (spectral centroid) unreliable | **LOWER** | Software Engineer | Acknowledge limitation in doc |
| SSE vs. WebSocket not decided | **LOWER** | Code Reviewer | Commit to one approach |
| Unauthenticated job access | **LOWER** | Security Engineer | Acknowledge as known v1 limitation |

### Overall Quality Score: 7/10

This is a solid v1 design document with clear architecture, good separation of concerns, and a well-scoped feature set. The main gaps are in the details: the BPM mapping is incomplete, performance targets lack decomposition, and security/testing/observability sections need more depth. The core architecture is sound.

### Overall Readiness Assessment: Needs Revision

The three HIGH-priority items (mapping gaps, upload size, prompt/goal inconsistency) should be addressed before implementation begins. The MEDIUM-priority items (testing strategy, classifier spec, latency breakdown) should ideally be addressed but could be resolved during implementation.
