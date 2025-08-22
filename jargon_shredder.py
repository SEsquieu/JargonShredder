#!/usr/bin/env python3
import argparse, json, re, sys, textwrap
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

BUZZMAP = {
    r"\bfederated\b": "spread across different places",
    r"\bembeddings?\b": "a way to compare meaning in text",
    r"\blatency\b": "delay",
    r"\bthroughput\b": "how much it can handle",
    r"\bscalable\b": "can grow without breaking",
    r"\brobust\b": "hard to break",
    r"\bresilient\b": "recovers from problems",
    r"\bseamless\b": "smooth",
    r"\bactionable\b": "useful and ready to use",
    r"\bintelligence\b": "information",
    r"\bdata enrichment\b": "adding extra info to data",
    r"\bdisrupt(ion|ive)\b": "a big change in how things are done",
    r"\bparadigm\b": "approach",
    r"\bleverage\b": "use",
    r"\bat scale\b": "for lots of users",
    r"\bAI[- ]powered\b": "uses AI",
    r"\bgenerative AI\b": "an AI that writes or makes things",
    r"\blarge language model(s)?\b": "a text AI",
    r"\bmicroservices?\b": "many small services",
    r"\bserverless\b": "you don't manage the servers",
    r"\bedge computing\b": "processing on the device",
    r"\bobservability\b": "seeing what the system is doing",
    r"\bzero[- ]trust\b": "always verify",
    r"\bblockchain\b": "a shared ledger",
    r"\bsmart contracts?\b": "programs on a blockchain",
    r"\bvector database\b": "a database for comparing meanings",
    r"\bmulti[- ]tenant\b": "many customers on one system",
    r"\bETL\b": "extract, transform, load data",
    r"\bRTOS\b": "a real-time operating system",
    r"\bHIL\b": "hardware-in-the-loop testing",
    r"\bDevOps\b": "dev + ops practices",
    r"\bSRE\b": "site reliability engineering",
    r"\bSDK\b": "software toolkit",
    r"\bKPI(s)?\b": "key metrics",
    r"\bOKR(s)?\b": "goals and results",
    r"\bIoT\b": "internet-connected devices",
    r"\bMQTT\b": "a pub-sub message protocol",
    r"\bLLM(s)?\b": "text AI models",
    r"\bknowledge graph\b": "a map of linked facts",
    r"\bdata lake\b": "a big raw data pool",
    r"\btime[- ]to[- ]value\b": "how fast it helps you",
    r"\bincremental(ly)?\b": "step by step",
    r"\bgreenfield\b": "built from scratch",
    r"\bbrownfield\b": "built on existing systems",
}

STYLE_PROMPTS = {
    "plain": "Rewrite in clear, plain English for a general audience. No jargon. Keep it brief but accurate.",
    "peasant": "Rewrite like you’re explaining to a medieval peasant, playful but still accurate. Short, simple sentences.",
    "grandma": "Rewrite in warm, simple language as if explaining to a grandparent. No buzzwords. Friendly and clear.",
    "exec": "Rewrite as crisp executive summary bullets. No fluff, no jargon, focus on outcome and why it matters.",
}

def buzz_sweep(text: str) -> str:
    out = text
    for pat, repl in BUZZMAP.items():
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()

def call_ollama(model: str, prompt: str, temperature: float = 0.2, timeout: int = 120) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {"temperature": temperature},
        "stream": False,
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "").strip()

def extract_facts(model: str, original: str) -> dict:
    """Ask the model to extract key facts in JSON so we can force retention."""
    sys_prompt = textwrap.dedent(f"""
    Extract key facts from the ORIGINAL text as strict JSON with the following fields:
    - numbers: array of numeric facts (with units)
    - dates: array of date/time references
    - names: array of proper nouns (companies, products, standards)
    - protocols: array of technical protocols/tech keywords
    - claims: array of quoted or paraphrased product claims or promises
    - constraints: array of limits, caveats, SLAs, compliance notes
    Only output JSON. Do not explain.
    ORIGINAL:
    \"\"\"{original.strip()}\"\"\"
    """).strip()
    try:
        raw = call_ollama(model, sys_prompt, temperature=0.0)
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end+1]
        data = json.loads(raw)
        for k in ["numbers","dates","names","protocols","claims","constraints"]:
            data.setdefault(k, [])
        return data
    except Exception:
        return {"numbers":[],"dates":[],"names":[],"protocols":[],"claims":[],"constraints":[]}

def build_prompt(style: str, original: str, preclean: str, facts: dict, maxlen: int, keep_terms=None, mode="faithful"):
    instruct = STYLE_PROMPTS[style]
    keep_terms = keep_terms or []
    fact_str = json.dumps(facts, ensure_ascii=False)
    keep_str = ", ".join(keep_terms) if keep_terms else "none"

    if mode == "faithful":
        policy = f"""
        - This is a faithful simplification: DO NOT drop facts.
        - You MUST preserve every number, date, proper noun, standard, protocol, and constraint shown in FACTS.
        - If a fact is unclear, include it verbatim rather than omitting.
        - Prefer short sentences. Avoid buzzwords.
        - Target max length ~{maxlen} words while preserving all facts.
        - Explicitly include these terms if present in the original: {keep_str}.
        """
    else:
        policy = f"""
        - This is a concise summary for non-experts.
        - Prioritize outcomes and what it does for the user.
        - Keep critical numbers/dates/constraints from FACTS.
        - Target max length ~{maxlen} words.
        - Explicitly include these terms if present in the original: {keep_str}.
        """

    return textwrap.dedent(f"""
    You are a jargon translator.

    {instruct}

    POLICY:
    {policy}

    ORIGINAL:
    \"\"\"{original.strip()}\"\"\"

    PRECLEAN (hints only):
    \"\"\"{preclean.strip()}\"\"\"

    FACTS (must be preserved per POLICY):
    {fact_str}
    """).strip()

def main():
    ap = argparse.ArgumentParser(description="BullshitShredder — turn buzzword soup into human words without losing facts.")
    ap.add_argument("-m", "--model", default="gemma:2b", help="Ollama model name (default: gemma:2b)")
    ap.add_argument("-s", "--style", default="plain", choices=list(STYLE_PROMPTS.keys()), help="Output style")
    ap.add_argument("--mode", choices=["faithful","summary"], default="faithful", help="faithful = keep all facts; summary = concise overview")
    ap.add_argument("--maxlen", type=int, default=120, help="Target word cap for LLM rewrite")
    ap.add_argument("--keep", default="", help="Comma-separated terms that must appear in output (e.g., 'HIPAA, MQTT, CE')")
    ap.add_argument("--no-llm", action="store_true", help="Only run rule-based sweep (no LLM)")
    ap.add_argument("--no-facts", action="store_true", help="Skip facts extraction pass (single-pass rewrite)")
    ap.add_argument("-f", "--file", help="Read input text from file (otherwise stdin/arg)")
    ap.add_argument("--temperature", type=float, default=0.2, help="LLM temperature")
    ap.add_argument("text", nargs="*", help="Input text (if no -f, read from here or stdin)")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            original = fh.read()
    elif args.text:
        original = " ".join(args.text)
    else:
        original = sys.stdin.read()

    preclean = buzz_sweep(original)

    if args.no_llm:
        print(preclean)
        return

    facts = {"numbers":[],"dates":[],"names":[],"protocols":[],"claims":[],"constraints":[]}
    if not args.no_facts:
        facts = extract_facts(args.model, original)

    keep_terms = [t.strip() for t in args.keep.split(",") if t.strip()]
    prompt = build_prompt(args.style, original, preclean, facts, args.maxlen, keep_terms, args.mode)

    try:
        out = call_ollama(args.model, prompt, temperature=args.temperature)
    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"[ERR] Ollama request failed: {e}\nFalling back to rule-based output.\n")
        out = preclean

    print(out)

if __name__ == "__main__":
    main()
