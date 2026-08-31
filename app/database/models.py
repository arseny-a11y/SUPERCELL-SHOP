from datetime import datetime, timezone
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from typing import Annotated
import enum


intpk = Annotated[int,mapped_column(primary_key=True)]
create_at = Annotated[datetime,mapped_column(server_default=func.now())]
update_at = Annotated[datetime, mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )]

class Base(DeclarativeBase):
    def __repr__(self):
        values = ", ".join(
            f"{col}={getattr(self, col)!r}"
            for col in self.__table__.columns.keys()
        )
        return f"{self.__class__.__name__}({values})"

class Workload(enum.Enum):
    fulltime = 'fulltime'
    parttime = 'parttime'

class WorkersORM(Base):
    __tablename__ = 'workers'

    id:  Mapped[intpk]
    user_name: Mapped[str]
    resumes: Mapped[list["ResumesORM"]] = relationship(
        back_populates="worker")

    resumes_parttime: Mapped[list["ResumesORM"]] = relationship(
        back_populates="worker",
        primaryjoin="and_(WorkersORM.id == ResumesORM.worker_id, ResumesORM.workload == 'parttime')",
        overlaps="resumes"
        )

class ResumesORM(Base):
    __tablename__ = 'resumes'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    compensation: Mapped[int] = mapped_column(nullable=True)
    workload: Mapped[Workload]
    worker_id: Mapped[int] = mapped_column(ForeignKey('workers.id',ondelete='CASCADE'))
    create_at: Mapped[create_at]
    update_at: Mapped[update_at]
    worker: Mapped["WorkersORM"] = relationship(back_populates="resumes")
