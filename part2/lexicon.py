"""Keyword lexicon mapping ISIC Rev. 5 divisions to indicative terms.

The classifier scores a project against every division by summing the TF-IDF
weight of the lexicon terms it matches (see classifier.py), so this file is the
only place where domain knowledge lives.

What is being classified
------------------------
ISIC classifies *economic activities*. A research project is therefore assigned
the division of the activity or industry its data is ABOUT, not the activity of
doing research. Otherwise every project in the archive would collapse into
division 72 (Scientific research and development), which carries no information.
Division 72 is reserved for projects whose subject really is research and
development itself.

Weights
-------
    3.0  unambiguous for this division ("nursing home", "collective bargaining")
    2.0  strong but context dependent ("curriculum", "psychiatric")
    1.0  weak or shared with other divisions ("training", "welfare")

Terms are matched as whole words / phrases against a lower-cased document, so
they must be written in lower case and in their most common surface form.
"""

LEXICON = {
    # ----- A. Agriculture, forestry and fishing ---------------------------
    "01": {"agriculture": 3, "agricultural": 3, "farming": 3, "farmer": 3,
           "farmers": 3, "farm": 2, "farms": 2, "crop": 2, "crops": 2,
           "livestock": 3, "cattle": 2, "harvest": 2, "irrigation": 2,
           "peasant": 2, "agrarian": 3, "rural livelihood": 2, "plantation": 2,
           "horticulture": 3, "subsistence farming": 3},
    "02": {"forestry": 3, "logging": 3, "timber": 3, "deforestation": 2,
           "forest management": 3, "sawlog": 2, "silviculture": 3},
    "03": {"fishing": 3, "fishery": 3, "fisheries": 3, "aquaculture": 3,
           "fishermen": 3, "fish farming": 3, "trawler": 3},

    # ----- B. Mining and quarrying ---------------------------------------
    "05": {"coal mining": 3, "coal miner": 3, "coal miners": 3, "lignite": 3,
           "colliery": 3},
    "06": {"crude petroleum": 3, "natural gas extraction": 3, "oil drilling": 3,
           "oil extraction": 3, "offshore drilling": 3, "oil field": 2,
           "petroleum extraction": 3},
    "07": {"metal ore": 3, "iron ore": 3, "copper mining": 3, "gold mining": 3,
           "ore mining": 3},
    "08": {"quarrying": 3, "quarry": 3, "gravel extraction": 3,
           "salt extraction": 3, "stone quarry": 3},
    "09": {"mining support": 3, "drilling service": 3},

    # ----- C. Manufacturing ----------------------------------------------
    "10": {"food processing": 3, "food manufacturing": 3, "dairy plant": 3,
           "meat packing": 3, "bakery": 2, "cannery": 3, "food factory": 3},
    "11": {"brewery": 3, "brewing": 3, "winery": 3, "distillery": 3,
           "beverage manufacturing": 3, "soft drink production": 3},
    "12": {"tobacco manufacturing": 3, "cigarette manufacturing": 3,
           "tobacco factory": 3},
    "13": {"textile mill": 3, "textile manufacturing": 3, "weaving": 2,
           "spinning mill": 3, "textile industry": 3, "textile worker": 3},
    "14": {"garment industry": 3, "garment worker": 3, "apparel manufacturing": 3,
           "clothing manufacture": 3, "sweatshop": 3, "seamstress": 2},
    "15": {"tannery": 3, "leather manufacturing": 3, "footwear manufacturing": 3,
           "shoe factory": 3},
    "16": {"sawmill": 3, "wood products": 2, "woodworking": 2, "cork": 2,
           "plywood": 2},
    "17": {"paper mill": 3, "pulp mill": 3, "paper manufacturing": 3},
    "18": {"printing press": 2, "printing industry": 3, "printer": 1,
           "typesetting": 2, "reproduction of recorded media": 3},
    "19": {"oil refinery": 3, "petroleum refining": 3, "coke oven": 3},
    "20": {"chemical industry": 3, "chemical manufacturing": 3, "fertilizer": 2,
           "petrochemical": 3, "chemical plant": 3, "pesticide production": 3},
    "21": {"pharmaceutical manufacturing": 3, "drug manufacturing": 3,
           "pharmaceutical industry": 3, "pharmaceutical company": 3},
    "22": {"rubber manufacturing": 3, "plastic products": 3, "tyre factory": 3,
           "plastics industry": 3},
    "23": {"cement": 2, "glass manufacturing": 3, "ceramic": 2, "brickworks": 3,
           "concrete products": 3},
    "24": {"steel mill": 3, "steelworks": 3, "smelting": 3, "foundry": 3,
           "basic metals": 3, "steel industry": 3, "steelworker": 3},
    "25": {"fabricated metal": 3, "metal products": 2, "machine shop": 2,
           "cutlery manufacture": 3},
    "26": {"semiconductor": 3, "electronics manufacturing": 3,
           "computer manufacturing": 3, "optical instrument": 2,
           "electronic components": 3},
    "27": {"electrical equipment manufacturing": 3, "battery manufacturing": 3,
           "wiring device": 2},
    "28": {"machinery manufacturing": 3, "machine tool": 3,
           "industrial machinery": 3},
    "29": {"automobile industry": 3, "automotive industry": 3,
           "motor vehicle manufacturing": 3, "car factory": 3,
           "assembly line": 2, "automobile plant": 3, "autoworker": 3},
    "30": {"shipbuilding": 3, "shipyard": 3, "aircraft manufacturing": 3,
           "aerospace manufacturing": 3, "railway rolling stock": 3},
    "31": {"furniture manufacturing": 3, "furniture factory": 3},
    "32": {"jewellery manufacture": 3, "toy manufacturing": 3,
           "medical instrument manufacture": 3, "musical instrument manufacture": 3},
    "33": {"machinery repair": 3, "equipment installation": 2,
           "industrial maintenance": 3},

    # ----- D / E. Utilities ----------------------------------------------
    "35": {"electricity supply": 3, "power generation": 3, "power plant": 3,
           "electric utility": 3, "electrification": 3, "power grid": 3,
           "gas supply": 2, "nuclear power": 3, "energy utility": 3},
    "36": {"water supply": 3, "drinking water": 3, "water treatment": 3,
           "waterworks": 3, "water utility": 3},
    "37": {"sewerage": 3, "sewage": 3, "wastewater": 3, "sanitation system": 2},
    "38": {"waste collection": 3, "waste management": 3, "recycling": 3,
           "landfill": 3, "garbage collection": 3, "refuse disposal": 3},
    "39": {"remediation": 3, "site cleanup": 3, "contaminated site": 3,
           "environmental remediation": 3},

    # ----- F. Construction ------------------------------------------------
    "41": {"building construction": 3, "residential construction": 3,
           "housing construction": 3, "homebuilding": 3, "construction site": 2},
    "42": {"civil engineering": 3, "road construction": 3, "bridge construction": 3,
           "infrastructure construction": 3, "public works": 2},
    "43": {"plumbing": 3, "electrical installation": 3, "specialized construction": 3,
           "demolition": 2, "building trades": 3, "construction worker": 2},

    # ----- G. Trade -------------------------------------------------------
    "46": {"wholesale trade": 3, "wholesaler": 3, "wholesale distribution": 3,
           "distributor": 2},
    "47": {"retail trade": 3, "retail store": 3, "retailing": 3, "supermarket": 3,
           "department store": 3, "shopkeeper": 3, "retail sales": 2,
           "shopping": 1, "consumer purchase": 2, "salesclerk": 3},

    # ----- H. Transportation ---------------------------------------------
    "49": {"land transport": 3, "trucking": 3, "railway": 2, "railroad": 2,
           "bus service": 3, "taxi": 3, "commuting": 2, "highway transport": 3,
           "pipeline transport": 3, "truck driver": 3},
    "50": {"water transport": 3, "shipping line": 3, "maritime transport": 3,
           "merchant marine": 3, "seafarer": 3, "port operations": 2},
    "51": {"air transport": 3, "airline": 3, "aviation": 3, "airport": 2,
           "flight attendant": 3, "pilot": 1},
    "52": {"warehousing": 3, "logistics": 2, "freight handling": 3,
           "cargo handling": 3},
    "53": {"postal service": 3, "courier service": 3, "mail delivery": 3,
           "postal worker": 3},

    # ----- I. Accommodation and food service ------------------------------
    "55": {"hotel": 3, "lodging": 3, "accommodation service": 3, "motel": 3,
           "hostel": 3, "guest house": 3, "hotel worker": 3},
    "56": {"restaurant": 3, "catering": 3, "food service": 3, "cafeteria": 2,
           "waitress": 3, "waiter": 3, "bartender": 3, "food and beverage service": 3},

    # ----- J. Publishing, broadcasting, content ---------------------------
    "58": {"publishing": 3, "book publishing": 3, "newspaper publishing": 3,
           "publisher": 3, "magazine publishing": 3, "editorial board": 2,
           "periodical": 2},
    "59": {"motion picture": 3, "film production": 3, "filmmaking": 3,
           "television programme": 3, "television production": 3,
           "sound recording": 3, "music publishing": 3, "cinema": 2,
           "documentary film": 2},
    "60": {"broadcasting": 3, "radio station": 3, "television station": 3,
           "news agency": 3, "journalism": 2, "mass media": 2,
           "media coverage": 2, "news broadcast": 3},

    # ----- K. Telecommunications and IT -----------------------------------
    "61": {"telecommunications": 3, "telephone service": 3, "mobile network": 3,
           "telephony": 3, "internet service provider": 3, "telecom operator": 3},
    "62": {"computer programming": 3, "software development": 3,
           "software engineering": 3, "it consultancy": 3, "programmer": 2,
           "information technology": 2, "software company": 3, "computing": 1},
    "63": {"data processing": 3, "web portal": 3, "web hosting": 3,
           "data centre": 3, "information service": 2, "database service": 2,
           "computing infrastructure": 3},

    # ----- L. Finance -----------------------------------------------------
    "64": {"banking": 3, "bank": 2, "financial service": 3, "credit union": 3,
           "lending": 2, "mortgage lending": 3, "monetary policy": 2,
           "financial institution": 3, "investment": 1, "savings": 1,
           "gdp": 1, "economic growth": 1},
    "65": {"insurance": 3, "reinsurance": 3, "pension fund": 3, "life insurance": 3,
           "health insurance": 2, "pension plan": 3, "annuity": 3},
    "66": {"brokerage": 3, "financial intermediation": 3, "fund management": 3,
           "stock exchange": 3, "securities trading": 3},

    # ----- M. Real estate --------------------------------------------------
    "68": {"real estate": 3, "housing market": 3, "property market": 3,
           "landlord": 3, "tenant": 2, "rental housing": 3, "residential mobility": 2,
           "home ownership": 2, "housing segregation": 2, "public housing": 2,
           "neighborhood": 1, "neighbourhood": 1, "residential segregation": 2},

    # ----- N. Professional, scientific and technical -----------------------
    "69": {"legal": 2, "law firm": 3, "attorney": 3, "lawyer": 3, "litigation": 3,
           "accounting": 2, "notary": 3, "legal profession": 3, "paralegal": 3,
           "legal aid": 3, "divorce law": 3, "family law": 3, "legal practice": 3,
           "bar association": 3},
    "70": {"head office": 3, "management consultancy": 3, "management consulting": 3,
           "corporate headquarters": 3, "business consultant": 3},
    "71": {"architecture": 2, "architectural": 3, "engineering firm": 3,
           "technical testing": 3, "surveying": 2, "architect": 3, "engineer": 1},
    "72": {"research and development": 3, "scientific research": 2,
           "laboratory research": 2, "biotechnology research": 3,
           "research institute": 2, "r&d": 3, "basic research": 2,
           "experimental development": 3, "science policy": 2, "scientist": 1},
    "73": {"advertising": 3, "market research": 3, "public relations": 3,
           "advertising agency": 3, "marketing campaign": 2, "opinion polling": 2},
    "74": {"photography": 2, "graphic design": 3, "translation service": 3,
           "interpreting service": 3, "design activities": 2,
           "specialized design": 3},
    "75": {"veterinary": 3, "veterinarian": 3, "animal clinic": 3},

    # ----- O. Administrative and support -----------------------------------
    "77": {"rental and leasing": 3, "equipment leasing": 3, "car rental": 3,
           "leasing company": 3},
    "78": {"employment agency": 3, "recruitment": 3, "labour supply": 3,
           "job placement": 3, "temporary staffing": 3, "headhunting": 3,
           "employment service": 3, "labor force participation": 2,
           "job search": 2, "vocational placement": 2},
    "79": {"travel agency": 3, "tour operator": 3, "tourism": 3, "tourist": 2,
           "travel booking": 3},
    "80": {"private security": 3, "security guard": 3, "detective agency": 3,
           "surveillance service": 2},
    "81": {"cleaning service": 3, "janitorial": 3, "landscaping": 3,
           "building maintenance": 3, "custodial": 2},
    "82": {"call centre": 3, "call center": 3, "office administration": 3,
           "secretarial": 3, "clerical work": 2, "business support service": 3,
           "office support": 2, "secretary": 1, "typist": 2},

    # ----- P. Public administration ----------------------------------------
    "84": {"public administration": 3, "government": 2, "public policy": 2,
           "defence": 2, "defense": 2, "military": 3, "army": 3, "veteran": 3,
           "soldier": 3, "war": 1, "social security": 3, "welfare policy": 2,
           "public sector": 2, "civil service": 3, "legislature": 3,
           "congress": 2, "parliament": 3, "election": 2, "elections": 2,
           "voting": 2, "voter": 2, "political party": 2, "president": 2,
           "presidential": 2, "politics": 2, "political": 1, "policy": 1,
           "municipal": 2, "federal": 1, "state agency": 2, "bureaucracy": 3,
           "court": 1, "judiciary": 3, "supreme court": 3, "police": 2,
           "criminal justice": 3, "prison": 2, "incarceration": 2,
           "immigration policy": 2, "public official": 2, "regulation": 1,
           "taxation": 2, "census": 1, "veto player": 3, "presidentialism": 3,
           "political institutions": 3, "governance": 2, "democracy": 2,
           "legislative": 2, "diplomacy": 2, "foreign policy": 3},

    # ----- Q. Education -----------------------------------------------------
    "85": {"education": 3, "educational": 3, "school": 3, "schools": 3,
           "schooling": 3, "student": 2, "students": 2, "teacher": 3,
           "teachers": 3, "teaching": 2, "classroom": 3, "curriculum": 3,
           "university": 3, "college": 2, "undergraduate": 3, "graduate school": 3,
           "academic achievement": 3, "kindergarten": 3, "preschool": 3,
           "elementary school": 3, "high school": 3, "secondary school": 3,
           "primary school": 3, "pupil": 3, "literacy": 2, "tutoring": 3,
           "educational attainment": 3, "school district": 3, "alumnae": 2,
           "alumni": 2, "faculty": 2, "campus": 2, "coursework": 2,
           "vocational training": 2, "adult education": 3, "instruction": 1,
           "educational intervention": 3, "grade point average": 3,
           "academic performance": 3, "dropout": 2, "enrollment": 1,
           "special education": 3, "learning disabilities": 2, "scholastic": 3},

    # ----- R. Health and social work ----------------------------------------
    "86": {"health": 2, "healthcare": 3, "health care": 3, "hospital": 3,
           "medical": 3, "medicine": 2, "physician": 3, "doctor": 1,
           "nurse": 3, "nursing": 2, "clinic": 3, "clinical": 2,
           "patient": 3, "patients": 3, "diagnosis": 2, "treatment": 1,
           "therapy": 2, "psychotherapy": 3, "mental health": 3,
           "psychiatric": 3, "psychiatry": 3, "depression": 2, "anxiety": 2,
           "illness": 2, "disease": 2, "epidemiological": 2, "epidemiology": 3,
           "public health": 3, "morbidity": 3, "mortality": 2, "symptom": 2,
           "medication": 2, "prenatal": 2, "pregnancy": 2, "childbirth": 2,
           "obstetric": 3, "dental": 3, "rehabilitation": 2, "disability": 1,
           "substance abuse": 2, "alcoholism": 2, "addiction": 2,
           "bulimia": 3, "anorexia": 3, "eating disorder": 3, "nutrition": 2,
           "premenstrual": 2, "menopause": 2, "contraception": 2,
           "abortion": 2, "hiv": 2, "cancer": 2, "smoking cessation": 2,
           "medical care": 3, "health services": 3},
    "87": {"nursing home": 3, "residential care": 3, "long-term care": 3,
           "orphanage": 3, "assisted living": 3, "institutional care": 3,
           "group home": 3, "residential treatment": 3, "hospice": 3,
           "foster care": 2, "boarding institution": 2},
    "88": {"social work": 3, "social services": 3, "social worker": 3,
           "welfare service": 3, "counseling": 2, "counselling": 2,
           "child welfare": 3, "child protection": 3, "day care": 3,
           "daycare": 3, "child care": 2, "childcare": 2,
           "family services": 3, "social assistance": 3, "food bank": 3,
           "vocational rehabilitation": 3, "community service": 2,
           "case worker": 3, "aid to families": 3, "public assistance": 3,
           "welfare recipient": 3, "support group": 2, "crisis intervention": 3,
           "shelter": 2, "homelessness": 2, "elder care": 3, "aging services": 3},

    # ----- S. Arts, sports and recreation ------------------------------------
    "90": {"performing arts": 3, "theatre": 3, "theater": 2, "artist": 2,
           "painting": 2, "sculpture": 3, "dance performance": 3,
           "orchestra": 3, "concert": 2, "creative arts": 3, "musician": 2},
    "91": {"library": 3, "libraries": 3, "archive": 1, "archives": 1,
           "museum": 3, "cultural heritage": 3, "curator": 3,
           "historical society": 3, "botanical garden": 3},
    "92": {"gambling": 3, "betting": 3, "lottery": 3, "casino": 3},
    "93": {"sports": 3, "sport": 2, "athletics": 3, "athlete": 3,
           "recreation": 2, "fitness": 2, "amusement park": 3,
           "physical activity": 1, "leisure activity": 2, "team sport": 3},

    # ----- T. Other services --------------------------------------------------
    "94": {"trade union": 3, "labor union": 3, "labour union": 3,
           "membership organization": 3, "professional association": 3,
           "religious organization": 3, "church": 2, "congregation": 3,
           "clergy": 3, "minister": 1, "ministers": 1, "parish": 3,
           "synagogue": 3, "mosque": 3, "religion": 2, "religious": 2,
           "advocacy group": 3, "social movement": 2, "activism": 2,
           "women's liberation movement": 3, "feminist movement": 3,
           "civil rights movement": 3, "voluntary association": 3,
           "collective bargaining": 3, "nonprofit organization": 2,
           "political organization": 2, "fraternity": 2, "sorority": 2},
    "95": {"computer repair": 3, "appliance repair": 3,
           "household goods repair": 3, "shoe repair": 3},
    "96": {"hairdressing": 3, "beauty salon": 3, "barber": 3, "funeral": 3,
           "laundry service": 3, "dry cleaning": 3, "personal service": 2,
           "spa": 2},

    # ----- U. Households --------------------------------------------------------
    "97": {"domestic worker": 3, "domestic servant": 3, "housekeeper": 3,
           "nanny": 3, "maid": 3, "household employer": 3, "au pair": 3,
           "domestic help": 3, "domestic service": 3},
    "98": {"subsistence production": 3, "household own use": 3,
           "unpaid household work": 3, "housework": 2, "domestic labour": 2,
           "domestic labor": 2, "household chores": 3, "homemaker": 2,
           "housewife": 2, "household division of labor": 3},

    # ----- V. Extraterritorial ---------------------------------------------------
    "99": {"united nations": 3, "extraterritorial": 3, "embassy": 3,
           "international organization": 2, "world bank": 3,
           "diplomatic mission": 3, "unesco": 3, "unicef": 3},
}


def all_terms():
    """Every lexicon phrase, for use as a fixed TF-IDF vocabulary."""
    terms = set()
    for division_terms in LEXICON.values():
        terms.update(division_terms)
    return sorted(terms)
