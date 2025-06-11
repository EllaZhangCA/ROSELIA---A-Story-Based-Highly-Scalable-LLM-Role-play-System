# ROSELIA - A Story Based Highly Scalable LLM Role play System
### ROSELIA 是 Role-Oriented Story Embedding &amp; LLM Interaction Architecture 的简写，这是一个基于剧情检索、可水平扩展的角色扮演框架

[**中文简体**](./README.md) [**English**](./README_EN.md)

## 快速开始

### 1.安装依赖
```bash
cd (你的文件路径，例如C:\Users\ellaz\roselia)
python -m pip install -r requirements.txt
```
### 2.配置Embedding模型
若用Hugging Face Hub，可直接在 .env 的 MODEL_PATH 中填模型名，无需下载；
若放本地目录，要在 .env 中用“MODEL_PATH=”指向它。
如果不知道用什么模型好，可以先用 MODEL_PATH=richinfoai/ritrieve_zh_v1 或者 MODEL_PATH=Qwen/Qwen3-Embedding-8B 试试

### 3.配置.env
```
DEEPSEEK_KEY= #你的LLM API Key
DEEPSEEK_API_URL= #你的LLM API URL
OPENAI_MODEL= #你用的LLM模型，中文聊天推荐deepseek-chat
CHARACTER_NAME= #角色名，如“摩卡”
CHARACTER_FULL_NAME= #角色全名，如“青叶摩卡”
MODEL_PATH= #Embedding模型地址，例如richinfoai/ritrieve_zh_v1
STORY_DIR=story #角色剧情地址
EMBEDDING_CACHE_PATH=story_embedding_cache.npz #Embedding缓存储存位置
META_CACHE_PATH=story_meta_cache.pkl #Meta路径缓存储存位置
LANG=CN #支持 CN,EN 和 JP. 只改变prompt的语言
LLM_TEMPERATURE=1.125 #LLM的temperature，越大越离散

DISCORD_TOKEN= (Discord Bot 需要）Discord bot的token
ALLOWED_CHANNEL_IDS_DC= (Discord Bot 需要）允许Discord bot发言的频道
```

### 4.导入故事文件
可以选择带Summary的文件，也可以选择不带Summary的文件然后用add_all_summary.py批量生成Summary。
需要注意的是，add_all_summary.py默认使用deepseek-reasoner，如果想使用其他模型需要手动改写脚本中的MODEL="deepseek-reasoner"
请务必把story文件夹的sample_summary.json删除。
story文件规范：
不带Summary:
```json
{
  "eventName": "这里是事件名",
  "chapterTitle": "这里是章节名",
  "extractedData": [
    "角色A: 这里角色A说了一些话",
    "B: 不赖"
  ]
}
```
带Summary:
```json
{
  "eventName": "这里是事件名",
  "chapterTitle": "这里是章节名",
  "extractedData": [
    "角色A: 这里角色A说了一些话",
    "B: 不赖"
  ],
  "Summary": "这是总结，可以自己写也可以LLM生成"
}
```
运行add_all_summary.py，这个脚本会自动对不带Summary的文件添加Summary
```bash
python add_all_summary.py
```

### 5.启动roleplay_engine.py，以进行embedding和测试
```bash
python roleplay_engine.py
```
首次运行时会自动进行embedding，并生成缓存。
需要注意的是，更换角色后需要手动移除缓存。
在roleplay_engine中用户可以与角色对话、进行测试。

### 6.调用function
可以使用generate_reply(author_name: str, user_msg: str, iso_dt: str) -> str | None来调用roleplay_engine.py的角色扮演功能。
author_name：消息发送者的名字。user_msg：消息发送者的消息。iso_dt：消息的ISO datetime
示例
```python
from roleplay_engine import generate_reply
message = generate_reply("Ella", "摩卡你今天练琴了吗？", "2025-06-16T11:45:14-07:00")
print(message)
```

## 许可
本项目代码遵循 Apache-2.0 许可，详情见 LICENSE。

