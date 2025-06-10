import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import json
from typing import List, Dict
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle

load_dotenv()
MODEL_PATH = os.getenv("MODEL_PATH", "richinfoai/ritrieve_zh_v1")
STORY_DIR = os.getenv("STORY_DIR","story")
EMBEDDING_CACHE_PATH = os.getenv("EMBEDDING_CACHE_PATH","story_embedding_cache.npz")
META_CACHE_PATH = os.getenv("META_CACHE_PATH","story_meta_cache.pkl")
BOT_LANG = os.getenv("BOT_LANG", "CN")
CHARACTER_NAME = os.getenv("CHARACTER_NAME", "Moka")

g_model = None
story_sentence_metas = []
all_embeddings_np = None

def load_model_and_tokenizer():
    global g_model
    if g_model is None:
        print(f"Loading SentenceTransformer Model: {MODEL_PATH} ...")
        g_model = SentenceTransformer(MODEL_PATH)
        print("Model Loaded Suceessfully")

def load_cache():
    global all_embeddings_np, story_sentence_metas
    if os.path.exists(EMBEDDING_CACHE_PATH) and os.path.exists(META_CACHE_PATH):
        print("Loading embedding cache...")
        all_embeddings_np = np.load(EMBEDDING_CACHE_PATH)["arr_0"]
        with open(META_CACHE_PATH, "rb") as f:
            story_sentence_metas = pickle.load(f)
        print(f"Loaded {len(story_sentence_metas)} embedding cache")
        return True
    return False

def process_stories():
    """
    Iterate through STORY_DIR: whenever a character name appears in extractedData,
    take the entire Summary (string or list) as a text for embedding.
    """
    global story_sentence_metas, all_embeddings_np
    story_sentence_metas = []
    all_sentences = []
    meta_infos = []

    if not os.path.exists(STORY_DIR):
        print(f"ERROR: {STORY_DIR} Does Not Exist")
        return

    print(f"Processing story fils in {STORY_DIR} ...")
    for filename in os.listdir(STORY_DIR):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(STORY_DIR, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            continue

        extracted = data.get("extractedData", [])
        has_character = any(
            isinstance(line, str) and CHARACTER_NAME in line
            for line in extracted
        )
        if not has_character:
            print(f"Skip {filename}, because extractedData doesn't have '{CHARACTER_NAME}'")
            continue

        summary = data.get("Summary", "")
        if isinstance(summary, list):
            summary = " ".join([s for s in summary if isinstance(s, str)])
        summary = summary.strip()

        if not summary:
            print(f"Skipped {filename} because it doesn't have Summary")
            continue

        all_sentences.append(summary)
        meta_infos.append({
            "sentence": summary,
            "file_name": filename,
            "event_name": data.get("eventName", "Unknown Event"),
            "chapter_title": data.get("chapterTitle", "Unknown Chapter"),
            "Summary": summary,
            "sentence_idx": 0
        })
        print(f"Collected {filename}'s Summary.")

    if all_sentences:
        print(f"Generating {len(all_sentences)} Summary embedding...")
        load_model_and_tokenizer()
        all_embeddings = g_model.encode(all_sentences, show_progress_bar=True)
        all_embeddings_np = np.array(all_embeddings)
        story_sentence_metas = meta_infos

        np.savez_compressed(EMBEDDING_CACHE_PATH, all_embeddings_np)
        with open(META_CACHE_PATH, "wb") as f:
            pickle.dump(story_sentence_metas, f)

        print(f"Success cached {len(story_sentence_metas)} Summary.")
    else:
        all_embeddings_np = None
        print("No matching summary results found")

def find_relevant_story(user_query: str, top_n: int = 1) -> List[Dict]:
    """
    Search for the most relevant story summary based on user input.
    Return a list containing the top_n information dictionaries.
    """
    if not story_sentence_metas or all_embeddings_np is None:
        print("Embedding not initialized, attempting to load automatically...")
        if not load_cache():
            process_stories()

    if g_model is None:
        load_model_and_tokenizer()

    if not story_sentence_metas:
        return []

    #Cosine Similarity
    user_embedding = g_model.encode([user_query])[0]
    sims = cosine_similarity(user_embedding.reshape(1, -1), all_embeddings_np)[0]
    sorted_indices = np.argsort(sims)[::-1]

    results = []
    for i in range(min(top_n, len(sorted_indices))):
        idx = sorted_indices[i]
        meta = story_sentence_metas[idx]

        # Read Summary to return full_content
        file_path = os.path.join(STORY_DIR, meta["file_name"])
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                full_content = data.get("extractedData", "")
        except Exception as e:
            full_content = ""
            print(f"Error reading {file_path}: {e}")

        results.append({
            "score": float(sims[idx]),
            **meta,
            "full_content": full_content
        })
    return results

if __name__ == '__main__':
    print("Starting RAG Handler test...")
    try:
        if not load_cache():
            process_stories()
    except Exception as e:
        print(f"Test initialization failed: {e}")
        sys.exit()

    if not story_sentence_metas:
        print("No story was loaded so the test couldn't continue.")
        sys.exit()

    test_queries = [
        "我在练习吉他哦！",
        "香橙在做什么",
        "巴说，鸫晕倒了……"
    ]
    for query in test_queries:
        print(f"\ninquiring: '{query}'")
        relevant_stories = find_relevant_story(query, top_n=1)
        if relevant_stories:
            info = relevant_stories[0]
            print(f"The most relevant story {info['event_name']} | {info['chapter_title']}")
            print(f"Summary: {info['Summary']}")
            print(f"similarity score: {info['score']:.4f}")
        else:
            print("Cannot find relavant story.")

    print("\nRAG Handler test finished")
