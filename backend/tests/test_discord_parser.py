"""Discord/Zabbix parser tests."""

from app.connectors.discord.parser import parse_discord_zabbix_events


def test_parse_zabbix_problem_message_extracts_alert_fields() -> None:
    problem_name = (
        "Huawei VRP: Interface GigabitEthernet0/0/2(to PALAIS-AGG): "
        "High bandwidth usage (>90%)"
    )
    payload = {
        "id": "discord-1",
        "timestamp": "2026-07-06T23:53:34.000000+00:00",
        "author": {"username": "Zabbix"},
        "content": "\n".join(
            [
                f"Problem: {problem_name}",
                "Problem started at 23:53:33 on 2026.07.06",
                f"Problem name: {problem_name}",
                "Host: MPTN-AGGSW01",
                "Severity: Warning",
                "Operational data: In: 4.12 Gbps, out: 14.18 Mbps, speed: 1 Gbps",
                "Original problem ID: 51546",
                "Event link: https://zabbix.example/events/51546",
            ]
        ),
    }

    events = parse_discord_zabbix_events(payload, source="discord")

    assert len(events) == 1
    event = events[0]
    assert event.problem_id == "51546"
    assert event.host == "MPTN-AGGSW01"
    assert event.severity == "Warning"
    assert event.status == "problem"
    assert event.problem_name.startswith("Huawei VRP: Interface GigabitEthernet0/0/2")
    assert event.started_at is not None
    assert event.duration is None
    assert event.raw_payload["normalized"]["operational_data"] == (
        "In: 4.12 Gbps, out: 14.18 Mbps, speed: 1 Gbps"
    )
    assert event.raw_payload["normalized"]["links"] == ["https://zabbix.example/events/51546"]


def test_parse_zabbix_resolved_message_extracts_resolution_fields() -> None:
    problem_name = (
        "Huawei VRP: Interface GigabitEthernet0/0/26(): "
        "High bandwidth usage (>90%)"
    )
    payload = {
        "id": "discord-2",
        "timestamp": "2026-07-06T22:57:56.000000+00:00",
        "author": {"username": "Zabbix"},
        "content": "\n".join(
            [
                f"Resolved in 8m 18s: {problem_name}",
                "Problem has been resolved in 8m 18s at 22:57:55 on 2026.07.06",
                f"Problem name: {problem_name}",
                "Host: MSPC-DCAGG-SW1",
                "Severity: Warning",
                "Original problem ID: 51536",
            ]
        ),
    }

    events = parse_discord_zabbix_events(payload, source="discord")

    assert len(events) == 1
    event = events[0]
    assert event.problem_id == "51536"
    assert event.status == "resolved"
    assert event.host == "MSPC-DCAGG-SW1"
    assert event.severity == "Warning"
    assert event.resolved_at is not None
    assert event.duration == 498
