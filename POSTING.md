# Posting to Instagram

For a one-off post made in a chat: research and fact-check it as in WEEKLY_BUILD.md, render it with
`scripts/render_explainer.py` (the default style), then post it as below.

Posting is on request. Nothing posts on a timer.

**Shorthand:** when the owner says **"mpu"**, it means "make a post and upload": post the next
fact-checked item from `queue/` (count=1). Check its row in the latest `reports/week-*.md` first.
If GitHub leaves the run queued for over 20 minutes, the run skips itself; send a fresh request.

**For Claude (when the owner asks to post):**
1. Attach the repo `kartikeyakotnala/Adalatiq-insta` if needed (add_repo).
2. Start the job ("today's posts" = the next 2 in `queue/` by folder name; posts are English only).
   ```
   gh api -X POST repos/kartikeyakotnala/Adalatiq-insta/actions/workflows/publish.yml/dispatches \
     -f ref=main -f 'inputs[mode]=batch' -f 'inputs[count]=2'
   ```
3. Wait ~1–2 minutes per post, then read the run log
   (`gh api repos/kartikeyakotnala/Adalatiq-insta/actions/runs?per_page=1`, then its job logs).
   Lines starting `Published` hold the Instagram links. Report them, and how many remain in the queue.

**For the owner (without Claude):** GitHub → Adalatiq-insta → Actions → Publish to Instagram →
Run workflow → mode `batch`, count `2` → Run. Links appear in the run log and in `published/*/result.json`.

**Test the token without posting:** same, with mode `check`.
