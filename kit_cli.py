import argparse
import json
from kit import Repository
import sys
import openai
import os


openai.api_key = os.environ.get("OPENAI_API_KEY")
def embed_fn(text: str):
    resp = openai.embeddings.create(model="text-embedding-3-small", input=[text])
    return resp.data[0].embedding

def build_index(repo_path, persist_dir):
    repo = Repository(repo_path)
    vs = repo.get_vector_searcher(embed_fn=embed_fn, persist_dir=persist_dir)
    vs.build_index()
    return vs

   
def main():
    parser = argparse.ArgumentParser(description="CLI for cased-kit Repository tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    vector_searcher = None

    # file-tree command
    subparsers.add_parser("file-tree", help="Show the file tree of the repository")

    # extract-symbols command 
    parser_symbols = subparsers.add_parser("extract-symbols", help="Extract code symbols from the repository or a file")
    parser_symbols.add_argument("--file", nargs="?", default=None, help="Optional file path (relative to repo root) to extract symbols from")

    # semantic-code-search command
    parser_semantic_code_search = subparsers.add_parser("semantic-code-search", help="Perform semantic code search over the repository")
    parser_semantic_code_search.add_argument("--query", help="Query to search for", required=True)
    parser_semantic_code_search.add_argument("--top_k", help="Number of top results to return", required=False, default=5)

    args = parser.parse_args()
    repo = Repository(args.repo_path)

    if args.command == "file-tree":
        tree = repo.get_file_tree()
        sys.stdout.write(json.dumps(tree, indent=2) + "\n")
        sys.stdout.flush()
    elif args.command == "extract-symbols":
        if args.file:
            symbols = repo.extract_symbols(args.file)
        else:
            symbols = repo.extract_symbols()
        sys.stdout.write(json.dumps(symbols, indent=2) + "\n")
        sys.stdout.flush()
    elif args.command == "semantic-code-search":
        if vector_searcher is None:
            vector_searcher = build_index(args.repo_path, "/home/user/.kit/my_index")

        results = vector_searcher.search(args.query, args.top_k)
        sys.stdout.write(json.dumps(results, indent=2) + "\n")
        sys.stdout.flush()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
