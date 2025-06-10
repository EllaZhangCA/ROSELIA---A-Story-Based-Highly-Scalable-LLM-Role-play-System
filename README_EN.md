# ROSELIA - A Story Based Highly Scalable LLM Role play System
### ROSELIA stands for Role-Oriented Story Embedding &amp; LLM Interaction Architecture. It is a story-retrieval-based, highly scalable role-play framework.
## Quick Start

### 1.Install Dependencies
```bash
cd (your file path，e.g., C:\Users\ellaz\roselia)
python -m pip install -r requirements.txt
```
### 2.Configure the Embedding Model
If using Hugging Face Hub, simply fill in the model name under MODEL_PATH in your .env file—no need to download anything.
If the model is stored locally, point MODEL_PATH= in your .env to the local directory.
If you're unsure which model to use, you can try MODEL_PATH=Qwen/Qwen3-Embedding-8B or any English supported embedding model. 

### 3.Configure the .env File
```
DEEPSEEK_KEY= # Your LLM API Key
DEEPSEEK_API_URL= # Your LLM API URL
OPENAI_MODEL= # The LLM model you’re using
CHARACTER_NAME= # Character name, e.g., "Moka"
CHARACTER_FULL_NAME= # Full character name, e.g., "Moka Aoba"
MODEL_PATH= # Embedding model path, e.g., Qwen/Qwen3-Embedding-8B
STORY_DIR=story # Path to the story files
EMBEDDING_CACHE_PATH=story_embedding_cache.npz # Path for storing embedding cache
META_CACHE_PATH=story_meta_cache.pkl # Path for storing meta info cache
LANG=CN # Supported options: CN, EN, JP — only affects prompt language
LLM_TEMPERATURE=1.125 # LLM temperature; higher values means more randomness
```

### 4.Import Story Files
You may use story files with or without summaries.
If the stories don’t include summaries, you can run add_all_summary.py to batch-generate them.
Note: add_all_summary.py uses deepseek-reasoner by default. If you want to use a different model, manually change the line MODEL="deepseek-reasoner" in the script.
Be sure to delete sample_summary.json in the story folder.
Story file format:
Without Summary:
```json
{
  "eventName": "Event Name Here",
  "chapterTitle": "Chapter Title Here",
  "extractedData": [
    "Character A: Some dialogue from Character A",
    "B: Some dialogue from Character B"
  ]
}
```
With Summary:
```json
{
  "eventName": "Event Name Here",
  "chapterTitle": "Chapter Title Here",
  "extractedData": [
    "Character A: Some dialogue from Character A",
    "B: Some dialogue from Character B"
  ],
  "Summary": "The summary. You can write it yourself or use LLM to generate it."
}
```
Run add_all_summary.py to automatically add summaries to files that don’t have them:
```bash
python add_all_summary.py
```

### 5.Run roleplay_engine.py for Embedding and Testing
```bash
python roleplay_engine.py
```
On the first run, embeddings will be generated automatically and cached.
Note: If you change the character, you must manually clear the cache.
Within roleplay_engine.py, users can chat with characters and run tests.

### 6.Use the Function Programmatically
You can call the role-play functionality via generate_reply(author_name: str, user_msg: str, iso_dt: str).
author_name: Name of the message sender.
user_msg: The content of the message.
iso_dt: The message’s ISO datetime string.
Example:
```python
from roleplay_engine import generate_reply
message = generate_reply("Ella", "Moka, did you practice guitar today?", "2025-06-16T11:45:14-07:00")
print(message)
```

## License
This project is licensed under the Apache-2.0 License. For more details, please see the LICENSE file.
