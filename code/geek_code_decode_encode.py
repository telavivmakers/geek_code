#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field


_DASH_TRANSLATION = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
        "\u00a0": " ",
    }
)

_MBTI_RE = re.compile(r"^([IE][NS][FT][JP])(?:-([AT]))?$")
_PRONOUN_RE = re.compile(r"^([a-z]+/[a-z]+)(.*)$")


@dataclass(frozen=True)
class CodeSpec:
    label: str
    rating_map: dict[str, str] = field(default_factory=dict)
    scale: str | None = None
    parent: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class DecodeProfile:
    name: str
    specs: dict[str, CodeSpec]


@dataclass
class ParsedQualifier:
    raw: str
    rating: str = ""
    unknown: bool = False
    refusal: bool = False
    variable: bool = False
    earns_money: bool = False
    credential: bool = False
    crossover: str | None = None
    goal: str | None = None
    exact_value: str | None = None


@dataclass
class DecodedToken:
    raw: str
    normalized: str
    code: str
    label: str
    description: str
    notes: list[str] = field(default_factory=list)
    inferred: bool = False


@dataclass
class DecodeResult:
    version: str | None
    source_text: str
    normalized_text: str
    tokens: list[DecodedToken]


def _code_specs(
    mapping: dict[str, str],
    *,
    parent: str | None = None,
    scale: str | None = None,
    note: str | None = None,
) -> dict[str, CodeSpec]:
    return {
        code: CodeSpec(label=label, parent=parent, scale=scale, note=note)
        for code, label in mapping.items()
    }


V4_GEEK_OF_CODES = {
    "GAI": "Geek of Artificial Intelligence",
    "GBIO": "Geek of Biomedical Engineering",
    "GB": "Geek of Business",
    "GC": "Geek of Classics",
    "GCA": "Geek of Commercial Arts",
    "GCM": "Geek of Computer Management",
    "GCS": "Geek of Computer Science",
    "GCC": "Geek of Communications",
    "GE": "Geek of Engineering",
    "GED": "Geek of Education",
    "GFA": "Geek of Fine Arts",
    "GG": "Geek of Government",
    "GH": "Geek of Humanities",
    "GIT": "Geek of Information Technology",
    "GJ": "Geek of Jurisprudence (Law)",
    "GLS": "Geek of Library Science",
    "GL": "Geek of Literature",
    "GMC": "Geek of Mass Communications",
    "GM": "Geek of Math",
    "GMD": "Geek of Medicine",
    "GMU": "Geek of Music",
    "GPA": "Geek of Performing Arts",
    "GP": "Geek of Philosophy",
    "GS": "Geek of Science (Physics, Chemistry, Biology, etc.)",
    "GSS": "Geek of Social Science (Psychology, Sociology, etc.)",
    "GTW": "Geek of Technical Writing",
    "GO": "Geek of Other",
    "GU": "Geek of Undecided",
    "G!": "Geek of no qualifications nor interests",
    "GAT": "Geek of All Trades",
}

MODERN_GEEK_OF_CODES = {
    **V4_GEEK_OF_CODES,
    "GDS": "Geek of Data Science",
    "GDVO": "Geek of DevOps",
    "GFS": "Geek of Forensic Science",
    "GVGD": "Geek of Video Game Design",
}

UNIX_CODES = {
    "U": "Unix",
    "UL": "Unix / Linux",
    "ULA": "Unix / Linux / Arch",
    "ULAP": "Unix / Linux / Arch / Pacman",
    "ULD": "Unix / Linux / Debian",
    "ULDU": "Unix / Linux / Debian / Ubuntu",
    "ULDUM": "Unix / Linux / Debian / Ubuntu / Linux Mint",
    "ULDU*": "Unix / Linux / Debian / Ubuntu / Other or discontinued Ubuntu",
    "ULDD": "Unix / Linux / Debian / Deepin",
    "ULDM": "Unix / Linux / Debian / Mepis",
    "ULDK": "Unix / Linux / Debian / Knoppix",
    "ULF": "Unix / Linux / Fedora",
    "ULR": "Unix / Linux / RPM family",
    "ULRH": "Unix / Linux / Red Hat Enterprise Linux",
    "ULRC": "Unix / Linux / CentOS",
    "ULRF": "Unix / Linux / Fedora",
    "ULRO": "Unix / Linux / OpenSUSE",
    "ULRU": "Unix / Linux / urpmi",
    "ULRA": "Unix / Linux / apt-rpm",
    "ULG": "Unix / Linux / Gentoo",
    "ULGC": "Unix / Linux / Gentoo / ChromeOS or ChromiumOS",
    "ULS": "Unix / Linux / Slackware",
    "ULP": "Unix / Linux / Pacman family",
    "UL*": "Unix / Linux / Other",
    "US": "Unix / SunOS / Solaris",
    "UA": "Unix / AIX",
    "UH": "Unix / HPUX",
    "UI": "Unix / IRIX",
    "UC": "Unix / SCO Unix",
    "U*": "Unix / Other",
}

V4_LANGUAGE_CODES = {
    "Lj": "Programming language / Java",
    "LC": "Programming language / C",
    "LCpp": "Programming language / C++",
    "LC#": "Programming language / C#",
    "Lvb": "Programming language / Visual Basic",
    "Lp": "Programming language / Python",
    "Ljs": "Programming language / JavaScript",
    "Lphp": "Programming language / PHP",
    "LOC": "Programming language / Objective-C",
    "Lsql": "Programming language / SQL",
    "LP": "Programming language / Perl",
    "LRu": "Programming language / Ruby",
    "LM": "Programming language / MATLAB",
    "Lasm": "Programming language / Assembly",
    "Lgo": "Programming language / Go",
    "LR": "Programming language / R",
}

MODERN_LANGUAGE_CODES = {
    "Lasm": "Programming language / Assembly",
    "Lbash": "Programming language / Bash",
    "LC": "Programming language / C",
    "LCpp": "Programming language / C++",
    "LC#": "Programming language / C#",
    "Lgo": "Programming language / Go",
    "LGPT": "Programming language / GPT",
    "Lj": "Programming language / Java",
    "Ljs": "Programming language / JavaScript",
    "Llll": "Programming language / Low-level Lisp",
    "Llua": "Programming language / Lua",
    "LM": "Programming language / MATLAB",
    "LoC": "Programming language / Objective-C",
    "LP": "Programming language / Perl",
    "Lphp": "Programming language / PHP",
    "Lpy": "Programming language / Python",
    "LQ#": "Programming language / Q#",
    "LR": "Programming language / R",
    "LRs": "Programming language / Rust",
    "LRu": "Programming language / Ruby",
    "Lsql": "Programming language / SQL",
    "Lvb": "Programming language / Visual Basic",
    "Lwps": "Programming language / Windows PowerShell",
}

SOFTWARE_DOMAIN_CODES = {
    "SDAI": "Software domain / AI and machine learning",
    "SDCV": "Software domain / computer vision",
    "SDNLP": "Software domain / natural language processing",
    "SDDS": "Software domain / data science",
    "SDDE": "Software domain / data engineering",
    "SDCG": "Software domain / cryptography",
    "SDBC": "Software domain / blockchain and cryptocurrency",
    "SDSE": "Software domain / search, retrieval, and recommenders",
    "SDRO": "Software domain / robotics",
    "SDCL": "Software domain / cloud and distributed systems",
    "SDFE": "Software domain / frontend applications",
    "SDBE": "Software domain / backend APIs and services",
}

V4_TV_CODES = {
    "TD": "TV / Doctor Who",
    "TR&M": "TV / Rick and Morty",
    "TF": "TV / Firefly",
    "TS": "TV / Stargate",
    "TTBB": "TV / The Big Bang Theory",
    "TB": "TV / Babylon 5",
    "TI": "TV / In Search Of...",
    "TM": "TV / Monty Python",
    "TMM": "TV / Mad Max",
    "TSW": "TV / Star Wars",
    "TG": "TV / Game of Thrones",
    "TLOTR": "TV / Lord of the Rings",
    "TL": "TV / Lost",
    "Tt": "TV / Star Trek",
}

MODERN_TV_CODES = {
    "TBBT": "TV / The Big Bang Theory",
    "TB5": "TV / Babylon 5",
    "TBG": "TV / Battlestar Galactica",
    "TDW": "TV / Doctor Who",
    "TEX": "TV / The Expanse",
    "TFF": "TV / Firefly",
    "TGT": "TV / Game of Thrones",
    "TIL": "TV / In Search Of...",
    "TMON": "TV / Monty Python",
    "TMM": "TV / Mad Max",
    "TLOTR": "TV / Lord of the Rings",
    "TL": "TV / Lost",
    "TOB": "TV / Orphan Black",
    "TRM": "TV / Rick and Morty",
    "TW13": "TV / Warehouse 13",
    "THRO": "TV / Heroes",
    "THROrb": "TV / Heroes Reborn",
    "TLV": "TV / Leverage",
    "TLVr": "TV / Leverage Redemption",
    "TSG": "TV / Stargate",
    "TSG1": "TV / Stargate SG-1",
    "TSGa": "TV / Stargate Atlantis",
    "TSGu": "TV / Stargate Universe",
    "TSGoc": "TV / Stargate Origins Catherine",
    "TST": "TV / Star Trek",
    "TSTanm": "TV / Star Trek Animated Series",
    "TSTng": "TV / Star Trek The Next Generation",
    "TSTds9": "TV / Star Trek Deep Space Nine",
    "TSTv": "TV / Star Trek Voyager",
    "TSTe": "TV / Star Trek Enterprise",
    "TSTdsc": "TV / Star Trek Discovery",
    "TSTpic": "TV / Star Trek Picard",
    "TSTld": "TV / Star Trek Lower Decks",
    "TSTst": "TV / Star Trek Short Treks",
    "TSTpro": "TV / Star Trek Prodigy",
    "TSTsnw": "TV / Star Trek Strange New Worlds",
    "TSW": "TV / Star Wars",
    "TSWcw": "TV / Star Wars Clone Wars",
    "TSWman": "TV / The Mandalorian",
    "TSWand": "TV / Star Wars Andor",
    "TSWobi": "TV / Star Wars Obi-Wan Kenobi",
    "TSWbob": "TV / Star Wars Book of Boba Fett",
    "TSWv": "TV / Star Wars Visions",
    "TSWbb": "TV / Star Wars The Bad Batch",
    "TSWres": "TV / Star Wars Resistance",
    "TSWreb": "TV / Star Wars Rebels",
}

V4_COMICS_CODES = {
    "k": "Comics",
    "kD": "Comics / Dilbert",
    "kX": "Comics / XKCD",
    "kM": "Comics / Manga",
}

MODERN_COMICS_CODES = {
    "K": "Comics",
    "KD": "Comics / Dilbert",
    "KX": "Comics / XKCD",
    "KM": "Comics / Manga",
    "KM!": "Comics / Hentai",
}

V4_AGE_MAP = {
    "+++": "60 and up",
    "++": "50-59",
    "+": "40-49",
    "": "30-39",
    "-": "25-29",
    "--": "20-24",
    "---": "15-19",
    "----": "10-14",
    "-----": "9 and under",
    "?": "Immortal?",
}

MODERN_AGE_MAP = {
    "++++": "60 and up",
    "+++": "50-59",
    "++": "40-49",
    "+": "30-39",
    "": "25-29",
    "-": "20-24",
    "--": "15-19",
    "---": "10-14",
    "----": "9 and under",
    "?": "Immortal?",
}

CLOTHING_MAP = {
    "++": "Conservative or formal dress, up to suit-and-tie territory.",
    "+": "Good leisure-wear like slacks and button shirts.",
    "": "Bland catalog-ad style clothing.",
    "-": "Usually jeans and a t-shirt.",
    "--": "T-shirts with trendy political messages.",
    "---": "Punk style, torn clothes, piercings, or prominent tattoos.",
    "x": "Cross-dresser.",
    "?": "Has no idea what they are wearing.",
    "pu": "Wears the same clothes all the time.",
}

V4_COMPUTERS_MAP = {
    "++++": "Would be first in line for a cybernetic interface.",
    "+++": "Computers dominate daily life.",
    "++": "Computers are a large part of life and coding happens in at least one language.",
    "+": "Computers are fun and regularly enjoyed.",
    "": "Computers are just tools.",
    "-": "Anything beyond a calculator feels difficult.",
    "--": "Barely knows where the power switch is.",
    "---": "Actively hostile to computers.",
}

V4_UNIX_MAP = {
    "++++": "Unix sysadmin-level expertise.",
    "+++": "Deep Unix access and confidence.",
    "++": "Heavy Unix user who annoys the admins.",
    "+": "Enjoys shell scripting and understands Unix fundamentals.",
    "": "Has a Unix account and uses it.",
    "-": "Would rather be on VMS.",
    "--": "Has seen Unix and disliked it.",
    "---": "Thinks Unix geeks are nerds in disguise.",
}

MAC_MAP = {
    "++": "Mac guru.",
    "+": "Uses Macs often and sees their value.",
    "": "Uses a Mac, but feels indifferent.",
    "-": "Prefers character-prompt systems and dislikes Macs.",
    "--": "Strongly anti-Mac.",
}

PGP_MAP = {
    "++++": "Philip Zimmerman level.",
    "+++": "Won't send or answer mail unless it is encrypted or signed.",
    "++": "Uses current PGP regularly.",
    "+": "Has a public key and uses PGP.",
    "": "Used it once but stopped.",
    "-": "Feels there is nothing to hide.",
    "--": "Thinks encryption bogs down the internet.",
    "---": "Suspects encryption supporters of being criminals.",
    "----": "Prefers something like the Clipper chip instead.",
}

ELECTRONICS_MAP = {
    "+++": "Lady Ada tier.",
    "++": "Comfortably fixes electronics at speed.",
    "+": "Knows CMOS vs. BJT and why a comparator is not just an op-amp.",
    "": "Baseline electronics familiarity.",
    "-": "Limited practical electronics comfort.",
    "--": "Only interested in electrons as theoretical constructs.",
}

HARDWARE_MAP = {
    "+++": "Charles Babbage tier.",
    "++": "Extreme hardware craftsmanship.",
    "+": "Comfortably builds, upgrades, or repairs hardware by hand.",
    "": "Baseline hardware familiarity.",
    "-": "Rarely uses literal hammers.",
    "--": "Prefers taking hardware to a shop.",
}

PS_MAP = {
    "+++": "Far-left / anarchic on social issues.",
    "++": "Clearly liberal or progressive on social issues.",
    "+": "Libertarian-leaning on personal freedoms.",
    "": "No strong opinion right now.",
    "-": "Socially conservative.",
    "--": "Strongly socially conservative.",
    "---": "Extremely socially conservative.",
}

# Keep `PE` aligned with `PS`: more `+` means more left, more `-` means more right.
PE_MAP = {
    "+++": "Far-left / anti-capitalist on economic issues.",
    "++": "Economically left: favors regulation, redistribution, and strong social safety nets.",
    "+": "Center-left economically: markets are useful, but need regulation and a solid safety net.",
    "": "Skeptical of both government and big business.",
    "-": "Center-right economically: prefers lower taxes, lighter regulation, and less redistribution.",
    "--": "Fiscally conservative: favors spending restraint and balanced-budget politics.",
    "---": "Hard-right / laissez-faire / trickle-down economics stance.",
}

PE_V4_MAP = PE_MAP
PE_MODERN_MAP = PE_MAP

V4_ROLEPLAY_MAP = {
    "+++": "Has written and published gaming material.",
    "++": "Very deep role-playing commitment.",
    "+": "Regular role-player with a well-developed character.",
    "": "Role-playing is an occasional Saturday activity.",
    "-": "Thinks role-playing is a waste of time.",
    "--": "Sees role-players as pure evil.",
    "---": "Works for TSR.",
    "*": "Treats life itself as role-playing.",
}

MODERN_RPG_MAP = {
    "+++": "Has authored and published role-playing material.",
    "++": "There is no life outside the die roll.",
    "+": "Has regular RPG sessions and a deeply known character.",
    "": "Role-playing is just a casual Saturday activity.",
    "-": "Thinks role-playing is a waste of time.",
    "--": "Sees role-players as tools of pure evil.",
    "---": "Works for TSR.",
    "?": "Believes life itself is role-playing.",
}

V4_BOOKS_MAP = {
    "++++": "Reads about a book a day.",
    "+++": "Reads a few books a week.",
    "++": "Finishes at least one new book a month.",
    "+": "Enjoys reading, but not that often.",
    "": "Reads the newspaper and an occasional book.",
    "-": "Reads only when there is no other way to get the information.",
    "--": "Did not actually read the Geek Code and got the summary second-hand.",
}

MODERN_BOOKS_MAP = {
    "++++": "Reads about a book a day.",
    "+++": "Reads a few books a week.",
    "++": "Finishes at least one new book a month.",
    "+": "Enjoys reading, but not that often.",
    "": "Reads the newspaper and an occasional book.",
    "-": "Reads only when there is no other way to get the information.",
    "--": "Absorbs knowledge by osmosis.",
    "---": "Did not read the Geek Code and had someone else compile it.",
}

V4_EDUCATION_MAP = {
    "+++++": "Stephen Hawking tier.",
    "++++": "Ph.D.",
    "+++": "Masters degree.",
    "++": "Bachelors degree.",
    "+": "Associates degree.",
    "": "Finished high school.",
    "-": "Has not finished high school.",
    "--": "Has not even entered high school.",
    "*": "Learned life from the Hitchhiker's Trilogy.",
}

V4_HOUSING_MAP = {
    "++": "Deep geek cave with lots of computers and internet.",
    "+": "Lives alone in a cluttered, geeky space.",
    "": "Friends can come over and there is room to sit.",
    "-": "Lives with one or more registered geeks.",
    "--": "Lives with non-geeks who refuse to watch Babylon 5.",
    "---": "Married or equivalent domestic setup.",
    "----": "Married with children.",
    "!": "Stuck living with parents.",
    "*": "The lab or workplace feels like home.",
}

V4_RELATIONSHIPS_MAP = {
    "+++": "Found someone, dated, and is now married.",
    "++": "Long-running current relationship.",
    "+": "Dates frequently.",
    "": "Dates periodically.",
    "-": "Has difficulty maintaining a relationship.",
    "--": "People do not seem interested in dating.",
    "---": "Feels completely avoided romantically.",
    "*": "Member of the Sour Bachelor(ette)'s Club of America.",
    "%": "Was dumped.",
}

MODERN_RESIDENCE_MAP = {
    "+++": "Lives in a full geek cave with many computers and constant internet.",
    "++": "Lives alone in a cluttered, geeky space.",
    "+": "Hosts fellow geeks for conversation.",
    "": "Lives with other registered geeks.",
    "-": "Lives with non-geeks and finds it challenging.",
    "--": "Married or living romantically with a partner.",
    "---": "Married with children.",
    "!": "Living with parents.",
    "?": "The lab or workplace feels more like home than anywhere else.",
}

TREK_V4_MAP = {
    "+++": "Treats Star Trek like a religion.",
    "++": "Big fan with episodes and quotes memorized, but not convention-going.",
    "+": "Thinks Star Trek is a great show.",
    "": "Sees Star Trek as just another TV show.",
    "-": "Does not really get the appeal.",
    "--": "Thinks it is bad drama and tired space opera.",
    "---": "Strongly hates Star Trek.",
}

TREK_MODERN_MAP = TREK_V4_MAP


LEGACY_GEEK_OF_CODES = {
    **MODERN_GEEK_OF_CODES,
    "GPM": "Geek of Pre-Med",
    "GT": "Geek of Theater",
}

V2_DRESS_MAP = {
    "++": "Conservative dress, business-suit territory.",
    "+": "Trendy slogan or political-message clothing.",
    "": "Bland catalog-ad clothing.",
    "-": "Countercultural slogan or authority-questioning clothing.",
    "--": "Wears jeans to work to annoy the boss.",
    "---": "Wears torn clothes or obscenities on shirts.",
    "----": "Punk dresser.",
    "x": "Cross-dresser.",
    "?": "Has no idea what they are wearing.",
}

LEGACY_AGE_MAP = {
    "+++": "60 and up",
    "++": "50-59",
    "+": "40-49",
    "": "30-39",
    "-": "20-29",
    "--": "10-19",
    "---": "9 and under",
    "?": "Ageless.",
}

LEGACY_GLASSES_MAP = {
    "+++": "Very thick glasses.",
    "++": "Glasses with tape-in-the-middle stereotype.",
    "+": "Regular glasses wearer.",
    "-": "Uses contacts.",
    "--": "Uses colored contacts.",
    "---": "Uses unusual decorative contacts.",
    "?": "Cannot find their glasses.",
}

LEGACY_AUTOMOBILE_MAP = {
    "++++": "Chauffeured limo tier.",
    "+++": "Owns multiple Mercedes.",
    "++": "Drives a new car costing more than many houses.",
    "+": "Drives a sporty babe-mobile style car.",
    "": "Drives an ordinary hand-me-down car.",
    "-": "Drives parents' car.",
    "--": "Drives a rusty beater with a dragging muffler.",
    "---": "Drives a very old Pinto-tier car.",
    "----": "Drives a Yugo.",
    "*": "Rides a motorcycle.",
}

LEGACY_WEIRDNESS_MAP = {
    "+++": "Extremely weird, far from the mainstream.",
    "++": "So weird that Al Yankovic looks sane.",
    "+": "Comfortably weird.",
    "": "Claims to be perfectly normal.",
    "-": "More normal than most people.",
    "--": "Incredibly boring.",
}

LEGACY_VERBAGE_MAP = {
    "+++": "Regional-forensics-champ eloquence.",
    "++": "People compliment the speaker's eloquence.",
    "+": "People compliment the speaker's vocabulary.",
    "": "Usually speaks in complete sentences.",
    "-": "Uses words like `grok` in everyday conversation.",
    "--": "Talking makes people mildly embarrassed.",
    "---": "Rarely talks; mostly types.",
    "?": "Mumbles.",
    "*": "Babbles.",
}

LEGACY_PERL_MAP = {
    "+++++": "Larry Wall / Tom Christiansen / Randal Schwartz tier.",
    "++++": "Does not write Perl, speaks it.",
    "+++": "Uses Perl instead of shell, awk, or sed for most smaller programs.",
    "++": "Writes shell-script-class work in Perl.",
    "+": "Likes Perl and intends to learn more.",
    "": "Knows Perl exists, but little more.",
    "-": "Prefers awk and sed to Perl.",
    "--": "Sees Perl users as twisted show-offs.",
    "---": "Wants Perl banned.",
    "?": "Does not know what Perl is.",
}

LEGACY_LINUX_MAP = {
    "++++": "Linus Torvalds tier.",
    "+++": "Linux wizard / net.god tier.",
    "++": "Uses Linux almost exclusively and answers questions about it.",
    "+": "Has Linux installed and uses it sometimes.",
    "": "Knows what Linux is.",
    "-": "No real desire to use Linux.",
    "--": "Rejects Linux and worships Bill Gates.",
    "---": "Bill Gates tier.",
    "?": "Does not even know what Linux is.",
}

LEGACY_386BSD_MAP = {
    "+++": "386BSD wizard / net.god tier.",
    "++": "Uses 386BSD almost exclusively.",
    "+": "Has 386BSD installed and uses it sometimes.",
    "": "Knows what 386BSD is.",
    "-": "No real desire to use 386BSD.",
    "--": "Rejects 386BSD and worships Bill Gates.",
    "---": "USL's lawyer tier.",
    "?": "Does not even know what 386BSD is.",
}

LEGACY_EMACS_MAP = {
    "+++": "Emacs-is-my-login-shell tier.",
    "++": "Uses elisp regularly.",
    "+": "Uses Emacs for mail and news too.",
    "": "Uses Emacs as a regular editor.",
    "-": "Finds Emacs too big and bloated.",
    "--": "Sees Emacs as a fancy word processor.",
    "---": "Emacs sucks; vi forever.",
    "----": "Emacs sucks; pico forever.",
    "?": "Does not know what Emacs is.",
}

LEGACY_WEB_MAP = {
    "+++": "Webmaster-tier, heavily invested in the Web.",
    "++": "Has a homepage and surfs daily.",
    "+": "Uses the latest browser and browses with purpose.",
    "": "Has a browser and connection; uses them occasionally.",
    "-": "Finds the Web a bandwidth-heavy pain.",
    "--": "Thinks the Web wastes time and bandwidth.",
}

LEGACY_USENET_MAP = {
    "++++": "Tim Pierce tier.",
    "+++": "Reads so much Usenet that it becomes a daily slog.",
    "++": "Reads all news in a select handful of groups.",
    "+": "Reads news recreationally.",
    "": "Has read Usenet once or casually.",
    "-": "Avoids news as a waste of time.",
    "--": "Thinks news sucks.",
    "*": "Reads news almost exclusively.",
}

LEGACY_KIBO_MAP = {
    "++++++": "Is Kibo.",
    "+++++": "Has had sex with Kibo.",
    "++++": "Has met Kibo.",
    "+++": "Has gotten mail from Kibo.",
    "++": "Has read Kibo.",
    "+": "Likes Kibo.",
    "": "Knows who Kibo is.",
    "-": "Does not know who Kibo is.",
    "--": "Dislikes Kibo.",
    "---": "Hunting Kibo down with murderous intent.",
    "----": "Is Xibo.",
}

LEGACY_WINDOWS_MAP = {
    "+++++": "Bill Gates tier.",
    "++++": "Runs all the Windows variants on an SMP RISC machine.",
    "+++": "Windows programming god tier.",
    "++": "Writes Windows programs and DLLs.",
    "+": "Customizes Windows heavily and lives in the fun house.",
    "": "Uses Windows without loving it.",
    "-": "Still fighting with Windows installs and peripherals.",
    "--": "Thinks Windows is a joke OS.",
    "---": "Sees Windows as a huge setback to computing.",
}

LEGACY_OS2_MAP = {
    "+++": "Lives, eats, and breathes OS/2.",
    "++": "Uses OS/2 for essentially all computing.",
    "+": "Keeps DOS around just in case.",
    "": "Got OS/2 installed and feels indifferent.",
    "-": "Tried OS/2 and did not like it.",
    "--": "Cannot even get OS/2 installed.",
    "---": "Windows rules; long live Bill Gates.",
    "----": "Bill Gates of Borg tier.",
}

LEGACY_VMS_MAP = {
    "++": "VMS loyalist; Unix is a passing fad.",
    "+": "Likes VMS better than Unix.",
    "": "Has used VMS.",
    "-": "Prefers Unix to VMS.",
    "--": "Would rather smash their head into a brick wall than use VMS.",
}

V2_POLITICS_MAP = {
    "+++": "Authoritarian far-right politics.",
    "++": "Against free speech in the name of order.",
    "+": "Wants government off big business's back.",
    "": "Does not really care about politics.",
    "-": "Bring back the 60s.",
    "--": "Still living in the 60s.",
    "---": "No taxes through no government.",
}

LEGACY_PE_MAP = {
    "+++": "Hard-right economics: deregulation and trickle-down.",
    "++": "Keep the government off the backs of businesses; deregulate heavily.",
    "+": "Balance the budget with spending cuts and restraints.",
    "": "Distrusts both government and business.",
    "-": "Increase spending to help poor people; tax the rich and cut defense.",
    "--": "Capitalism is evil; government should provide key services.",
}

LEGACY_CYPHERPUNK_MAP = {
    "+++": "T.C. May tier.",
    "++": "Active cypherpunks / EFF / anti-Clipper stance.",
    "+": "Interested and concerned about privacy issues.",
    "": "Pretty indifferent to cypherpunk issues.",
    "-": "Sees cypherpunk concerns as overblown.",
    "--": "Thinks only people with something to hide need this.",
    "---": "L. Detweiler tier.",
}

LEGACY_XFILES_MAP = {
    "++++": "Chris Carter tier.",
    "+++": "Obsessive X-Files superfan.",
    "++": "Strong fan who debates details online.",
    "+": "Enjoys and watches it when remembered.",
    "": "Just another Fox show.",
    "-": "Thinks it is basically paranoia-flavored crap.",
    "--": "Would rather talk to Oliver Stone.",
}

LEGACY_DILBERT_MAP = {
    "+++++": "Scott Adams tier.",
    "++++": "In the DNRC / has heard from Scott Adams.",
    "+++": "A Dilbert prototype.",
    "++": "Works with people like Dilbert and his boss.",
    "+": "Reads Dilbert daily, often understanding it.",
    "": "Reads Dilbert infrequently, rarely understanding it.",
    "-": "Barely knows it as the engineer comic.",
    "--": "Only thinks the dog is cute.",
    "---": "Does not find manager satire funny.",
}

LEGACY_DOOM_MAP = {
    "+++": "DOOM god / PWAD-making tier.",
    "++": "Strong player who also downloads PWADs.",
    "+": "Finds DOOM a fun diversion.",
    "": "Has played and feels indifferent.",
    "-": "Played it and was not impressed.",
    "--": "Thinks it is overly violent crap.",
    "---": "Would rather play Zork.",
    "----": "Has seen better on an Atari 2600.",
}

LEGACY_GEEKCODE_MAP = {
    "++++": "Robert Hayden or future-version contributor tier.",
    "+++": "Has memorized the Geek Code and can decode it from memory.",
    "++": "Knows what each letter means, but sometimes checks the details.",
    "+": "Used to be more into the Geek Code before it got longer.",
    "": "Knows the Geek Code and filled one out.",
    "-": "Thinks the Geek Code is a waste of time.",
    "--": "Thinks the Geek Code is a waste and Hayden needs a life.",
}

LEGACY_BABYLON5_MAP = {
    "++++": "J. Michael Straczynski tier.",
    "+++": "Church of Joe worshipper tier.",
    "++": "Sees Babylon 5 as the real future of sci-fi television.",
    "+": "Watches weekly and likes its fresh perspective.",
    "": "Has seen Babylon 5 and feels indifferent.",
    "-": "Sees it as a cheap Star Trek ripoff.",
    "--": "Thinks it is soap-opera sci-fi trash.",
}

V2_MAGIC_MAP = {
    "++++": "Magic: The Gathering god tier.",
    "+++": "Owns top cards and plays for hours every night.",
    "++": "Has spent serious money and a lot of time on decks.",
    "+": "Bought a few packs and plays some.",
    "": "Plays Magic if a deck can be borrowed.",
    "-": "Mostly collects now.",
    "--": "Magic is eating class, work, and sleep.",
    "---": "Magic munchkin tier.",
    "----": "Runs a booster-pack arbitrage scheme to buy more cards.",
}

LEGACY_BARNEY_MAP = {
    "+++": "Worships Barney and wants to build a shrine.",
    "++": "Does not miss an episode.",
    "+": "Likes Barney and the wholesome message.",
    "": "Sees Barney as fine for kids.",
    "-": "Finds Barney annoying.",
    "--": "Feels physically ill from Barney's message.",
    "---": "Boycotts Barney and wants his head on the wall.",
    "?": "Does not know who Barney is.",
}

LEGACY_MUSIC_MAP = {
    "+++": "Over-refined elevator-music grokker.",
    "++": "Refined classical / new-age listener.",
    "+": "Owns a tape or CD collection.",
    "": "Occasionally listens to the radio.",
    "-": "Just play it loud.",
    "--": "Air-guitar champion tier.",
    "---": "Only wants it louder.",
    "*": "Listens to music no one else has ever heard of.",
    "**": "Listens to so many kinds of music they blur together.",
}

LEGACY_FRIENDS_MAP = {
    "++": "Has so many friends it makes others jealous.",
    "+": "Has quite a few close geek friends.",
    "": "Claims to have friends.",
    "-": "Has a few friends who barely speak anymore.",
    "--": "About one friend left.",
    "---": "Used to have friends and did not like it.",
    "?": "Thinks they have friends.",
    "*": "Everyone is a friend.",
}

LEGACY_NUTRITION_MAP = {
    "+++": "Grazes like a bunny.",
    "++": "Likes fiber in food.",
    "+": "Likes healthy food.",
    "-": "Grabs whatever has meat in it.",
    "--": "Eats the cheapest artificial stuff available.",
    "---": "Eats meat, Jurassic Park style.",
    "----": "Lives on snacks and Coke.",
}


def _build_legacy_common_specs() -> dict[str, CodeSpec]:
    return {
        **_code_specs(LEGACY_GEEK_OF_CODES),
        "s": CodeSpec(label="Shape", scale="dimensions_pair"),
        "a": CodeSpec(label="Age", rating_map=LEGACY_AGE_MAP, note="`aNN` means an exact age."),
        "C": CodeSpec(label="Computers", rating_map=V4_COMPUTERS_MAP),
        "U": CodeSpec(label="Unix", scale="legacy_unix"),
        "P": CodeSpec(label="Perl", rating_map=LEGACY_PERL_MAP),
        "L": CodeSpec(label="Linux", rating_map=LEGACY_LINUX_MAP),
        "3": CodeSpec(label="386BSD", rating_map=LEGACY_386BSD_MAP),
        "E": CodeSpec(label="Emacs", rating_map=LEGACY_EMACS_MAP),
        "N": CodeSpec(label="Usenet news", rating_map=LEGACY_USENET_MAP),
        "K": CodeSpec(label="Kibo", rating_map=LEGACY_KIBO_MAP),
        "M": CodeSpec(label="Macintosh", rating_map=MAC_MAP),
        "V": CodeSpec(label="VMS", rating_map=LEGACY_VMS_MAP),
        "Y": CodeSpec(label="Cypherpunks / privacy politics", rating_map=LEGACY_CYPHERPUNK_MAP),
        "t": CodeSpec(label="Star Trek", rating_map=TREK_V4_MAP),
        "5": CodeSpec(label="Babylon 5", rating_map=LEGACY_BABYLON5_MAP),
        "R": CodeSpec(label="Role-playing games", rating_map=V4_ROLEPLAY_MAP),
        "tv": CodeSpec(label="Television", scale="legacy_tv"),
        "b": CodeSpec(label="Books", rating_map=MODERN_BOOKS_MAP),
        "D": CodeSpec(label="DOOM / 3D shooters", rating_map=LEGACY_DOOM_MAP),
        "e": CodeSpec(label="Education", rating_map=V4_EDUCATION_MAP),
        "h": CodeSpec(label="Housing", rating_map=V4_HOUSING_MAP),
        "r": CodeSpec(label="Relationships", rating_map=V4_RELATIONSHIPS_MAP),
        "x": CodeSpec(label="Sex / gender / female", scale="sex_scale_legacy", rating_map={"?": "Uses `x` to mark female gender without sharing sex-life details."}),
        "y": CodeSpec(label="Sex / gender / male", scale="sex_scale_legacy", rating_map={"?": "Uses `y` to mark male gender without sharing sex-life details."}),
        "z": CodeSpec(label="Sex / gender / undisclosed", scale="sex_scale_legacy", rating_map={"?": "Uses `z` to mark undisclosed gender without sharing sex-life details."}),
    }


def _build_legacy_v2_specs() -> dict[str, CodeSpec]:
    specs = _build_legacy_common_specs()
    specs.update(
        {
            "d": CodeSpec(label="Dress", rating_map=V2_DRESS_MAP),
            "H": CodeSpec(label="Hair", scale="legacy_hair", rating_map={"?": "Uses wigs to vary hair."}),
            "g": CodeSpec(label="Glasses", rating_map=LEGACY_GLASSES_MAP),
            "p": CodeSpec(label="Pens / pocket writing instruments", scale="pen_count", rating_map={"?": "Cannot find a writing instrument."}),
            "au": CodeSpec(label="Automobile", rating_map=LEGACY_AUTOMOBILE_MAP),
            "w": CodeSpec(label="Weirdness", rating_map=LEGACY_WEIRDNESS_MAP),
            "v": CodeSpec(label="Verbage / spoken language", rating_map=LEGACY_VERBAGE_MAP),
            "W": CodeSpec(label="Microsoft Windows", rating_map=LEGACY_WINDOWS_MAP),
            "po": CodeSpec(label="Politics", rating_map=V2_POLITICS_MAP),
            "-po": CodeSpec(label="Politics", rating_map={"+": "Rejects political labeling and sees both sides as equally broken."}),
            "j": CodeSpec(label="Jeopardy", scale="media_interest"),
            "G": CodeSpec(label="Magic: The Gathering", rating_map=V2_MAGIC_MAP),
            "B": CodeSpec(label="Barney", rating_map=LEGACY_BARNEY_MAP),
            "u": CodeSpec(label="Music", rating_map=LEGACY_MUSIC_MAP),
            "f": CodeSpec(label="Friends", rating_map=LEGACY_FRIENDS_MAP),
            "n": CodeSpec(label="Nutrition", rating_map=LEGACY_NUTRITION_MAP),
        }
    )
    return specs


def _build_legacy_v3_specs() -> dict[str, CodeSpec]:
    specs = _build_legacy_common_specs()
    specs.update(
        {
            "d": CodeSpec(label="Dress", rating_map=CLOTHING_MAP),
            "w": CodeSpec(label="Microsoft Windows", rating_map=LEGACY_WINDOWS_MAP),
            "W": CodeSpec(label="World Wide Web", rating_map=LEGACY_WEB_MAP),
            "O": CodeSpec(label="OS/2", rating_map=LEGACY_OS2_MAP),
            "PS": CodeSpec(label="Political and social issues", rating_map=PS_MAP),
            "PE": CodeSpec(label="Politics and economic issues", rating_map=LEGACY_PE_MAP),
            "PGP": CodeSpec(label="Pretty Good Privacy (PGP)", rating_map=PGP_MAP),
            "X": CodeSpec(label="X-Files", rating_map=LEGACY_XFILES_MAP),
            "DI": CodeSpec(label="Dilbert", rating_map=LEGACY_DILBERT_MAP),
            "G": CodeSpec(label="The Geek Code", rating_map=LEGACY_GEEKCODE_MAP),
        }
    )
    return specs


def _build_v4_specs() -> dict[str, CodeSpec]:
    specs: dict[str, CodeSpec] = {}
    specs.update(_code_specs(V4_GEEK_OF_CODES))
    specs.update(_code_specs(UNIX_CODES, parent="U"))
    specs.update(_code_specs(V4_LANGUAGE_CODES, parent="L"))
    specs.update(_code_specs(V4_TV_CODES, parent="T"))
    specs.update(_code_specs(V4_COMICS_CODES, scale="comic_interest"))

    specs.update(
        {
            "a": CodeSpec(label="Age", rating_map=V4_AGE_MAP, note="`aNN` means an exact age."),
            "b": CodeSpec(label="Beardliness / facial hair", scale="facial_hair"),
            "bm": CodeSpec(label="Mustache", scale="facial_hair"),
            "bs": CodeSpec(label="Sideburns", scale="facial_hair"),
            "bb": CodeSpec(label="Bushy eyebrows", scale="facial_hair"),
            "c": CodeSpec(label="Clothing", rating_map=CLOTHING_MAP),
            "d": CodeSpec(label="Dimensions", scale="dimensions_pair"),
            "C": CodeSpec(label="Computers", rating_map=V4_COMPUTERS_MAP),
            "U": CodeSpec(label="Unix", rating_map=V4_UNIX_MAP),
            "L": CodeSpec(label="Programming languages", scale="language_skill"),
            "G:": CodeSpec(label="GitHub handle"),
            "GB:": CodeSpec(label="Bitbucket handle"),
            "FE": CodeSpec(label="Frontend", scale="discipline_interest"),
            "BE": CodeSpec(label="Backend", scale="discipline_interest"),
            "M": CodeSpec(label="Macintosh", rating_map=MAC_MAP),
            "PGP": CodeSpec(label="Pretty Good Privacy (PGP)", rating_map=PGP_MAP),
            "E": CodeSpec(
                label="Electronics",
                rating_map=ELECTRONICS_MAP,
                scale="skill",
            ),
            "H": CodeSpec(
                label="Hardware",
                rating_map=HARDWARE_MAP,
                scale="skill",
            ),
            "P": CodeSpec(
                label="Ambiguous `P` token",
                scale="ambiguous_p_v4",
                note=(
                    "The v4 README sample includes `P++`, but the same changelist says Perl was removed. "
                    "Older Geek Code versions used `P` for Perl."
                ),
            ),
            "PS": CodeSpec(label="Political and social issues", rating_map=PS_MAP),
            "PSG": CodeSpec(
                label="Political and social issues / green politics, sustainability, climate",
                scale="policy_subissue",
            ),
            "PSL": CodeSpec(label="Political and social issues / civil liberties", scale="policy_subissue"),
            "PSS": CodeSpec(label="Political and social issues / gender politics", scale="policy_subissue"),
            "PE": CodeSpec(label="Politics and economic issues", rating_map=PE_V4_MAP),
            "T": CodeSpec(label="TV shows / series / movies", scale="media_interest"),
            "Tt": CodeSpec(label="TV / Star Trek", rating_map=TREK_V4_MAP, parent="T"),
            "R": CodeSpec(label="Role playing", rating_map=V4_ROLEPLAY_MAP),
            "B": CodeSpec(label="Books", rating_map=V4_BOOKS_MAP),
            "e": CodeSpec(label="Education", rating_map=V4_EDUCATION_MAP),
            "h": CodeSpec(label="Housing", rating_map=V4_HOUSING_MAP),
            "r": CodeSpec(label="Relationships", rating_map=V4_RELATIONSHIPS_MAP),
            "x": CodeSpec(label="Sex / gender (female)", scale="sex_scale_v4"),
            "y": CodeSpec(label="Sex / gender (male)", scale="sex_scale_v4"),
            "z": CodeSpec(label="Sex / gender (undisclosed)", scale="sex_scale_v4"),
        }
    )
    return specs


def _build_modern_specs() -> dict[str, CodeSpec]:
    specs: dict[str, CodeSpec] = {}
    specs.update(_code_specs(MODERN_GEEK_OF_CODES))
    specs.update(_code_specs(UNIX_CODES, parent="U"))
    specs.update(_code_specs(MODERN_LANGUAGE_CODES, parent="L"))
    specs.update(_code_specs(SOFTWARE_DOMAIN_CODES, parent="SD"))
    specs.update(_code_specs(MODERN_TV_CODES, parent="T"))
    specs.update(_code_specs(MODERN_COMICS_CODES, scale="comic_interest"))

    specs.update(
        {
            "A": CodeSpec(label="Age", rating_map=MODERN_AGE_MAP, note="`A=NN` means an exact age."),
            "B": CodeSpec(label="Beardliness / hair", scale="hair_profile"),
            "C": CodeSpec(label="Clothing", rating_map=CLOTHING_MAP),
            "D": CodeSpec(label="Dimensions", scale="dimensions_pair"),
            "CM": CodeSpec(label="Computers", rating_map=V4_COMPUTERS_MAP),
            "MW": CodeSpec(label="Microsoft Windows", scale="windows_release"),
            "U": CodeSpec(label="Unix", rating_map=V4_UNIX_MAP),
            "MC": CodeSpec(label="Mac / Apple", rating_map=MAC_MAP),
            "L": CodeSpec(label="Programming languages", scale="language_skill"),
            "SD": CodeSpec(label="Software domains", scale="discipline_interest"),
            "IO": CodeSpec(label="Input / output", scale="io_pair"),
            "PGP": CodeSpec(label="Pretty Good Privacy (PGP)", rating_map=PGP_MAP),
            "G:": CodeSpec(label="Version control username / GitHub"),
            "Gl:": CodeSpec(label="Version control username / GitLab"),
            "Gb:": CodeSpec(label="Version control username / Bitbucket"),
            "Gbk:": CodeSpec(label="Version control username / BitKeeper"),
            "Gbn:": CodeSpec(label="Version control username / Beanstalk"),
            "Gsvn:": CodeSpec(label="Version control username / Subversion"),
            "Gtfs:": CodeSpec(label="Version control username / Team Foundation Server"),
            "E": CodeSpec(
                label="Electronics",
                rating_map=ELECTRONICS_MAP,
                scale="skill",
            ),
            "H": CodeSpec(
                label="Hardware",
                rating_map=HARDWARE_MAP,
                scale="skill",
            ),
            "PS": CodeSpec(label="Political and social issues", rating_map=PS_MAP),
            "PSG": CodeSpec(
                label="Political and social issues / green politics, sustainability, climate",
                scale="policy_subissue",
            ),
            "PSL": CodeSpec(label="Political and social issues / civil liberties", scale="policy_subissue"),
            "PSS": CodeSpec(label="Political and social issues / gender politics", scale="policy_subissue"),
            "PE": CodeSpec(label="Politics and economic issues", rating_map=PE_MODERN_MAP),
            "T": CodeSpec(label="TV shows / series / movies", scale="media_interest"),
            "TST": CodeSpec(label="TV / Star Trek", rating_map=TREK_MODERN_MAP, parent="T"),
            "RPG": CodeSpec(label="Roleplaying games", rating_map=MODERN_RPG_MAP),
            "BK": CodeSpec(label="Books", rating_map=MODERN_BOOKS_MAP),
            "R": CodeSpec(label="Residence", rating_map=MODERN_RESIDENCE_MAP),
        }
    )
    return specs


V4_PROFILE = DecodeProfile(name="v4", specs=_build_v4_specs())
MODERN_PROFILE = DecodeProfile(name="modern", specs=_build_modern_specs())
LEGACY_V2_PROFILE = DecodeProfile(name="legacy_v2", specs=_build_legacy_v2_specs())
LEGACY_V3_PROFILE = DecodeProfile(name="legacy_v3", specs=_build_legacy_v3_specs())


def normalize_text(text: str) -> str:
    return text.translate(_DASH_TRANSLATION)


def extract_version(text: str) -> str | None:
    begin_match = re.search(r"BEGIN\s+GEEK\s+CODE\s+VERSION\s+([0-9.]+)", text, re.IGNORECASE)
    if begin_match:
        return begin_match.group(1)

    line_match = re.search(r"Version:\s*([0-9.]+)", text, re.IGNORECASE)
    if line_match:
        return line_match.group(1)

    banner_match = re.search(r"GEEK\s+CODE\s+([0-9.]+)", text, re.IGNORECASE)
    if banner_match:
        return banner_match.group(1)

    code_of_geeks_match = re.search(r"Code of the Geeks v([0-9.]+)", text, re.IGNORECASE)
    if code_of_geeks_match:
        return code_of_geeks_match.group(1)

    return None


def extract_body_lines(text: str) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        upper_line = line.upper()
        if "BEGIN GEEK CODE" in upper_line or "END GEEK CODE" in upper_line:
            continue
        if upper_line.startswith("VERSION:"):
            continue
        lines.append(line)
    return lines


def tokenize(text: str) -> list[str]:
    body = " ".join(extract_body_lines(text))
    parts = [token for token in body.split() if token]
    tokens: list[str] = []
    pending = ""

    for part in parts:
        token = pending + part
        pending = ""
        if token.endswith("/"):
            pending = token
            continue
        tokens.append(token)

    if pending:
        tokens.append(pending)

    return tokens


def _major_version(version: str | None) -> int | None:
    if not version:
        return None
    try:
        return int(version.split(".", 1)[0])
    except ValueError:
        return None


def _infer_profile(raw_tokens: list[str]) -> DecodeProfile:
    modern_prefixes = ("CM", "MC", "MW", "IO", "BK", "RPG", "KD", "KX", "KM", "TST", "TDW", "TEX", "SD")
    modern_unique_codes = (
        set(MODERN_LANGUAGE_CODES)
        | set(SOFTWARE_DOMAIN_CODES)
        | set(MODERN_TV_CODES)
        | (set(MODERN_COMICS_CODES) - {"K"})
        | {"CM", "MC", "MW", "IO", "BK", "RPG"}
    )

    if any(token.startswith(modern_prefixes) for token in raw_tokens):
        return MODERN_PROFILE
    if any(_PRONOUN_RE.match(token) for token in raw_tokens):
        return MODERN_PROFILE
    if any(_MBTI_RE.match(token) for token in raw_tokens):
        return MODERN_PROFILE
    if any(re.match(r"^A(?:[=:+?+\-]|$)", token) for token in raw_tokens):
        return MODERN_PROFILE
    if any(re.match(r"^B[^ ]*:[^ ]*:[^ ]*:[^ ]*:[^ ]*$", token) for token in raw_tokens):
        return MODERN_PROFILE
    if any(re.match(r"^D[^ ]*:[^ ]+$", token) for token in raw_tokens):
        return MODERN_PROFILE
    if any(
        (_match_known_code(token.lstrip("!"), MODERN_PROFILE.specs) in modern_unique_codes)
        for token in raw_tokens
    ):
        return MODERN_PROFILE

    legacy_v3_markers = (
        "DI",
        "PGP",
        "PS",
        "PE",
        "X",
        "O",
    )
    if any(token.startswith(legacy_v3_markers) for token in raw_tokens):
        return LEGACY_V3_PROFILE
    if any(re.match(r"^(?:au|po|-po|g|p|H|v|u|f|n|j|B)[+*?%!:(0-9-]", token) for token in raw_tokens):
        return LEGACY_V2_PROFILE

    if any(re.match(r"^[ABCD](?:[=:_?+\-]|$)", token) for token in raw_tokens):
        return MODERN_PROFILE
    return V4_PROFILE


def _select_profile(version: str | None, raw_tokens: list[str]) -> DecodeProfile:
    major = _major_version(version)
    if major in {1, 2}:
        return LEGACY_V2_PROFILE
    if major == 3:
        return LEGACY_V3_PROFILE
    if major == 4:
        return V4_PROFILE
    if major in {5, 6}:
        return MODERN_PROFILE
    return _infer_profile(raw_tokens)


def _prefix_codes(specs: dict[str, CodeSpec]) -> tuple[str, ...]:
    return tuple(sorted((code for code in specs if code.endswith(":")), key=len, reverse=True))


def _known_codes(specs: dict[str, CodeSpec]) -> tuple[str, ...]:
    return tuple(sorted((code for code in specs if not code.endswith(":")), key=len, reverse=True))


def _is_unsplittable_token(token: str, profile: DecodeProfile) -> bool:
    if profile.name == "modern" and _PRONOUN_RE.match(token):
        return True
    return False


def _match_known_code(body: str, specs: dict[str, CodeSpec]) -> str | None:
    for prefix_code in _prefix_codes(specs):
        if body.startswith(prefix_code):
            return prefix_code

    for code in _known_codes(specs):
        if not body.startswith(code):
            continue
        rest = body[len(code) :]
        spec = specs[code]
        if not rest or not rest[0].isalpha():
            return code
        if spec.scale == "legacy_unix" and re.match(r"^[A-Z*?]+(?:[+?-].*|)$", rest):
            return code
    return None


def expand_group_token(token: str, profile: DecodeProfile) -> list[str]:
    if "/" not in token or _is_unsplittable_token(token, profile):
        return [token]

    specs = profile.specs
    parts = token.split("/")
    expanded = [parts[0]]
    anchor_body = parts[0].lstrip("!")
    anchor_code = _match_known_code(anchor_body, specs)

    for part in parts[1:]:
        negated = part.startswith("!")
        body = part[1:] if negated else part
        if _match_known_code(body, specs):
            expanded.append(part)
            continue

        candidate = None
        if anchor_code:
            for prefix_length in range(1, len(anchor_code)):
                prefix = anchor_code[:prefix_length]
                possible = prefix + body
                if _match_known_code(possible, specs):
                    candidate = possible
                    break

        if candidate is None:
            previous_code = _match_known_code(expanded[-1].lstrip("!"), specs)
            if previous_code:
                for prefix_length in range(1, len(previous_code)):
                    prefix = previous_code[:prefix_length]
                    possible = prefix + body
                    if _match_known_code(possible, specs):
                        candidate = possible
                        break

        expanded.append(f"!{candidate}" if negated and candidate else (candidate or part))

    return expanded


def _spec_or_parent_has_rating(spec: CodeSpec, code: str, rating: str, specs: dict[str, CodeSpec]) -> bool:
    current_code = code if code in specs else None
    current_spec = spec
    while True:
        if rating in current_spec.rating_map:
            return True
        if current_code is None or current_spec.parent is None:
            return False
        current_code = current_spec.parent
        current_spec = specs[current_code]


def parse_qualifier(
    code: str,
    spec: CodeSpec,
    suffix: str,
    refused: bool,
    specs: dict[str, CodeSpec],
) -> ParsedQualifier:
    parsed = ParsedQualifier(raw=suffix, refusal=refused)
    working = suffix

    if code in {"a", "A"}:
        if working.isdigit():
            parsed.exact_value = working
            parsed.rating = working
            return parsed
        if working.startswith("=") and working[1:].isdigit():
            parsed.exact_value = working[1:]
            parsed.rating = parsed.exact_value
            return parsed

    if ">" in working:
        current, goal = working.split(">", 1)
        parsed.goal = goal or None
        working = current

    if "^" in working:
        parsed.credential = True
        working = working.replace("^", "")

    if "@" in working:
        parsed.variable = True
        working = working.replace("@", "")

    if "$" in working:
        parsed.earns_money = True
        working = working.replace("$", "")

    crossover_match = re.search(r"\(([^)]*)\)", working)
    if crossover_match:
        parsed.crossover = crossover_match.group(1)
        working = re.sub(r"\([^)]*\)", "", working)

    if working == "?" and not _spec_or_parent_has_rating(spec, code, "?", specs):
        parsed.unknown = True
        return parsed

    parsed.rating = working
    return parsed


def _describe_dimensions(rating: str) -> str:
    if ":" not in rating:
        return f"dimension profile `{rating}`"

    vertical, horizontal = rating.split(":", 1)
    vertical_map = {
        "+++": "extremely tall",
        "++": "quite tall",
        "+": "a little taller than average",
        "_": "average height",
        "": "average height",
        "-": "shorter than average",
        "--": "much shorter than average",
        "---": "extremely short",
    }
    horizontal_map = {
        "+++": "extremely broad",
        "++": "quite broad",
        "+": "a little broader than average",
        "_": "average build",
        "": "average build",
        "-": "thinner than average",
        "--": "much thinner than average",
        "---": "extremely thin",
    }
    left = vertical_map.get(vertical, f"vertical level `{vertical}`")
    right = horizontal_map.get(horizontal, f"horizontal level `{horizontal}`")
    return f"{left} and {right}"


def _describe_hair_profile(rating: str) -> str:
    parts = rating.split(":")
    labels = ["head hair", "beard", "brows", "mustache", "sideburns"]
    level_map = {
        "+++": "very heavy",
        "++": "substantial",
        "+": "above-average",
        "_": "average",
        "": "average",
        "-": "below-average",
        "--": "bald / shaved / little",
        "---": "unable or unwilling to grow",
    }
    if len(parts) != 5:
        return f"hair profile `{rating}`"

    descriptions = [f"{label} {level_map.get(value, f'level `{value}`')}" for label, value in zip(labels, parts)]
    return "; ".join(descriptions)


def _describe_windows_release(rating: str) -> str:
    match = re.match(r"^([A-Za-z0-9.*_-]*?)([+_?-].*|)$", rating)
    if not match:
        return f"Windows profile `{rating}`"

    release = match.group(1)
    level = match.group(2)
    skill_map = {
        "++++": "expert Windows programming proficiency",
        "+++": "strong Windows platform expertise",
        "++": "confident troubleshooting and registry-level Windows use",
        "+": "enthusiastic day-to-day Windows use",
        "": "uses Windows for specific reasons without much affection",
        "-": "frequent Windows installation or peripheral trouble",
        "--": "strongly dislikes Windows",
        "---": "sees Windows as a huge setback to computing",
    }
    base = skill_map.get(level, f"Windows level `{level}`")
    if release:
        return f"Windows {release}; {base}"
    return base


def _describe_io_pair(rating: str) -> str:
    if ":" not in rating:
        return f"input/output profile `{rating}`"

    input_rating, output_rating = rating.split(":", 1)
    input_map = {
        "+++": "works directly with raw data and deep internals",
        "++": "leans toward lower-level input and data handling",
        "+": "comfortably handles technical input and data work",
        "": "uses keyboard and mouse equally for input",
        "_": "uses keyboard and mouse equally for input",
        "-": "prefers more abstracted input layers",
        "--": "prefers higher-level input abstractions",
        "---": "keeps data and code out of sight and focuses on attractive GUI input flows",
    }
    output_map = {
        "+++": "is extremely output and interface oriented",
        "++": "cares strongly about polished output",
        "+": "cares about presentation and output quality",
        "": "uses keyboard and mouse equally for output",
        "_": "uses keyboard and mouse equally for output",
        "-": "leans away from presentation-heavy output",
        "--": "prefers text-only terminal output",
        "---": "does not care much about user experience and treats users abstractly",
    }
    return f"input: {input_map.get(input_rating, f'level `{input_rating}`')}; output: {output_map.get(output_rating, f'level `{output_rating}`')}"


def _describe_legacy_unix(rating: str) -> str:
    match = re.match(r"^([A-Z*?]*)(\+{1,4}|-{1,3}|\?)?$", rating)
    if not match:
        return f"Unix profile `{rating}`"

    platforms = match.group(1)
    level = match.group(2) or ""
    platform_map = {
        "B": "BSD",
        "L": "Linux",
        "U": "Ultrix",
        "A": "AIX",
        "V": "SysV",
        "H": "HPUX",
        "I": "IRIX",
        "O": "OSF/1",
        "S": "SunOS / Solaris",
        "C": "SCO Unix",
        "X": "NeXT",
        "*": "other Unix",
        "?": "unknown Unix variant",
    }
    level_map = {
        "++++": "sysadmin-level Unix mastery",
        "+++": "deep Unix access and confidence",
        "++": "heavy Unix user who annoys the admins",
        "+": "has a Unix account and happily slams VMS",
        "": "has a Unix account and uses it",
        "-": "would rather be on VMS",
        "--": "has seen Unix and disliked it",
        "---": "thinks Unix geeks are nerds in disguise",
        "?": "does not know what Unix is",
    }

    platform_names = [platform_map.get(ch, ch) for ch in platforms]
    base = level_map.get(level, f"Unix level `{level}`")
    if platform_names:
        return f"{base}; platforms: {', '.join(platform_names)}"
    return base


def _describe_pen_count(rating: str) -> str:
    if rating == "":
        return "Average shirt-pocket pen count."
    if rating == "?":
        return "Cannot find a writing instrument."

    match = re.match(r"^(\d+)(\+?)$", rating)
    if not match:
        return f"pen-count level `{rating}`"

    count = match.group(1)
    if match.group(2):
        return f"Carries about {count} pens or pencils, plus a calculator or portable computer."
    return f"Carries about {count} pens or pencils."


def _describe_legacy_hair(rating: str) -> str:
    if rating == "?":
        return "Uses wigs to vary hair."

    dyed = rating.endswith("*")
    base = rating[:-1] if dyed else rating
    table = {
        "++++": "hair down past the waist",
        "+++": "hair down to mid-back",
        "++": "hair down to the shoulders",
        "+": "hair is on the longer side",
        "": "pretty normal hair",
        "-": "hair cut above the neck",
        "--": "hair above the neck and ear / flattop territory",
        "---": "hair about 1/8 inch long",
        "----": "shaves head daily",
    }
    description = table.get(base, f"hair level `{rating}`")
    if dyed:
        description += "; dyed unusual colors"
    return description


def _describe_legacy_sex(code: str, rating: str) -> str:
    prefix = {
        "x": "female",
        "y": "male",
        "z": "gender undisclosed",
    }.get(code, "gender unspecified")

    if rating == "?":
        return f"{prefix}; does not want to share sex-life details"
    if rating == "!+":
        return f"{prefix}; no experience yet, but willing to learn"

    base_table = {
        "++++": "has children to prove there has been real-world experience",
        "+++": "married and can theoretically get it whenever wanted",
        "++": "has a reputation for being easy or adventurous",
        "+": "has had real, live sex",
        "": "has had sex, but not with another person",
        "-": "is not having sex by choice",
        "--": "is not having sex because they cannot get any",
        "---": "is not having sex due to strong vocation or beliefs",
    }
    modifier_table = {
        "*": "also self-identifies as a pervert",
        "**": "also makes perverts look like angels",
    }

    if rating in modifier_table:
        return f"{prefix}; {modifier_table[rating]}"

    match = re.match(r"^(\+{1,4}|-{1,3}|)(\*{1,2})?$", rating)
    if not match:
        return f"{prefix}; sex-life level `{rating}`"

    base = match.group(1)
    modifier = match.group(2) or ""
    description = f"{prefix}; {base_table.get(base, f'sex-life level `{rating}`')}"
    if modifier:
        description += f"; {modifier_table[modifier]}"
    return description


def generic_scale_text(scale: str, rating: str, code: str) -> tuple[str, bool]:
    if scale == "facial_hair":
        table = {
            "+++": "very heavy facial hair",
            "++": "substantial facial hair",
            "+": "above-average facial hair",
            "": "average facial hair",
            "_": "average facial hair",
            "-": "less facial hair than average",
            "--": "little or no facial hair",
            "---": "effectively unable or unwilling to grow facial hair",
        }
        return table.get(rating, f"facial-hair level `{rating}`"), True

    if scale == "hair_profile":
        return _describe_hair_profile(rating), True

    if scale == "dimensions_pair":
        return _describe_dimensions(rating), True

    if scale == "language_skill":
        table = {
            "++++": "creator or world-class expert level",
            "+++": "expert, likely uses it for nearly everything appropriate",
            "++": "advanced, high-confidence proficiency",
            "+": "above-average proficiency and frequent use",
            "": "basic familiarity or neutral stance",
            "_": "basic familiarity or neutral stance",
            "-": "limited enthusiasm or mild dislike",
            "--": "strong dislike",
            "---": "intense rejection",
        }
        return table.get(rating, f"language-skill level `{rating}`"), True

    if scale == "discipline_interest":
        table = {
            "+++": "strongly identified with this area",
            "++": "very into this area",
            "+": "likes and values this area",
            "": "neutral about this area",
            "_": "neutral about this area",
            "-": "not especially into this area",
            "--": "actively dislikes this area",
            "---": "strongly rejects this area",
        }
        return table.get(rating, f"interest level `{rating}`"), True

    if scale == "skill":
        table = {
            "++++": "world-class skill",
            "+++": "expert-level skill",
            "++": "strong practical skill",
            "+": "above-average skill",
            "": "baseline familiarity",
            "_": "baseline familiarity",
            "-": "below-average comfort",
            "--": "very limited comfort",
            "---": "strong aversion or minimal ability",
        }
        return table.get(rating, f"skill level `{rating}`"), True

    if scale == "media_interest" or scale == "comic_interest":
        table = {
            "++++": "fanatical devotion",
            "+++": "obsessive fan level",
            "++": "very strong fan",
            "+": "likes it",
            "": "neutral or casual familiarity",
            "_": "neutral or casual familiarity",
            "-": "does not really get the appeal",
            "--": "actively dislikes it",
            "---": "strongly hates it",
        }
        return table.get(rating, "Selected / included." if rating == "" else f"interest level `{rating}`"), True

    if scale == "sex_scale_v4":
        table = {
            "+++++": "extremely sexually experienced / famous-for-it tier",
            "++++": "has children and clear real-world experience",
            "+++": "married and can theoretically get it whenever wanted",
            "++": "more sexually experienced than average",
            "+": "has had real, live sex",
            "": "no partnered sex",
            "-": "not having sex by choice",
            "--": "not having sex because they cannot get any",
            "---": "celibate by vocation or vow",
            "*": "self-identifies as a pervert",
            "**": "pervert among perverts",
            "?": "sex is unknown or entirely absent from experience",
        }
        prefix = {
            "x": "female",
            "y": "male",
            "z": "gender undisclosed",
        }.get(code, "gender unspecified")
        if rating in table:
            return f"{prefix}; {table[rating]}", True
        return f"{prefix}; sex-life level `{rating}`", True

    if scale == "pronoun_scale_modern":
        table = {
            "**": "taboo-sex expert level",
            "*": "sexually non-normative or kinky",
            "++++": "has children and clear real-world experience",
            "+++": "married and can theoretically get it whenever wanted",
            "++": "has a reputation for being sexually easy or adventurous",
            "+": "has had sex with other people",
            "": "shares pronouns without an explicit relationship / sex modifier",
            "-": "is abstaining by choice",
            "--": "others do not show romantic interest",
            "---": "abstaining due to strong religious or personal beliefs",
            "%": "member of the Sour Bachelor(ette)'s Club of America",
            "!": "does not want to share sexual details",
            ">+": "is actively seeking sexual experience",
        }
        if rating in table:
            return table[rating], True
        return f"relationship / sex marker `{rating}`", True

    if scale == "policy_subissue":
        table = {
            "+++": "very strongly aligned with this sub-issue",
            "++": "strongly aligned with this sub-issue",
            "+": "somewhat aligned with this sub-issue",
            "": "mentions this sub-issue without a rating",
            "-": "somewhat opposed on this sub-issue",
            "--": "strongly opposed on this sub-issue",
            "---": "extremely opposed on this sub-issue",
        }
        return table.get(rating, f"sub-issue stance `{rating}`"), True

    if scale == "legacy_unix":
        return _describe_legacy_unix(rating), True

    if scale == "pen_count":
        return _describe_pen_count(rating), True

    if scale == "legacy_hair":
        return _describe_legacy_hair(rating), True

    if scale == "sex_scale_legacy":
        return _describe_legacy_sex(code, rating), True

    if scale == "legacy_tv":
        table = {
            "+++": "lives in front of television and wishes for more channels",
            "++": "leaves the TV on to avoid missing anything",
            "+": "watches some television every day",
            "": "watches only worthwhile shows",
            "-": "watches mainly for news and special programming",
            "--": "turns on TV mostly for natural disasters",
        }
        return table.get(rating, f"television level `{rating}`"), True

    if scale == "ambiguous_p_v4":
        base = "Ambiguous in v4: the sample block includes `P`, but the v4 category list does not define it."
        perl_hint = {
            "+++++": "In older versions, `P` meant Perl at Larry Wall level.",
            "++++": "In older versions, `P` meant very deep Perl expertise.",
            "+++": "In older versions, `P` meant strong Perl preference.",
            "++": "In older versions, `P` meant solid Perl proficiency.",
            "+": "In older versions, `P` meant some Perl knowledge and interest.",
            "": "In older versions, `P` meant awareness of Perl.",
            "-": "In older versions, `P` meant mild Perl skepticism.",
            "--": "In older versions, `P` meant strong Perl dislike.",
            "---": "In older versions, `P` meant intense Perl rejection.",
        }
        if rating in perl_hint:
            return f"{base} {perl_hint[rating]}", True
        return f"{base} Older versions used `P` for Perl with rating `{rating}`.", True

    if scale == "windows_release":
        return _describe_windows_release(rating), True

    if scale == "io_pair":
        return _describe_io_pair(rating), True

    return (rating if rating else "Selected / included."), True


def describe_token(
    code: str,
    spec: CodeSpec,
    qualifier: ParsedQualifier,
    payload: str | None,
    specs: dict[str, CodeSpec],
) -> tuple[str, list[str], bool]:
    notes: list[str] = []
    inferred = False

    if qualifier.refusal:
        description = f"Refuses to participate in {spec.label.lower()}."
    elif qualifier.unknown:
        description = f"No stated knowledge about {spec.label.lower()}."
    elif code.endswith(":") and payload is not None:
        description = payload
    elif code in {"a", "A"} and qualifier.exact_value is not None:
        description = f"Exact age {qualifier.exact_value}."
    else:
        description = ""
        current_code = code if code in specs else None
        current_spec = spec
        while True:
            if qualifier.rating in current_spec.rating_map:
                description = current_spec.rating_map[qualifier.rating]
                break
            if current_spec.scale:
                description, inferred = generic_scale_text(current_spec.scale, qualifier.rating, code)
                break
            if current_code is None or current_spec.parent is None:
                break
            current_code = current_spec.parent
            current_spec = specs[current_code]

        if not description:
            if qualifier.rating:
                description = f"Rating `{qualifier.rating}`."
                inferred = True
            else:
                description = "Selected / included."

    if spec.note:
        notes.append(spec.note)
    if qualifier.credential:
        notes.append("Marked with a degree or certificate in this area.")
    if qualifier.variable:
        notes.append("Marked as variable or changeable.")
    if qualifier.earns_money:
        notes.append("This is done professionally / for pay.")
    if qualifier.crossover:
        notes.append(f"Crossover or range includes `{qualifier.crossover}`.")
    if qualifier.goal:
        if qualifier.goal == "$":
            notes.append("Wants to do this professionally / for pay.")
        else:
            notes.append(f"Wannabe / goal marker points toward `{qualifier.goal}`.")

    return description, notes, inferred


def _parse_special_token(raw_token: str, profile: DecodeProfile) -> DecodedToken | None:
    normalized = raw_token.strip()

    if profile.name in {"legacy_v2", "legacy_v3"} and normalized == ":":
        return DecodedToken(
            raw=raw_token,
            normalized=normalized,
            code="s",
            label="Shape",
            description=_describe_dimensions(":"),
            notes=[],
            inferred=True,
        )

    if profile.name == "modern":
        pronoun_match = _PRONOUN_RE.match(normalized)
        if pronoun_match:
            pronouns = pronoun_match.group(1)
            suffix = pronoun_match.group(2)
            spec = CodeSpec(label=f"Pronouns / gender / {pronouns}", scale="pronoun_scale_modern")
            qualifier = parse_qualifier(pronouns, spec, suffix, False, {})
            description, notes, inferred = describe_token(pronouns, spec, qualifier, None, {})
            description = f"Uses {pronouns} pronouns; {description}"
            return DecodedToken(
                raw=raw_token,
                normalized=normalized,
                code=pronouns,
                label=spec.label,
                description=description,
                notes=notes,
                inferred=inferred,
            )

        mbti_match = _MBTI_RE.match(normalized)
        if mbti_match:
            personality = mbti_match.group(1)
            variant = mbti_match.group(2)
            if variant == "A":
                description = f"Myers-Briggs type {personality}, assertive variant."
            elif variant == "T":
                description = f"Myers-Briggs type {personality}, turbulent variant."
            else:
                description = f"Myers-Briggs type {personality}."
            return DecodedToken(
                raw=raw_token,
                normalized=normalized,
                code=normalized,
                label="MBTI / personality",
                description=description,
                notes=[],
                inferred=True,
            )

    return None


def parse_token(raw_token: str, profile: DecodeProfile) -> DecodedToken:
    special = _parse_special_token(raw_token, profile)
    if special is not None:
        return special

    normalized = raw_token.strip()
    refused = normalized.startswith("!")
    body = normalized[1:] if refused else normalized

    specs = profile.specs
    payload = None
    code = _match_known_code(body, specs) or ""
    suffix = body[len(code) :] if code else ""

    if code.endswith(":"):
        payload = body[len(code) :]
        suffix = ""

    if not code:
        return DecodedToken(
            raw=raw_token,
            normalized=normalized,
            code="UNKNOWN",
            label="Unknown token",
            description=f"Could not match `{raw_token}` to a known Geek Code v4-v6 token.",
            notes=[],
            inferred=True,
        )

    spec = specs[code]
    qualifier = parse_qualifier(code, spec, suffix, refused, specs)
    description, notes, inferred = describe_token(code, spec, qualifier, payload, specs)
    label = spec.label if payload is None else f"{spec.label} / {payload}"
    return DecodedToken(
        raw=raw_token,
        normalized=normalized,
        code=code,
        label=label,
        description=description,
        notes=notes,
        inferred=inferred,
    )


def decode_geek_code(text: str) -> DecodeResult:
    normalized_text = normalize_text(text)
    version = extract_version(normalized_text)
    raw_tokens = tokenize(normalized_text)
    profile = _select_profile(version, raw_tokens)
    expanded_tokens: list[str] = []
    for token in raw_tokens:
        expanded_tokens.extend(expand_group_token(token, profile))
    decoded_tokens = [parse_token(token, profile) for token in expanded_tokens]
    return DecodeResult(
        version=version,
        source_text=text,
        normalized_text=normalized_text,
        tokens=decoded_tokens,
    )


def _render_text(result: DecodeResult) -> str:
    lines = []
    if result.version:
        lines.append(f"Version: {result.version}")
    for token in result.tokens:
        note_suffix = ""
        if token.notes:
            note_suffix = " | " + " ".join(token.notes)
        inferred_suffix = " [inferred]" if token.inferred else ""
        lines.append(
            f"- {token.raw} -> {token.code}: {token.label}: {token.description}{inferred_suffix}{note_suffix}"
        )
    return "\n".join(lines)


def _read_input(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.path:
        with open(args.path, "r", encoding="utf-8") as handle:
            return handle.read()
    return sys.stdin.read()


def age_token_from_years_v6(years: int, *, exact: bool = False) -> str:
    if years < 0:
        raise ValueError("age must be non-negative")
    if exact:
        return f"A={years}"
    if years >= 60:
        return "A++++"
    if years >= 50:
        return "A+++"
    if years >= 40:
        return "A++"
    if years >= 30:
        return "A+"
    if years >= 25:
        return "A"
    if years >= 20:
        return "A-"
    if years >= 15:
        return "A--"
    if years >= 10:
        return "A---"
    return "A----"


def build_geek_code_string(tokens: list[str]) -> str:
    return " ".join(token for token in tokens if token)


def wrap_geek_code_tokens(tokens: list[str], width: int = 72) -> list[str]:
    lines: list[str] = []
    current = ""
    for token in tokens:
        if not current:
            current = token
            continue
        candidate = f"{current} {token}"
        if len(candidate) <= width:
            current = candidate
            continue
        lines.append(current)
        current = token
    if current:
        lines.append(current)
    return lines


def format_geek_code_v6_block(tokens: list[str], width: int = 72) -> str:
    lines = wrap_geek_code_tokens(tokens, width=width)
    return "\n".join(
        [
            "----- BEGIN GEEK CODE VERSION 6.0 -----",
            *lines,
            "----- END GEEK CODE VERSION 6.0 -----",
        ]
    )


def _display_rating_key(rating: str) -> str:
    return "_" if rating == "" else rating


def _prompt_text(prompt: str) -> str:
    return input(prompt).strip()


def _prompt_yes_no(prompt: str, *, default: bool = False) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        answer = input(f"{prompt}{suffix}").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer y or n.")


def _print_code_options(options: dict[str, str]) -> None:
    for code, label in sorted(options.items()):
        separator = " " if code.endswith(":") else ": "
        print(f"  {code}{separator}{label}")


def _prompt_choice_token(
    title: str,
    prefix: str,
    rating_map: dict[str, str],
    *,
    note: str | None = None,
) -> str | None:
    print(f"\n{title}")
    if note:
        print(note)
    for rating, description in rating_map.items():
        print(f"  {_display_rating_key(rating)} -> {description}")

    while True:
        answer = _prompt_text("Choose a rating code, or press Enter to skip: ")
        if not answer:
            return None
        actual_rating = "" if answer == "_" else answer
        if actual_rating in rating_map:
            return prefix if actual_rating == "" else f"{prefix}{actual_rating}"
        print("That rating is not in the list above.")


def _prompt_token_list(
    title: str,
    allowed_codes: dict[str, str],
    *,
    example: str,
) -> list[str]:
    print(f"\n{title}")
    print(f"Enter comma-separated tokens like: {example}")
    print("Type ? to list the available codes, or press Enter to skip.")

    while True:
        answer = _prompt_text("> ")
        if not answer:
            return []
        if answer == "?":
            _print_code_options(allowed_codes)
            continue

        tokens = [token.strip() for token in answer.split(",") if token.strip()]
        invalid: list[str] = []
        for token in tokens:
            decoded = parse_token(token, MODERN_PROFILE)
            if decoded.code == "UNKNOWN" or decoded.code not in allowed_codes:
                invalid.append(token)
        if not invalid:
            return tokens
        print(f"Unrecognized or wrong-category tokens: {', '.join(invalid)}")


def _prompt_age_token_v6() -> str | None:
    print("\nAge (A)")
    print("Enter your age in years, or press Enter to skip this category.")
    while True:
        answer = _prompt_text("Age in years: ")
        if not answer:
            return None
        if answer.isdigit():
            years = int(answer)
            use_exact = _prompt_yes_no("Use exact age in the output?", default=False)
            return age_token_from_years_v6(years, exact=use_exact)
        print("Please enter a whole number, or press Enter to skip.")


def _prompt_hair_token_v6() -> str | None:
    print("\nBeardliness / Hair (B)")
    print("We'll build `Bhead:beard:brows:mustache:sideburns`.")
    print("Use `+++`, `++`, `+`, `_`, `-`, `--`, or `---` for each part.")
    choices = {
        "+++": "very heavy",
        "++": "substantial",
        "+": "above average",
        "_": "average",
        "-": "below average",
        "--": "bald / shaved / very little",
        "---": "unable or unwilling to grow",
    }
    for code, description in choices.items():
        print(f"  {code} -> {description}")

    parts = []
    labels = ["head hair", "beard", "brows", "mustache", "sideburns"]
    while True:
        parts.clear()
        skipped = False
        for index, label in enumerate(labels):
            answer = _prompt_text(
                f"{label} rating ({'press Enter to skip all of B' if index == 0 else 'required once started'}): "
            )
            if index == 0 and not answer:
                skipped = True
                break
            if answer not in choices:
                print("Please use one of the listed rating codes.")
                parts.clear()
                break
            parts.append(answer)
        if skipped:
            return None
        if len(parts) == len(labels):
            return f"B{':'.join(parts)}"


def _prompt_dimensions_token_v6() -> str | None:
    print("\nDimensions (D)")
    print("Choose one vertical rating and one horizontal rating.")
    vertical = {
        "+++": "extremely tall",
        "++": "quite tall",
        "+": "a little taller than average",
        "_": "average height",
        "-": "shorter than average",
        "--": "much shorter than average",
        "---": "extremely short",
    }
    horizontal = {
        "+++": "extremely broad",
        "++": "quite broad",
        "+": "a little broader than average",
        "_": "average build",
        "-": "thinner than average",
        "--": "much thinner than average",
        "---": "extremely thin",
    }
    print("Vertical:")
    for code, description in vertical.items():
        print(f"  {code} -> {description}")
    print("Horizontal:")
    for code, description in horizontal.items():
        print(f"  {code} -> {description}")

    while True:
        left = _prompt_text("Vertical rating, or press Enter to skip D: ")
        if not left:
            return None
        right = _prompt_text("Horizontal rating: ")
        if left in vertical and right in horizontal:
            left_value = "" if left == "_" else left
            right_value = "" if right == "_" else right
            return f"D{left_value}:{right_value}"
        print("Please use one of the listed rating codes for both parts.")


def _prompt_windows_token_v6() -> str | None:
    print("\nMicrosoft Windows (MW)")
    print("Examples: `MW11+++`, `MW10_`, `MW-`.")
    print("Use `_` for a generic Windows token with no specific release.")
    while True:
        release = _prompt_text(
            "Windows release/version tag (for example 11 or 10), `_` for generic Windows, or press Enter to skip: "
        )
        if not release:
            return None
        if release == "_":
            prefix = "MW"
            break
        if re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", release):
            prefix = f"MW{release}"
            break
        print("Please enter a simple Windows tag like `11`, `10`, `xp`, `7`, or `_` for generic Windows.")
    rating = _prompt_choice_token(
        "Windows rating",
        prefix,
        {
            "++++": "expert Windows programming proficiency",
            "+++": "strong Windows platform expertise",
            "++": "confident troubleshooting and registry-level use",
            "+": "enthusiastic Windows user",
            "": "uses Windows for specific reasons without much affection",
            "-": "frequent Windows setup trouble",
            "--": "strongly dislikes Windows",
            "---": "sees Windows as a huge setback to computing",
        },
        note="Use `_` for the neutral / no-suffix form.",
    )
    return rating


def _prompt_unix_token_v6() -> str | None:
    print("\nUnix (U)")
    print("Examples: `U`, `UL`, `ULD`, `ULDU`, `ULF`, `ULRH`, `ULRC`.")
    print("Type ? to list more Unix family codes, or press Enter to skip.")
    while True:
        code = _prompt_text("Unix family code: ")
        if not code:
            return None
        if code == "?":
            _print_code_options(UNIX_CODES)
            continue
        if code not in UNIX_CODES:
            print("That Unix code is not recognized.")
            continue
        rating = _prompt_choice_token(
            f"Unix rating for {code}",
            code,
            V4_UNIX_MAP,
            note="Use `_` for the neutral / no-suffix form.",
        )
        return rating


def _prompt_io_token_v6() -> str | None:
    print("\nInput / Output (IO)")
    print("Choose one input rating and one output rating.")
    choices = {
        "+++": "very deep / extreme",
        "++": "strong",
        "+": "above average",
        "_": "neutral / balanced",
        "-": "below average",
        "--": "strong terminal / low-output preference",
        "---": "extreme GUI-or-bust / user-experience polarity",
    }
    for code, description in choices.items():
        print(f"  {code} -> {description}")
    while True:
        input_rating = _prompt_text("Input rating, or press Enter to skip IO: ")
        if not input_rating:
            return None
        output_rating = _prompt_text("Output rating: ")
        if input_rating in choices and output_rating in choices:
            left = "" if input_rating == "_" else input_rating
            right = "" if output_rating == "_" else output_rating
            return f"IO{left}:{right}"
        print("Please use one of the listed rating codes for both parts.")


def _prompt_version_control_token_v6() -> str | None:
    print("\nVersion Control Username (G)")
    services = {
        "G:": "GitHub",
        "Gl:": "GitLab",
        "Gb:": "Bitbucket",
        "Gbk:": "BitKeeper",
        "Gbn:": "Beanstalk",
        "Gsvn:": "Subversion",
        "Gtfs:": "Team Foundation Server",
    }
    _print_code_options(services)
    service = _prompt_text("Service code, or press Enter to skip: ")
    if not service:
        return None
    if service not in services:
        print("That service code is not recognized; skipping this category.")
        return None
    username = _prompt_text("Username: ")
    if not username:
        return None
    return f"{service}{username}"


def _prompt_politics_subissues_v6() -> list[str]:
    print("\nOptional politics sub-issues")
    print("Enter comma-separated tokens like `PSG++`, `PSL+`, `PSS-`, or press Enter to skip.")
    print("Type ? to list them.")
    while True:
        answer = _prompt_text("> ")
        if not answer:
            return []
        if answer == "?":
            _print_code_options(
                {
                    "PSG": "green politics / sustainability / climate",
                    "PSL": "civil liberties",
                    "PSS": "gender politics",
                }
            )
            continue
        tokens = [token.strip() for token in answer.split(",") if token.strip()]
        invalid: list[str] = []
        for token in tokens:
            decoded = parse_token(token, MODERN_PROFILE)
            if decoded.code not in {"PSG", "PSL", "PSS"}:
                invalid.append(token)
        if not invalid:
            return tokens
        print(f"Unrecognized sub-issue tokens: {', '.join(invalid)}")


def _prompt_software_domains_v6() -> list[str]:
    return _prompt_token_list(
        "Software domains (SD...)",
        SOFTWARE_DOMAIN_CODES,
        example="SDCV++,SDDS+++,SDCG+",
    )


def _prompt_mbti_token_v6() -> str | None:
    print("\nMBTI / Personality")
    print("Examples: `INTJ-A`, `ENFP-T`, `INFJ`.")
    while True:
        answer = _prompt_text("MBTI code, or press Enter to skip: ")
        if not answer:
            return None
        if _MBTI_RE.match(answer):
            return answer
        print("That does not look like a valid MBTI code.")


def _prompt_pronoun_token_v6() -> str | None:
    print("\nPronouns / Relationships / Sex / Gender")
    pronouns = _prompt_text("Pronouns such as he/him, she/her, they/them, or press Enter to skip: ")
    if not pronouns:
        return None
    if not _PRONOUN_RE.match(f"{pronouns}+"):
        print("That pronoun format is unexpected; continuing with it anyway.")
    rating = _prompt_choice_token(
        "Pronoun-linked relationship / sex rating",
        pronouns,
        {
            "++++": "has children and clear real-world experience",
            "+++": "married and can theoretically get it whenever wanted",
            "++": "has a reputation for being sexually easy or adventurous",
            "+": "has had sex with other people",
            "": "no partnered sex",
            "-": "is abstaining by choice",
            "--": "others do not show romantic interest",
            "---": "abstaining due to strong religious or personal beliefs",
            "%": "member of the Sour Bachelor(ette)'s Club of America",
            "!": "does not want to share sexual details",
            ">+": "actively seeking sexual experience",
            "*": "sexually non-normative or kinky",
            "**": "taboo-sex expert level",
        },
        note="Use `_` for the neutral / no-suffix form.",
    )
    if rating is None:
        return pronouns
    return rating


def generate_geek_code_v6_interactive() -> str:
    print("Geek Code v6 Generator")
    print("Press Enter at any prompt to skip that category.\n")

    tokens: list[str] = []

    tokens.extend(
        _prompt_token_list(
            "Geek of / vocation (G...)",
            MODERN_GEEK_OF_CODES,
            example="GCS^,GM^",
        )
    )

    for token in (
        _prompt_age_token_v6(),
        _prompt_hair_token_v6(),
        _prompt_choice_token("Clothing (C)", "C", CLOTHING_MAP, note="Use `_` for the neutral / no-suffix form."),
        _prompt_dimensions_token_v6(),
        _prompt_choice_token("Computers (CM)", "CM", V4_COMPUTERS_MAP, note="Use `_` for the neutral / no-suffix form."),
        _prompt_windows_token_v6(),
        _prompt_unix_token_v6(),
        _prompt_choice_token("Mac / Apple (MC)", "MC", MAC_MAP, note="Use `_` for the neutral / no-suffix form."),
    ):
        if token:
            tokens.append(token)

    tokens.extend(
        _prompt_token_list(
            "Programming languages (L...)",
            MODERN_LANGUAGE_CODES,
            example="Lpy++,LC#+,Lbash+",
        )
    )

    tokens.extend(_prompt_software_domains_v6())

    for token in (
        _prompt_io_token_v6(),
        _prompt_version_control_token_v6(),
        _prompt_choice_token("PGP", "PGP", PGP_MAP, note="Use `_` for the neutral / no-suffix form."),
        _prompt_choice_token("Electronics (E)", "E", {"+++": "expert", "++": "strong practical skill", "+": "above average", "": "baseline / neutral", "-": "below average", "--": "mostly theoretical"}, note="Use `_` for the neutral / no-suffix form."),
        _prompt_choice_token("Hardware (H)", "H", {"+++": "expert", "++": "strong practical skill", "+": "above average", "": "baseline / neutral", "-": "limited comfort", "--": "prefers the repair shop"}, note="Use `_` for the neutral / no-suffix form."),
        _prompt_choice_token("Politics / social issues (PS)", "PS", PS_MAP, note="Use `_` for the neutral / no-suffix form."),
    ):
        if token:
            tokens.append(token)

    tokens.extend(_prompt_politics_subissues_v6())

    for token in (
        _prompt_choice_token("Politics / economic issues (PE)", "PE", PE_MODERN_MAP, note="Use `_` for the neutral / no-suffix form."),
    ):
        if token:
            tokens.append(token)

    tokens.extend(
        _prompt_token_list(
            "TV / series / movies (T...)",
            MODERN_TV_CODES,
            example="TDW+,TSTsnw+++,TEX++",
        )
    )

    for token in (
        _prompt_choice_token("Roleplaying games (RPG)", "RPG", MODERN_RPG_MAP, note="Use `_` for the neutral / no-suffix form."),
        _prompt_choice_token("Books (BK)", "BK", MODERN_BOOKS_MAP, note="Use `_` for the neutral / no-suffix form."),
    ):
        if token:
            tokens.append(token)

    tokens.extend(
        _prompt_token_list(
            "Comics (K...)",
            MODERN_COMICS_CODES,
            example="KX+++,KM+",
        )
    )

    for token in (
        _prompt_mbti_token_v6(),
        _prompt_choice_token("Residence (R)", "R", MODERN_RESIDENCE_MAP, note="Use `_` for the neutral / no-suffix form."),
        _prompt_pronoun_token_v6(),
    ):
        if token:
            tokens.append(token)

    code_string = build_geek_code_string(tokens)
    block = format_geek_code_v6_block(tokens)

    print("\nGenerated Geek Code v6 string:\n")
    print(code_string or "(no categories selected)")
    print("\nGenerated Geek Code v6 block:\n")
    print(block)

    return block


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Decode or generate Geek Code v4-v6 strings.")
    parser.add_argument("path", nargs="?", help="Optional text file containing a Geek Code block.")
    parser.add_argument("--text", help="Geek Code text to decode directly.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--generate", action="store_true", help="Interactively generate a Geek Code v6 block.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.generate:
        if args.text or args.path:
            parser.error("--generate cannot be combined with --text or a file path")
        generate_geek_code_v6_interactive()
        return 0
    text = _read_input(args)
    if not text.strip():
        parser.error("provide Geek Code text via --text, a file path, or stdin")

    result = decode_geek_code(text)
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(_render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
