# Website maintenance

The [public site](https://bearatol.github.io/ceo-ai/) is plain HTML, CSS and
JavaScript in `site/`. English is at the root; Russian and Simplified Chinese
have separate pages. There is no build step or third-party runtime dependency.
Edit the three pages together and keep their installation guidance consistent
with [INSTALL.md](../INSTALL.md).

The installation button copies a message. It does not run an installer.
The message names the selected tool, limits installation to the current project,
asks the agent to check the operating system and prerequisites, and points to
the instructions tagged `v0.3.0`.
Without JavaScript, visitors can select the message manually. If clipboard
access fails, the page selects the message and explains how to copy it.

## Checks and publication

Run `python3 -B -m unittest discover -s tests`, `bash scripts/doctor.sh`,
`python3 scripts/check_docs.py` and `python3 scripts/check_site.py`.
The site checker permits an exact list of public files, rejects symlinks and
unexpected files, checks local links and resources, and verifies the font hashes.
This is a validator for the small, reviewed source format, not a general HTML
or JavaScript security scanner. Changes to its allowlist need review.

Preview only `site/`, mounted under `/ceo-ai/`, to match GitHub Pages paths.
Before publishing, check all three languages on desktop and mobile, keyboard
navigation, tool selection, clipboard success and failure, no-JavaScript use,
reduced motion, and the browser console and network panel.

`Publish site` validates the publication tree and uploads only `site/`.
A separate job deploys that artifact using GitHub Pages OIDC permissions.
Both jobs run only on `main`. The `github-pages` environment must restrict
deployments to the `main` branch. Set Pages to GitHub Actions in repository
settings. Official actions are pinned to commit hashes.

There are no analytics, cookies, accounts or forms. All runtime assets are local;
links to GitHub open only when followed. The page CSP blocks outbound fetches,
inline scripts and third-party resources. A meta CSP does not provide all
protections available through response headers, such as `frame-ancestors`.

## Browser verification

On 2026-10-12, Chromium checks for the 0.3.0 site covered all three locales at
320, 390, 768, 1024 and 1440 CSS pixels with no horizontal overflow. All nine
language/tool combinations copied the exact displayed message. Keyboard controls,
denied-clipboard fallback, no-JavaScript scenarios and reduced motion passed.
The workflow animation advanced, paused, resumed and stopped outside the viewport.
No external runtime requests or JavaScript errors were observed. These checks
concern the website, not skill execution in the three host applications.

The checked site tree has SHA-256 `f3367523510b026dc9a5f12f68cd69f1bb1100193ec2dfe4557333b8540a3c9c`.
To reproduce this fingerprint, sort the files under `site/` by POSIX path, form
one UTF-8 line per file as `<SHA-256>  <path>\n`, then hash the concatenated lines.

### Skill example verification on 2026-10-21

The five fictional skill examples were checked in Chromium for English, Russian
and Simplified Chinese at 320, 390, 768 and 1440 CSS pixels. Each example opened
with Enter and closed with Space. Focus outlines were visible, summary targets
were at least 44 pixels high, titles stayed upright and no horizontal overflow
was detected. At 390 pixels, all five examples also worked with JavaScript
disabled in each locale. A Russian mobile screenshot was inspected; Tab and
Shift+Tab returned focus to summaries without placing them behind the header.
No page errors, console errors or external request attempts were observed in
these checks. This verifies the examples' presentation, not skill execution or
assistive-technology conformance. Clipboard and installation flows were not rerun.

All 13 focused site/documentation tests passed. They include checking all five
localized full-story links against actual Markdown files and heading fragments.
The static site validator passed. The Markdown check passed for 97 documents
with the local research `.runtime` directory excluded; its existing unrelated
link errors remain outside this change.

The checked site-tree SHA-256 is
`1f1742bc20d111d75135de2a555cec3f83b0d3c318e832c4b6ffaf04e506b168`,
using the fingerprint procedure above. These are local checks, not a publication
record.

Before publication on 2026-10-21, the full suite ran 242 tests: 215 passed and
27 were skipped. Package integrity, site validation and the 97-document link
check passed. In Chromium, all nine locale/application combinations copied the
displayed installation message; the three extra-scan prompts copied correctly
too. All six denied-clipboard cases selected the full message for manual copying.
Reduced-motion behavior and 390/1440-pixel overflow checks passed in all locales.
Russian desktop and mobile screenshots were visually inspected. These checks
exercise the website controls, not installation in the host applications.

## Design and assets

The visual direction is corporate cyberpunk: graphite panels, orange controls,
restrained blue details, a central AI coordinator and readable body text.
The workflow illustration is decorative, not live agent status. The five skill
dialogues are fictional, satirical examples, not recorded benchmarks or guaranteed
results. Keep the English, Russian and Simplified Chinese cards aligned with
their full `docs/DIALOGUE*.md` scenes and the anchors `ceo`, `writer`,
`security-scan`, `debugger` and `user-review`. Preserve the `#conversation` entry
link, the five unique `example-*` IDs, native `details` controls and CEO open by
default. Keep release availability and the core-only project/APM scope explicit.
App invocation and model behavior remain unverified; preserve that distinction
when updating the copy. The cards require keyboard, narrow-screen and
no-JavaScript checks after changes; the earlier browser record above does not
verify them.

Visual references: the [Arasaka concept by Elias Holtsmann](https://dribbble.com/shots/17141782-Arasaka-Corporation-Landing-Page)
and [Industrial Media interface](https://hostbento.com/templates/industrial-media-portfolio-website-template).
No images, code, logos or other assets from these references are included.
The diagram and icon are original SVGs. The workflow animation has a pause control, stops outside the viewport and in
hidden tabs, and stays static with `prefers-reduced-motion`. The stage labels
describe an illustration, not a live run. Six profession scenarios remain usable
without JavaScript. Author links are explicit navigation to Telegram and LinkedIn;
no third-party widgets are loaded.

Golos Text is included unmodified from the
[Google Fonts repository](https://github.com/google/fonts/tree/c1eda9233c33ad7775b27efd794f931095cf6133/ofl/golostext).
Copyright 2019 The Golos Text Project Authors. The original SIL Open Font License
1.1 is shipped beside the font at `site/assets/fonts/OFL.txt`; the repository's
MIT license does not replace it. Chinese uses the visitor's system CJK font.

SHA-256 provenance:

```text
GolosText.ttf  17bb58fb69aec2dfb047a2ebf52534023e9b688c97a6b7ac795b0a72912c2063
OFL.txt       ff532f9e8789f09a9fdffc3c0954eedfb0a48be77b2e2eb90f5f82e4f347f50c
```
