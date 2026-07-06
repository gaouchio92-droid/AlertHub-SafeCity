"""Common connector event model contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventModelField:
    """Common event model field definition."""

    name: str
    data_type: str
    required: bool
    description: str


EVENT_MODEL_FIELDS: tuple[EventModelField, ...] = (
    EventModelField(
        name="source",
        data_type="string",
        required=True,
        description="Connector source key that produced the event.",
    ),
    EventModelField(
        name="problem_id",
        data_type="string | null",
        required=False,
        description="Source-specific event, problem, trigger, or message identifier.",
    ),
    EventModelField(
        name="host",
        data_type="string | null",
        required=False,
        description="Host, device, service, or origin associated with the event.",
    ),
    EventModelField(
        name="severity",
        data_type="string | null",
        required=False,
        description="Normalized or source-native severity value.",
    ),
    EventModelField(
        name="status",
        data_type="string | null",
        required=False,
        description="Current event state such as received, problem, or resolved.",
    ),
    EventModelField(
        name="problem_name",
        data_type="string | null",
        required=False,
        description="Human-readable event or problem summary.",
    ),
    EventModelField(
        name="started_at",
        data_type="datetime | null",
        required=False,
        description="Timestamp when the source problem started.",
    ),
    EventModelField(
        name="resolved_at",
        data_type="datetime | null",
        required=False,
        description="Timestamp when the source problem was resolved.",
    ),
    EventModelField(
        name="duration",
        data_type="integer | null",
        required=False,
        description="Problem duration in seconds when known.",
    ),
    EventModelField(
        name="raw_payload",
        data_type="object",
        required=True,
        description="Original source payload retained for traceability.",
    ),
)
