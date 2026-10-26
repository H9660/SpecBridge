"""Build the code library (if needed) and score a search method on the golden tickets.

Writes data/retrieval/<method>.md (readable report) and data/retrieval/<method>.json (every number).

Methods: keyword (whole files, 4a), pieces (4b), combined (pieces + link-following, 4d, no
embeddings), vector (meaning only, 4c) and hybrid (pieces + meaning + links). vector and hybrid
embed every piece first if needed (local Ollama, a few minutes the first time) and need numpy.

Usage:
  py -3.12 scripts/eval_retrieval.py [--workdir C:/specbridge-work] [--method keyword] [--rebuild]
--workdir defaults to SPECBRIDGE_WORKDIR from .env.
"""
import argparse
import datetime
import json
import pathlib
import sys
import time

PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
from specbridge.code_index import CodeIndex, files_from_pieces  # noqa: E402
from specbridge.embedder import load_embedder  # noqa: E402
from specbridge.env import load_env  # noqa: E402
from specbridge.retrieval_eval import golden_queries, report_md, score, summarise  # noqa: E402

OUT = PROJECT / "data" / "retrieval"


NEEDS_VECTORS = {"vector", "hybrid"}


def methods(index, embedder=None):
    """Search methods that can be scored: name -> function (text, k) -> [(repo, path)]."""
    return {
        "keyword": lambda text, k: [(h.repo, h.path) for h in index.search(text, k)],
        "pieces": lambda text, k: files_from_pieces(index.search_pieces(text, 300), k),
        "combined": lambda text, k: index.rank_files(text, k),
        "vector": lambda text, k: files_from_pieces(index.search_vectors(text, embedder, 300), k),
        "hybrid": lambda text, k: index.rank_files(text, k, embedder),
    }


def workdir_from(arg):
    path = arg or load_env().get("SPECBRIDGE_WORKDIR")
    if not path:
        raise SystemExit("give --workdir or set SPECBRIDGE_WORKDIR in .env")
    return pathlib.Path(path)


def run(workdir, method, rebuild=False):
    index = CodeIndex(workdir)
    started = time.time()
    built = index.build(force=rebuild)
    build_s = time.time() - started
    embedder = load_embedder() if method in NEEDS_VECTORS else None
    if embedder:
        started = time.time()
        added = index.build_vectors(embedder, progress=lambda done, total: print(
            f"  embedded {done}/{total} pieces", end="\r", flush=True))
        if added:
            print(f"\n  {added} pieces embedded with {embedder.model} in {time.time() - started:.0f} s")
    search = methods(index, embedder)[method]
    queries = golden_queries(workdir)
    started = time.time()
    rows = score(search, queries)
    per_query_ms = (time.time() - started) / len(queries) * 1000
    summary = summarise(rows)
    stats = {"method": method, "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
             "files_indexed": index.file_count(), "source_files": index.file_count(include_tests=False),
             "index_built_now": built, "build_seconds": round(build_s, 1),
             "search_ms_per_ticket": round(per_query_ms, 1), "commits": index.stored_commits(),
             "pieces": index.piece_count(), "embed_model": embedder.model if embedder else None}
    index.close()
    return stats, rows, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir")
    parser.add_argument("--method", default="keyword")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the index even if it is up to date")
    args = parser.parse_args()

    stats, rows, summary = run(workdir_from(args.workdir), args.method, args.rebuild)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{args.method}.json").write_text(json.dumps(
        {"stats": stats, "summary": summary, "tickets": rows}, indent=1), encoding="utf-8")
    extra = [f"Run {stats['date']}. Index: {stats['files_indexed']} code files ({stats['source_files']} non-test), "
             f"{stats['pieces']} pieces{', embeddings: ' + stats['embed_model'] if stats['embed_model'] else ''}; "
             f"{'built now in ' + str(stats['build_seconds']) + ' s' if stats['index_built_now'] else 'already up to date'}; "
             f"search {stats['search_ms_per_ticket']} ms per ticket."]
    (OUT / f"{args.method}.md").write_text(report_md(args.method, rows, summary, extra=extra), encoding="utf-8")
    s = summary["all"]
    print(f"{args.method}: {s['tickets']} tickets scored; hit@10 {s['hit@10']:.2f}, recall@20 {s['recall@20']:.2f}, "
          f"mrr {s['mrr']:.2f} -> data/retrieval/{args.method}.md")


if __name__ == "__main__":
    main()
