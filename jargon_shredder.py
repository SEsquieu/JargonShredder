#!/usr/bin/env python3
import argparse, json, re, sys, textwrap
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

# Lightweight, opinionated buzzword → plain-English map.
# It runs as a first pass before the LLM cleans things up in context.
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
    r"\bzero[- ]trust\b": "verify everything, always",
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
    r"\bvector embeddings?\b": "numeric meaning of text",
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
    # Collapse multiple spaces after replacements
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()

def build_prompt(style: str, original: str, preclean: str) -> str:
    instruct = STYLE_PROMPTS[style]
    return textwrap.dedent(f"""
    You are a jargon translator. {instruct}

    1) Start from the ORIGINAL text.
    2) Use the PRECLEAN version only as hints for definitions.
    3) Do not invent features. Preserve the true meaning.
    4) Keep it concise.

    ORIGINAL:
    \"\"\"{original.strip()}\"\"\"

    PRECLEAN (hints only):
    \"\"\"{preclean.strip()}\"\"\"
    """).strip()

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

def main():
    ap = argparse.ArgumentParser(description="Jargon Shredder — turn buzzword soup into human words.")
    ap.add_argument("-m", "--model", default="gemma:2b", help="Ollama model name (default: gemma:2b)")
    ap.add_argument("-s", "--style", default="plain", choices=list(STYLE_PROMPTS.keys()), help="Output style")
    ap.add_argument("--no-llm", action="store_true", help="Only run rule-based sweep (no LLM)")
    ap.add_argument("-f", "--file", help="Read input text from file (otherwise stdin/arg)")
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

    prompt = build_prompt(args.style, original, preclean)
    try:
        out = call_ollama(args.model, prompt)
    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"[ERR] Ollama request failed: {e}\nFalling back to rule-based output.\n")
        out = preclean

    print(out)

if __name__ == "__main__":
    main()
