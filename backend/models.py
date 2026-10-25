from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # demo | import
    source: Mapped[str] = mapped_column(String(500), default="")
    period: Mapped[str] = mapped_column(String(250), default="")
    license: Mapped[str] = mapped_column(String(500), default="")
    variable_type: Mapped[str] = mapped_column(String(50), default="other")
    unit: Mapped[str] = mapped_column(String(20), default="°C")
    resolution: Mapped[str] = mapped_column(String(250), default="")
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    invalid_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    observations: Mapped[list["Observation"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[str] = mapped_column(String(80), default="")
    quality: Mapped[dict] = mapped_column(JSON, default=dict)
    dataset: Mapped[Dataset] = relationship(back_populates="observations")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    algorithm: Mapped[str] = mapped_column(String(50), default="DBSCAN")
    params: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    dataset: Mapped[Dataset] = relationship(back_populates="analyses")
