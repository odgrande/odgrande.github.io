# Odunayo Bolarinwa Portfolio

Static GitHub Pages portfolio adapted from the visual language and structure of the free Grunge template. A small Python build script keeps the portfolio folder-driven.

## Folder-driven content

Add media directly inside the matching folder and it will be picked up during the next build.

### Projects
`assets/projects/<project-folder>/`

Images (`jpg`, `jpeg`, `png`, `webp`, `gif`, `avif`, `svg`) appear in the project gallery automatically.
Videos (`mp4`, `webm`, `mov`, `m4v`, `ogg`) appear above the gallery automatically.

Optional `project.json` or `meta.json` can override project title, category, services, year, description and live URL.

### Blastfest testimonial
Drop the future testimonial/project video into:
`public/assets/projects/blast-music-fest-project/`

The project page already has a fallback placeholder, so the real video will replace the placeholder after the next build.

### Personal media
`assets/personal/images/` feeds the About page visual archive.
`assets/personal/videos/` is reserved for future personal video additions.

### Credentials
`assets/credentials/awards/` feeds Awards.
`assets/credentials/certificates/` feeds Certificates.

The current Designer of the Year asset has already been copied into the Awards folder.

## Local build

Requires Python 3.10+.

```bash
python scripts/build_portfolio.py
```

The generated website is written to `site/`. The GitHub Actions workflow runs this same build automatically on every push to `main`, then publishes `site/` to GitHub Pages.
