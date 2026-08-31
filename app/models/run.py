from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class TaskRun(Base):
    __tablename__ = "task_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="queued"
    )  # queued, running, verifying, passed, failed, timed_out
    start_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    score: Mapped[float] = mapped_column(Float, default=0.0)
    failure_category: Mapped[str] = mapped_column(
        String, default="NONE"
    )  # NONE, MODEL_FAILURE, ENVIRONMENT_FAILURE, TASK_FAILURE
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agent_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tool_calls: Mapped[list["ToolCallRecord"]] = relationship(
        "ToolCallRecord", back_populates="run", cascade="all, delete-orphan"
    )


class ToolCallRecord(Base):
    __tablename__ = "tool_call_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("task_runs.id"), nullable=False)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    arguments_json: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)

    run: Mapped["TaskRun"] = relationship("TaskRun", back_populates="tool_calls")
