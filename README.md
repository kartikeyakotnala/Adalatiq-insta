# AdalatIQ Instagram

Automated legal-awareness carousels for AdalatIQ's Instagram.

**How it works**
1. Every Sunday, Claude researches 14 common legal questions (each posted in English and Hindi) from government sources only, has every claim
   fact-checked independently, and renders the slides. Fact-check reports are kept in `reports/`.
2. The week's posts are committed to `queue/` and you get a summary. They post automatically; to stop one before
   its time, delete its folder from `queue/`. To remove a live post, delete it on Instagram.
3. The `Publish to Instagram` workflow runs at 09:37, 13:37, 18:37 and 21:37 IST and posts the next due carousel from `queue/`,
   then moves it to `published/` with a link to the live post.

**Folders**
- `queue/` – approved posts waiting for their time (`YYYY-MM-DD-HHMM-<id>-<lang>`, time in IST)
- `published/` – posts already live, each with `result.json` holding the Instagram link
- `topics.md` – the question bank; `WEEKLY_BUILD.md` – the rules Claude follows
- `scripts/render.py` – turns `post.json` into slides; `scripts/publish.py` – posts via Instagram's official API

**Handy controls**
- Test the token without posting: Actions → Publish to Instagram → Run workflow → `check`.
- Stop a post: delete its folder from `queue/` before its time.
- Pause everything: Actions → Publish to Instagram → ⋯ → Disable workflow.
- The token lives only in Settings → Secrets → `IG_TOKEN`. Never commit it.
