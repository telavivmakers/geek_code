# geek_code 5.x decoder 

# Base codes without modifiers (+++, --, etc) since those are handled separately
# Each code must be a distinct word for regex matching with \b word boundaries

geek_of = {
'GAI' : 'Geek of Artificial Intelligence',
'GBIO' : 'Geek of Biomedical Engineering', 
'GB' : 'Geek of Business',
'GC' : 'Geek of Classics',
'GCA' : 'Geek of Commercial Arts',
'GCM' : 'Geek of Computer Management',
'GCS' : 'Geek of Computer Science',
'GCC' : 'Geek of Communications',
'GDS' : 'Geek of Data Science',
'GDVO' : 'Geek of DevOps',
'GE' : 'Geek of Engineering',
'GED' : 'Geek of Education',
'GFA' : 'Geek of Fine Arts',
'GFS' : 'Geek of Forensic Science',
'GG' : 'Geek of Government',
'GH' : 'Geek of Humanities',
'GIT' : 'Geek of Information Technology',
'GJ' : 'Geek of Jurisprudence (Law)',
'GLS' : 'Geek of Library Science',
'GL' : 'Geek of Literature',
'GMC' : 'Geek of Mass Communications',
'GM' : 'Geek of Math',
'GMD' : 'Geek of Medicine',
'GMU' : 'Geek of Music',
'GPA' : 'Geek of Performing Arts',
'GP' : 'Geek of Philosophy',
'GS' : 'Geek of Science (Physics, Chemistry, Biology, etc.)',
'GSS' : 'Geek of Social Science (Psychology, Sociology, etc.)',
'GTW' : 'Geek of Technical Writing',
'GVDD' : 'Geek of Video Game Design',
'GO' : 'Geek of Other',
'GU' : 'Geek of Undecided',
'G!' : 'Geek of no qualifications',
'GAT' : 'Geek of All Trades'
}

# TV show codes - base identifiers only
tv_shows = {
'TBBT' : 'The Big Bang Theory',
'TB5' : 'Babylon 5',
'TBG' : 'Battlestar Galactica',
'TDW' : 'Doctor Who',
'TEX' : 'The Expanse',
'TFF' : 'Firefly',
'TGT' : 'Game of Thrones',
'TIL' : 'In Search Of with Leonard Nimoy',
'TMON' : 'Monty Python',
'TMM' : 'Mad Max',
'TLOTR' : 'Lord of the Rings',
'TL' : 'Lost',
'TOB' : 'Orphan Black',
'TRM' : 'Rick and Morty',
'TW13' : 'Warehouse 13',
'THRO' : 'Heroes',
'THROrb' : 'Heroes Reborn',
'TLV' : 'Leverage',
'TLVr' : 'Leverage Redemption',
'TSG' : 'Stargate',
'TSG1' : 'Stargate SG-1',
'TSGa' : 'Stargate Atlantis', 
'TSGu' : 'Stargate Universe',
'TSGoc' : 'Stargate Origins Catherine',
'TST' : 'Star Trek',
'TSTanm' : 'Star Trek Animated Series',
'TSTng' : 'Star Trek The Next Generation',
'TSTds9' : 'Star Trek Deep Space Nine',
'TSTv' : 'Star Trek Voyager',
'TSTe' : 'Star Trek Enterprise',
'TSTdsc' : 'Star Trek Discovery',
'TSTpic' : 'Star Trek Picard',
'TSTld' : 'Star Trek Lower Decks',
'TSTst' : 'Star Trek Short Treks',
'TSTpro' : 'Star Trek Prodigy',
'TSTsnw' : 'Star Trek Strange New Worlds',
'TSW' : 'Star Wars',
'TSWcw' : 'Star Wars Clone Wars',
'TSWman' : 'The Mandalorian',
'TSWand' : 'Star Wars Andor',
'TSWobi' : 'Star Wars Obi-Wan Kenobi',
'TSWbob' : 'Star Wars Book of Boba Fett',
'TSWv' : 'Star Wars Visions',
'TSWbb' : 'Star Wars Bad Batch',
'TSWres' : 'Star Wars Resistance',
'TSWreb' : 'Star Wars Rebels'
}

# Programming language codes - base identifiers only
programming_languages = {
'Lasm' : 'Assembly',
'Lbash' : 'Bourne Again Shell',
'LC' : 'C',
'LCpp' : 'C++',
'LC#' : 'C#',
'Lgo' : 'Go',
'LGPT' : 'GPT',
'Lj' : 'Java',
'Ljs' : 'JavaScript',
'Llll' : 'Low-level Lisp',
'Llua' : 'Lua',
'LM' : 'MATLAB',
'LoC' : 'Objective C',
'LP' : 'Perl',
'Lphp' : 'PHP',
'Lpy' : 'Python',
'LQ#' : 'Q#',
'LR' : 'R',
'LRs' : 'Rust',
'LRu' : 'Ruby',
'Lsql' : 'SQL',
'Lvb' : 'Visual Basic',
'Lwps' : 'Windows PowerShell'
}

# Version control codes - base identifiers only
version_control = {
'G' : 'GitHub',
'Gl' : 'GitLab', 
'Gb' : 'BitBucket',
'Gbk' : 'Bitkeeper',
'Gbn' : 'Beanstalk',
'Gsvn' : 'Subversion',
'Gtfs' : 'Team Foundation Server'
}

# Comic codes - base identifiers only
comics = {
'KD' : 'Dilbert',
'KX' : 'XKCD',
'KM' : 'Manga',
'KM!' : 'Hentai'
}

# Computer codes - base identifiers only
computers = {
'CM' : 'Computer Proficiency',
'MW' : 'Microsoft Windows',
'U' : 'Unix',
'UL' : 'Linux',
'ULA' : 'Arch Linux',
'ULAP' : 'Pacman',
'ULD' : 'Debian',
'ULDU' : 'Ubuntu',
'ULDUM' : 'Linux Mint',
'ULDD' : 'Deepin',
'ULF' : 'Fedora',
'ULRH' : 'Red Hat Enterprise Linux',
'ULRC' : 'CentOS',
'ULRO' : 'OpenSUSE',
'ULG' : 'Gentoo',
'ULGC' : 'ChromeOS',
'ULS' : 'Slackware',
'US' : 'Sun OS/Solaris',
'UA' : 'AIX',
'UH' : 'HPUX',
'UI' : 'IRIX',
'UC' : 'SCO Unix',
'MC' : 'Mac/Apple'
}

# Politics codes - base identifiers only
politics = {
'PSG' : 'Green Politics/Sustainability/Climate',
'PSL' : 'Civil Liberties',
'PSS' : 'Gender Politics',
'PS' : 'Politics and Social Issues',
'PE' : 'Politics and Economic Issues'
}

# Entertainment codes - base identifiers only
entertainment = {
'RPG' : 'Role Playing Games',
'BK' : 'Books',
'KD' : 'Dilbert',
'KX' : 'XKCD',
'KM' : 'Manga'
}

# Lifestyle codes - base identifiers only
lifestyle = {
'R' : 'Residence',
'E' : 'Electronics',
'H' : 'Hardware',
'PGP' : 'Pretty Good Privacy'
}
