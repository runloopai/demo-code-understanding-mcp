import argparse
import json
from kit import Repository


def main():
    parser = argparse.ArgumentParser(description="CLI for cased-kit Repository tools")
    parser.add_argument("repo_path", help="Path to the code repository (local directory or git URL)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # file-tree command
    parser_tree = subparsers.add_parser("file-tree", help="Show the file tree of the repository")

    # extract-symbols command
    parser_symbols = subparsers.add_parser("extract-symbols", help="Extract code symbols from the repository or a file")
    parser_symbols.add_argument("file", nargs="?", default=None, help="Optional file path (relative to repo root) to extract symbols from")

    args = parser.parse_args()
    repo = Repository(args.repo_path if args.repo_path != "." else ".")

    if args.command == "file-tree":
        tree = repo.get_file_tree()
        print(json.dumps(tree, indent=2))
    elif args.command == "extract-symbols":
        symbols = repo.extract_symbols(args.file)
        print(json.dumps(symbols, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
