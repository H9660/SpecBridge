"""The one code-reading interface for the workers (ARCHITECTURE.md D5): search_code, read_file, grep, find_usages.

`LibrarySource` answers from the Step 4 code library (`CodeTools` over the frozen repos); a live-GitHub source with
the same `call(name, args)` comes in Step 10. Workers run in parallel threads, so each worker opens its own
library connection; `ToolCache` is shared by all workers of a run, so a file read by two workers is fetched once
(this shares no model context). Hybrid search falls back to keywords + links if Ollama stops answering.
"""
import json
import threading
from pathlib import Path

from specbridge.code_index import CodeIndex
from specbridge.code_tools import CodeTools
from specbridge.embedder import EmbedderError, load_embedder


class CodeSourceError(RuntimeError):
    pass


class ToolCache:
    def __init__(self):
        self._data, self._lock = {}, threading.Lock()
        self.hits = 0

    @staticmethod
    def key(name, args):
        return name + json.dumps(args, sort_keys=True)

    def get(self, name, args):
        with self._lock:
            value = self._data.get(self.key(name, args))
            if value is not None:
                self.hits += 1
            return value

    def put(self, name, args, value):
        with self._lock:
            self._data[self.key(name, args)] = value


class LibrarySource:
    def __init__(self, env, cache=None):
        workdir = env.get("SPECBRIDGE_WORKDIR")
        db = Path(workdir) / "specbridge_index.sqlite" if workdir else None
        if not db or not db.exists():
            raise CodeSourceError("the code library is missing (SPECBRIDGE_WORKDIR/specbridge_index.sqlite)")
        self.index = CodeIndex(Path(workdir), db)
        try:
            embedder = load_embedder(env=env)
            embedder = embedder if self.index.vector_count(embedder.model) else None
        except Exception:  # noqa: BLE001 - no embedder: keyword search still works
            embedder = None
        self.tools = CodeTools(self.index, embedder)
        self.cache = cache or ToolCache()

    def call(self, name, args):
        cached = self.cache.get(name, args)
        if cached is not None:
            return cached
        try:
            result = self.tools.call(name, args)
        except EmbedderError:
            self.tools.embedder = None   # Ollama stopped answering: keywords + links from now on
            result = self.tools.call(name, args)
        if "error" not in result:
            self.cache.put(name, args, result)
        return result

    def close(self):
        self.index.close()
