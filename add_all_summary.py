import os, json, asyncio, time
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio
from openai import AsyncClient

load_dotenv()
MODEL      = "deepseek-reasoner"
DATA_DIR   = Path("story")
OUT_SUFFIX = ".with_summary.json"
MAX_CHARS  = 50000
BATCH      = 10
BOT_LANG = os.getenv("BOT_LANG", "CN")

CLIENT = AsyncClient(
    api_key=os.getenv("DEEPSEEK_KEY"),
    base_url=os.getenv("DEEPSEEK_API_URL")
)

if BOT_LANG == "EN":
    PROMPT_TMPL = """
        The following is a dialogue script. Please summarize all the main characters and the main plot in 1-2 sentences, 
        keeping it as concise as possible:
    """
elif BOT_LANG == "JP":
    PROMPT_TMPL = """
        以下は会話の脚本です。主要なキャラクターと主要なストーリーを1～2文で要約し、
        できるだけ簡潔にまとめてください：
    """
else:
    PROMPT_TMPL = """
        以下是一段对话脚本，请用 1-2 句话概括所有主要角色和主要剧情，在此基础上尽量简短：
    """

async def call_with_retry(messages: List[dict], *, max_attempts=6, base_wait=2):
    attempt = 0
    while True:
        try:
            resp = await CLIENT.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except (RateLimitError, APIError) as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            wait = getattr(e, "retry_after", base_wait * 2 ** (attempt - 1))
            print(f"WARNING: API rate limit/error, {attempt}th retry, waiting {wait:.1f}s")
            await asyncio.sleep(wait)

async def process_file(path: Path):
    # If .with_summary.json already exists, skip it.
    out_path = path if OUT_SUFFIX == "" else path.with_suffix(OUT_SUFFIX)
    if out_path.exists():
        return

    # 1) Read JSON
    def _read_json(p: Path):
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    data = await asyncio.to_thread(_read_json, path)

    if "Summary" in data and data["Summary"]:
        return  # Skip if Summary already exist

    dialogue = "\n".join(data.get("extractedData", []))[:MAX_CHARS]
    prompt   = PROMPT_TMPL.format(dialogue=dialogue)
    summary  = await call_with_retry([{"role": "user", "content": prompt}])

    data["Summary"] = summary

    def _write_json(p: Path, obj):
        with p.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    await asyncio.to_thread(_write_json, out_path, data)

async def main():
    files = [
        fp for fp in DATA_DIR.glob("*.json")
        if not fp.name.endswith(OUT_SUFFIX)
    ]
    ...

    if not files:
        print("ERROR: story directory is empty")
        return

    sem = asyncio.Semaphore(BATCH)

    async def sem_task(fp):
        async with sem:
            await process_file(fp)

    await tqdm_asyncio.gather(*(sem_task(fp) for fp in files), desc="Processing")
    print("All done!")

if __name__ == "__main__":
    asyncio.run(main())
