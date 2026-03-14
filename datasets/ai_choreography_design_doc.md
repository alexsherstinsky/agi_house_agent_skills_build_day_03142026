# LLM Council Results


## Review the following software design document for an AI Choreography system and evaluate its quality, completeness, and technical soundness.

### Senior Engineer

---

# MoveFlow: AI Choreography System — Software Design Document

**Version:** 1.0
**Author:** Agent (Claude Sonnet 4.6)
**Date:** 2026-03-14

---

## 1. Overview

MoveFlow is a web-based AI choreography platform that accepts a music file as input and produces a short (15–30 second) high-fidelity dance video as output. The system analyzes musical structure — tempo, beat grid, genre, and emotional valence — and translates these signals into a natural-language prompt that drives a text-to-video generation model.

---

## 2. Goals and Non-Goals

**Goals:**
- Accept any MP3/WAV audio file up to 60 seconds
- Analyze musical features in under 5 seconds (BPM, key, energy, genre)
- Generate a dance style prompt aligned to the musical character
- Produce a 15–30s MP4 video at 720p or higher via API-based video generation
- Return the result to the user within 90 seconds end-to-end (P50)

**Non-Goals:**
- Real-time / interactive choreography
- User-defined avatar or costume customization (v1)
- On-premise video generation (uses external API)
- Multi-person choreography scenes (v1)

---

## 3. System Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────────────┐
│   Browser   │────▶│                    Next.js Frontend                  │
│ (Upload UI) │◀────│  - File upload component                             │
└─────────────┘     │  - Progress polling (SSE or WebSocket)               │
                    │  - Video player                                       │
                    └──────────────────┬───────────────────────────────────┘
                                       │ POST /api/generate
                                       ▼
                    ┌──────────────────────────────────────────────────────┐
                    │                 FastAPI Backend                       │
                    │                                                       │
                    │  ┌─────────────┐    ┌───────────────────────────┐   │
                    │  │   Ingest    │───▶│   Music Analysis Service  │   │
                    │  │  (upload,   │    │   (librosa)               │   │
                    │  │   validate) │    │   → BPM, key, energy,     │   │
                    │  └─────────────┘    │     genre, mood           │   │
                    │                     └──────────┬────────────────┘   │
                    │                                │                     │
                    │                     ┌──────────▼────────────────┐   │
                    │                     │   Prompt Builder          │   │
                    │                     │   (rule-based + template) │   │
                    │                     │   → dance style prompt    │   │
                    │                     └──────────┬────────────────┘   │
                    │                                │                     │
                    │                     ┌──────────▼────────────────┐   │
                    │                     │   Video Generation Client │   │
                    │                     │   (fal.ai adapter layer)  │   │
                    │                     │   → MP4 URL               │   │
                    │                     └──────────┬────────────────┘   │
                    │                                │                     │
                    │                     ┌──────────▼────────────────┐   │
                    │                     │   Job Store (Redis/SQLite) │   │
                    │                     │   → status, result_url    │   │
                    │                     └───────────────────────────┘   │
                    └──────────────────────────────────────────────────────┘
```

---

## 4. Component Design

### 4.1 Music Analysis Service

**Input:** Raw audio bytes (MP3 or WAV)
**Output:** `MusicFeatures` struct

```python
@dataclass
class MusicFeatures:
    bpm: float               # e.g. 128.0
    key: str                 # e.g. "A minor"
    energy: float            # 0.0–1.0 (RMS-based)
    valence: float           # 0.0–1.0 (spectral brightness proxy)
    genre: str               # e.g. "electronic", "hip-hop", "classical"
    beat_times: list[float]  # onset times in seconds
```

**Implementation:** Uses `librosa` for BPM extraction (`beat_track`), chroma features for key estimation, RMS energy, and spectral centroid as a valence proxy. Genre classification uses a pre-trained lightweight classifier (e.g., a fine-tuned MobileNet on mel spectrograms).

**Performance target:** < 5s for a 60s audio clip on a single CPU core.

---

### 4.2 Prompt Builder

Maps `MusicFeatures` → a natural-language video generation prompt.

**Mapping logic (rule-based):**

| BPM range | Energy | Genre hint | Dance style |
|-----------|--------|------------|-------------|
| < 80 | low | any | slow waltz, contemporary |
| 80–110 | medium | pop | jazz, lyrical |
| 110–130 | high | electronic | house, club dance |
| > 130 | high | hip-hop | breakdance, popping |
| any | low | classical | ballet, contemporary |

**Prompt template:**
```
A [gender-neutral] dancer performing [dance_style] to [genre] music at [bpm] BPM.
Fluid, expressive movement. High-fidelity cinematic render. 4K quality.
Shot from a [angle] angle. Mood: [mood_adjective].
```

Mood adjective is derived from valence: < 0.4 → "melancholic", 0.4–0.7 → "energetic", > 0.7 → "euphoric".

---

### 4.3 Video Generation Client (Adapter Layer)

An abstraction layer isolating the backend from any specific video generation API.

```python
class VideoGenerationClient(Protocol):
    async def generate(self, prompt: str, duration_seconds: int) -> str:
        """Returns a URL to the generated MP4."""
        ...

class FalAiClient:
    """Concrete implementation using fal.ai Seedance API."""
    MODEL_ID = "fal-ai/bytedance/seedance/v1/lite/text-to-video"

    async def generate(self, prompt: str, duration_seconds: int) -> str:
        result = await fal_client.subscribe_async(
            self.MODEL_ID,
            arguments={"prompt": prompt, "duration": duration_seconds}
        )
        return result["video"]["url"]
```

This abstraction allows swapping to Seedance 2.0 (or any future model) by replacing only `FalAiClient` — zero changes to calling code.

---

### 4.4 Job Store

A lightweight async job store to support polling from the frontend.

**Schema:**
```
jobs
  id          TEXT PRIMARY KEY
  status      TEXT  -- "pending" | "processing" | "done" | "error"
  result_url  TEXT  -- populated when done
  error_msg   TEXT
  created_at  DATETIME
  updated_at  DATETIME
```

SQLite is used in v1 for simplicity. Redis with TTL can replace it in v2 if horizontal scaling is needed.

---

## 5. API Contract

### POST `/api/generate`
**Request:** `multipart/form-data` with `audio_file` field
**Response:**
```json
{ "job_id": "abc123" }
```

### GET `/api/jobs/{job_id}`
**Response:**
```json
{
  "status": "done",
  "result_url": "https://cdn.fal.ai/...output.mp4"
}
```

---

## 6. Error Handling

| Failure point | Behavior |
|---------------|----------|
| Invalid audio format | 400 with user-friendly message |
| Audio too long (>60s) | 400, suggest trimming |
| librosa analysis fails | 500, fallback to default prompt |
| fal.ai API timeout (>120s) | Mark job as error, surface retry option |
| fal.ai API error | Propagate error message to frontend |

---

## 7. Security Considerations

- Audio files are validated by MIME type and magic bytes before processing
- Files are stored in a temp directory with a UUID filename; original filename is never used in any path operation
- fal.ai API key is read from environment variable only, never logged
- Job IDs are UUIDs (v4); no sequential IDs exposed to clients
- Result URLs are short-lived CDN URLs provided by fal.ai (not stored permanently)

---

## 8. Scalability Path

v1 is a single-process deployment. Bottleneck is the video generation API (external, async). The adapter layer and job store design mean that moving to a worker queue (Celery + Redis) requires only wrapping the generation step — the API surface and frontend do not change.

---

## 9. Open Questions

1. Should the system support audio longer than 60s by automatically trimming to the most energetic segment?
2. What is the acceptable P95 latency budget for the full pipeline?
3. Should genre classification use an embedded model or an external API for higher accuracy?
4. Do we need to watermark generated videos in v1?
