# Jargon Shredder

Tired of startup buzzword soup?  
**Jargon Shredder** takes heavy tech-speak and rewrites it into plain, human words.  

It works in two steps:
1. **Rule-based sweep** — replaces common buzzwords with clear synonyms.  
2. **LLM cleanup** — asks a local [Ollama](https://ollama.com) model (e.g. `gemma:2b`) to rewrite the text in a chosen style.

---

## Features
- Converts tech jargon into:
  - `plain` → clear, neutral English  
  - `peasant` → medieval peasant explainer  
  - `grandma` → friendly “explain to grandma” mode  
  - `exec` → crisp executive summary  
- Works offline with your local Ollama model (default: `gemma:2b`)  
- Rule-based fallback if LLM isn’t available  
- CLI-friendly — pipe in text, or run on files

---

## Quickstart

1. Install [Ollama](https://ollama.com/download) and pull a model (e.g. `gemma:2b`):

   ```bash
   ollama pull gemma:2b
   ```

2. Clone this repo and run:

   ```bash
   python jargon_shredder.py "Our AI-powered federated data enrichment pipeline leverages embeddings to deliver actionable intelligence."
   ```

   **Output (plain mode):**
   ```
   We built a system that scrapes data, finds useful info, and alerts you when something important changes.
   ```

---

## Styles

```bash
python jargon_shredder.py -s peasant "We enable scalable, zero-trust edge computing with vector databases."
```
```
Peasant mode → "We made a magic box that works far away and still keeps your secrets safe."
```

```bash
python jargon_shredder.py -s grandma "Our multi-tenant observability platform ensures seamless integration."
```
```
Grandma mode → "It’s like one machine helping many people at once, and you can always see what it’s doing."
```

```bash
python jargon_shredder.py -s exec -f pitch.txt
```
```
Exec mode → 
- Organizes data across locations
- Alerts team when changes occur
- Cuts time wasted searching
```

---

## Options
- `-s, --style` → output style (`plain`, `peasant`, `grandma`, `exec`)  
- `-m, --model` → Ollama model (default: `gemma:2b`)  
- `--no-llm` → run rule-based sweep only (no LLM inference)  
- `-f, --file` → input from file instead of CLI arg  

---

## Roadmap
- Add a tiny FastAPI web UI  
- Expand buzzword dictionary with community PRs  
- Fun “meme modes” (pirate, Shakespeare, hacker 1337)  

---

## Contributing
Pull requests welcome! Add your favorite buzzword-to-English mappings to `BUZZMAP` or new styles to `STYLE_PROMPTS`.

---

## License
MIT. Use it, remix it, shred jargon freely.
