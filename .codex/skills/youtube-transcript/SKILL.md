---
name: youtube-transcript
description: Extract and analyse YouTube video transcripts. Use when the user shares
  a YouTube URL or asks you to watch, review, summarise, or extract information from
  a YouTube video. Handles URL parsing, transcript fetching via the youtube-transcript-api
  Python library, and structured content extraction. Do NOT attempt to "watch" videos
  or scrape YouTube directly — this skill is the only reliable path.
allowed-tools: Bash(python3 *), Bash(python *), Bash(youtube_transcript_api *), Bash(pip
  install youtube-transcript-api), Read, Write
metadata:
  short-description: Extract and analyse YouTube video transcripts.
---

# YouTube Transcript Extraction

You are extracting and analysing the transcript of a YouTube video. The user has given you a video URL or ID and wants you to pull out useful information.

---

## Critical: What Does NOT Work

Agents consistently fail at YouTube transcript extraction by trying approaches that look plausible but return nothing useful. **Do not attempt any of these:**

- **WebFetch on YouTube** — returns bot-blocked HTML, no transcript data
- **WebFetch on transcript web services** (youtubetranscript.com, kome.ai, tactiq.io, etc.) — all render via client-side JavaScript; WebFetch gets the marketing page, not the transcript
- **YouTube timedtext API** (`/api/timedtext?v=...`) — returns 0 bytes server-side
- **YouTube InnerTube API** — returns UNPLAYABLE or no caption data
- **Invidious API** — most public instances have API disabled or block server requests
- **Asking the user to copy-paste the transcript** — defeats the purpose

**The only reliable method is the `youtube-transcript-api` Python library via Bash.** This is not a fallback — it is the primary and only path.

---

## Step 1: Extract the Video ID

YouTube URLs come in several formats. Extract the 11-character video ID:

| URL Format | Example | Video ID |
|---|---|---|
| Standard | `https://www.youtube.com/watch?v=iUSdS-6uwr4` | `iUSdS-6uwr4` |
| Short | `https://youtu.be/iUSdS-6uwr4` | `iUSdS-6uwr4` |
| Short with params | `https://youtu.be/iUSdS-6uwr4?si=abc123` | `iUSdS-6uwr4` |
| Embed | `https://www.youtube.com/embed/iUSdS-6uwr4` | `iUSdS-6uwr4` |
| Shorts | `https://www.youtube.com/shorts/iUSdS-6uwr4` | `iUSdS-6uwr4` |
| With timestamp | `https://www.youtube.com/watch?v=iUSdS-6uwr4&t=120` | `iUSdS-6uwr4` |
| Bare ID | `iUSdS-6uwr4` | `iUSdS-6uwr4` |

Use Python to extract reliably:

```bash
python3 -c "
import re, sys
url = 'THE_URL_OR_ID'
patterns = [
    r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/|v/))([a-zA-Z0-9_-]{11})',
    r'^([a-zA-Z0-9_-]{11})$'
]
for p in patterns:
    m = re.search(p, url)
    if m:
        print(m.group(1))
        sys.exit(0)
print('ERROR: Could not extract video ID from:', url, file=sys.stderr)
sys.exit(1)
"
```

---

## Step 2: Fetch the Transcript

Run this via Bash. Replace `VIDEO_ID` with the extracted ID:

```bash
python3 << 'PYEOF'
from youtube_transcript_api import YouTubeTranscriptApi

VIDEO_ID = "VIDEO_ID"

api = YouTubeTranscriptApi()

# Try fetching — prefers manual captions, falls back to auto-generated
try:
    transcript = api.fetch(video_id=VIDEO_ID)
    full_text = ' '.join(snippet.text for snippet in transcript)
    print(full_text)
except Exception as e:
    print(f"ERROR: {e}")
    # List available transcripts to diagnose
    try:
        transcript_list = api.list(video_id=VIDEO_ID)
        print(f"\nAvailable transcripts: {transcript_list}")
    except Exception as e2:
        print(f"Could not list transcripts either: {e2}")
        print("This video may have captions disabled or be region-restricted.")
PYEOF
```

**If `youtube-transcript-api` is not installed**, install it first:

```bash
pip install youtube-transcript-api
```

### Language selection

If the user wants a specific language, or the default fails:

```bash
python3 << 'PYEOF'
from youtube_transcript_api import YouTubeTranscriptApi

VIDEO_ID = "VIDEO_ID"
api = YouTubeTranscriptApi()

# List what's available
transcript_list = api.list(video_id=VIDEO_ID)
print("Available transcripts:")
for t in transcript_list:
    print(f"  {t.language} ({t.language_code}) - {'generated' if t.is_generated else 'manual'}")

# Fetch specific language
transcript = api.fetch(video_id=VIDEO_ID, languages=['en'])
print('\n' + ' '.join(s.text for s in transcript))
PYEOF
```

---

## Step 3: Process the Transcript

The raw transcript is a continuous text block. Before analysis, assess its size — long videos (60+ min) can produce 30,000+ characters.

### For the user's request, pick the appropriate output:

**If asked to summarise:** Provide a structured summary — key topics, main arguments, conclusions. Include timestamps if the user asked for them (available in the `snippet.start` field).

**If asked to extract specific information:** Search the transcript for the relevant content and quote the key passages.

**If asked for a full transcript:** Write it to a file rather than dumping it into chat. Use markdown with paragraph breaks where topic shifts occur.

**If asked to "watch" or "review" the video:** Treat this as a summarise request — the user wants the key takeaways, not a literal play-by-play.

### Writing transcript to file

For long transcripts, write to a file:

```bash
python3 << 'PYEOF'
from youtube_transcript_api import YouTubeTranscriptApi

VIDEO_ID = "VIDEO_ID"
api = YouTubeTranscriptApi()
transcript = api.fetch(video_id=VIDEO_ID)

with open("transcript_VIDEO_ID.md", "w") as f:
    f.write(f"# YouTube Transcript: VIDEO_ID\n\n")
    current_paragraph = []
    last_end = 0
    for snippet in transcript:
        # Break paragraphs on gaps > 2 seconds (topic shifts)
        if snippet.start - last_end > 2.0 and current_paragraph:
            f.write(' '.join(current_paragraph) + '\n\n')
            current_paragraph = []
        current_paragraph.append(snippet.text)
        last_end = snippet.start + (snippet.duration or 0)
    if current_paragraph:
        f.write(' '.join(current_paragraph) + '\n')

print(f"Transcript written to transcript_VIDEO_ID.md")
PYEOF
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `TranscriptsDisabled` | Video owner disabled captions | Cannot extract — tell the user |
| `NoTranscriptFound` | No captions in requested language | List available languages (Step 2 language selection) and try another |
| `VideoUnavailable` | Private, deleted, or region-restricted | Cannot extract — tell the user |
| `ModuleNotFoundError` | Library not installed | `pip install youtube-transcript-api` |
| Empty or garbled text | Auto-generated captions on poor audio | Note this to the user — the transcript quality reflects YouTube's auto-captioning |

---

## What NOT to Do

- Do not try WebFetch, curl, or any HTTP-based approach to get transcripts — they all fail
- Do not install headless browsers (selenium, playwright) just to get a transcript — the Python library handles it without a browser
- Do not apologise and say you "can't watch videos" — you can extract and read the transcript, which contains the full spoken content
- Do not truncate long transcripts without telling the user — write to file instead
