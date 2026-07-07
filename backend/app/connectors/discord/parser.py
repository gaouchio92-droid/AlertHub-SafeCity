"""Discord/Zabbix message parsing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.connectors.base import ConnectorEvent

URL_PATTERN = re.compile(r"https?://[^\s>)]+")
SECTION_START_PATTERN = re.compile(r"^(Problem|Resolved in .+?):\s*(?P<title>.+)$")
FIELD_PATTERN = re.compile(r"^(?P<key>[A-Za-z][A-Za-z ]+):\s*(?P<value>.+)$")
STARTED_AT_PATTERN = re.compile(
    r"Problem started at (?P<time>\d{2}:\d{2}:\d{2}) on (?P<date>\d{4}\.\d{2}\.\d{2})"
)
RESOLVED_AT_PATTERN = re.compile(
    r"Problem has been resolved in (?P<duration>.+?) at "
    r"(?P<time>\d{2}:\d{2}:\d{2}) on (?P<date>\d{4}\.\d{2}\.\d{2})"
)


@dataclass(frozen=True)
class DiscordMessageContext:
    """Discord message metadata used while building normalized events."""

    message_id: str | None
    timestamp: datetime | None
    author_name: str | None
    payload: dict[str, Any]


def parse_discord_zabbix_events(
    payload: dict[str, Any],
    *,
    source: str,
) -> list[ConnectorEvent]:
    """Parse one Discord message into one or more normalized Zabbix events."""
    context = _message_context(payload)
    text = _message_text(payload)
    sections = _zabbix_sections(text)
    if not sections:
        return [_fallback_event(source=source, context=context, text=text)]

    events: list[ConnectorEvent] = []
    seen_problem_ids: set[str] = set()
    for section in sections:
        fields = _section_fields(section)
        problem_id = fields.get("Original problem ID")
        if not problem_id:
            problem_id = f"{context.message_id}:{len(events) + 1}" if context.message_id else None
        if problem_id and problem_id in seen_problem_ids:
            continue
        if problem_id:
            seen_problem_ids.add(problem_id)

        status = "resolved" if section[0].startswith("Resolved in") else "problem"
        started_at = _parse_started_at(section) or context.timestamp
        resolved_at = _parse_resolved_at(section)
        events.append(
            ConnectorEvent(
                source=source,
                problem_id=problem_id,
                host=fields.get("Host") or context.author_name,
                severity=fields.get("Severity"),
                status=status,
                problem_name=fields.get("Problem name") or _section_title(section),
                started_at=started_at,
                resolved_at=resolved_at,
                duration=_duration_seconds(_resolved_duration(section)),
                raw_payload={
                    **payload,
                    "normalized": {
                        "discord_message_id": context.message_id,
                        "zabbix_problem_id": problem_id,
                        "status": status,
                        "operational_data": fields.get("Operational data"),
                        "links": _links(section),
                        "section_text": "\n".join(section),
                    },
                },
            )
        )
    return events or [_fallback_event(source=source, context=context, text=text)]


def _message_context(payload: dict[str, Any]) -> DiscordMessageContext:
    timestamp = payload.get("timestamp")
    author_payload = payload.get("author")
    author = author_payload if isinstance(author_payload, dict) else {}
    return DiscordMessageContext(
        message_id=str(payload.get("id")) if payload.get("id") else None,
        timestamp=_parse_discord_timestamp(timestamp),
        author_name=str(author.get("username")) if author.get("username") else None,
        payload=payload,
    )


def _message_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    content = payload.get("content")
    if isinstance(content, str) and content.strip():
        parts.append(content)

    embeds = payload.get("embeds")
    if isinstance(embeds, list):
        for embed in embeds:
            if isinstance(embed, dict):
                parts.extend(_embed_text(embed))
    return "\n".join(parts)


def _embed_text(embed: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("title", "description", "url"):
        value = embed.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value)
    fields = embed.get("fields")
    if isinstance(fields, list):
        for field in fields:
            if isinstance(field, dict):
                name = field.get("name")
                value = field.get("value")
                if isinstance(name, str) and isinstance(value, str):
                    values.append(f"{name}: {value}")
    return values


def _zabbix_sections(text: str) -> list[list[str]]:
    sections: list[list[str]] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if SECTION_START_PATTERN.match(line):
            if current:
                sections.append(current)
            current = [line]
            continue
        if current:
            current.append(line)
    if current:
        sections.append(current)
    return sections


def _section_fields(section: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in section[1:]:
        match = FIELD_PATTERN.match(line)
        if match:
            fields[match.group("key")] = match.group("value").strip()
    return fields


def _section_title(section: list[str]) -> str | None:
    match = SECTION_START_PATTERN.match(section[0])
    if not match:
        return None
    return match.group("title").strip()


def _parse_discord_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_zabbix_timestamp(date_value: str, time_value: str) -> datetime:
    return datetime.strptime(f"{date_value} {time_value}", "%Y.%m.%d %H:%M:%S").astimezone()


def _parse_started_at(section: list[str]) -> datetime | None:
    for line in section:
        match = STARTED_AT_PATTERN.search(line)
        if match:
            return _parse_zabbix_timestamp(match.group("date"), match.group("time"))
    return None


def _parse_resolved_at(section: list[str]) -> datetime | None:
    for line in section:
        match = RESOLVED_AT_PATTERN.search(line)
        if match:
            return _parse_zabbix_timestamp(match.group("date"), match.group("time"))
    return None


def _resolved_duration(section: list[str]) -> str | None:
    for line in section:
        match = RESOLVED_AT_PATTERN.search(line)
        if match:
            return match.group("duration")
    first_line = section[0]
    if first_line.startswith("Resolved in "):
        return first_line.removeprefix("Resolved in ").split(":", 1)[0]
    return None


def _duration_seconds(value: str | None) -> int | None:
    if not value:
        return None
    seconds = 0
    matches = re.findall(r"(\d+)\s*([dhms])", value)
    for amount, unit in matches:
        number = int(amount)
        if unit == "d":
            seconds += number * 86400
        elif unit == "h":
            seconds += number * 3600
        elif unit == "m":
            seconds += number * 60
        elif unit == "s":
            seconds += number
    return seconds or None


def _links(lines: list[str]) -> list[str]:
    return [match for line in lines for match in URL_PATTERN.findall(line)]


def _fallback_event(
    *,
    source: str,
    context: DiscordMessageContext,
    text: str,
) -> ConnectorEvent:
    return ConnectorEvent(
        source=source,
        problem_id=context.message_id,
        host=context.author_name,
        severity=None,
        status="received",
        problem_name=text[:255] if text else None,
        started_at=context.timestamp,
        resolved_at=None,
        duration=None,
        raw_payload=context.payload,
    )
