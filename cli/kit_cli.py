import argparse
import json
from kit import Repository
import sys
import openai
import os


# Get OpenAI API key from environment variables for security
openai.api_key = os.environ.get("OPENAI_API_KEY")


# Define embedding function that uses OpenAI's text-embedding model
def embed_fn(text: str):
    # Using text-embedding-3-small for good balance of quality and cost
    resp = openai.embeddings.create(model="text-embedding-3-small", input=[text])
    return resp.data[0].embedding


# Build and return a vector index for semantic search
def build_index(repo_path=".", persist_dir="/home/user/.kit/my_index"):
    # Create Repository object to access the codebase
    repo = Repository(repo_path)
    # Initialize vector search with our embedding function and persistence directory
    vs = repo.get_vector_searcher(embed_fn=embed_fn, persist_dir=persist_dir)
    # Build the index (this may take time for large codebases)
    vs.build_index()
    return vs


def main():
    parser = argparse.ArgumentParser(description="CLI for cased-kit Repository tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    # Initialize vector_searcher as None to lazy-load only when needed
    vector_searcher = None

    # file-tree command - simple command with no additional arguments
    subparsers.add_parser("file-tree", help="Show the file tree of the repository")

    # extract-symbols command - can work on entire repo or single file
    parser_symbols = subparsers.add_parser(
        "extract-symbols", help="Extract code symbols from the repository or a file"
    )
    parser_symbols.add_argument(
        "--file",
        nargs="?",
        default=None,
        help="Optional file path (relative to repo root) to extract symbols from",
    )

    # semantic-code-search command - requires query and optional top_k parameter
    parser_semantic_code_search = subparsers.add_parser(
        "semantic-code-search", help="Perform semantic code search over the repository"
    )
    parser_semantic_code_search.add_argument(
        "--query", help="Query to search for", required=True
    )
    parser_semantic_code_search.add_argument(
        "--top_k", help="Number of top results to return", required=False, default=5
    )

    args = parser.parse_args()
    repo = Repository(".")

    if args.command == "file-tree":
        # Get and output the file tree structure as JSON
        tree = repo.get_file_tree()
        sys.stdout.write(json.dumps(tree, indent=2) + "\n")
        sys.stdout.flush()
    elif args.command == "extract-symbols":
        # Extract symbols from specific file or entire repo
        if args.file:
            symbols = repo.extract_symbols(args.file)
        else:
            symbols = repo.extract_symbols()
        sys.stdout.write(json.dumps(symbols, indent=2) + "\n")
        sys.stdout.flush()
    elif args.command == "semantic-code-search":
        # Lazy-load the vector index only when needed to save resources
        if vector_searcher is None:
            # Store index in user's home directory for persistence between runs
            vector_searcher = build_index()

        # Perform semantic search with the provided query
        results = vector_searcher.search(args.query, args.top_k)
        sys.stdout.write(json.dumps(results, indent=2) + "\n")
        sys.stdout.flush()
    else:
        # Fallback to help if command not recognized (should not happen with required=True)
        parser.print_help()


if __name__ == "__main__":
    main()
