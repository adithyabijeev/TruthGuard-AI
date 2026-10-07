import re
import socket
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser

# Curated registry of recognized major news organizations & fact-checkers
RECOGNIZED_NEWS_DOMAINS = {
    # International & Wire
    'reuters.com': ('Reuters', 'International Wire Agency', True),
    'apnews.com': ('Associated Press', 'International Wire Agency', True),
    'afp.com': ('Agence France-Presse', 'International Wire Agency', True),
    'bbc.com': ('BBC News', 'Public Broadcaster', True),
    'bbc.co.uk': ('BBC News UK', 'Public Broadcaster', True),
    'theguardian.com': ('The Guardian', 'Major News Publisher', True),
    'nytimes.com': ('The New York Times', 'Major News Publisher', True),
    'washingtonpost.com': ('The Washington Post', 'Major News Publisher', True),
    'wsj.com': ('The Wall Street Journal', 'Financial News Publisher', True),
    'bloomberg.com': ('Bloomberg', 'Financial News Publisher', True),
    'aljazeera.com': ('Al Jazeera', 'International Broadcaster', True),
    'cnn.com': ('CNN', 'International Broadcaster', True),
    
    # National & Regional Indian News
    'pib.gov.in': ('Press Information Bureau (PIB)', 'Government Official Fact-Checker & Media Portal', True),
    'thehindu.com': ('The Hindu', 'National Daily Newspaper', True),
    'indianexpress.com': ('The Indian Express', 'National Daily Newspaper', True),
    'telegraphindia.com': ('The Telegraph (India)', 'National Daily Newspaper', True),
    'timesofindia.indiatimes.com': ('The Times of India', 'National News Publisher', True),
    'hindustantimes.com': ('Hindustan Times', 'National Daily Newspaper', True),
    'ndtv.com': ('NDTV', 'National News Network', True),
    'indiatoday.in': ('India Today', 'National News Broadcaster', True),
    'news18.com': ('News18 / Network18', 'National News Network', True),
    'aniin.com': ('ANI News', 'National Wire Agency', True),
    'ddnews.gov.in': ('DD News', 'Public Service Broadcaster', True),
    'livemint.com': ('Mint', 'Financial Daily', True),
    'economictimes.indiatimes.com': ('The Economic Times', 'Financial Daily', True),
    'scroll.in': ('Scroll.in', 'Digital News Publication', True),
    'thewire.in': ('The Wire', 'Digital News Publication', True),
    'deccanherald.com': ('Deccan Herald', 'Regional / National Daily', True),
    'tribuneindia.com': ('The Tribune', 'Regional Daily', True),
    
    # Fact-checking portals
    'altnews.in': ('Alt News', 'Certified Fact-Checking Outlet', True),
    'boomlive.in': ('BOOM Live', 'Certified Fact-Checking Outlet', True),
    'snopes.com': ('Snopes', 'Fact-Checking Organization', True),
    'factcheck.org': ('FactCheck.org', 'Non-profit Fact-Checking Project', True),
    'politifact.com': ('PolitiFact', 'Fact-Checking Project', True),
}

class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.site_name = ""
        self._in_title = False
        self._in_script_or_style = False
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        
        if tag_lower in ('script', 'style', 'noscript', 'header', 'footer', 'nav'):
            self._in_script_or_style = True
        elif tag_lower == 'title':
            self._in_title = True
        elif tag_lower == 'meta':
            name = attrs_dict.get('name', '').lower()
            prop = attrs_dict.get('property', '').lower()
            content = attrs_dict.get('content', '')
            
            if name in ('description', 'twitter:description') or prop in ('og:description',):
                if not self.description:
                    self.description = content
            elif prop in ('og:title', 'twitter:title'):
                if not self.title:
                    self.title = content
            elif prop in ('og:site_name',):
                self.site_name = content

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ('script', 'style', 'noscript', 'header', 'footer', 'nav'):
            self._in_script_or_style = False
        elif tag_lower == 'title':
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data.strip()
        elif not self._in_script_or_style:
            cleaned = data.strip()
            if cleaned and len(cleaned) > 2:
                self.text_parts.append(cleaned)

    def get_body_text(self, max_chars=3000):
        full_text = " ".join(self.text_parts)
        full_text = re.sub(r'\s+', ' ', full_text)
        return full_text[:max_chars].strip()


def extract_and_verify_news_links(text_or_url):
    """
    Extracts URLs, checks news channel domain classification,
    and fetches article headlines and summaries.
    Accurately classifies source access status (ACCESSIBLE, BLOCKED, NOT_FOUND, TIMEOUT, ERROR).
    """
    url_pattern = r'https?://[^\s<>"]+'
    found_urls = re.findall(url_pattern, text_or_url)
    
    # If the text itself looks like a domain or bare URL without scheme
    if not found_urls and re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$', text_or_url.strip()):
        found_urls = ['https://' + text_or_url.strip()]

    if not found_urls:
        return {
            'has_news_links': False,
            'links_count': 0,
            'links': [],
            'primary_source_access': {
                'status': 'NOT_APPLICABLE',
                'http_status': None,
                'url': None,
                'message': 'No external URL provided in input.'
            }
        }

    results = []
    
    for raw_url in found_urls[:3]:  # Analyze up to 3 links
        clean_url = raw_url.rstrip('.,);]')
        try:
            parsed = urllib.parse.urlparse(clean_url)
            netloc = parsed.netloc.lower()
            if netloc.startswith('www.'):
                clean_netloc = netloc[4:]
            else:
                clean_netloc = netloc
        except Exception:
            continue

        # Check domain against recognized news outlets
        matched_info = None
        for domain, info in RECOGNIZED_NEWS_DOMAINS.items():
            if clean_netloc == domain or clean_netloc.endswith('.' + domain):
                matched_info = info
                break

        if matched_info:
            source_name, source_category, is_trusted = matched_info
            domain_status = "ESTABLISHED_NEWS_PUBLISHER"
            reputation_note = f"Established news / media organization ({source_name})"
        elif any(clean_netloc.endswith(ext) for ext in ('.gov.in', '.nic.in', '.gov', '.mil')):
            source_name = clean_netloc
            source_category = "Official Government Portal"
            is_trusted = True
            domain_status = "OFFICIAL_GOVERNMENT_PORTAL"
            reputation_note = "Official Government / Institutional domain"
        elif any(news_kw in clean_netloc for news_kw in ['news', 'times', 'post', 'daily', 'herald', 'tribune', 'tv', 'bulletin']):
            source_name = clean_netloc
            source_category = "Regional / Independent News Domain"
            is_trusted = False
            domain_status = "REGIONAL_OR_INDEPENDENT_MEDIA"
            reputation_note = "Independent or regional news publication (not in central registry)"
        else:
            source_name = clean_netloc
            source_category = "General Web Domain"
            is_trusted = False
            domain_status = "GENERAL_DOMAIN"
            reputation_note = "General web publication domain"

        # Attempt to fetch page metadata and article text
        page_title = ""
        page_description = ""
        extracted_body = ""
        fetch_success = False
        access_status = "ERROR"
        http_status_code = None
        status_message = "The source could not be retrieved."

        try:
            req = urllib.request.Request(
                clean_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 TruthGuard-Bot/1.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5'
                }
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                http_status_code = response.getcode() or 200
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type or 'text/plain' in content_type:
                    charset = response.headers.get_content_charset() or 'utf-8'
                    html_bytes = response.read(150000)  # Read first 150KB
                    html_text = html_bytes.decode(charset, errors='replace')
                    
                    parser = SimpleHTMLTextExtractor()
                    parser.feed(html_text)
                    page_title = parser.title or ""
                    page_description = parser.description or ""
                    extracted_body = parser.get_body_text(max_chars=1800)
                    fetch_success = True
                    access_status = "ACCESSIBLE"
                    status_message = "Source content retrieved successfully."
        except urllib.error.HTTPError as e:
            http_status_code = e.code
            if e.code in (401, 403):
                access_status = "BLOCKED"
                status_message = f"The source blocked automated retrieval (HTTP {e.code})."
            elif e.code in (404, 410):
                access_status = "NOT_FOUND"
                status_message = f"The requested source was not found (HTTP {e.code})."
            else:
                access_status = "ERROR"
                status_message = f"HTTP Error {e.code} during source retrieval."
        except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
            if "timed out" in str(e).lower() or isinstance(e, (socket.timeout, TimeoutError)):
                access_status = "TIMEOUT"
                http_status_code = None
                status_message = "The source did not respond within the allowed time."
            else:
                access_status = "ERROR"
                http_status_code = None
                status_message = "The source could not be reached due to a network connection error."
        except Exception:
            access_status = "ERROR"
            http_status_code = None
            status_message = "The source could not be retrieved due to an unexpected retrieval error."

        source_access_info = {
            'status': access_status,
            'http_status': http_status_code,
            'url': clean_url,
            'message': status_message
        }

        results.append({
            'url': clean_url,
            'domain': clean_netloc,
            'source_name': source_name,
            'source_category': source_category,
            'domain_status': domain_status,
            'is_trusted': is_trusted,
            'reputation_note': reputation_note,
            'page_title': page_title,
            'page_description': page_description,
            'extracted_article_snippet': extracted_body,
            'fetch_success': fetch_success,
            'source_access': source_access_info
        })

    primary_access = results[0]['source_access'] if results else {
        'status': 'NOT_APPLICABLE',
        'http_status': None,
        'url': None,
        'message': 'No external URL provided in input.'
    }

    return {
        'has_news_links': len(results) > 0,
        'links_count': len(results),
        'links': results,
        'primary_source_access': primary_access
    }
