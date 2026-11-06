# Weekly build playbook

Claude follows this every Sunday to prepare next week's 14 Instagram carousels for AdalatIQ:
14 questions, **English only** (2 posts a day).
The output is committed straight to `main` and waits in `queue/`. The owner posts it on request, usually 4 at a time
(see POSTING.md), and removes anything wrong after the fact, so the fact-check below is the only gate: be strict.

## The non-negotiables

1. **Government sources only.** Every fact must come from an official source:
   indiacode.nic.in, egazette.gov.in, legislative.gov.in, a ministry or department site (`*.gov.in`, `*.nic.in`),
   nalsa.gov.in or a State/District Legal Services Authority, sci.gov.in or a High Court site, pib.gov.in,
   a regulator (RBI, SEBI, IRDAI, TRAI…) or an official government handbook/PDF.
   Blogs, law-firm sites, news sites, coaching sites and Wikipedia may help you *find* a source, but are never the source.
2. **No guessing.** If a claim can't be matched to the official text, cut it. If the post can't stand without it, drop the topic.
3. **Current law.** Criminal law is now BNS / BNSS / BSA (in force from 1 July 2024), not IPC / CrPC / Evidence Act.
   Check every Act you cite for later amendments.
4. **State-dependent rules** (income limits, rent laws, minimum wage, stamp duty…): say "depends on your State"
   rather than quoting one State's number as if it applied everywhere.
5. **Every answer slide carries a reference** (Act + section, or the official body). The last slide lists sources.
6. **Every caption** ends with the disclaimer, the link, and the fixed hashtags `#UPSC #Constitution #Exam #Job #AdalatIQ`
   (in both languages) after 2–3 topic hashtags — see the template below. The renderer refuses a caption without them.

## Steps

### 1. Set up
```
git clone https://github.com/kartikeyakotnala/Adalatiq-insta.git && cd Adalatiq-insta   # if access is refused, attach the repo first (add_repo, push access)
pip install playwright --break-system-packages   # only if `import playwright` fails
```
Read `topics.md` and list what's already in `queue/` and `published/` so nothing repeats.

### 2. Pick 14 topics
Take the first 14 unticked topics in `topics.md` (skip any that clearly need State-specific numbers you can't verify
for all States). Each topic becomes **one English post** (`lang: "en"`) with a 3-digit id continuing from the highest id
used so far (e.g. `015-landlord-deposit-en`). **Posts are English only** — do not make Hindi or other language versions.
If fewer than 30 unticked topics remain after this week, add 20 new common, timeless legal questions to `topics.md`
(no duplicates, no news-driven topics). The renderer still supports other languages if that ever changes.

### 3. Research (one topic at a time)
For each topic: find the governing Act/section or official scheme on an official site, read the actual text,
and write down each claim with its source URL and section. Keep a research note per post in the PR description.

### 4. Write the post (`post.json`)
Write it in the target language from the start — natural everyday language, not a word-for-word translation.
Use the official name of the Act in that language if one exists; otherwise keep the English name.
Section numbers and helpline numbers stay as digits.

```json
{
  "id": "003-landlord-deposit",
  "lang": "en",
  "hook": "The common worry, as people say it.",
  "hook_q": "The question, short. Ends with ?",
  "slides": [
    {"title": "Short answer headline.", "body": "One or two plain sentences.", "ref": "Act Year · Sec N"},
    {"title": "A list slide.", "list": ["Point", "Point", "Point"], "ref": "Act Year · Sec N(a)"}
  ],
  "sources": ["Full Act name, Year – Section N", "Official body (site.gov.in)"],
  "caption": "…"
}
```
Explainer extras (use them; they're what makes the style work):
- Wrap the 1–3 most important words of the hook, each title and occasionally a body in `**double asterisks**`
  to draw the coral highlighter. Never highlight more than one phrase per line.
- For date-based or step-by-step answers, use a timeline slide instead of a body:
  `{"title": "Two dates that **matter.**", "timeline": [{"date": "20 Dec 2004", "text": "..."}], "ref": "..."}` (2–4 items).
- Optionally add `"note"`: a short handwritten aside (under 8 words). Notes and timeline items are claims too, so the
  fact-checker must verify them.
Rules: 3–7 answer slides; titles under ~8 words; bodies under ~35 words; lists 3–5 items.
Caption template (in the post's language):
```
<hook line> 👇

<3–6 short points, one per line>

Source: <Act, Section>

<disclaimer: AI-assisted, for general awareness only, not legal advice, speak to a lawyer>

<Like & follow @adalatiq for daily legal facts and know-your-rights tips (in the post's language)>

<Stuck with a legal problem? Ask AdalatIQ free → adalatiq.com>

<2–3 topic hashtags> #UPSC #Constitution #Exam #Job #AdalatIQ
```
Hashtags are always in English (Latin letters).
```
```

### 5. Independent fact-check (required)
Spawn a separate agent that has **not** seen your drafting. Give it only the `post.json` files and the list of
official source URLs. Ask it to open each source and mark every claim on every slide and in every caption as
VERIFIED (quote the matching official text), WRONG, or UNSUPPORTED.  Fix or cut anything not VERIFIED, then re-check those claims. Drop a post that still fails.

### 6. Schedule and render
Two posts per day of the coming week (Monday to Sunday). The folder name sets the posting order, so name them
`0930` (first topic) and `1830` (second topic) for each date. Folder name: `queue/YYYY-MM-DD-HHMM-<id>-<lang>/post.json`.
```
python3 scripts/render_explainer.py queue/<each new folder>   # default style: explainer (paper, serif, highlighter)
# Reels are PAUSED (owner wants to approve the music first). Do not run animate_reel.py until POST_REELS is
# set to "true" in .github/workflows/publish.yml.
# python3 scripts/animate_reel.py queue/<each new folder>
```
The carousel slides include the Nyaya mascot automatically. The posting job publishes the carousel (and the Reel, once Reels are resumed).
Look at every rendered slide (build a contact sheet and view it). Fix overflow, cut-off words or broken script,
and re-render.

### 7. Commit, push and report
Tick the used topics in `topics.md` with their ids and languages. Commit to `main` with the message
`Instagram posts: week of <Monday's date>` and push. Posts go out when the owner asks (see POSTING.md).

Then send the owner a short report:
- how many posts are queued, with each question, in order;
- anything dropped and why;
- anything worth a closer look (e.g. State-dependent rules);
- that they can post the day's 4 by asking Claude in any chat ("post today's AdalatIQ posts"), and can skip a post
  by deleting its folder from `queue/` on GitHub
  (https://github.com/kartikeyakotnala/Adalatiq-insta/tree/main/queue).
Also write the fact-check results to `reports/week-<Monday's date>.md` in the same commit, so there is a record.
