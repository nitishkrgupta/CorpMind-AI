import time
import argparse
import requests
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from src.config import (
    DOCUMENTS_DIR,
    VECTOR_DB_DIR,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    DEFAULT_COMPANY_URLS,
)


def load_pdf_documents(documents_dir: Optional[Path] = None) -> List[Document]:
    """
    Load all PDF documents from the specified directory.
    """
    path = documents_dir or DOCUMENTS_DIR
    if not path.exists():
        print(f"[Warning] Documents directory '{path}' does not exist.")
        return []

    print(f"[*] Loading PDF documents from '{path}'...")
    loader = DirectoryLoader(
        str(path),
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
        use_multithreading=True,
    )
    docs = loader.load()
    print(f"[+] Successfully loaded {len(docs)} document pages.")
    return docs


def load_web_urls(urls: Optional[List[str]] = None) -> List[Document]:
    """
    Scrape and parse company website URLs, extracting clean text while preserving sentence structure.
    """
    target_urls = urls if urls is not None else DEFAULT_COMPANY_URLS
    if not target_urls:
        return []

    print(f"[*] Ingesting {len(target_urls)} company website pages...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    cleaned_docs: List[Document] = []

    for url in target_urls:
        try:
            print(f"  -> Scraping: {url}")
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"     [!] Skipped (HTTP {resp.status_code})")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            page_title = soup.title.string.strip() if soup.title and soup.title.string else url

            # Strip noisy, non-content tags
            for tag in soup(["script", "style", "noscript", "svg", "form"]):
                tag.decompose()

            text = soup.get_text(separator=" ")
            cleaned_text = " ".join(text.split())

            if len(cleaned_text) > 80:
                cleaned_docs.append(
                    Document(
                        page_content=f"Web Page Title: {page_title}\nURL: {url}\n\n{cleaned_text}",
                        metadata={
                            "source": url,
                            "title": page_title,
                            "type": "website",
                        },
                    )
                )
        except Exception as e:
            print(f"     [!] Error scraping {url}: {e}")

    print(f"[+] Successfully scraped and cleaned {len(cleaned_docs)} website pages.")
    return cleaned_docs


def split_documents(
    docs: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """
    Split documents into overlapping chunks for dense semantic embedding.
    """
    print(f"[*] Splitting {len(docs)} documents (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(docs)
    print(f"[+] Generated {len(chunks)} chunks.")
    return chunks


def build_and_save_index(
    chunks: List[Document],
    save_dir: Optional[Path] = None,
    embedding_model_name: str = EMBEDDING_MODEL,
) -> FAISS:
    """
    Generate embeddings for chunks and persist the FAISS index to disk.
    """
    target_dir = save_dir or VECTOR_DB_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Initializing embedding model: '{embedding_model_name}'...")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

    print(f"[*] Building FAISS vector store with {len(chunks)} total chunks...")
    vector_db = FAISS.from_documents(chunks, embeddings)

    print(f"[*] Saving FAISS index to '{target_dir}'...")
    vector_db.save_local(str(target_dir))
    print(f"[+] FAISS index saved successfully at '{target_dir}'.")
    return vector_db


def run_ingestion(
    include_pdfs: bool = True,
    include_web: bool = True,
    web_urls: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
) -> None:
    """
    Execute the unified ingestion pipeline (PDF policies + Company website pages).
    """
    start_time = time.time()
    all_docs: List[Document] = []

    if include_pdfs:
        pdf_docs = load_pdf_documents()
        all_docs.extend(pdf_docs)

    if include_web:
        web_docs = load_web_urls(web_urls or DEFAULT_COMPANY_URLS)
        all_docs.extend(web_docs)

    if not all_docs:
        print("[!] No documents found to ingest. Aborting.")
        return

    chunks = split_documents(all_docs)
    build_and_save_index(chunks, save_dir=output_dir)

    elapsed = time.time() - start_time
    print(f"Done! Unified ingestion completed in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest company policies & website data into FAISS.")
    parser.add_argument(
        "--skip-web",
        action="store_true",
        help="Skip crawling company website pages (index PDFs only).",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Skip PDF documents (index website only).",
    )
    args = parser.parse_args()

    run_ingestion(
        include_pdfs=not args.skip_pdf,
        include_web=not args.skip_web,
    )
