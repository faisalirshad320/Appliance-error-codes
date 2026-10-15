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

GitHub Actions builds the site on every push to `main` and force-pushes the built document
root to a branch called `deploy`. The root of `deploy` **is** the document root, which is
exactly the shape Cloudways' git deployment expects. You connect once and then every future
content change is a `git push`.

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

The `deploy` branch only exists after the first push to `main` runs the workflow. If you
want it immediately, run the workflow manually from the **Actions** tab
(`Build and validate site` → **Run workflow**).

## Option C: deploy branch already exists

`dist/` is build output and is not tracked on this branch. A ready-to-serve `deploy` branch
is published directly, so you can connect Cloudways to it immediately without waiting for a
GitHub Actions run. Its root is the document root. Option A's connect steps apply unchanged;
Actions simply keeps it up to date afterwards.

To refresh it by hand at any time:

```bash
python3 site/build.py
cd dist
git init -q && git add -A && git commit -qm "build"
git push -f git@github.com:faisalirshad320/Appliance-error-codes.git HEAD:deploy
```

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

1. **Set the real domain.** Edit `site/config.json` and change `site_url` from the
   placeholder to your live domain, then rebuild and redeploy. That value drives every
   canonical tag, the Open Graph URLs and the sitemap, so leaving the placeholder in place
   will actively harm indexing.
2. **Attach the domain in Cloudways** under **Domain Management**, then issue a Let's
   Encrypt certificate under **SSL Certificate**. The `.htaccess` already forces HTTPS via
   the `X-Forwarded-Proto` header, which is the correct check behind the Cloudways proxy.
3. **Enable the canonical-host redirect.** `.htaccess` ships with the www-to-apex rule
   commented out. Uncomment whichever direction you want once the domain resolves.
4. **Submit the sitemap** at `https://yourdomain/sitemap.xml` in Google Search Console and
   Bing Webmaster Tools.
5. **Turn on Cloudways Varnish** for the application. A static site benefits enormously and
   there is no session state to break.

## Health check after deploying

```bash
curl -sI https://yourdomain/                       # expect 200
curl -sI https://yourdomain/samsung/washer/4c-error-code/   # expect 200
curl -sI https://yourdomain/nope/                  # expect 404, not 200
curl -s  https://yourdomain/robots.txt             # sitemap line points at your domain
curl -sI https://yourdomain/assets/main.css | grep -i cache-control
```

If pages 404, the deployment path is pointing one directory too deep. The document root
should contain `index.html` directly, not a `dist` folder.
