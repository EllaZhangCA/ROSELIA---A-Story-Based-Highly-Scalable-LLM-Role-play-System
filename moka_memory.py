from typing import List, Dict

class MochaMemory:
    def __init__(self,CHARACTER_FULL_NAME: str, CHARACTER_NAME: str, system_prompt_template: str, knowledge_base: str, max_rounds: int = 50):
        self.system_prompt_template = system_prompt_template
        self.knowledge_base = knowledge_base
        self.current_relevant_story_prompt = "" # 用于存储 RAG 返回的 story prompt
        self.CHARACTER_FULL_NAME = CHARACTER_FULL_NAME
        self.CHARACTER_NAME = CHARACTER_NAME

        # 初始的 system_prompt，不包含 RAG
        self.base_system_prompt_content = self._build_system_prompt()
        self.chat_history: List[Dict[str, str]] = [{"role": "system", "content": self.base_system_prompt_content}]
        self.max_rounds = max_rounds


    def _build_system_prompt(self, relevant_story_prompt: str = "") -> str:
        """根据模板和当前信息构建 system_prompt 内容"""
        return self.system_prompt_template.format(
            knowledge_base=self.knowledge_base,
            CHARACTER_FULL_NAME=self.CHARACTER_FULL_NAME,
            CHARACTER_NAME=self.CHARACTER_NAME,
            relevant_story_prompt=relevant_story_prompt # RAG 的内容会在这里插入
        )

    def update_system_prompt_with_rag(self, relevant_story_prompt: str):
        """用 RAG 返回的 story 更新当前的 system prompt 内容"""
        self.current_relevant_story_prompt = relevant_story_prompt
        # 更新 chat_history 中的第一个 system message
        # 这确保了 get_history() 总是拿到最新的，包含RAG的system prompt
        new_system_content = self._build_system_prompt(relevant_story_prompt=self.current_relevant_story_prompt)
        if self.chat_history and self.chat_history[0]["role"] == "system":
            self.chat_history[0]["content"] = new_system_content
        else:
            # 如果历史为空或第一个不是system，则插入一个新的。这通常不应该发生。
            self.chat_history.insert(0, {"role": "system", "content": new_system_content})
            print("警告: MochaMemory 的 chat_history 结构异常，已重新插入 system prompt。")

    def add_user_message(self, author: str, content: str):
        # 在添加用户消息前，确保 system prompt 是最新的（包含了上一轮的 RAG 结果）
        # _build_system_prompt 会使用 self.current_relevant_story_prompt
        # 如果 RAG 是每轮都更新的，那么 update_system_prompt_with_rag 应该在 add_user_message 之前被调用
        # bot.py 中的逻辑是：收到消息 -> RAG -> update_system_prompt_with_rag -> add_user_message
        # 所以这里的 system prompt 应该是最新的。
        
        self.chat_history.append({"role": "user", "content": f"{author} : {content}"})
        self._trim_history()

    def add_mocha_reply(self, content: str):
        self.chat_history.append({"role": "assistant", "content": content})
        # 在添加完 assistant 回复后，可以清除本次的 RAG story，避免影响下一轮的初始 prompt
        # 如果希望 RAG 的内容只对当前这一轮对话生效的话。
        self.current_relevant_story_prompt = "" 
        self.update_system_prompt_with_rag("") # 重置，以便下一轮的 system prompt 不包含旧 RAG
        # 但如果希望大模型持续知道这个上下文，直到新的RAG出现，则不清除
        self._trim_history()

    def get_history(self) -> List[Dict[str, str]]:
        # 确保 chat_history[0] 是最新的 system prompt
        # update_system_prompt_with_rag 已经保证了这一点
        return self.chat_history

    def _trim_history(self):
        """保留最近 N 轮 user+assistant（2个message = 1轮），加上开头 system"""
        # 第一个元素是 system prompt，不参与轮数计算
        if len(self.chat_history) > 1: # 至少有一个 system prompt
            non_system_messages = self.chat_history[1:]
            if len(non_system_messages) > self.max_rounds * 2:
                # 保留 system prompt 和最新的对话
                self.chat_history = [self.chat_history[0]] + non_system_messages[-self.max_rounds * 2:]

    def clear_memory(self):
        # 清空时也重置 RAG 的内容
        self.current_relevant_story_prompt = ""
        self.base_system_prompt_content = self._build_system_prompt() # 使用空的 RAG prompt 重建基础
        self.chat_history = [{"role": "system", "content": self.base_system_prompt_content}]

    def get_formatted_system_prompt(self, relevant_story_prompt: str = "") -> str:
        """提供给 bot.py 一个直接获取格式化后 system_prompt 的方法 (如果需要外部构建)"""
        return self._build_system_prompt(relevant_story_prompt)
