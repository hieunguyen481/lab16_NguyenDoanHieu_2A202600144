from __future__ import annotations
import json
import time
from typing import Tuple
from openai import OpenAI
from pydantic import ValidationError

from .schemas import QAExample, JudgeResult, ReflectionEntry
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM

import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini"

def call_llm(messages: list[dict], system_prompt: str, json_mode: bool = False) -> Tuple[str, int, int]:
    msgs = [{"role": "system", "content": system_prompt}] + messages
    start_time = time.time()
    kwargs = {
        "model": MODEL_NAME,
        "messages": msgs,
        "temperature": 0.1
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
        
    try:
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        token_count = response.usage.total_tokens if response.usage else 0
    except Exception as e:
        print(f"[!] LLM API error: {e}")
        content = "" if not json_mode else "{}"
        token_count = 0
        
    latency_ms = int((time.time() - start_time) * 1000)
    return content, token_count, latency_ms

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> Tuple[str, int, int]:
    msg_content = f"Question: {example.question}\n"
    if reflection_memory and attempt_id > 1:
        msg_content += "Previous lessons learned (Reflection Memory):\n"
        for i, mem in enumerate(reflection_memory):
            msg_content += f"- {mem}\n"
        msg_content += "\nPlease answer the question based on these lessons. Provide only the concise answer."
    else:
        msg_content += "Provide a concise answer to the question."
        
    messages = [{"role": "user", "content": msg_content}]
    content, tokens, latency = call_llm(messages, ACTOR_SYSTEM, json_mode=False)
    return content.strip(), tokens, latency

def evaluator(example: QAExample, answer: str) -> Tuple[JudgeResult, int, int]:
    msg_content = (
        f"Question: {example.question}\n"
        f"Gold Answer: {example.gold_answer}\n"
        f"Predicted Answer: {answer}\n"
        f"Does the predicted answer match the gold answer conceptually? Provide your evaluate in the requested JSON format."
    )
    messages = [{"role": "user", "content": msg_content}]
    content, tokens, latency = call_llm(messages, EVALUATOR_SYSTEM, json_mode=True)
    
    try:
        data = json.loads(content)
        result = JudgeResult(
            score=int(data.get("score", 0)),
            reason=data.get("reason", "No reason provided"),
            missing_evidence=data.get("missing_evidence", []),
            spurious_claims=data.get("spurious_claims", [])
        )
    except (json.JSONDecodeError, ValidationError) as e:
        result = JudgeResult(score=0, reason=f"Failed to parse Evaluator output: {e}\nRaw output: {content}")
        
    return result, tokens, latency

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult, answer: str) -> Tuple[ReflectionEntry, int, int]:
    msg_content = (
        f"Question: {example.question}\n"
        f"Gold Answer: {example.gold_answer}\n"
        f"Actor's Failed Answer: {answer}\n"
        f"Evaluator's Reason for Failure: {judge.reason}\n\n"
        f"Provide a brief lesson and the next strategy to answer correctly."
    )
    messages = [{"role": "user", "content": msg_content}]
    content, tokens, latency = call_llm(messages, REFLECTOR_SYSTEM, json_mode=False)
    
    # Simple extraction since we just want to save it as text.
    entry = ReflectionEntry(
        attempt_id=attempt_id,
        failure_reason=judge.reason,
        lesson=content,
        next_strategy="Follow the lesson learned"
    )
    return entry, tokens, latency
