import re

# bound each keyword, return a list
# [re.compile('\\bvisualization\\b', re.IGNORECASE)]
def make_bounded_patterns(keyword_list):
    return [
        re.compile(r'\b' + re.escape(k) + r'\b', re.I)
        for k in keyword_list
    ]
YEAR_START = 2020
YEAR_END = 2025

TOPIC_KEYWORDS = [
    'Economy', 'Poverty', 
    'Education', 
    'Energy',
    'Food', 'Agriculture', 
    'Human Right', 'Democracy', 'Election', 'Civic',
    'Health', 'Disease',
    'Housing', 'Living Condition', 'Community', 'Wellbeing', 'Public Safety',
    'Politic', 'Policy', 'Government',
    'Population', 'Demography', 'Demographic', 'Census',
    'Violence', 'War', 'Disaster', 'Crisis',
    'Weather', 'Climate', 'Sustainability', 'Pollution',
    'COVID-19', 
    'Open Data',
    'Social Impact',
    'Museum',
    'News Media', 'News', 'Journalist', 'Journalism',
    'Public',
    'Personal',
    'Personal Informatics',
    'In-the-wild', 'In the Wild', 'Participatory', 'Situated'
    # 'Real-world', 'Real World'
]

AUDIENCE_KEYWORDS = [
    'Casual user',
    'Citizen',
    'Community member',
    'Laypeople',
    'Layperson',
    'General audience',
    'General public',
    'General reader',
    'General user',
    'Non-expert',
    'Non-technical audience',
    'Novice',
    'Passersby',
    'Public viewer',
    'Wider audience'
]

VISUALIZATION_KEYWORDS = [
    'visualization'
]

TOPIC_PATTERNS = make_bounded_patterns(TOPIC_KEYWORDS)
AUDIENCE_PATTERNS = make_bounded_patterns(AUDIENCE_KEYWORDS)
# JUST FOR CHI AND CGF
VISUALIZATION_PATTERNS = make_bounded_patterns(VISUALIZATION_KEYWORDS)

EXCLUDE_KEYWORDS = [
    'virtual reality',
    'augmented reality',
    'mixed reality',
    'xr',
    'vr',
    'ar'
]

EXCLUDE_PATTERNS = make_bounded_patterns(EXCLUDE_KEYWORDS)
