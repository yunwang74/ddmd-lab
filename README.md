
# DDMD Lab Website (Gold & Silver theme)

A simple static site for the Data-Driven Materials Design Lab, ready for GitHub Pages. Publications are auto-updated from ORCID **without any token**.

## Structure
```
.
├── assets/
│   └── css/main.css
├── scripts/
│   └── update_publications.py
├── .github/workflows/update-publications.yml
├── index.html
├── publications.html
├── first-principles.html
├── ai-assisted.html
├── people.html
├── join.html
└── 404.html
```

## Deploy to GitHub Pages
1. Create a repository (e.g. `ddmd-lab`) under your account.
2. Copy these files to the repo root and push to `main`.
3. In **Settings → Pages**, choose **Deploy from a branch**, set **Branch = main** and **Folder = /** (root).
4. Your site will be available at `https://<username>.github.io/ddmd-lab/`.

## Auto-update publications
- The workflow runs daily at 03:00 UTC or manually via **Actions → Update Publications from ORCID → Run workflow**.
- It fetches from `https://pub.orcid.org/v3.0/0000-0001-8619-0455/works` and writes inside the HTML markers on `publications.html`.
- No `ORCID_TOKEN` is required.

## Editing notes
- Colors and typography live in `assets/css/main.css`.
- Navigation is duplicated across pages for simplicity. For larger sites, consider a generator (Jekyll, Eleventy) later.

## License
MIT — use and modify freely.
