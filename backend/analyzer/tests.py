import json
import urllib.error
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from analyzer.engine import analyze
from services.groq_service import analyze_content_with_groq
from services.news_verifier import extract_and_verify_news_links

class TruthGuardEngineTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_news_link_verification_established_domain(self):
        """Test news domain recognition for established major publishers."""
        info = extract_and_verify_news_links("Check this report on https://www.thehindu.com/news/national/article.html")
        self.assertTrue(info['has_news_links'])
        self.assertEqual(len(info['links']), 1)
        self.assertEqual(info['links'][0]['source_name'], 'The Hindu')
        self.assertEqual(info['links'][0]['domain_status'], 'ESTABLISHED_NEWS_PUBLISHER')
        self.assertTrue(info['links'][0]['is_trusted'])

    def test_news_link_verification_regional_or_independent(self):
        """Test news domain recognition for regional or independent web domains."""
        info = extract_and_verify_news_links("Breaking news at https://breaking-daily-news.xyz/claim")
        self.assertTrue(info['has_news_links'])
        self.assertEqual(info['links'][0]['domain_status'], 'REGIONAL_OR_INDEPENDENT_MEDIA')
        self.assertFalse(info['links'][0]['is_trusted'])
        self.assertNotIn('untrusted', info['links'][0]['reputation_note'].lower())

    def test_source_access_not_applicable_when_no_url(self):
        """Test source_access returns NOT_APPLICABLE when no URL is provided."""
        info = extract_and_verify_news_links("This is a pure text message without any links.")
        self.assertFalse(info['has_news_links'])
        self.assertEqual(info['primary_source_access']['status'], 'NOT_APPLICABLE')
        self.assertIsNone(info['primary_source_access']['http_status'])

    @patch('urllib.request.urlopen')
    def test_source_access_http_403_blocked(self, mock_urlopen):
        """Test HTTP 403 Forbidden is classified as BLOCKED with http_status 403."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='https://www.telegraphindia.com/article.html',
            code=403,
            msg='Forbidden',
            hdrs={},
            fp=None
        )

        info = extract_and_verify_news_links("Report at https://www.telegraphindia.com/article.html")
        self.assertTrue(info['has_news_links'])
        link = info['links'][0]
        self.assertEqual(link['source_access']['status'], 'BLOCKED')
        self.assertEqual(link['source_access']['http_status'], 403)
        self.assertEqual(info['primary_source_access']['status'], 'BLOCKED')
        self.assertEqual(info['primary_source_access']['http_status'], 403)

    @patch('urllib.request.urlopen')
    def test_source_access_timeout(self, mock_urlopen):
        """Test network timeout is classified as TIMEOUT."""
        mock_urlopen.side_effect = urllib.error.URLError("The read operation timed out")

        info = extract_and_verify_news_links("Report at https://slow-domain.org/article")
        self.assertTrue(info['has_news_links'])
        link = info['links'][0]
        self.assertEqual(link['source_access']['status'], 'TIMEOUT')
        self.assertIsNone(link['source_access']['http_status'])

    @patch('urllib.request.urlopen')
    @patch('analyzer.engine.analyze_content_with_groq')
    def test_fraud_engine_preserved_when_url_blocked(self, mock_groq, mock_urlopen):
        """Test that deterministic fraud engine detects all fraud indicators even if URL is 403 blocked."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='https://claim-grant.xyz/claim',
            code=403,
            msg='Forbidden',
            hdrs={},
            fp=None
        )
        mock_groq.return_value = {
            "verdict": "UNVERIFIED",
            "status_code": "unverified",
            "confidence": None,
            "summary": "Source access was blocked; evidence insufficient.",
            "claims": [],
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "manipulated_elements": []
        }

        res = analyze(
            title="Farmer assistance scheme",
            content="The Government has announced a ₹50,000 benefit. You have been selected. Pay ₹499 immediately and send your UPI PIN at https://claim-grant.xyz/claim",
            source="SMS"
        )

        # Source accessibility should be BLOCKED
        self.assertEqual(res['source_access']['status'], 'BLOCKED')
        self.assertEqual(res['source_access']['http_status'], 403)

        # Fraud risk must be HIGH/CRITICAL due to impersonation, payment demand, UPI PIN credential request, and urgency
        self.assertGreaterEqual(res['risk_score'], 80)
        self.assertEqual(res['severity'], 'CRITICAL')
        self.assertTrue(res['fraud_dna']['impersonation'])
        self.assertTrue(res['fraud_dna']['payment_request'])
        self.assertTrue(res['fraud_dna']['credential_request'])
        self.assertTrue(res['fraud_dna']['urgency'])
        self.assertTrue(res['fraud_dna']['suspicious_link'])
        self.assertGreater(len(res['attack_graph']), 0)

    @patch('os.environ.get')
    def test_groq_service_missing_api_key(self, mock_env):
        """Test that missing GROQ_API_KEY returns graceful UNVERIFIED fallback without crashing."""
        mock_env.side_effect = lambda key, default=None: None if key == "GROQ_API_KEY" else default

        result = analyze_content_with_groq(
            title="Test", content="Some test content", source="SMS",
            signals=[], fraud_dna={}, urls=[], risk_score=10, severity="LOW"
        )

        self.assertEqual(result['verdict'], 'UNVERIFIED')
        self.assertEqual(result['status_code'], 'unverified')
        self.assertIsNone(result['confidence'])
        self.assertIn('GROQ_API_KEY', result['summary'])

    @patch('services.groq_service.Groq')
    @patch.dict('os.environ', {'GROQ_API_KEY': 'mock-key-123', 'GROQ_MODEL': 'openai/gpt-oss-120b'})
    def test_groq_service_successful_analysis(self, mock_groq_cls):
        """Test successful Groq API integration returning structured authenticity result."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "verdict": "LIKELY GENUINE",
                "status_code": "likely_genuine",
                "confidence": None,
                "summary": "The news link is an authentic report from a major outlet.",
                "claims": [
                    {"claim": "Public benefit scheme announced", "status": "SUPPORTED", "evidence": "Verified news article"}
                ],
                "supporting_evidence": [
                    {"source": "The Hindu", "source_type": "News Organization", "relevance": "Official coverage", "status": "SUPPORTS"}
                ],
                "contradicting_evidence": [],
                "manipulated_elements": [],
                "reasoning": "Genuine reporting from verified publisher."
            })))
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        result = analyze_content_with_groq(
            title="News coverage",
            content="Read reporting at https://www.thehindu.com",
            source="News Article / URL",
            signals=[],
            fraud_dna={},
            urls=['https://www.thehindu.com'],
            risk_score=10,
            severity="LOW",
            source_access={'status': 'ACCESSIBLE', 'http_status': 200, 'url': 'https://www.thehindu.com', 'message': 'OK'}
        )

        self.assertEqual(result['verdict'], 'LIKELY GENUINE')
        self.assertIsNone(result['confidence'])
        self.assertEqual(len(result['claims']), 1)
        self.assertEqual(result['claims'][0]['status'], 'SUPPORTED')

    @patch('services.groq_service.Groq')
    @patch.dict('os.environ', {'GROQ_API_KEY': 'mock-key-123'})
    def test_groq_service_api_error_handling(self, mock_groq_cls):
        """Test API error handling when Groq raises an exception."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Groq API Timeout")

        result = analyze_content_with_groq(
            title="Error test", content="Test text", source="Web",
            signals=[], fraud_dna={}, urls=[], risk_score=0, severity="LOW"
        )

        self.assertEqual(result['verdict'], 'UNVERIFIED')
        self.assertIsNone(result['confidence'])
        self.assertIn('temporarily unavailable', result['summary'])

    @patch('analyzer.engine.analyze_content_with_groq')
    def test_analyze_api_endpoint(self, mock_groq):
        """Test POST /api/analyze/ API response structure with source_access and news verification."""
        mock_groq.return_value = {
            "verdict": "LIKELY GENUINE",
            "status_code": "likely_genuine",
            "confidence": None,
            "summary": "Mocked verified result.",
            "claims": [{"claim": "Agriculture grant", "status": "SUPPORTED", "evidence": "Verified"}],
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "manipulated_elements": []
        }

        response = self.client.post(
            '/api/analyze/',
            data=json.dumps({
                'title': 'Agriculture Grant Reporting',
                'content': 'Check the official news report at https://www.thehindu.com/news/national/article.html',
                'source': 'News Article / URL'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('scan_id', data)
        self.assertIn('source_access', data)
        self.assertIn('content_authenticity', data)
        self.assertIn('fraud_analysis', data)
        self.assertIn('risk_score', data)
        self.assertIn('news_verification', data)
        self.assertTrue(data['news_verification']['has_news_links'])

    @patch('analyzer.engine.analyze_content_with_groq')
    def test_news_article_search_disables_suspicious_link(self, mock_groq):
        """Test that searching/analyzing a News Article or URL does not flag suspicious_link in Fraud DNA."""
        mock_groq.return_value = {
            "verdict": "LIKELY GENUINE",
            "status_code": "likely_genuine",
            "confidence": None,
            "summary": "Verified news",
            "claims": [],
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "manipulated_elements": []
        }

        res = analyze(
            title="Supreme Court Verdict Coverage",
            content="Read the full coverage at https://www.thehindu.com/news/national/article.html",
            source="News Article / URL"
        )

        self.assertFalse(res['fraud_dna']['suspicious_link'])
        self.assertFalse(res['fraud_dna']['misspelled_link'])
        self.assertEqual(res['severity'], 'LOW')
        self.assertEqual(res['risk_score'], 0)

    @patch('analyzer.engine.analyze_content_with_groq')
    def test_misspelled_and_lookalike_link_detection(self, mock_groq):
        """Test detection of misspelled or combosquatted lookalike domains replicating legit brands."""
        mock_groq.return_value = {
            "verdict": "LIKELY FALSE",
            "status_code": "likely_false",
            "confidence": None,
            "summary": "Phishing lookalike site",
            "claims": [],
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "manipulated_elements": []
        }

        # Case A: Combosquatting SBI
        res_sbi = analyze(
            title="SBI KYC Update",
            content="URGENT: Update your SBI account KYC immediately at https://sbi-kyc-verification.top before your account is blocked. Share your PIN.",
            source="SMS"
        )
        self.assertTrue(res_sbi['fraud_dna']['misspelled_link'])
        self.assertEqual(res_sbi['severity'], 'CRITICAL')
        self.assertTrue(any(s['type'] == 'misspelled_link' for s in res_sbi['signals']))

        # Case B: Homoglyph lookalike Amazon (amaz0n)
        res_amz = analyze(
            title="Order Refund",
            content="Claim your Amazon refund of ₹5,000 at https://amaz0n.in/claim-refund",
            source="WhatsApp"
        )
        self.assertTrue(res_amz['fraud_dna']['misspelled_link'])
        self.assertTrue(any('Homoglyph lookalike' in ev or 'replicates' in ev for s in res_amz['signals'] for ev in s.get('evidence', [])))

        # Case C: Levenshtein typosquatting Flipkart (flipkarrt)
        res_fk = analyze(
            title="Big Sale",
            content="Special discount at https://flipkarrt.com/deals",
            source="Web"
        )
        self.assertTrue(res_fk['fraud_dna']['misspelled_link'])

    @patch('analyzer.engine.analyze_content_with_groq')
    def test_legitimate_domains_not_flagged_as_misspelled(self, mock_groq):
        """Test that legitimate official domains are not falsely flagged as misspelled lookalikes."""
        mock_groq.return_value = {
            "verdict": "LIKELY GENUINE",
            "status_code": "likely_genuine",
            "confidence": None,
            "summary": "Genuine banking portal",
            "claims": [],
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "manipulated_elements": []
        }

        res = analyze(
            title="Official SBI Net Banking",
            content="Visit official State Bank of India portal at https://onlinesbi.sbi or https://sbi.co.in",
            source="Web"
        )
        self.assertFalse(res['fraud_dna']['misspelled_link'])


