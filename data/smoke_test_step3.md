# Step 3 smoke test - 2026-10-28 18:23

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Brain settings file is complete (config/brains.json) | PASS | brains: ['llm', 'slm']; gaps: none |
| 2 | Default brain is the cloud LLM via OpenRouter | PASS | <Brain llm: openrouter google/gemini-3.8-flash> |
| 3 | BRAIN=slm switches to the local SLM with no code change | PASS | <Brain slm: ollama qwen2.5-coder:3b> |
| 4 | BRAIN_MODEL swaps in any other OpenRouter model | PASS | <Brain llm: openrouter openai/gpt-5> |
| 5 | Clear error for an unknown brain or a missing key | PASS | both explained |
| 6 | Plain answer: text, tokens and cost come back | PASS | 'Hello from the fake model', 10 in, $0.0001 |
| 7 | JSON answer checked against the expected shape | PASS | data={'kind': 'bug', 'steps': ['Open form', 'Click Save']} |
| 8 | Bad JSON: asks once more with the problem, then gives a clear error | PASS | retry fixed it in 2 tries; second case: invalid JSON twice |
| 9 | Server busy is retried; wrong key gives a clear error without showing the key | PASS | openrouter returned 401 after 1 tries: {"error": {"message": "invalid key"}} |
| 10 | Model that runs out of tokens while thinking gives a clear error, not an empty answer | PASS | fake/model used all 20 tokens before answering; raise max_tokens |
| 11 | Same code path works for a local SLM-style server (no key sent) | PASS | ollama qwen2.5-coder:3b |
| 12 | No real API keys in files git could commit (.env excluded by .gitignore) | PASS | none found |
| 13 | Configured model exists on OpenRouter | PASS | google/gemini-3.8-flash |
| 14 | Live LLM: plain answer | PASS | google/gemini-3.8-flash: 'ready', $0, 212.42s |
| 15 | Live LLM: JSON answer about a sample ticket | PASS | bug, 4 steps, 1 tries, $0.0015135, 420.45s |
| 16 | Live SLM (Ollama) | SKIPPED | not used yet - SLM model to be chosen later |
