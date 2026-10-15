# Deploying to Cloudways

Target: Cloudways application **6730149** ("Appliance-error-codes", 2027 Server,
project `affiliate-sites`).

The site is static HTML. It needs no PHP, no database and no Composer step, which is why
it will be fast on a shared PHP stack. The build writes a complete document root to
`dist/`, including `.htaccess`.

## What I could and could not do from this session

I do not have Cloudways credentials in this environment, so I could not push to the
application myself. Everything below is ready; the connecting step is yours and takes a
couple of minutes. Pick option A or option B.

---

## Option A: Git deployment from Cloudways (recommended)

GitHub Actions publishes to a branch called `deploy`, whose root **is** the document root —
exactly the shape Cloudways' git deployment expects. You connect once, and after that the
site updates itself: a daily workflow releases each wave of pages on its scheduled day
(see `RELEASE.md`). You do not need to push, and your machine does not need to be on.

1. In the Cloudways panel open the application, then **Deployment via Git**.
2. Click **Generate SSH Keys** if you have not already, and copy the public key.
3. In GitHub go to `faisalirshad320/Appliance-error-codes` → **Settings → Deploy keys →
   Add deploy key**. Paste the key, name it `cloudways`, and leave write access off.
4. Back in Cloudways, set:
   - **Git Remote Address**: `git@github.com:faisalirshad320/Appliance-error-codes.git`
   - **Branch**: `deploy`
   - **Deployment Path**: leave empty, so it deploys to `public_html` itself
5. Click **Start Deployment**.
6. For later updates, use **Pull/Deploy** in the same screen, or set up the auto-deploy
   webhook Cloudways offers on that page.

To publish on demand at any point, run the workflow manually from the **Actions** tab
(`Release due pages` → **Run workflow**). It will never publish a wave early — it only
ever ships what the schedule says is due.

## The deploy branch holds only what is released

`dist/` is build output and is not tracked on the source branch. The `deploy` branch is
published and ready to connect. It does **not** contain all 252 pages: it contains the
waves that have gone live so far, which on launch day is the 16-page seed. The rest arrive
on their own schedule over the following three months. `RELEASE.md` explains why, and
`python3 tools/release_status.py` tells you where the drip has got to.

Set the Cloudways **Deployment Path** to empty. If you set it to `dist`, every page will
404, because there is no `dist` directory on this branch; the files are at the top level.

## Option B: rsync over SSH

Faster for a one-off and does not need the deploy branch.

```bash
# Build locally
python3 site/build.py

# Credentials are in Cloudways under Application → Access Details (the screen you linked).
# Master credentials live under Server → Master Credentials.
rsync -avz --delete \
  -e "ssh -p 22" \
  dist/ \
  <application_user>@<server_public_ip>:applications/<app_folder>/public_html/
```

`--delete` removes files that no longer exist in the build. That is what you want for a
generated site, but it does mean anything you uploaded into `public_html` by hand will be
wiped. Check the directory is empty of anything precious before the first run.

---

## After the first deploy

1. **The domain is already set.** `site/config.json` carries
   `https://appliancecodex.com`, which drives every canonical tag, the Open Graph URLs
   and the sitemap. If you ever serve the site from a different hostname, change it there
   and the next daily release picks it up.
2. **Attach the domain in Cloudways** under **Domain Management**, then issue a Let's
   Encrypt certificate under **SSL Certificate**. The `.htaccess` already forces HTTPS via
   the `X-Forwarded-Proto` header, which is the correct check behind the Cloudways proxy.
3. **Enable the canonical-host redirect.** `.htaccess` ships with the www-to-apex rule
   commented out. Uncomment whichever direction you want once the domain resolves.
4. **Submit the sitemap** at `https://appliancecodex.com/sitemap.xml` in Google Search Console and
   Bing Webmaster Tools.
5. **Turn on Cloudways Varnish** for the application. A static site benefits enormously and
   there is no session state to break.

## Health check after deploying

```bash
curl -sI https://appliancecodex.com/                       # expect 200
curl -sI https://appliancecodex.com/samsung/washer/4c-error-code/  # expect 200
curl -sI https://appliancecodex.com/nope/                  # expect 404, not 200
curl -s  https://appliancecodex.com/robots.txt             # sitemap line points at your domain
curl -sI https://appliancecodex.com/assets/main.css | grep -i cache-control
```

If pages 404, the deployment path is pointing one directory too deep. The document root
should contain `index.html` directly, not a `dist` folder.
