import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Ensure environment variables are loaded
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR.parent / '.env')

logger = logging.getLogger(__name__)

def test_groq_connectivity():
    """
    Minimal health check function to test Groq API key and model connectivity.
    Returns (success: bool, message: str)
    """
    api_key = os.environ.get("GROQ_API_KEY")
    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

    if not api_key or api_key.strip() in ("", "YOUR_GROQ_API_KEY_HERE"):
        return False, "GROQ_API_KEY is missing or unconfigured in backend/.env"

    try:
        client = Groq(api_key=api_key.strip())
        res = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Respond with exactly: GROQ_OK"}],
            max_tokens=10
        )
        content = res.choices[0].message.content.strip()
        return True, f"Groq OK ({content})"
    except Exception as e:
        logger.exception("Groq Connectivity Test Failed")
        print(f"[GROQ HEALTH ERROR] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return False, f"{type(e).__name__}: {str(e)}"


def analyze_content_with_groq(title, content, source, signals, fraud_dna, urls, risk_score, severity, news_verification=None, source_access=None):
    """
    Analyzes content authenticity and news link integrity using Groq LLM API.
    Evaluates claims, manipulation, news publisher reputation, and evidence independently from deterministic fraud scoring.
    """
    # Always refresh env vars
    load_dotenv(BASE_DIR / '.env')
    api_key = os.environ.get("GROQ_API_KEY")
    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

    if not api_key or api_key.strip() in ("", "YOUR_GROQ_API_KEY_HERE"):
        logger.warning("GROQ_API_KEY environment variable is missing or default.")
        print("[GROQ WARNING] GROQ_API_KEY is not configured in backend/.env file.", file=sys.stderr, flush=True)
        return {
            "verdict": "UNVERIFIED",
            "status_code": "unverified",
            "confidence": None,
            "summary": "Content authenticity analysis is temporarily unconfigured (GROQ_API_KEY missing in backend/.env).",
            "claims": [],
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "manipulated_elements": [],
            "reasoning": "Missing GROQ_API_KEY in backend environment."
        }

    system_prompt = (
        "You are the Content Authenticity & Fact-Checking Intelligence Engine for TruthGuard AI.\n\n"
        "TruthGuard has two strictly separated intelligence layers:\n"
        "1. Fraud Detection Engine (deterministic rules for urgency, payment demands, credential theft, impersonation, etc.)\n"
        "2. Content Authenticity Analysis (evaluates factual claims, reporting veracity, manipulated context, and available evidence)\n\n"
        "YOUR CORE PRINCIPLES & RULES:\n"
        "1. SOURCE ACCESSIBILITY IS NOT EVIDENCE OF FALSITY:\n"
        "   - If a source URL cannot be retrieved or returns HTTP 403 Forbidden, 404, or a timeout, this is an automated access limitation, NOT evidence that the content is false, suspicious, or untrusted.\n"
        "   - Never claim an article is fake or publisher is untrusted simply because a scraper received HTTP 403 or was blocked by anti-bot protections.\n"
        "2. DO NOT USE DOMAIN POPULARITY AS A PROXY FOR TRUTH:\n"
        "   - Do not infer that a publisher or domain is unreliable or suspicious solely because it is not a major, global, or central wire news organization. Smaller, regional, or specialized publications can report authentic facts.\n"
        "   - Base your evaluation on verifiable claims, factual consistency, and available authoritative context.\n"
        "3. SEPARATE AUTHENTICITY FROM FRAUDULENT CONTEXT:\n"
        "   - A message can cite genuine underlying public information (e.g. real government scheme, farmer assistance, public event) and still be weaponized in a fraudulent context (e.g. 'Pay ₹499 fee immediately to claim it', 'Send your UPI PIN').\n"
        "   - Evaluate whether the underlying claim is supported vs whether malicious context has been attached to it.\n"
        "4. EVIDENCE GROUNDING & UNVERIFIED STATUS:\n"
        "   - If available evidence is insufficient to verify or contradict a claim, return verdict: 'UNVERIFIED', status_code: 'unverified', confidence: null.\n"
        "   - Explain in the summary/reasoning that independent evidence is insufficient to confirm or refute the claim (not that it is fake).\n"
        "   - NEVER invent or fabricate citations, URLs, government orders, or press releases.\n"
        "5. ALLOWED VERDICTS:\n"
        "   - 'LIKELY GENUINE' (status_code: 'likely_genuine')\n"
        "   - 'LIKELY FALSE' (status_code: 'likely_false')\n"
        "   - 'MISLEADING / MANIPULATED' (status_code: 'misleading_manipulated')\n"
        "   - 'UNVERIFIED' (status_code: 'unverified')\n\n"
        "6. CONFIDENCE SCORE:\n"
        "   - Confidence must be null when verdict is UNVERIFIED or when no probabilistic metric is calculated.\n\n"
        "Return ONLY a valid, raw JSON object with the following structure:\n"
        "{\n"
        '  "verdict": "LIKELY GENUINE" | "LIKELY FALSE" | "MISLEADING / MANIPULATED" | "UNVERIFIED",\n'
        '  "status_code": "likely_genuine" | "likely_false" | "misleading_manipulated" | "unverified",\n'
        '  "confidence": null,\n'
        '  "summary": "Objective explanation of authenticity finding, evidence evaluated, and context.",\n'
        '  "claims": [\n'
        '    {\n'
        '      "claim": "Specific claim extracted from content or news article",\n'
        '      "status": "SUPPORTED" | "CONTRADICTED" | "PARTIALLY_SUPPORTED" | "UNVERIFIED",\n'
        '      "evidence": "Detailed explanation of claim evaluation"\n'
        '    }\n'
        '  ],\n'
        '  "supporting_evidence": [\n'
        '    {\n'
        '      "source": "Source / News Outlet name",\n'
        '      "source_type": "News Organization" | "Government" | "Public Institution",\n'
        '      "relevance": "Relevance description",\n'
        '      "status": "SUPPORTS"\n'
        '    }\n'
        '  ],\n'
        '  "contradicting_evidence": [\n'
        '    {\n'
        '      "source": "Source / Fact-checker name",\n'
        '      "source_type": "News Organization" | "Government" | "Public Institution",\n'
        '      "relevance": "Relevance description",\n'
        '      "status": "CONTRADICTS"\n'
        '    }\n'
        '  ],\n'
        '  "manipulated_elements": [\n'
        '    {\n'
        '      "supported_info": "Underlying supported or plausible news / information",\n'
        '      "manipulated_context": "Fraudulent, altered, or clickbait context added to it",\n'
        '      "type": "Fraudulent Context Addition" | "Fabricated Threat" | "Sensationalized / Clickbait Distortion"\n'
        '    }\n'
        '  ],\n'
        '  "reasoning": "Reasoning summary emphasizing available evidence and noting any source access constraints."\n'
        "}"
    )

    user_prompt = (
        f"INPUT TITLE:\n{title or 'Untitled'}\n\n"
        f"INPUT CONTENT:\n{content}\n\n"
        f"SOURCE / CHANNEL:\n{source or 'Unknown'}\n\n"
        f"SOURCE ACCESSIBILITY STATUS:\n{json.dumps(source_access or {})}\n\n"
        f"DETECTED FRAUD SIGNALS:\n{json.dumps(signals)}\n\n"
        f"FRAUD DNA:\n{json.dumps(fraud_dna)}\n\n"
        f"EXTRACTED URLS:\n{json.dumps(urls)}\n\n"
        f"NEWS LINKS VERIFICATION DATA:\n{json.dumps(news_verification or {})}\n\n"
        f"DETERMINISTIC FRAUD RISK SCORE:\n{risk_score}/100\n\n"
        f"DETERMINISTIC FRAUD SEVERITY:\n{severity}\n\n"
        "Analyze the content authenticity according to the system instructions and output strictly valid JSON."
    )

    # Production supported models fallback chain
    models_to_try = [model_name]
    if "openai/gpt-oss-20b" not in models_to_try:
        models_to_try.append("openai/gpt-oss-20b")

    last_error = None
    client = Groq(api_key=api_key.strip())

    for target_model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            raw_json = response.choices[0].message.content.strip()
            parsed = json.loads(raw_json)

            return {
                "verdict": parsed.get("verdict", "UNVERIFIED"),
                "status_code": parsed.get("status_code", "unverified"),
                "confidence": parsed.get("confidence", None),
                "summary": parsed.get("summary", "Authenticity and news verification analysis complete."),
                "claims": parsed.get("claims", []),
                "supporting_evidence": parsed.get("supporting_evidence", []),
                "contradicting_evidence": parsed.get("contradicting_evidence", []),
                "manipulated_elements": parsed.get("manipulated_elements", []),
                "reasoning": parsed.get("reasoning", "")
            }
        except Exception as e:
            last_error = e
            logger.warning(f"Groq API call failed with model {target_model}: {e}")
            print(f"[GROQ ERROR] Model '{target_model}' failed: {type(e).__name__} - {e}", file=sys.stderr, flush=True)

    # If all models fail, return safe fallback with logged exception info
    error_msg = f"{type(last_error).__name__}: {str(last_error)}" if last_error else "Unknown error"
    return {
        "verdict": "UNVERIFIED",
        "status_code": "unverified",
        "confidence": None,
        "summary": f"Content authenticity analysis is temporarily unavailable ({error_msg}).",
        "claims": [],
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "manipulated_elements": [],
        "reasoning": f"Groq exception: {error_msg}"
    }
