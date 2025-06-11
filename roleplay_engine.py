"""
generate_reply(author_name: str, user_msg: str, iso_dt: str) -> str | None
"""
import os, json, sys, traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from openai import OpenAI
import tzlocal

import rag_handler
from moka_memory import MochaMemory
import logging, pathlib, json

LOG_PATH = pathlib.Path("logs/roleplay_log.jsonl")
LOG_PATH.parent.mkdir(exist_ok=True)

_log_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
_log_handler.setFormatter(logging.Formatter('%(message)s'))
logger = logging.getLogger("roleplay")
logger.setLevel(logging.INFO)
logger.addHandler(_log_handler)

load_dotenv()
BOT_LANG = os.getenv("BOT_LANG", "CN")
CHARACTER_NAME      = os.getenv("CHARACTER_NAME", "Moka")
CHARACTER_FULL_NAME = os.getenv("CHARACTER_FULL_NAME", "Moca Aoba")
MODEL_NAME          = os.getenv("OPENAI_MODEL", "deepseek-chat")
LLM_TEMPERATURE     = float(os.getenv("LLM_TEMPERATURE",1))
AIclient            = OpenAI(api_key=os.getenv("DEEPSEEK_KEY"),
                             base_url=os.getenv("DEEPSEEK_API_URL"))

try:
    with open("knowledge.txt", encoding="utf-8") as f:
        KNOWLEDGE_BASE = f.read()
except FileNotFoundError:
    KNOWLEDGE_BASE = ""
if BOT_LANG == "EN":
    SYSTEM_PROMPT_TPL = f"""
        Please reply as {CHARACTER_FULL_NAME} in a chat based on the knowledge base information below and the relevant plot excerpts provided.
        If you think the message is irrelevant and you do not need to reply it, please reply with “(NO REPLY)”.
        Do not use emojis or emoticons, and do not reveal that you are a language model.
        If you do not know the answer, please be honest and do not make anything up.
    """
    RAG_PREFIX       = "Based on the user's message, here is a related story"

elif BOT_LANG == "JP":
    SYSTEM_PROMPT_TPL = f"""
        以下の知識庫資料および提供された関連するストーリーのシーンを参考に、チャット中の{CHARACTER_FULL_NAME}の返信を模倣してください。
        メッセージが関係ないと判断し、返信する必要がない場合は、「(NO REPLY)」と返信してください。
        絵文字/顔文字は使用しないでください；言語モデルであることを明かさないでください。
        知らない情報がある場合は、正直に答えてください。嘘をつかないでください。
    """
    RAG_PREFIX       = "ユーザーのメッセージに基づき、関連シーンを提示します"

else:
    SYSTEM_PROMPT_TPL = f"""
        请你根据下方知识库资料、以及提供的相关剧情片段，模仿正在聊天的{CHARACTER_FULL_NAME}进行回复。
        如果你认为该信息无需回复，请输出"(NO REPLY)"
        不要用 emoji / 颜文字；不要暴露自己是语言模型。
        如果有不知道的信息，请实话实说，不要编造。
    """
    RAG_PREFIX       = "根据用户的话，这里有一段相关剧情"

PERSONALITY_TMPL = f"""
{SYSTEM_PROMPT_TPL}
{{knowledge_base}}
{{relevant_story_prompt}}
"""

#Memory
mocha_memory = MochaMemory(
    system_prompt_template=PERSONALITY_TMPL,
    knowledge_base=KNOWLEDGE_BASE,
    CHARACTER_NAME=CHARACTER_NAME,
    CHARACTER_FULL_NAME=CHARACTER_FULL_NAME,
    max_rounds=50,
)

# Initializing RAG
try:
    rag_handler.load_model_and_tokenizer()
    if not rag_handler.load_cache():
        rag_handler.process_stories()
except Exception as e:
    print("RAG Initialization failed:", e, file=sys.stderr)

def generate_reply(author_name: str, user_msg: str, iso_dt: str) -> str | None:
    """
    Return the role response. For no reply return None
    - author_name: author name of the message
    - user_msg:    Message text
    - iso_dt:      ISO datetime
    """
    relevant_story_prompt = ""
    try:
        rels = rag_handler.find_relevant_story(user_msg, top_n=1)
        if rels:
            info = rels[0]
            relevant_story_prompt = (
                f"\n {{RAG_PREFIX}} "
                f"(EVENT: {info['event_name']} CHAPTER: {info['chapter_title']} SIMILARITY: {info['score']:.2f})"
                f"\n```story\n{info['full_content']}\n```"
            )
    except Exception:
        traceback.print_exc()

    mocha_memory.update_system_prompt_with_rag(relevant_story_prompt)

    mocha_memory.add_user_message(
        author=author_name,
        content=f" {iso_dt} :{user_msg}"
    )

    try:
        resp = AIclient.chat.completions.create(
            model=MODEL_NAME,
            messages=mocha_memory.get_history(),
            temperature=LLM_TEMPERATURE,
        )
        reply = resp.choices[0].message.content.strip()
        mocha_memory.add_mocha_reply(reply)

        deny = {"(NO REPLY)", "NO REPLY", "（NO REPLY）",
                f"({CHARACTER_NAME}NO REPLY)", f"（{CHARACTER_NAME}NO REPLY）."}

        usage = resp.usage
        tokens_prompt     = usage.prompt_tokens
        tokens_completion = usage.completion_tokens
        tokens_total      = usage.total_tokens

        log_obj = {
            "time": iso_dt,
            "user": author_name,
            "user_msg": user_msg,
            "rag_event": info["event_name"] if rels else None,
            "rag_chapter": info["chapter_title"] if rels else None,
            "rag_score": info["score"] if rels else None,
            "rag_summary":info["Summary"] if rels else None,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "tokens_total": tokens_total,
            "reply": reply
        }
        logger.info(json.dumps(log_obj, ensure_ascii=False))

        deny = {...}
        return None if reply in deny else reply

    except Exception:
        traceback.print_exc()
        return None


if __name__ == "__main__":
    while True:
        try:
            txt = input("USER > ").strip()
            if not txt:
                continue
            local_tz = ZoneInfo(tzlocal.get_localzone_name())
            now_iso  = datetime.now(local_tz).isoformat()
            ans = generate_reply("Tester", txt, now_iso)
            print(f"{CHARACTER_NAME} >", ans or "(NO REPLY)")
        except (EOFError, KeyboardInterrupt):
            break
