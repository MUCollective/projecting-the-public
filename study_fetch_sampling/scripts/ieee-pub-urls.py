import scrape_config
import pandas as pd
from helpers import (matches_all_groups,
                     matches_excluded)

# fetch
# downloaded as of 2025-11-08 from https://www.vispubdata.org/home
vis_main = pd.read_csv('data/IEEE_1990_2024_main.csv')
vis_journal = pd.read_csv('data/IEEE_1990_2024_journal.csv')
papers_main = vis_main[['Year',
                        'Conference',
                        'Title',
                        'AuthorNames-Deduped',
                        'DOI',
                        'AuthorKeywords',
                        'Abstract',
                        'Link',
                        'PaperType'
                        ]].dropna(subset=['Title']).rename(columns={
    'Title': 'title',
    'AuthorKeywords': 'keywords',
    'Abstract': 'abstract',
    'Conference': 'venue'
})
papers_journal = vis_journal[['Year',
                              'Journal',
                              'Title',
                              'AuthorNames-Deduped',
                              'DOI',
                              'AuthorKeywords',
                              'Abstract',
                              'Link',
                              'PaperType'
                              ]].dropna(subset=['Title']).rename(columns={
    'Title': 'title',
    'AuthorKeywords': 'keywords',
    'Abstract': 'abstract',
    'Journal': 'venue'
})
papers_main['type'] = 'conference'
papers_journal ['type'] = 'journal'

# combine
papers_combined = pd.concat([papers_main, papers_journal], ignore_index=True)

# filter
# match on year
papers_combined = papers_combined[(papers_combined['Year'] >= scrape_config.YEAR_START) & 
                                  (papers_combined['Year'] <= scrape_config.YEAR_END)]

print(len(papers_combined))

exit()

# match on keywords
papers_combined = papers_combined[[
    matches_all_groups(row, True)
    for _, row in papers_combined.iterrows()
]]

# filter out misc
papers_combined = papers_combined[papers_combined['PaperType'] != 'M']

# exclude
papers_combined['is_excluded'] = papers_combined.apply(matches_excluded, axis=1)
papers_combined = papers_combined[~papers_combined['is_excluded']]

# write to csv
papers_combined.to_csv(f'urls/final/IEEE_{scrape_config.YEAR_START}_{scrape_config.YEAR_END}.csv')
print(f'Wrote {len(papers_combined)} works to IEEE_{scrape_config.YEAR_START}_{scrape_config.YEAR_END}.csv')
