import argparse
import subprocess
import json
import chromadb
from chromadb.utils import embedding_functions
import os

COLLECTION_NAME = "github_prs"  

class GitHubHistoryEmbedder:
    def __init__(self, chroma_collection: str = COLLECTION_NAME):
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(chroma_collection)
        self.embed_all_prs()  # Embed all PRs on initialization

    def get_prs(self):
        # Get all PRs (closed and open) for the repo
        cmd = [
            "gh", "pr", "list", "--state", "all", "--json", "number,title,body"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def get_pr_files(self, pr_number):
        # Get the files changed in a PR
        cmd = ["gh", "pr", "view", str(pr_number), "--json", "files"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files_info = json.loads(result.stdout)
        # files_info["files"] is a list of dicts with at least a 'path' key
        return [f["path"] for f in files_info.get("files", [])]

    def embed_all_prs(self):
        prs = self.get_prs()
        for pr in prs:
            pr_number = pr["number"]
            title = pr.get("title", "")
            body = pr.get("body", "")[:1000] if pr.get("body") else ""
            # Get files changed in the PR
            files = self.get_pr_files(pr_number)
            text = f"{title}\n{body}"
            # Embed and add to Chroma
            self.collection.add(
                documents=[text],
                metadatas=[{"pr_number": pr_number, "title": title, "files": ",".join(files)}],
                ids=[f"pr-{pr_number}"]
            )
        print(f"Embedded {len(prs)} PRs into Chroma collection '{self.collection.name}'")

    def semantic_search(self, query, top_k=5):
        # Embed the query and search Chroma
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
        )
        # Format results for output
        hits = []
        for i in range(len(results["ids"][0])):
            hit = {
                "id": results["ids"][0][i],
                "title": results["metadatas"][0][i].get("title", ""),
                "score": results["distances"][0][i],
                "files": results["metadatas"][0][i].get("files", []),
            }
            hits.append(hit)
        print(json.dumps(hits, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Embed GitHub PR history using ChromaDB and search it semantically")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Only semantic search command
    parser_search = subparsers.add_parser("semantic-search", help="Semantic search over PR embeddings")
    parser_search.add_argument("--query", required=True, help="Search query")
    parser_search.add_argument("--top_k", type=int, default=5, help="Number of top results to return")

    args = parser.parse_args()

    embedder = GitHubHistoryEmbedder()    

    if args.command == "semantic-search":
        embedder.semantic_search(args.query, args.top_k)

if __name__ == "__main__":
    main()
