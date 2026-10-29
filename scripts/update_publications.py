#!/usr/bin/env python3
"""Weekly check for new publications on OpenAlex (run by .github/workflows/update-publications.yml).

Adds papers that are on OpenAlex but not yet in _data/publications.yml to the top of that file,
and writes a summary to new-publications.md for the pull request. Only journal articles and
reviews published on or after `openalex.since` (in _config.yml) are considered; papers listed
in _data/publications_exclude.yml are skipped. Uses the Python standard library only.
"""
import difflib
import html
import json
import pathlib
import re
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / '_config.yml'
PUBS = ROOT / '_data' / 'publications.yml'
EXCLUDE = ROOT / '_data' / 'publications_exclude.yml'
SUMMARY = ROOT / 'new-publications.md'


def setting(name):
    block = re.search(r'^openalex:[^\n]*\n((?:[ \t]+[^\n]*\n?)+)', CONFIG.read_text(), re.M)
    return re.search(rf'^\s+{name}:\s*([^\s#]+)', block.group(1), re.M).group(1).strip('"\'')


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
        value = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    return value


def norm(title):
    return re.sub(r'[^a-z0-9]', '', (title or '').lower())


def doi_of(text):
    m = re.search(r'10\.\d{4,9}/[^\s"\'<>]+', text or '')
    return m.group(0).rstrip('.,;)').lower() if m else None


def clean(text):
    text = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', text or ''))).strip()
    return re.sub(r'\bPM\s+(2\.5|10)\b', r'PM\1', text)  # subscripts arrive as "PM 2.5"


def quote(value):
    s = str(value)
    if re.match(r'[\s\-?:,\[\]{}#&*!|>\'"%@`]', s) or re.search(r':\s|\s#|:$', s) or re.fullmatch(r'[\d.]+', s):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s


def listed_values(path, key=None):
    """Values from a simple YAML list; with `key`, the values of that field."""
    if not path.exists():
        return []
    pattern = rf'^\s*-?\s*{key}:\s*(.+)$' if key else r'^\s*-\s*(.+?)\s*$'
    return [unquote(v) for v in re.findall(pattern, path.read_text(), re.M)]


def openalex_works(author, since):
    params = {
        'filter': f'author.id:{author},from_publication_date:{since},type:article|review',
        'sort': 'publication_date:desc',
        'per_page': '100',
        'select': 'id,doi,title,publication_year,publication_date,primary_location,is_paratext,is_retracted',
    }
    request = urllib.request.Request('https://api.openalex.org/works?' + urllib.parse.urlencode(params),
                                     headers={'User-Agent': 'HANG website publication check'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)['results']


def main():
    author, since = setting('author_id'), setting('since')
    known_titles = {norm(t) for t in listed_values(PUBS, 'title')}
    known_dois = {d for d in map(doi_of, listed_values(PUBS, 'link')) if d}
    skip = listed_values(EXCLUDE)
    skip_titles, skip_dois = {norm(v) for v in skip}, {d for d in map(doi_of, skip) if d}

    def already_listed(title, doi):
        if doi and (doi in known_dois or doi in skip_dois):
            return True
        if title in known_titles or title in skip_titles:
            return True
        # same paper with small differences in punctuation or capitalisation
        return any(difflib.SequenceMatcher(None, title, t).ratio() >= 0.93 for t in known_titles)

    found, seen = [], set()
    for work in openalex_works(author, since):
        location = work.get('primary_location') or {}
        source = location.get('source') or {}
        # journal papers only: drops preprint servers, data repositories and conference abstracts
        if work.get('is_paratext') or work.get('is_retracted') or source.get('type') != 'journal':
            continue
        title = clean(work.get('title'))
        doi = doi_of(work.get('doi'))
        if not title or norm(title) in seen or already_listed(norm(title), doi):
            continue
        seen.add(norm(title))
        found.append({'year': work.get('publication_year'), 'journal': clean(source.get('display_name')),
                      'title': title, 'link': f'https://doi.org/{doi}' if doi else location.get('landing_page_url') or work['id'],
                      'date': work.get('publication_date') or ''})

    if not found:
        print('No new publications.')
        return

    found.sort(key=lambda p: p['date'], reverse=True)
    entries = '\n\n'.join(f"- year: {p['year']}\n  journal: {quote(p['journal'])}\n  title: {quote(p['title'])}\n  link: {quote(p['link'])}"
                          for p in found)
    text = PUBS.read_text()
    first = re.search(r'^- ', text, re.M)
    text = (text[:first.start()] + entries + '\n\n' + text[first.start():]) if first else text.rstrip('\n') + '\n\n' + entries + '\n'
    PUBS.write_text(text)

    lines = [f'The weekly check found **{len(found)} new publication{"s" if len(found) > 1 else ""}** on '
             f'[OpenAlex](https://openalex.org/authors/{author}) that {"are" if len(found) > 1 else "is"} not on the website yet:', '']
    lines += [f"- {p['year']}, *{p['journal']}*: [{p['title']}]({p['link']})" for p in found]
    lines += ['', 'To publish them, open the link above, click **Create pull request**, then **Merge pull request**. '
              'They appear at the top of "Recent Publications" on the Research page, and this issue closes itself.',
              '', 'If a paper is not ours or should not be listed, add its DOI to `_data/publications_exclude.yml`; '
              'the next weekly check will update this list without it.']
    SUMMARY.write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
