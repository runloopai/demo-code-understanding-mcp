import argparse
import json
from kit import Repository
import sys


def main():
    parser = argparse.ArgumentParser(description="CLI for cased-kit Repository tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # file-tree command
    parser_tree = subparsers.add_parser("file-tree", help="Show the file tree of the repository")
    parser_tree.add_argument("--repo_path", help="Path to the code repository (local directory or git URL)", required=False, default=".")

    # extract-symbols command 
    parser_symbols = subparsers.add_parser("extract-symbols", help="Extract code symbols from the repository or a file")
    parser_symbols.add_argument("--repo_path", help="Path to the code repository (local directory or git URL)", required=False, default=".")
    parser_symbols.add_argument("--file", nargs="?", default=None, help="Optional file path (relative to repo root) to extract symbols from")

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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
