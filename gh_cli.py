import argparse
import subprocess
import json
import chromadb
from chromadb.utils import embedding_functions
import os

COLLECTION_NAME = "github_prs"  

class GitHubHistoryEmbedder:
    def __init__(self, repo: str, chroma_collection: str = COLLECTION_NAME):
        self.repo = repo
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(chroma_collection)
        # Use OpenAI embedding function (requires OPENAI_API_KEY env var)
        self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY"),  # Uses env var
            model_name="text-embedding-3-small"
        )
        self.embed_all_prs()  # Embed all PRs on initialization

    def get_prs(self):
        # Get all PRs (closed and open) for the repo
        cmd = [
            "gh", "pr", "list", "--state", "all", "--json", "number,title,body", "--repo", self.repo
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def get_pr_diff(self, pr_number):
        # Get the diff for a PR
        cmd = ["gh", "pr", "diff", str(pr_number), "--repo", self.repo]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    def embed_all_prs(self):
        prs = self.get_prs()
        for pr in prs:
            pr_number = pr["number"]
            title = pr.get("title", "")
            body = pr.get("body", "")
            diff = self.get_pr_diff(pr_number)
            text = f"{title}\n{body}\n{diff}"
            # Embed and add to Chroma
            self.collection.add(
                documents=[text],
                metadatas=[{"pr_number": pr_number, "title": title}],
                ids=[f"pr-{pr_number}"],
                embedding_function=self.embed_fn
            )
        print(f"Embedded {len(prs)} PRs into Chroma collection '{self.collection.name}'")

    def semantic_search(self, query, top_k=5):
        # Embed the query and search Chroma
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            embedding_function=self.embed_fn
        )
        # Format results for output
        hits = []
        for i in range(len(results["ids"][0])):
            hit = {
                "id": results["ids"][0][i],
                "score": results["distances"][0][i],
                "metadata": results["metadatas"][0][i],
                "document": results["documents"][0][i],
            }
            hits.append(hit)
        print(json.dumps(hits, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Embed GitHub PR history using ChromaDB and search it semantically")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Only semantic search command
    parser_search = subparsers.add_parser("semantic-search", help="Semantic search over PR embeddings")
    parser_search.add_argument("repo", help="GitHub repo in the form owner/repo")
    parser_search.add_argument("--query", required=True, help="Search query")
    parser_search.add_argument("--top_k", type=int, default=5, help="Number of top results to return")

    args = parser.parse_args()

    embedder = GitHubHistoryEmbedder(args.repo)    

    if args.command == "semantic-search":
        embedder.semantic_search(args.query, args.top_k)

if __name__ == "__main__":
    main()
