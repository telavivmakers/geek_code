# geek_code 5.x decoder 

import re
import inspect
import sys
from codes import *

def get_code_dictionaries():
    """Get all dictionaries from codes module"""
    import codes
    return {name: obj for name, obj in inspect.getmembers(codes)
            if isinstance(obj, dict)}

def parse_geekcode(s):
    """Parse a geek code string and return its meaning"""
    full_meaning = []
    remaining_string = s
    
    # Get all dictionaries dynamically
    dictionaries = get_code_dictionaries()
    
    # Check each dictionary for matches
    for dict_name, d in dictionaries.items():
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

if __name__ == '__main__':
    # If run from command line, parse the geek code provided as argument
    if len(sys.argv) > 1:
        geek_code = ' '.join(sys.argv[1:])  # Join all args in case code has spaces
        meanings, remaining = parse_geekcode(geek_code)
        print('\nMeanings:')
        for meaning in meanings:
            print(f'- {meaning}')
        if remaining.strip():
            print(f'\nUnparsed: {remaining.strip()}')
    else:
        print('Usage: python geek_decode.py "GCS++ U+++ Lpy+"')
