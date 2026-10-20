import re

# Common typos and their corrections
TYPO_CORRECTIONS = {
    'payy': 'pay',
    'mineing': 'mining',
    'equiptment': 'equipment',
    'amercian': 'american',
    'amercan': 'american',
    'enterprizes': 'enterprises',
    'sollutions': 'solutions',
    'servises': 'services',
    'teh': 'the',
    'adn': 'and',
    'tehcnology': 'technology',
    'techology': 'technology',
    'technolgy': 'technology',
    'solutionss': 'solutions',
    'servicess': 'services',
    'consultings': 'consulting',
    'consultantss': 'consultants',
    'developerss': 'developers',
    'developements': 'developments',
    'softwares': 'software',
    'platformss': 'platforms',
    'applicationss': 'applications',
    'integrationss': 'integrations',
    'connectorss': 'connectors',
    'pluginss': 'plugins',
    'extensionss': 'extensions',
    'addonss': 'addons',
    'moduless': 'modules',
    'componentss': 'components',
    'widgetss': 'widgets',
    'templatess': 'templates',
    'themess': 'themes',
    'layouts': 'layout',
    'designss': 'designs',
    'productionss': 'productions',
    'communicationss': 'communications',
    'accountings': 'accounting',
    'accountantss': 'accountants',
    'auditorss': 'auditors',
    'solicitorss': 'solicitors',
    'barristerss': 'barristers',
    'recruitments': 'recruitment',
    'staffings': 'staffing',
    'resources': 'resource',
    'architectss': 'architects',
    'engineerss': 'engineers',
    'contractorss': 'contractors',
    'consultantss': 'consultants',
    'adviserss': 'advisers',
    'managerss': 'managers',
    'foundations': 'foundation',
    'trusts': 'trust',
    'funds': 'fund',
    'investments': 'investment',
    'companys': 'company',
    'companiess': 'companies',
    'groups': 'group',
    'holdingss': 'holdings',
    'internationals': 'international',
    'globalss': 'globals',
    'venturess': 'ventures',
    'capitals': 'capital',
    'partnerss': 'partners',
    'associatess': 'associates',
    'agencys': 'agency',
    'studioss': 'studios',
    'workss': 'works',
    'hubs': 'hub',
    'networks': 'network',
    'onlines': 'online',
    'stores': 'store',
    'shops': 'shop',
    'retails': 'retail',
    'markets': 'market',
    'foodss': 'foods',
    'beveragess': 'beverages',
    'restaurants': 'restaurant',
    'hotels': 'hotel',
    'airliness': 'airlines',
    'airwayss': 'airways',
    'motorss': 'motors',
    'automotives': 'automotive',
    'truckss': 'trucks',
    'equipments': 'equipment',
    'machinerys': 'machinery',
    'industrials': 'industrial',
    'manufacturings': 'manufacturing',
    'factorys': 'factory',
    'plants': 'plant',
    'mills': 'mill',
    'farms': 'farm',
    'agricultures': 'agriculture',
    'forestrys': 'forestry',
    'educations': 'education',
    'trainings': 'training',
    'institutes': 'institute',
    'academys': 'academy',
    'schools': 'school',
    'universitys': 'university',
    'colleges': 'college',
    'learnings': 'learning',
    'researchs': 'research',
}


def normalize_vendor_name(name: str) -> str:
    """
    Normalize a vendor/company name for fuzzy matching.
    
    Uses conservative normalization - only strips generic suffixes like
    Inc/LLC/Ltd/Pty/Corp, and corrects obvious typos.
    """
    if not name:
        return ""
    
    # Lowercase
    name = name.lower().strip()
    
    # Remove punctuation (keep spaces and alphanumeric)
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Tokenize
    tokens = name.split()
    
    # Only strip these generic suffixes (conservative set)
    GENERIC_SUFFIXES = {
        'inc', 'llc', 'ltd', 'limited', 'pty', 'corp', 'corporation',
        'gmbh', 'sa', 'sarl', 'bv', 'nv', 'plc', 'llp', 'lp', 'co', 'company'
    }
    
    normalized_tokens = []
    for token in tokens:
        # Skip pure numbers
        if token.isdigit():
            continue
        # Skip generic corporate suffixes only
        if token in GENERIC_SUFFIXES:
            continue
        normalized_tokens.append(token)
    
    return ' '.join(normalized_tokens)


def normalize_description_for_matching(desc: str) -> str:
    """
    Normalize a bank description for matching.
    
    More aggressive than vendor normalization because bank descriptions
    often contain transaction context.
    """
    if not desc:
        return ""
    
    # Start with vendor name normalization
    normalized = normalize_vendor_name(desc)
    
    # Remove common bank transaction prefixes
    prefixes_to_remove = [
        'payment to', 'payment from', 'transfer to', 'transfer from',
        'debit card', 'credit card', 'card payment', 'direct debit',
        'standing order', 'online payment', 'mobile payment',
        'pos purchase', 'atm withdrawal', 'cash withdrawal',
        'bill payment', 'invoice payment', 'vendor payment',
    ]
    
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
            break
    
    return normalized
