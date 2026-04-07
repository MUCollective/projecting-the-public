import scrape_config
import requests
import time
import pandas as pd

def flatten_index_terms(article: dict) -> list[str]:
    """
    Collapse IEEE index_terms into a single flat list of strings.
    De-duplicates while preserving order.
    """
    index_terms = article.get("index_terms", {})
    flat = []

    if isinstance(index_terms, dict):
        for bucket in index_terms.values():
            if isinstance(bucket, dict):
                terms = bucket.get("terms")
                if isinstance(terms, list):
                    for t in terms:
                        if isinstance(t, str) and t.strip():
                            flat.append(t.strip())

    # de-duplicate, preserve order
    seen = set()
    uniq = []
    for t in flat:
        if t not in seen:
            seen.add(t)
            uniq.append(t)

    return uniq

def matches_group(haystacks, patterns):
    """True if any pattern matches any text field"""
    return any(p.search(h) for p in patterns for h in haystacks)

def matches_all_groups(row, isVIS):
    haystacks = [
        _safe_get(row, 'title'),
        _safe_get(row, 'keywords'),
        _safe_get(row, 'abstract')
    ]

    if isVIS:
        return (
            (matches_group(haystacks, scrape_config.TOPIC_PATTERNS)
            or matches_group(haystacks, scrape_config.AUDIENCE_PATTERNS))
        )
    else:
        return (
            (matches_group(haystacks, scrape_config.TOPIC_PATTERNS)
            or matches_group(haystacks, scrape_config.AUDIENCE_PATTERNS))
            and matches_group(haystacks, scrape_config.VISUALIZATION_PATTERNS)
        )

def matches_excluded(row):
    haystacks = [
        _safe_get(row, 'title'),
        _safe_get(row, 'keywords'),
        _safe_get(row, 'abstract')
    ]

    return any(p.search(h) for p in scrape_config.EXCLUDE_PATTERNS for h in haystacks)

# -------- main streamer --------
def stream_openalex_works_by_sources(
    source_ids,
    year_start = 2023,
    year_end = 2025,
    search = None, # optional extra text filter (e.g., "visualization")
    per_page = 200,
    id_chunk_size = 20, # keep filters reasonable
    sleep_sec = 0.2,
    mailto = 'mandicai2028@u.northwestern.edu',
    include_abstract = True
):
    """
    Yields dicts with venue (from primary_location), title, doi, year, open_url, keywords.
    """
    base = 'https://api.openalex.org/works'
    select_fields = 'id,title,doi,publication_year,primary_location,keywords,concepts'
    if include_abstract:
        select_fields += ',abstract_inverted_index' 

    for batch in _chunks(list(source_ids), id_chunk_size):
        # OR the source IDs within one filter
        sources_filter = 'primary_location.source.id:' + '|'.join(batch)
        date_from = f'from_publication_date:{year_start}-01-01'
        date_to   = f'to_publication_date:{year_end}-12-31'
        filter_str = f'{sources_filter},{date_from},{date_to}'

        cursor = '*'
        while True:
            params = {
                'filter': filter_str,
                'per-page': per_page,
                'cursor': cursor,
                'select': select_fields,
                'mailto': mailto
            }
            if search:
                params['search'] = search

            r = requests.get(base, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()

            for w in data.get('results', []):
                loc = w.get('primary_location') or {}
                src = (loc.get('source') or {})
                pdf = loc.get('pdf_url') or loc.get('landing_page_url')
                abstract = _build_abstract(w.get('abstract_inverted_index')) if include_abstract else None

                yield {
                    'source_id': src.get('id'),
                    'venue': src.get('display_name'),
                    'title': w.get('title'),
                    'doi': w.get('doi'),
                    'year': w.get('publication_year'),
                    'open_url': pdf,
                    'keywords': '; '.join(_normalize_keywords(w)),
                    'abstract': abstract,
                    'openalex_id': w.get('id'),
                }

            cursor = data.get('meta', {}).get('next_cursor')
            if not cursor:
                break
            time.sleep(sleep_sec)

def _build_abstract(inv):
    """Reconstruct plaintext from OpenAlex abstract_inverted_index."""
    if not inv:
        return None
    # positions are 0-based word indices
    maxpos = max(p for positions in inv.values() for p in positions)
    words = [''] * (maxpos + 1)
    for token, positions in inv.items():
        for p in positions:
            words[p] = token
    # simple join; you can add smarter de-spacers for punctuation if you like
    txt = ' '.join(words).strip()
    return txt or None

def _safe_get(row, col):
    v = row.get(col)
    return '' if pd.isna(v) else v

# used in stream_openalex_works_by_sources() to handle the source_ids?
# not sure why
def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def _normalize_keywords(work):
    """Prefer explicit keywords; fall back to concepts."""
    kws = []
    if isinstance(work.get('keywords'), list):
        for k in work['keywords']:
            # accommodate different shapes that appear in the wild
            for key in ('display_name', 'keyword', 'name'):
                if k.get(key):
                    kws.append(k[key])
                    break
    if not kws and isinstance(work.get('concepts'), list):
        for c in work['concepts']:
            if c.get('display_name'):
                kws.append(c['display_name'])
    # de-duplicate while preserving order
    seen = set()
    out = []
    for x in kws:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

# split keywords into a list
# def split_kw(x):
#     if pd.isna(x): return []
    
#     # keywords are usually semicolon or comma separated
#     for sep in [";","|",","]:
#         if sep in x: return [k.strip() for k in x.split(sep) if k.strip()]
#     return [x.strip()]