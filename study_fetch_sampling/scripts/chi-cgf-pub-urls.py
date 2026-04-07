import scrape_config
import csv
from helpers import (stream_openalex_works_by_sources, 
                     matches_all_groups,
                     matches_excluded)

# fetch
SOURCE_IDS = ['S4363607743', 'S67831204'] # 'S4363607743' (CHI), 'S67831204' (CGF)
rows = list(stream_openalex_works_by_sources(SOURCE_IDS, 
                                             year_start=scrape_config.YEAR_START, 
                                             year_end=scrape_config.YEAR_END))

# dedup
seen = set(); dedup = []
for r in rows:
    if r['openalex_id'] not in seen:
        seen.add(r['openalex_id']); dedup.append(r)

# total
print(len(dedup))

# exit()

# filter
filtered = [r for r in dedup if matches_all_groups(r, False)]

# exclude
filtered = [
    row for row in filtered
    if not matches_excluded(row)
]

# write to csv
fields = ['source_id','venue','title','doi','year','open_url','keywords','abstract', 'openalex_id']
with open(f'urls/final/CHI_CGF_{scrape_config.YEAR_START}_{scrape_config.YEAR_END}.csv', 
          'w', 
          newline='', 
          encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(filtered)

print(f'Wrote {len(filtered)} works to CHI_CGF_{scrape_config.YEAR_START}_{scrape_config.YEAR_END}.csv')

# ---------- 2) OpenAlex (CHI visualization subset + EuroVis via CGF) ----------
# No key required. We (a) find the venue’s OpenAlex Source ID, then (b) stream all matching works.
# CHI only started having a visualization track from 2019 onwards
# NEED TO MANUALLY GRAB CHI PROCEEDINGS BY VISUALIZATION SUBCOMMITTEE STARTING FROM 2019
# PDF URLS ARE PAYWALLED
# DID SUCCESSFULLY FETCH ALL 637 WORKS FROM CHI PROCEEDINGS 2022 THOUGH
