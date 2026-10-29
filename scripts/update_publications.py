#!/usr/bin/env python3
"""Weekly publication update from OpenAlex (run by .github/workflows/update-publications.yml).

Adds journal papers co-authored by the group leader that are on OpenAlex but not yet in
_data/publications.yml (newest first, at the top of the file). Settings are under `openalex:`
in _config.yml. A paper is added only if it is verified as hers: on the paper she is listed with
one of the configured institutions, or the publisher's record (Crossref) carries her ORCID.
Every added paper is remembered in _data/publications_added.yml, so a paper deleted from the
website is not added again; _data/publications_exclude.yml blocks papers before they are added.
Uses the Python standard library only.
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
ADDED = ROOT / '_data' / 'publications_added.yml'
EXCLUDE = ROOT / '_data' / 'publications_exclude.yml'


def setting(name):
    block = re.search(r'^openalex:[^\n]*\n((?:[ \t]+[^\n]*\n?)+)', CONFIG.read_text(), re.M)
    value = re.search(rf'^\s+{name}:\s*(.*?)\s*(?:#.*)?$', block.group(1), re.M).group(1)
    return value.strip('"\'')


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


def get_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'HANG website publication update'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def openalex_works(author, since):
    params = {
        'filter': f'author.id:{author},from_publication_date:{since},type:article|review',
        'sort': 'publication_date:desc',
        'per_page': '100',
        'select': 'id,doi,title,publication_year,publication_date,primary_location,authorships,is_paratext,is_retracted',
    }
    return get_json('https://api.openalex.org/works?' + urllib.parse.urlencode(params))['results']


def listed_with_institution(work, author, institutions):
    """On this paper, the author's affiliation names one of the given institutions."""
    for a in work.get('authorships') or []:
        if (a.get('author') or {}).get('id', '').rsplit('/', 1)[-1] == author:
            names = [i.get('display_name') or '' for i in a.get('institutions') or []] + (a.get('raw_affiliation_strings') or [])
            return any(inst.lower() in name.lower() for name in names for inst in institutions)
    return False


def orcid_on_paper(doi, orcid):
    """The publisher's record of the paper (Crossref) lists this ORCID among its authors."""
    if not doi:
        return False
    try:
        authors = get_json('https://api.crossref.org/works/' + urllib.parse.quote(doi))['message'].get('author', [])
    except Exception:
        return False
    return any((a.get('ORCID') or '').rstrip('/').endswith(orcid) for a in authors)


def main():
    author, orcid, since = setting('author_id'), setting('orcid'), setting('since')
    institutions = [s.strip() for s in setting('institutions').split(';') if s.strip()]

    known_titles = {norm(t) for t in listed_values(PUBS, 'title')}
    known_dois = {d for d in map(doi_of, listed_values(PUBS, 'link')) if d}
    blocked = listed_values(EXCLUDE) + listed_values(ADDED)  # excluded, or added before (maybe removed since)
    blocked_titles, blocked_dois = {norm(v) for v in blocked}, {d for d in map(doi_of, blocked) if d}

    def already_known(title, doi):
        if doi and (doi in known_dois or doi in blocked_dois):
            return True
        if title in known_titles or title in blocked_titles:
            return True
        # same paper with small differences in punctuation or capitalisation
        return any(difflib.SequenceMatcher(None, title, t).ratio() >= 0.93 for t in known_titles)

    found, unverified, seen = [], [], set()
    for work in openalex_works(author, since):
        location = work.get('primary_location') or {}
        source = location.get('source') or {}
        # journal papers only: drops preprint servers, data repositories and conference abstracts
        if work.get('is_paratext') or work.get('is_retracted') or source.get('type') != 'journal':
            continue
        title = clean(work.get('title'))
        doi = doi_of(work.get('doi'))
        if not title or norm(title) in seen or already_known(norm(title), doi):
            continue
        seen.add(norm(title))
        paper = {'year': work.get('publication_year'), 'journal': clean(source.get('display_name')), 'title': title,
                 'link': f'https://doi.org/{doi}' if doi else location.get('landing_page_url') or work['id'],
                 'date': work.get('publication_date') or '', 'key': doi or title}
        if listed_with_institution(work, author, institutions) or orcid_on_paper(doi, orcid):
            found.append(paper)
        else:
            unverified.append(paper)

    for p in unverified:
        print(f"Not added (affiliation and ORCID could not be verified): {p['year']}, {p['journal']}: {p['title']} {p['link']}")
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

    added = ADDED.read_text().rstrip('\n') + '\n' if ADDED.exists() else ''
    ADDED.write_text(added + ''.join(f"- {quote(p['key'])}\n" for p in found))

    print(f'Added {len(found)} publication(s):')
    for p in found:
        print(f"  {p['year']}, {p['journal']}: {p['title']} {p['link']}")


if __name__ == '__main__':
    main()
