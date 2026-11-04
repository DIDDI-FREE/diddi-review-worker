from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ReviewRunRow(Base):
    __tablename__ = "review_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scenario: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    steps: Mapped[list["ReviewStepRow"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class ReviewStepRow(Base):
    __tablename__ = "review_steps"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("review_runs.id"), index=True)
    step_key: Mapped[str] = mapped_column(String(120), nullable=False)
    product: Mapped[str] = mapped_column(String(30), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_detail: Mapped[str | None] = mapped_column(Text)
    run: Mapped[ReviewRunRow] = relationship(back_populates="steps")


class ReviewEventLedgerRow(Base):
    __tablename__ = "review_event_ledger"
    event_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


def session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


class SqlRunRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    async def create(self, run_id: str, scenario: str, steps: list[dict]) -> None:
        async with self.sessions.begin() as session:
            row = ReviewRunRow(id=run_id, scenario=scenario, status="queued")
            row.steps = [ReviewStepRow(run_id=run_id, step_key=s["key"], product=s["product"], role=s["role"], resource_id=s["resource_id"], status="queued") for s in steps]
            session.add(row)

    async def update_status(self, run_id: str, status: str) -> None:
        async with self.sessions.begin() as session:
            await session.execute(update(ReviewRunRow).where(ReviewRunRow.id == run_id).values(status=status))


class SqlEventLedger:
    """PostgreSQL-backed claim ledger using the primary key as the mutex."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    async def claim(self, event_key: str) -> bool:
        async with self.sessions() as session:
            try:
                session.add(ReviewEventLedgerRow(event_key=event_key, state="claimed"))
                await session.commit()
                return True
            except IntegrityError:
                await session.rollback()
                return False

    async def mark_terminal(self, event_key: str) -> None:
        async with self.sessions.begin() as session:
            await session.execute(
                update(ReviewEventLedgerRow)
                .where(ReviewEventLedgerRow.event_key == event_key)
                .values(state="terminal")
            )
