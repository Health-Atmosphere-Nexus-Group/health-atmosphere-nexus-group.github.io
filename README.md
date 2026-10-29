# HANG website

Website of the Health-Atmosphere Nexus Group (UTHealth School of Public Health), rebuilt from the former Wix site.
It is a [Jekyll](https://jekyllrb.com/) site: GitHub Pages builds and hosts it for free, and the content lives in
plain-text files that anyone with access to the repository can edit.

## Where to edit what

| To change | Edit |
|---|---|
| People | `_data/people.yml` (photos in `images/people/`) |
| Moments | `_data/moments.yml` (photos in `images/moments/`) |
| Publication cards (Research page) | `_data/publications.yml` |
| Datasets | `_data/datasets.yml` (Zenodo links) |
| Page text | `index.md`, `capabilities.md`, `research.md`, `opportunities.md`, `people.md`, `teaching.md` |
| Capabilities picture grid | `services:` list at the top of `capabilities.md` |
| Research figures | `figures:` list at the top of `research.md` |
| Opportunities videos | `videos:` list at the top of `opportunities.md` |
| Home banner (title, video) | top of `index.md` |
| Menu | `_data/navigation.yml` |
| Header, footer | `_includes/header.html`, `_includes/footer.html` |
| Colours, fonts, spacing | `assets/css/site.css` |

`teaching.md` and `publications.md` are hidden pages (not in the menu), as on the original site.

## Editing on github.com (nothing to install)

1. Open the file in the repository and click the pencil icon (**Edit this file**).
2. Make the change and click **Commit changes**.
3. The site updates within a minute or two (progress is shown under the **Actions** tab).

To add a photo, open the folder (for example `images/people`) and use **Add file → Upload files**.
Keep photos reasonably small (under ~500 KB); any size works, they are cropped automatically.

## Common tasks

In the YAML files, indentation matters: copy an existing entry and keep the same spaces.

**Add a person** – in `_data/people.yml`, under `members:` (or `collaborators:`), in the position where they should appear:

```yaml
  - name: Jane Doe, MPH
    role: PhD Student (2026-)
    photo: people/jane-doe.jpg
    linkedin: https://www.linkedin.com/in/janedoe/
    bio: |
      Jane is a PhD student in ...

      Fun Facts: ...
```

`email`, `uthealth`, `scholar` and `linkedin` are optional; icons appear only for the links you fill in.

**Add a moment** – at the top of `_data/moments.yml` (newest first; pictures alternate left/right automatically):

```yaml
- title: Our group at the 2026 AGU Annual Meeting
  date: December 2026
  image: moments/2026-12-agu.jpg
  text: |
    Group members presented ...
```

Use `youtube: https://www.youtube.com/watch?v=...` instead of `image:` to show a video.

**Add a publication** – at the top of `_data/publications.yml`:

```yaml
- year: 2026
  journal: Environmental Health Perspectives
  title: Title of the paper
  link: https://doi.org/...
```

The first 12 cards are shown; **Show More** reveals the rest.

**Add a dataset** – at the top of `_data/datasets.yml` (newest first):

```yaml
- title: Name of the dataset
  authors: Jane Doe, Yun Hang
  year: 2026
  license: CC BY 4.0
  zenodo: https://zenodo.org/records/1234567
  doi: 10.5281/zenodo.1234567
  paper: https://doi.org/10.xxxx/xxxxx
  description: |
    What the data contain, coverage, resolution ...
```

Only `title`, `zenodo` and `description` are needed; the rest is optional (`image:` adds a preview picture).
To hide the Datasets page from the menu, delete its two lines in `_data/navigation.yml`.

## Automatic publication updates

Every Monday, GitHub checks [OpenAlex](https://openalex.org) (a free scholarly database covering the same papers as
Google Scholar) for journal papers co-authored by Yun Hang that are not on the website yet, and adds them to the top of
`_data/publications.yml`; the website updates a few minutes later. Any co-author position counts, so students'
first-author papers with her as a co-author are included.

- **Only verified papers are added:** on the paper, her affiliation must name one of the `institutions` in
  `_config.yml`, or the publisher's record (Crossref) must list her ORCID. Papers that fail both checks are not
  added; they are listed in the run log (Actions tab) and can be added by hand.
- **To take a paper down,** delete its four lines in `_data/publications.yml`. The update remembers every paper it
  added (`_data/publications_added.yml`) and never adds it again.
- **To block a paper before it appears,** add its DOI to `_data/publications_exclude.yml`.
- **To run the update right away:** Actions → Update publications → Run workflow.

Settings (`openalex` in `_config.yml`): OpenAlex author ID, ORCID, accepted institutions, and the date from which
papers are added. Preprints, datasets and conference abstracts are always skipped.

In public repositories GitHub pauses scheduled runs after 60 days without any commits (it emails a warning first);
switch the update back on in the Actions tab. This does not apply to private repositories.

## Text formatting (Markdown)

- A blank line starts a new paragraph; `<br>` breaks a line inside a paragraph.
- `## Heading` is an orange section heading, `### Heading` a black sub-heading.
- Links: `[link text](https://example.org)`.
- `{% include group-name.html %}` prints *Health-Atmosphere Nexus Group* with orange initials (page files only).
- `[People](people.html){:.cap}` is a link with an orange first letter, as on the home page.
- `{:.small}` on the line directly under a paragraph makes it small print.

## Preview on your computer (optional)

Needs Ruby 3 (macOS: `brew install ruby@3.3`). In this folder:

```bash
bundle install
bundle exec jekyll serve
```

Then open http://localhost:4000. The preview reloads when you save a file (restart it after editing `_config.yml`).

## Publishing with GitHub Pages

1. Put this folder in a GitHub repository.
2. **Settings → Pages → Build and deployment**: Source *Deploy from a branch*, branch `main`, folder `/ (root)`.
3. The site appears at `https://<user>.github.io/<repository>/`.

Custom domain (e.g. `www.utsph-hang.org`): enter it under **Settings → Pages → Custom domain**, then at the domain
registrar add a `CNAME` record for `www` pointing to `<user>.github.io` (for the bare domain, `A` records to
185.199.108.153, 185.199.109.153, 185.199.110.153 and 185.199.111.153). All links in the site are relative, so it
works at both addresses without changes.
