# geek_code 5.x decoder 

import re
from codes import *

def parse_geekcode(s):
    full_meaning = []
    remaining_string = s
    for d in [geek_of]:
        for code,meaning in d.items():
            search_string = r'\b' + code + r'\b'
            m = re.search(search_string,s)
            if m: 
                print(f'found {search_string} in {remaining_string}')
                remaining_string = re.sub(search_string, '', remaining_string)
                full_meaning.append(meaning)	
    return(full_meaning, remaining_string)
