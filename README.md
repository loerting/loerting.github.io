# Loerting Games website

Static site for Loerting Games: Vena, What the Buck?! and Fish Don't Return. Plain
HTML, one stylesheet, one small script. No build step: GitHub Pages serves the repo
as it is. Design rules are in [DESIGN.md](DESIGN.md).

```
index.html              studio page with the game cards
de/                     German pages, built by tools/build_de.py
vena/                   Vena page and its Android privacy policy
what-the-buck/          What the Buck?! page
fish-dont-return/       Fish Don't Return page
press/                  facts and downloads for press
legal/                  imprint and privacy
404.html                GitHub Pages serves it for missing pages
assets/css|js|fonts     style, behaviour, self-hosted fonts (OFL)
assets/media/           built images and clips (tools/build_media.py)
assets/press/           press kit PDF and asset zips
tools/                  media build, screenshot grid markup, site check
```

## Working on it

```sh
python3 -m http.server 8765        # then open http://127.0.0.1:8765
tools/check_site.py                # links, anchors, alt/size, download sizes, banned characters
tools/check_site.py --external     # also requests every external link
tools/build_media.py               # rebuild missing media (--force for all)
```

German pages under `de/` are built from the English ones. After changing English text,
run `tools/build_de.py` and add the German for any new sentence to `tools/de.py`;
`check_site.py` lists every English sentence still left on a German page. The German
uses "du", like Vena's German translation.

`build_media.py` reads the sources on the author's machine: the Steam store (cached in
`.cache/`), the vertical clips in `/mnt/nvme/09_ShortClips` and
`~/fish-dont-return-clips`, the Fish Don't Return marketing folder, the Vena logo zip
and the What the Buck?! press kit zip (its trailer is cut into the vertical clips).
Fish Don't Return's logo, capsules, screenshots and press downloads all come from its
marketing folder, which is ahead of its Steam page; only its hero is read from Steam.
Paths can be overridden with `VENA_CLIPS`, `FDR_CLIPS`, `FDR_MARKETING`,
`VENA_LOGOS_ZIP` and `WTB_KIT_ZIP`. Which clip plays where is the `CLIPS` table at the
top.

## Going live on GitHub Pages

1. Create a public repository named `loerting.github.io` and push `main`. A repo with
   that name is served from the root, which the `404.html` links expect.
2. Settings → Pages → Build and deployment: *Deploy from a branch*, `main`, `/ (root)`.
   The site appears at `https://loerting.github.io/` after a minute or two.
3. Turn off Pages in the old `loerting/vena` repo (Settings → Pages → *Unpublish site*,
   or set the source to *None*). Until then that repo keeps `/vena/` for its link page.
   The Vena Android privacy policy lives on here at the same addresses
   (`/vena/PRIVACY_POLICY`, `.html` and `.md`), so the Google Play link keeps working.

## Domain from Porkbun

In this order, so nobody else can claim the domain on GitHub in between:

1. GitHub → your profile Settings → Pages → *Add a domain*. In Porkbun (Domain
   Management → the domain → DNS) add the `TXT` record GitHub shows: host
   `_github-pages-challenge-loerting`, answer = the code. Then click *Verify*.
2. Repo Settings → Pages → *Custom domain*: enter the domain and save. GitHub commits a
   `CNAME` file, so `git pull` before the next push.
3. In Porkbun's DNS, delete the default parking records (`pixie.porkbun.com`), then add:
   - `A`, host empty: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `AAAA`, host empty: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `CNAME`, host `www`: `loerting.github.io`
4. Once the DNS check in the Pages settings is green, tick *Enforce HTTPS*. `www` then
   redirects to the bare domain, and old `loerting.github.io` links redirect too.
5. Make the `og:image` URLs absolute (`https://<domain>/assets/media/...`) so link
   previews work everywhere.
