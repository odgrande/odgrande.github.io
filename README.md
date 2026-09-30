# Odunayo Bolarinwa Portfolio

Static GitHub Pages portfolio adapted from the visual language and structure of the free Grunge template. A small Python build script keeps the portfolio folder-driven.

## Folder-driven content

`assets/Odunayo Portfolio Assets/` is the **authoritative** source for all project media. Add media directly inside the matching project folder there and it will be picked up during the next build.

The legacy slugified `assets/projects/` collection is deprecated and is never scanned by the build — do not add new content there.

### Projects
`assets/Odunayo Portfolio Assets/<Project Folder Name>/`

Folder names can be human-readable (e.g. `GlowBar Project`); the build script slugifies them automatically to match the entries in `scripts/site_config.json`.

Images (`jpg`, `jpeg`, `png`, `webp`, `gif`, `avif`, `svg`) appear in the project gallery automatically.
Videos (`mp4`, `webm`, `mov`, `m4v`, `ogg`) appear above the gallery automatically.

Optional `project.json` or `meta.json` inside a project folder can override its title, category, services, year, description and live URL.

If a project folder has not yet been moved into `assets/Odunayo Portfolio Assets/`, the build also looks for a matching folder directly under `assets/` (excluding `assets/projects/`), so nothing breaks mid-migration. Once both exist, the copy inside `assets/Odunayo Portfolio Assets/` wins.

### Blastfest testimonial
Drop the future testimonial/project video into the `Blast Music Fest Project` folder (inside `assets/Odunayo Portfolio Assets/` once migrated).

The project page already has a fallback placeholder, so the real video will replace the placeholder after the next build.

### Personal media
`assets/Odunayo Portfolio Assets/Personal images/` feeds the About page visual archive.
`assets/Odunayo Portfolio Assets/Personal Videos/` is reserved for future personal video additions.

### Credentials
`assets/Odunayo Portfolio Assets/Personal images/Award Images/` feeds Awards.
`assets/Odunayo Portfolio Assets/Certifications/` (or `assets/Certifications/` until migrated) feeds Certificates.

## Local build

Requires Python 3.10+.

```bash
python scripts/build_portfolio.py
```

The generated website is written to `site/`. The GitHub Actions workflow runs this same build automatically on every push to `main`, then publishes `site/` to GitHub Pages.
