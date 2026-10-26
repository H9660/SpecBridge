"""Local embeddings for the code library: text -> vector, through Ollama's HTTP API.

Settings are in config/embedder.json; EMBED_MODEL overrides the model. Documents and questions
get different prefixes, as the nomic models expect ("search_document: " / "search_query: ").
"""
import json
import urllib.error
import urllib.request

from specbridge.env import PROJECT, load_env

CONFIG = PROJECT / "config" / "embedder.json"


class EmbedderError(RuntimeError):
    pass


class OllamaEmbedder:
    def __init__(self, settings):
        self.settings = settings
        self.model = settings["model"]
        self.base_url = settings["base_url"].rstrip("/")

    def __repr__(self):
        return f"<Embedder ollama {self.model}>"

    def _embed(self, texts):
        body = json.dumps({"model": self.model, "input": texts, "truncate": True}).encode()
        req = urllib.request.Request(f"{self.base_url}/api/embed", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.settings.get("timeout_seconds", 300)) as resp:
                return json.load(resp)["embeddings"]
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="ignore")[:300]
            raise EmbedderError(f"ollama returned {err.code} for {self.model}: {detail}") from None
        except (urllib.error.URLError, TimeoutError) as err:
            raise EmbedderError(f"cannot reach ollama at {self.base_url} (is `ollama serve` running?): {err}") from None

    def embed_documents(self, texts):
        cap, prefix = self.settings["max_chars"], self.settings.get("document_prefix", "")
        size, out = self.settings.get("batch_size", 16), []
        for i in range(0, len(texts), size):
            out += self._embed([prefix + t[:cap] for t in texts[i:i + size]])
        return out

    def embed_query(self, text):
        return self._embed([self.settings.get("query_prefix", "") + text[:self.settings["max_chars"]]])[0]


def load_embedder(env=None, settings=None):
    env = load_env() if env is None else env
    settings = dict(settings or json.loads(CONFIG.read_text(encoding="utf-8")))
    if env.get("EMBED_MODEL"):
        settings["model"] = env["EMBED_MODEL"]
    if settings["provider"] != "ollama":
        raise EmbedderError(f"unknown embedder provider {settings['provider']!r}")
    return OllamaEmbedder(settings)
