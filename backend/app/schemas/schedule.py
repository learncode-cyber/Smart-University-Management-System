from datetime import time

from pydantic import BaseModel

from app.models.enums import DayOfWeek


class ScheduleCreateRequest(BaseModel):
    course_section_id: int
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    room: str


class ScheduleUpdateRequest(BaseModel):
    day_of_week: DayOfWeek | None = None
    start_time: time | None = None
    end_time: time | None = None
    room: str | None = None


class ScheduleResponse(BaseModel):
    id: int
    course_section_id: int
    course_code: str
    course_title: str
    teacher_id: int
    teacher_name: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    room: str


class ScheduleConflictResponse(BaseModel):
    slot_a_id: int | None
    slot_b_id: int | None
    reason: str
