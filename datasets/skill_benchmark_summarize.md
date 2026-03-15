# Skill Benchmark Dataset: Summarize

**Purpose:** Evaluate different `summarize` skill implementations using the LLM Council.
**Task:** Given the same input text, different skills produce different summaries. The Council judges which skill produces the best summary.
**Skill being benchmarked:** `summarize` (e.g., openclaw/summarize vs. custom implementations)

---

## How to Use This Dataset

For each test case below:
1. Run the text through Skill Implementation A (baseline: no skill, raw prompt)
2. Run the text through Skill Implementation B (openclaw/summarize instructions)
3. Run the text through Skill Implementation C (your custom skill)
4. Feed all outputs to the LLM Council for evaluation

Evaluation criteria the Council should use:
- **Accuracy** — does the summary correctly capture the key points?
- **Conciseness** — is it appropriately brief without losing meaning?
- **Structure** — is the output well-organized and easy to scan?
- **Coverage** — are the most important points included?
- **Fidelity** — does it avoid hallucinating details not in the source?

---

## Test Case 1: Technical Blog Post

**Type:** Technical article
**Expected summary length:** 3-5 bullet points

**Input:**
```
Large language models (LLMs) have transformed how developers build software. Tools like
GitHub Copilot and Cursor have demonstrated that AI can meaningfully accelerate code
completion and generation. However, a less-discussed challenge is evaluation: how do you
know if one AI-generated output is better than another?

The LLM-as-judge paradigm, introduced by researchers at Stanford and CMU, addresses this
by using a capable language model to evaluate the outputs of other models. Rather than
relying on hand-crafted metrics like BLEU or ROUGE — which measure surface-level text
similarity — an LLM judge can assess semantic quality, correctness, and coherence.

A key concern with LLM-as-judge is position bias: models tend to prefer the first option
presented to them. The LLM Council method addresses this by using multiple independent
judges with different personas, then aggregating their evaluations democratically. This
reduces individual model biases and produces more reliable quality assessments.

Early benchmarks suggest that LLM Council evaluations correlate well with human expert
judgments — sometimes better than single-model evaluations. The method is particularly
effective for evaluating open-ended tasks like code review, design document critique, and
long-form writing.
```

---

## Test Case 2: Meeting Transcript

**Type:** Meeting notes / transcript
**Expected summary length:** Action items + key decisions

**Input:**
```
[Weekly Engineering Sync — March 14, 2026]

Sarah: Alright, let's get started. First item — the deployment pipeline has been failing
intermittently since Tuesday. Jake, can you update us?

Jake: Yeah, so we tracked it down to a race condition in the health check. The fix is
ready, just waiting on code review. Should be merged today.

Sarah: Great. What's the timeline for the Q2 feature freeze?

Maria: We're targeting April 15th. Three features are still in progress — the notification
redesign, the export functionality, and the API rate limiting. Rate limiting is the most
at risk; it's about 60% done and the implementation is more complex than we estimated.

Sarah: Can we scope it down for Q2 and do a full implementation in Q3?

Maria: Yes, a basic rate limiting with fixed windows could ship in Q2. Full sliding window
with per-user quotas can move to Q3.

Sarah: Let's do that. Jake, can you open a ticket to split the scope?

Jake: On it.

Sarah: Last item — the on-call rotation. Three people are traveling next week. I'll send
out a revised schedule by end of day.
```

---

## Test Case 3: News Article

**Type:** News / current events
**Expected summary length:** 2-3 sentences, headline style

**Input:**
```
Scientists at the Allen Institute for Brain Science published findings this week showing
that a new imaging technique can map the activity of individual neurons in a living mouse
brain at unprecedented resolution. The technique, called multiphoton resonance imaging
(MPRI), uses ultrafast laser pulses to excite fluorescent proteins in neurons without
damaging surrounding tissue.

In their study, published in Nature Neuroscience, the team tracked over 50,000 neurons
simultaneously during a spatial navigation task — roughly ten times more than previous
methods allowed. The researchers found that the brain encodes spatial position using
distributed patterns of activity across multiple regions simultaneously, rather than
isolated "place cells" as previously thought.

The finding challenges a foundational model in neuroscience established in the 1970s.
"We're not saying place cells don't exist," said lead author Dr. Elena Vasquez, "but
they're part of a much larger distributed code we're only beginning to understand."
The team plans to apply MPRI to Alzheimer's research next, studying how spatial memory
degrades in early disease stages.
```

---

## Test Case 4: Legal / Dense Prose

**Type:** Dense, formal text
**Expected summary length:** Plain-language explanation, 3-4 sentences

**Input:**
```
LIMITATION OF LIABILITY. TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT
SHALL THE COMPANY, ITS AFFILIATES, LICENSORS, SERVICE PROVIDERS, EMPLOYEES, AGENTS,
OFFICERS, OR DIRECTORS BE LIABLE FOR ANY INDIRECT, PUNITIVE, INCIDENTAL, SPECIAL,
CONSEQUENTIAL, OR EXEMPLARY DAMAGES, INCLUDING WITHOUT LIMITATION DAMAGES FOR LOSS OF
PROFITS, GOODWILL, USE, DATA, OR OTHER INTANGIBLE LOSSES, ARISING OUT OF OR RELATING TO
YOUR USE OF, OR INABILITY TO USE, THE SERVICE, EVEN IF THE COMPANY HAS BEEN ADVISED OF
THE POSSIBILITY OF SUCH DAMAGES.

NOTWITHSTANDING THE FOREGOING, THE COMPANY'S TOTAL LIABILITY TO YOU FOR ALL CLAIMS
ARISING OUT OF OR RELATING TO THE AGREEMENT OR YOUR USE OF ANY PART OF THE SERVICE,
WHETHER IN CONTRACT, TORT, OR OTHERWISE, IS LIMITED TO THE GREATER OF: (A) THE AMOUNTS
YOU HAVE PAID TO THE COMPANY IN THE TWELVE (12) MONTHS PRIOR TO THE CLAIM; OR (B) ONE
HUNDRED DOLLARS ($100).
```

---

## Test Case 5: Startup Pitch

**Type:** Business / pitch content
**Expected summary length:** Elevator pitch format (2-3 sentences)

**Input:**
```
We're building the operating system for physical therapy. Today, 65% of patients prescribed
physical therapy never complete their program — they drop out because the exercises are
boring, feedback is delayed, and there's no accountability between sessions.

Our platform uses computer vision running on a standard smartphone camera to analyze
patient movement in real time, comparing each rep against clinical benchmarks. Patients
get immediate visual feedback — "your knee angle is 10 degrees off" — rather than waiting
a week to hear from their therapist. Therapists get a dashboard showing compliance rates,
movement quality scores, and flags for patients at risk of re-injury.

We've been live with 3 PT clinics for 6 months. Completion rates for patients on our
platform are 78% vs. the industry average of 35%. Average therapist case load has
increased from 40 to 65 patients per week without additional staff. We're raising a $2M
seed round to expand to 50 clinics by end of year.
```

---

## Evaluation Prompt for LLM Council

When running Council evaluation, use the following prompt template:

```
You are evaluating summaries of the same source text produced by different AI skill
implementations. Compare the summaries below on these dimensions:

1. Accuracy (0-20): Does it correctly represent the source?
2. Conciseness (0-20): Is it appropriately brief?
3. Structure (0-20): Is it well-organized and easy to scan?
4. Coverage (0-20): Are the most important points included?
5. Fidelity (0-20): Does it avoid adding information not in the source?

Total score: 0-100. Provide scores and a brief justification for each dimension.

Source text: [INSERT TEXT]

Summary A (no skill): [INSERT]
Summary B (openclaw/summarize): [INSERT]
Summary C (custom skill): [INSERT]
```
