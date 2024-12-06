# geek_code 5.x decoder 

import re
from codes import *

def parse_geekcode(s):
    """Parse a geek code string and return its meaning"""
    full_meaning = []
    remaining_string = s
    
    # List of all code dictionaries to check
    dictionaries = [
        geek_of,
        tv_shows,
        programming_languages,
        version_control,
        comics,
        computers,
        politics,
        entertainment,
        lifestyle
    ]
    
    # Check each dictionary for matches
    for d in dictionaries:
        for code, meaning in d.items():
            # Use word boundaries to match exact codes
            search_string = r'\b' + code + r'\b'
            m = re.search(search_string, s)
            if m:
                print(f'found {search_string} in {remaining_string}')
                # Remove the matched code from remaining string
                remaining_string = re.sub(search_string, '', remaining_string)
                # Get any modifiers (+++, --, etc) that follow the code
                mod_match = re.search(r'[+\-]+', remaining_string)
                if mod_match:
                    modifier = mod_match.group()
                    remaining_string = re.sub(r'[+\-]+', '', remaining_string, 1)
                    full_meaning.append(f'{meaning} [{modifier}]')
                else:
                    full_meaning.append(meaning)

    return(full_meaning, remaining_string)
