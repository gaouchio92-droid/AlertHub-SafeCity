"""Report API schemas."""

from pydantic import BaseModel, ConfigDict


class WeeklyDiscordReportStatusResponse(BaseModel):
    """Weekly Discord report feature status."""

    model_config = ConfigDict(frozen=True)

    feature: str
    implemented: bool
    visible_in_ui: bool
    reason: str
    required_before_available: list[str]
