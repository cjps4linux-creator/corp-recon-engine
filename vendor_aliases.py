"""
Vendor alias mappings for reconciliation matching.

Maps known vendor name variations to canonical names to handle:
- Acronyms vs full names (AWS vs Amazon Web Services)
- Product lines (GitHub Organizations vs GitHub Inc)
- Regional variations (Woolworths SA vs Woolworths)
- Typos (Pick n Payy vs Pick n Pay)
- Brand variations (Vodacome vs Vodacom)

This is a production pattern for handling real-world accounting data messiness.
"""
from typing import Dict
import pandas as pd

# Company 1: Nexus Digital
NEXUS_ALIASES: Dict[str, str] = {
    'aws': 'amazon web services',
    'aws web services': 'amazon web services',
    'amazon web services': 'amazon web services',
    'github organizations': 'github inc',
    'github inc': 'github inc',
    'atlas by stripe': 'stripe inc',
    'stripe fees': 'stripe inc',
    'stripe inc': 'stripe inc',
    'upwork freelancer': 'upwork global',
    'upwork global': 'upwork global',
    'zoom workplace': 'zoom video',
    'zoom video': 'zoom video',
    'notion team plan': 'notion labs',
    'notion labs': 'notion labs',
    'heroku cloud': 'heroku inc',
    'heroku inc': 'heroku inc',
    'heroku salesforce': 'heroku inc',
    'netlify pro plan': 'netlify inc',
    'netlify inc': 'netlify inc',
    'netlify pro': 'netlify inc',
    'vercel team': 'vercel inc',
    'vercel inc': 'vercel inc',
    'vercel deploy': 'vercel inc',
    'google workspace': 'google workspace',
    'microsoft 365': 'microsoft corp',
    'microsoft corp': 'microsoft corp',
    'figma design tool': 'figma inc',
    'figma inc': 'figma inc',
    'slack technologies': 'slack technologies',
    'slack inc': 'slack technologies',
    'mailchimp premium': 'mailchimp inc',
    'mailchimp inc': 'mailchimp inc',
    'namecheap domain': 'namecheap inc',
    'namecheap inc': 'namecheap inc',
    'digitalocean droplet': 'digitalocean llc',
    'digitalocean llc': 'digitalocean llc',
    'cloudflare pro': 'cloudflare inc',
    'cloudflare inc': 'cloudflare inc',
    'adobe creative cloud': 'adobe inc',
    'adobe inc': 'adobe inc',
    'framer studio': 'framer bv',
    'framer bv': 'framer bv',
    'webflow cms': 'webflow inc',
    'webflow inc': 'webflow inc',
    'microsoft 365': 'microsoft corp',
    'microsoft corp': 'microsoft corp',
    'figma design tool': 'figma inc',
    'figma inc': 'figma inc',
    'slack technologies': 'slack technologies',
    'slack inc': 'slack technologies',
    'mailchimp premium': 'mailchimp inc',
    'mailchimp inc': 'mailchimp inc',
    'aws web services': 'amazon web services',
    'amazon web services': 'amazon web services',
    'github organizations': 'github inc',
    'heroku cloud': 'heroku inc',
    'netlify pro plan': 'netlify inc',
    'vercel team': 'vercel inc',
    'atlas by stripe': 'stripe inc',
    'stripe fees': 'stripe inc',
    'upwork freelancer': 'upwork global',
    'zoom workplace': 'zoom video',
    'notion team plan': 'notion labs',
    'paypal za': 'paypal services',
    'paypal services': 'paypal services',
}

# Company 2: Muller Family Trust
MULLER_ALIASES: Dict[str, str] = {
    'pick n pay': 'pick n pay',
    'pick n payy': 'pick n pay',
    'woolworths sa': 'woolworths',
    'woolworths pty ltd': 'woolworths',
    'woolworths': 'woolworths',
    'engen petrol': 'engen limited',
    'engen pty ltd': 'engen limited',
    'engen limited': 'engen limited',
    'eskom holdings': 'eskom holdings soc',
    'eskom holdings soc': 'eskom holdings soc',
    'eskom': 'eskom holdings soc',
    'telkom sa soc': 'telkom sa',
    'telkom': 'telkom sa',
    'vodacom sa': 'vodacom',
    'vodacome sa': 'vodacom',
    'vodacome': 'vodacom',
    'multichoice dstv': 'multichoice',
    'multichoice': 'multichoice',
    'discovery health medical': 'discovery health',
    'discovery health': 'discovery health',
    'nedbank atm': 'nedbank ltd',
    'nedbank ltd': 'nedbank ltd',
    'nedbank': 'nedbank ltd',
    'standard bank': 'standard bank',
    'sasol limited': 'sasol limited',
    'sasol': 'sasol limited',
}

# Company 3: Oasis Hospitality
OASIS_ALIASES: Dict[str, str] = {
    'cape town hotel': 'cape town hotel',
    'marriott intl': 'marriott international',
    'marriott international': 'marriott international',
    'bidfood catering': 'bidfood',
    'bidfood': 'bidfood',
    'spier hotel': 'spier hotel',
    'spier hotels': 'spier hotel',
    'city bowl trading': 'city bowl',
    'city bowl': 'city bowl',
    'cape town tours': 'cape town tours',
    'cape town tourism': 'cape town tours',
    'south African airways': 'south african airways',
    'saa': 'south african airways',
    'car rental company': 'car rental company',
    'car rentals': 'car rental company',
    'travel insurance': 'travel insurance',
    'travel insurance co': 'travel insurance',
    'cleaning services': 'cleaning services',
    'cleaning services cc': 'cleaning services',
    'garden supplies': 'garden supplies',
    'garden supplies pty': 'garden supplies',
    'pool maintenance': 'pool maintenance',
    'pool maintenance services': 'pool maintenance',
    'security company': 'security company',
    'security services': 'security company',
    'pest control': 'pest control',
    'pest control services': 'pest control',
}

# Company 4: Khumalo Mining
KHUMALO_ALIASES: Dict[str, str] = {
    'anglo amercan': 'anglo american',
    'anglo american': 'anglo american',
    'thiess mineing': 'thiess mining',
    'thiess mining': 'thiess mining',
    'bell equiptment': 'bell equipment',
    'bell equipment': 'bell equipment',
    'sandvik mineing': 'sandvik mining',
    'sandvik mining': 'sandvik mining',
    'exarro': 'exxaro',
    'exxaro': 'exxaro',
    'komatsu': 'komatsu',
    'caterpillar inc': 'caterpillar',
    'caterpillar': 'caterpillar',
    'khumalo mining supplies': 'khumalo mining supplies',
    'khumalo mining supplies ltd': 'khumalo mining supplies',
}

# Company 5: Verdant Eco
VERDANT_ALIASES: Dict[str, str] = {
    'wärtsilä corporation': 'wärtsilä',
    'wärtsilä': 'wärtsilä',
    'wartsila corporation': 'wärtsilä',
    'wartsila': 'wärtsilä',
    'tesla energy — solar panels': 'tesla energy',
    'tesla energy solar panels': 'tesla energy',
    'tesla energy': 'tesla energy',
    'lg energy solution': 'lg energy solutions',
    'lg energy solutions': 'lg energy solutions',
    'jinkosolar': 'jinkosolar',
    'jinko solar': 'jinkosolar',
    'sunpower corporation': 'sunpower',
    'sunpower': 'sunpower',
    'Canadian solar': 'canadian solar',
    'canadian solar': 'canadian solar',
    'enphase energy': 'enphase energy',
    'enphase energy inc': 'enphase energy',
    'solaredge technologies': 'solaredge',
    'solaredge': 'solaredge',
    'abb ltd': 'abb',
    'abb': 'abb',
    'siemens ag': 'siemens',
    'siemens': 'siemens',
    'schneider electric': 'schneider electric',
    'schneider': 'schneider electric',
    ' Eaton corporation': 'eaton',
    'eaton': 'eaton',
    'abb power': 'abb',
    'abb automation': 'abb',
    'ge renewable energy': 'ge renewable energy',
    'general electric renewable': 'ge renewable energy',
    'vestas wind systems': 'vestas',
    'vestas': 'vestas',
    'nordex se': 'nordex',
    'nordex': 'nordex',
    'goldwind science': 'goldwind',
    'goldwind': 'goldwind',
    'mingyang smart energy': 'mingyang',
    'mingyang': 'mingyang',
    'sany heavy industry': 'sany',
    'sany': 'sany',
    'united power': 'united power',
    'united power technology': 'united power',
    'darfon corporation': 'darfon',
    'darfon': 'darfon',
    'growatt new energy': 'growatt',
    'growatt': 'growatt',
    'huawei digital power': 'huawei',
    'huawei': 'huawei',
    'sungrow power supply': 'sungrow',
    'sungrow': 'sungrow',
}

# Master alias map
ALL_ALIASES: Dict[str, str] = {}
ALL_ALIASES.update(NEXUS_ALIASES)
ALL_ALIASES.update(MULLER_ALIASES)
ALL_ALIASES.update(OASIS_ALIASES)
ALL_ALIASES.update(KHUMALO_ALIASES)
ALL_ALIASES.update(VERDANT_ALIASES)


def get_canonical_name(name: str) -> str:
    """
    Get the canonical vendor name from an alias map.
    
    If the name is not in the alias map, returns the normalized original.
    """
    if not name or pd.isna(name):
        return ""
    
    # Lowercase and strip
    normalized = str(name).lower().strip()
    
    # Look up in alias map
    if normalized in ALL_ALIASES:
        return ALL_ALIASES[normalized]
    
    # Not in alias map - return normalized original
    return normalized
