# REAU Studio

The REAU Studio website, deployed on Netlify.

## Structure

- `site/` – the published website (Netlify serves this folder)
  - `index.html` – home page
  - `consultation.html` – consultation request form (Netlify Forms)
  - `work/` – case study pages (generated, see below)
  - `journal/` – journal articles
  - `assets/` – images, logos, and the Dalmatian animation frames
- `cases/` – case study content and the page builder
  - `<slug>.json` – one file per case study
  - `build.py` – turns every case study file into `site/work/<slug>.html`

## Adding or editing a case study

1. Edit or add a JSON file in `cases/`.
2. Put its images in `site/assets/work/<slug>/`, using the filenames referenced in the JSON. Any image that is missing shows a labelled placeholder.
3. Run `python3 cases/build.py`, then commit and push. Netlify redeploys automatically.

## Consultation form

Submissions are handled by Netlify Forms. In Netlify, enable form detection and add an email notification for the `consultation` form.
