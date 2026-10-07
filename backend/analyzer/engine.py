import hashlib
import re
from urllib.parse import urlparse
from services.groq_service import analyze_content_with_groq
from services.news_verifier import extract_and_verify_news_links

SIGNALS = {
    'urgency': (18, [r'urgent', r'immediately', r'within\s+\d+', r'today', r'last chance', r'act now', r'expire', r'midnight']),
    'impersonation': (22, [r'bank', r'police', r'government', r'customs', r'ceo', r'hr department', r'official', r'support team', r'account manager', r'ministry', r'reserve bank', r'rbi']),
    'credential_request': (24, [r'password', r'otp', r'one[- ]time password', r'pin', r'cvv', r'login', r'verify your identity', r'credentials']),
    'payment_request': (24, [r'pay', r'payment', r'fee', r'gift card', r'crypto', r'bitcoin', r'upi', r'bank transfer', r'send money', r'deposit', r'₹\d+']),
    'suspicious_link': (20, [r'bit\.ly', r'tinyurl\.com', r't\.co/', r'is\.gd', r'cutt\.ly', r'shorturl\.at', r'rb\.gy', r'\.zip\b', r'\.top\b', r'\.xyz\b', r'\.tk\b', r'\.ml\b', r'\.ga\b', r'\.cf\b', r'\.gq\b', r'\.work\b', r'\.click\b', r'\.loan\b', r'\.buzz\b']),
    'social_engineering': (15, [r'do not tell', r'keep this secret', r'don.t share', r'confidential', r'only you', r'don.t call', r'avoid verification']),
    'threat_or_penalty': (16, [r'blocked', r'suspended', r'arrest', r'seized', r'legal action', r'penalty', r'fine', r'account will be closed']),
    'too_good_to_be_true': (12, [r'guaranteed', r'free money', r'won', r'winner', r'lottery', r'prize', r'100% profit', r'double your money', r'assistance scheme']),
}

# Legitimate Brand Registry for Typosquatting & Lookalike Replica Detection
LEGITIMATE_BRANDS = {
    'sbi': {
        'name': 'State Bank of India (SBI)',
        'legit_domains': ['sbi.co.in', 'onlinesbi.sbi', 'onlinesbi.com', 'sbi.bank.in'],
        'tokens': ['sbi', 'onlinesbi', 'sbibank']
    },
    'hdfc': {
        'name': 'HDFC Bank',
        'legit_domains': ['hdfcbank.com', 'hdfc.com'],
        'tokens': ['hdfc', 'hdfcbank', 'hdfcnetbanking']
    },
    'icici': {
        'name': 'ICICI Bank',
        'legit_domains': ['icicibank.com', 'icicidirect.com'],
        'tokens': ['icici', 'icicibank']
    },
    'axis': {
        'name': 'Axis Bank',
        'legit_domains': ['axisbank.com'],
        'tokens': ['axisbank', 'axisnetbanking']
    },
    'pnb': {
        'name': 'Punjab National Bank (PNB)',
        'legit_domains': ['pnbindia.in', 'netpnb.com'],
        'tokens': ['pnbindia', 'pnbbank']
    },
    'paytm': {
        'name': 'Paytm',
        'legit_domains': ['paytm.com', 'paytmbank.com'],
        'tokens': ['paytm', 'paytmbank']
    },
    'phonepe': {
        'name': 'PhonePe',
        'legit_domains': ['phonepe.com'],
        'tokens': ['phonepe']
    },
    'google': {
        'name': 'Google / Google Pay',
        'legit_domains': ['google.com', 'google.co.in', 'pay.google.com'],
        'tokens': ['google', 'gpay']
    },
    'paypal': {
        'name': 'PayPal',
        'legit_domains': ['paypal.com', 'paypal.me'],
        'tokens': ['paypal']
    },
    'rbi': {
        'name': 'Reserve Bank of India (RBI)',
        'legit_domains': ['rbi.org.in'],
        'tokens': ['rbi', 'reservebank']
    },
    'incometax': {
        'name': 'Income Tax Department',
        'legit_domains': ['incometax.gov.in', 'incometaxindiaefiling.gov.in'],
        'tokens': ['incometax', 'incometaxindia']
    },
    'uidai': {
        'name': 'UIDAI / Aadhaar',
        'legit_domains': ['uidai.gov.in', 'myaadhaar.uidai.gov.in'],
        'tokens': ['uidai', 'myaadhaar', 'eaadhaar']
    },
    'amazon': {
        'name': 'Amazon',
        'legit_domains': ['amazon.com', 'amazon.in', 'amazon.co.uk', 'amazonpay.in'],
        'tokens': ['amazon', 'amazonpay']
    },
    'flipkart': {
        'name': 'Flipkart',
        'legit_domains': ['flipkart.com'],
        'tokens': ['flipkart']
    },
    'microsoft': {
        'name': 'Microsoft',
        'legit_domains': ['microsoft.com', 'live.com', 'office.com', 'outlook.com'],
        'tokens': ['microsoft', 'outlook', 'office365']
    },
    'apple': {
        'name': 'Apple',
        'legit_domains': ['apple.com', 'icloud.com'],
        'tokens': ['apple', 'icloud']
    },
    'netflix': {
        'name': 'Netflix',
        'legit_domains': ['netflix.com'],
        'tokens': ['netflix']
    },
    'whatsapp': {
        'name': 'WhatsApp',
        'legit_domains': ['whatsapp.com', 'wa.me'],
        'tokens': ['whatsapp']
    },
    'telegram': {
        'name': 'Telegram',
        'legit_domains': ['telegram.org', 't.me'],
        'tokens': ['telegram']
    },
    'facebook': {
        'name': 'Facebook / Meta',
        'legit_domains': ['facebook.com', 'fb.com', 'meta.com'],
        'tokens': ['facebook', 'meta']
    },
    'instagram': {
        'name': 'Instagram',
        'legit_domains': ['instagram.com'],
        'tokens': ['instagram']
    }
}

SCAM_KEYWORDS = {
    'kyc', 'login', 'verify', 'verification', 'update', 'refund', 'reward', 
    'cashback', 'security', 'support', 'alert', 'claim', 'online', 'service', 
    'banking', 'gift', 'bonus', 'free', 'bill', 'activation', 'portal', 'pin'
}

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def detect_misspelled_or_spoofed_links(urls):
    """
    Detects typosquatted, lookalike, or combosquatted domain names that replicate legitimate companies/services.
    """
    detected = []
    for u in urls:
        domain = u.get('domain', '').lower()
        if domain.startswith('www.'):
            domain = domain[4:]

        if not domain:
            continue

        for brand_key, brand_info in LEGITIMATE_BRANDS.items():
            # If domain is legitimate, skip
            is_legit = False
            for legit_d in brand_info['legit_domains']:
                if domain == legit_d or domain.endswith('.' + legit_d):
                    is_legit = True
                    break
            if is_legit:
                continue

            # Check subdomain spoofing: e.g. sbi.co.in.fake.com or hdfcbank.com.scam.top
            for legit_d in brand_info['legit_domains']:
                if legit_d in domain and not domain.endswith('.' + legit_d) and domain != legit_d:
                    detected.append({
                        'domain': domain,
                        'brand': brand_info['name'],
                        'legit_domain': legit_d,
                        'reason': f"Subdomain spoofing replicating legitimate '{legit_d}'"
                    })
                    break
            if detected and detected[-1]['domain'] == domain:
                break

            # Check homoglyph swaps (e.g. 0->o, 1->l, vv->w, rn->m)
            homoglyph_domain = domain.replace('0', 'o').replace('1', 'l').replace('vv', 'w').replace('rn', 'm')
            
            # Split domain labels
            domain_parts = domain.split('.')
            main_label = domain_parts[0] if domain_parts else ''
            norm_main_label = homoglyph_domain.split('.')[0] if domain_parts else ''

            # 1. Combosquatting: brand name + scam keywords (e.g. sbi-kyc.top, hdfc-netbanking.com, paytm-reward.net)
            for token in brand_info['tokens']:
                if token in domain:
                    # Check if domain has scam keywords or hyphens
                    has_scam_kw = any(kw in domain for kw in SCAM_KEYWORDS)
                    has_hyphen_brand = f"{token}-" in domain or f"-{token}" in domain or f"{token}." in domain
                    if has_scam_kw or has_hyphen_brand:
                        detected.append({
                            'domain': domain,
                            'brand': brand_info['name'],
                            'legit_domain': brand_info['legit_domains'][0],
                            'reason': f"Lookalike domain replicating '{brand_info['name']}' with deceptive keywords/hyphens"
                        })
                        break
            if detected and detected[-1]['domain'] == domain:
                break

            # 2. Homoglyph brand lookalike: e.g. amaz0n.com, paypa1.com, faceb00k.com, g00gle.com
            for token in brand_info['tokens']:
                if token in norm_main_label and token not in main_label:
                    detected.append({
                        'domain': domain,
                        'brand': brand_info['name'],
                        'legit_domain': brand_info['legit_domains'][0],
                        'reason': f"Homoglyph lookalike domain replicating '{brand_info['name']}' (character substitution)"
                    })
                    break
            if detected and detected[-1]['domain'] == domain:
                break

            # 3. Levenshtein typosquatting (edit distance 1 or 2)
            for token in brand_info['tokens']:
                if len(token) >= 4 and len(main_label) >= 4:
                    # Strip common separators
                    clean_label = re.sub(r'[^a-z0-9]', '', main_label)
                    dist = levenshtein_distance(clean_label, token)
                    if 1 <= dist <= 2:
                        detected.append({
                            'domain': domain,
                            'brand': brand_info['name'],
                            'legit_domain': brand_info['legit_domains'][0],
                            'reason': f"Misspelled / typosquatted domain mimicking '{brand_info['name']}' (edit distance: {dist})"
                        })
                        break
            if detected and detected[-1]['domain'] == domain:
                break

    return detected

def extract_urls(text):
    urls = re.findall(r'https?://[^\s<>"]+', text)
    result = []
    for raw in urls:
        clean = raw.rstrip('.,);]')
        p = urlparse(clean)
        result.append({'url': clean, 'domain': p.netloc.lower(), 'scheme': p.scheme})
    return result

def normalize(text):
    return re.sub(r'\s+', ' ', text.lower()).strip()

def fingerprint(dna):
    canonical = '|'.join(f'{k}:{dna.get(k)}' for k in sorted(dna))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]

def analyze(title, content, source=''):
    text = normalize(f'{title} {content}')
    signals = []
    raw_score = 0
    is_news_source = bool(source and ('news' in source.lower() or source == 'News Article / URL'))

    for name, (weight, patterns) in SIGNALS.items():
        hits = []
        for pattern in patterns:
            if re.search(pattern, text):
                hits.append(pattern)
        if hits:
            # If it's a news search and pattern is just general link indicators, don't penalize
            if is_news_source and name == 'suspicious_link':
                continue
            raw_score += weight
            signals.append({'type': name, 'weight': weight, 'evidence': hits[:4]})

    urls = extract_urls(content)
    
    # Check for Misspelled / Spoofed lookalike links replicating legit companies
    spoofed_links = detect_misspelled_or_spoofed_links(urls)
    if spoofed_links:
        raw_score += 35
        signals.append({
            'type': 'misspelled_link',
            'weight': 35,
            'evidence': [f"Domain '{s['domain']}' replicates legitimate {s['brand']} ({s['reason']})" for s in spoofed_links]
        })

    # Only add external_link signal for non-news search contexts with multiple links
    if urls and not is_news_source and len(urls) > 1:
        raw_score += min(10, len(urls) * 3)
        signals.append({'type': 'external_link', 'weight': min(10, len(urls) * 3), 'evidence': [u['domain'] for u in urls]})

    # Penalize combinations because coordinated fraud patterns are stronger than isolated words.
    types = {s['type'] for s in signals}
    combo_bonus = 0
    if 'impersonation' in types and ('payment_request' in types or 'credential_request' in types): combo_bonus += 15
    if 'urgency' in types and ('suspicious_link' in types or 'misspelled_link' in types): combo_bonus += 12
    if 'threat_or_penalty' in types and 'credential_request' in types: combo_bonus += 10
    if 'misspelled_link' in types and ('credential_request' in types or 'payment_request' in types): combo_bonus += 15
    raw_score += combo_bonus

    score = min(100, raw_score)
    if score >= 80: severity = 'CRITICAL'
    elif score >= 60: severity = 'HIGH'
    elif score >= 40: severity = 'MEDIUM'
    else: severity = 'LOW'

    if severity == 'CRITICAL': verdict = 'Strong coordinated fraud pattern detected'
    elif severity == 'HIGH': verdict = 'High-risk fraud pattern detected'
    elif severity == 'MEDIUM': verdict = 'Suspicious fraud indicators detected'
    else: verdict = 'No strong fraud pattern detected'

    has_suspicious_link = ('suspicious_link' in types) and not is_news_source
    has_misspelled_link = bool(spoofed_links) or ('misspelled_link' in types)

    dna = {
        'impersonation': 'impersonation' in types,
        'urgency': 'urgency' in types,
        'payment_request': 'payment_request' in types,
        'credential_request': 'credential_request' in types,
        'social_engineering': 'social_engineering' in types,
        'threat_or_penalty': 'threat_or_penalty' in types,
        'suspicious_link': has_suspicious_link,
        'misspelled_link': has_misspelled_link,
        'source': source or 'unknown',
        'channel': source.lower() if source else 'unknown',
    }

    attack_graph = []
    if dna['impersonation']: attack_graph.append({'from': 'Actor', 'to': 'Impersonation', 'relation': 'uses'})
    if dna['urgency']: attack_graph.append({'from': 'Impersonation' if dna['impersonation'] else 'Actor', 'to': 'Urgency', 'relation': 'creates'})
    if dna['misspelled_link']:
        attack_graph.append({'from': 'Actor', 'to': 'Misspelled / Lookalike Link', 'relation': 'replicates_legitimate_website'})
        attack_graph.append({'from': 'Misspelled / Lookalike Link', 'to': 'Credentials' if dna['credential_request'] else 'Payment' if dna['payment_request'] else 'Victim', 'relation': 'deceives'})
    elif dna['suspicious_link']:
        attack_graph.append({'from': 'Urgency' if dna['urgency'] else 'Actor', 'to': 'Link/Infrastructure', 'relation': 'routes_to'})
    if dna['credential_request'] and not dna['misspelled_link']: attack_graph.append({'from': 'Link/Infrastructure' if dna['suspicious_link'] else 'Actor', 'to': 'Credentials', 'relation': 'targets'})
    if dna['payment_request'] and not dna['misspelled_link']: attack_graph.append({'from': 'Urgency' if dna['urgency'] else 'Actor', 'to': 'Payment', 'relation': 'demands'})

    prevention = []
    if dna['misspelled_link']: prevention.append('Beware of lookalike or misspelled domain names mimicking official brands. Always check the exact domain in your browser address bar.')
    if dna['credential_request']: prevention.append('Never share OTPs, PINs, passwords, CVV, or login credentials through an unsolicited message.')
    if dna['payment_request']: prevention.append('Verify payment requests using a trusted channel before sending money.')
    if dna['suspicious_link']: prevention.append('Do not open the link; navigate to the organization using a known official website or app.')
    if dna['impersonation']: prevention.append('Independently verify the sender identity instead of trusting the claimed role.')
    if dna['urgency'] or dna['threat_or_penalty']: prevention.append('Pause when a message pressures you to act immediately or threatens consequences.')
    if not prevention: prevention.append('No specific action is required beyond normal verification and caution.')

    campaign = fingerprint(dna)

    # NEWS LINK & MEDIA CHANNEL VERIFICATION
    news_verification = extract_and_verify_news_links(f"{title} {content}")
    source_access = news_verification.get('primary_source_access', {
        'status': 'NOT_APPLICABLE',
        'http_status': None,
        'url': None,
        'message': 'No external URL provided in input.'
    })

    # If the user provided a URL and article body was scraped, enrich content passed to LLM
    enriched_content = content
    if news_verification.get('has_news_links'):
        for link_item in news_verification.get('links', []):
            if link_item.get('extracted_article_snippet') and len(content.strip()) < 150:
                enriched_content += f"\n\n[EXTRACTED ARTICLE FROM {link_item.get('source_name')}]:\nHeadline: {link_item.get('page_title')}\n{link_item.get('extracted_article_snippet')}"

    # CONTENT AUTHENTICITY MODULE via GROQ LLM API
    content_auth = analyze_content_with_groq(
        title=title, 
        content=enriched_content, 
        source=source, 
        signals=signals, 
        fraud_dna=dna, 
        urls=urls, 
        risk_score=score, 
        severity=severity,
        news_verification=news_verification,
        source_access=source_access
    )

    fraud_analysis_data = {
        'risk_score': score,
        'severity': severity,
        'verdict': verdict,
        'fraud_dna': dna,
        'signals': signals,
        'attack_graph': attack_graph,
        'campaign_fingerprint': campaign,
        'prevention_actions': prevention
    }

    return {
        'source_access': source_access,
        'content_authenticity': content_auth,
        'fraud_analysis': fraud_analysis_data,
        'risk_score': score, 
        'severity': severity, 
        'verdict': verdict,
        'fraud_dna': dna, 
        'signals': signals,
        'attack_graph': attack_graph, 
        'campaign_fingerprint': campaign,
        'prevention_actions': prevention,
        'urls': urls,
        'news_verification': news_verification,
        'engine': {'name': 'TruthGuard Intelligence Engine', 'version': '2.2.0', 'explainable': True},
    }

