import logging
import redis as redis_lib
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import TZ, REDIS_URL, REDIS_TOKEN, REDIS_RESEARCH_CURSOR_KEY
from budget import get_requests_today, log_request, DAILY_REQUEST_LIMIT

logger = logging.getLogger(__name__)

_send_to_alex = None


def set_sender(fn):
    global _send_to_alex
    _send_to_alex = fn


async def _send(text: str):
    if _send_to_alex:
        await _send_to_alex(text)
    else:
        logger.warning("No sender registered, dropping: %s", text[:80])


async def morning_brief():
    logger.info("Running morning brief")
    try:
        from llm_client import chat_scheduled
        brief = chat_scheduled(
            "Generate a concise morning brief for Alex. Include: "
            "1) Key focus areas today from active projects, "
            "2) Any deadlines in the next 3 days, "
            "3) One actionable suggestion. "
            "Max 200 words, bullet points, in Greek.",
            max_tokens=400
        )
        await _send(f"☀️ *Morning Brief — {datetime.now().strftime('%d/%m/%Y')}*\n\n{brief}")
    except Exception as e:
        logger.error("Morning brief failed: %s", e)


async def deadline_nudge():
    logger.info("Running deadline nudge")
    try:
        from llm_client import chat_scheduled
        result = chat_scheduled(
            "Scan Alex's active projects for deadlines within the next 3 days. "
            "If none found, reply with exactly: NO_DEADLINES\n"
            "If found, list them concisely in Greek (max 100 words).",
            max_tokens=200
        )
        if "NO_DEADLINES" not in result:
            await _send(f"⏰ *Deadline Alert*\n\n{result}")
    except Exception as e:
        logger.error("Deadline nudge failed: %s", e)


async def idle_research():
    logger.info("Running idle research")
    if get_requests_today() > DAILY_REQUEST_LIMIT * 0.4:
        logger.info("Budget >40%%, skipping idle research")
        return
    try:
        from llm_client import chat_scheduled

        r = redis_lib.from_url(REDIS_URL, password=REDIS_TOKEN)
        cursor = int(r.get(REDIS_RESEARCH_CURSOR_KEY) or 0)

        result = chat_scheduled(
            f"Pick active project #{cursor + 1} (cycling) and give: "
            "1) One relevant tool/trend/insight right now, "
            "2) One concrete next step Alex could take this week. "
            "Under 150 words, specific, actionable, in Greek.",
            max_tokens=300
        )
        r.incr(REDIS_RESEARCH_CURSOR_KEY)
        await _send(f"🔬 *Nightly Research*\n\n{result}")
    except Exception as e:
        logger.error("Idle research failed: %s", e)


async def budget_reset_notify():
    from budget import get_budget_status_message
    await _send(f"🔄 Νέα μέρα — budget reset.\n{get_budget_status_message()}")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(morning_brief,      CronTrigger(hour=7,  minute=0,  timezone=TZ))
    scheduler.add_job(deadline_nudge,     CronTrigger(hour=20, minute=0,  timezone=TZ))
    scheduler.add_job(idle_research,      CronTrigger(hour=2,  minute=0,  timezone=TZ))
    scheduler.add_job(budget_reset_notify, CronTrigger(hour=0, minute=1,  timezone=TZ))
    return scheduler
