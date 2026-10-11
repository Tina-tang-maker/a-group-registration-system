import asyncio
from sqlalchemy import select
from app.database import async_session_factory
from app.models.ai import AiJob, AiMessage, AiSession
from app.models.member import ActivityMember
from app.dependencies import now_iso
from app.database import generate_uuid
import json


async def process_reply_job(job: AiJob):
    from app.config import get_settings
    settings = get_settings()

    input_data = job.input_data or {}
    content = input_data.get("content", "")
    role = input_data.get("role", "STUDENT")
    topic_key = input_data.get("topic_key", "")

    if settings.ai_api_key and settings.ai_base_url:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.ai_api_key, base_url=settings.ai_base_url)

            system_prompt = _build_system_prompt(role, topic_key)
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=settings.ai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},
                    ],
                    max_tokens=500,
                    temperature=0.7,
                ),
                timeout=60,
            )
            reply_text = response.choices[0].message.content or ""
        except asyncio.TimeoutError:
            job.status = "FAILED"
            job.error_code = "TIMEOUT"
            return
        except Exception as e:
            job.status = "FAILED"
            job.error_code = "AI_UNAVAILABLE"
            return
    else:
        reply_text = _fallback_reply(role, topic_key, content)

    async with async_session_factory() as session:
        assistant_msg = AiMessage(
            session_id=job.session_id,
            role="ASSISTANT",
            content=reply_text,
            client_message_id=f"auto-{generate_uuid()[:8]}",
        )
        session.add(assistant_msg)

        job.status = "SUCCEEDED"
        job.result_data = {"reply": reply_text}
        job.error_code = None
        await session.commit()


def _build_system_prompt(role: str, topic_key: str) -> str:
    if role == "STUDENT":
        return (
            "你是一位友善的资料访谈助手，正在帮助学员整理报名资料。"
            "根据学员的回答，围绕其经历背景、交流话题和交流期待进行追问。"
            "每次最多追问一个重点，帮助学员补充具体细节。"
            "不要自动填写资料，不要给出建议结论。"
        )
    else:
        return (
            "你是一位友善的资料访谈助手，正在帮助导师整理报名资料。"
            "根据导师的回答，围绕其经验、可以帮助的问题和能力边界进行追问。"
            "每次最多追问一个重点，帮助导师补充具体细节。"
            "不要自动填写资料，不要给出建议结论。"
        )


def _fallback_reply(role: str, topic_key: str, content: str) -> str:
    if role == "STUDENT":
        return f"感谢你的分享。能否具体说说你在{topic_key}方面的经历？比如做过什么项目、遇到了什么挑战？"
    else:
        return f"谢谢你的经验描述。在{topic_key}方面，你能举一个具体的例子吗？比如你曾经如何帮助过类似情况的人？"


async def run_ai_worker():
    while True:
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(AiJob).where(
                        AiJob.job_type == "REPLY",
                        AiJob.status == "PENDING",
                    ).limit(1)
                )
                job = result.scalar_one_or_none()
                if not job:
                    await asyncio.sleep(2)
                    continue

                job.status = "RUNNING"
                job.worker_token = generate_uuid()
                job.attempts += 1
                await session.commit()

                await process_reply_job(job)
                await session.commit()

        except Exception as e:
            print(f"AI worker error: {e}")
            await asyncio.sleep(5)
