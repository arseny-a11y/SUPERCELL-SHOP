from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, BigInteger, Numeric, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from typing import Annotated
from enum import Enum

class Base(DeclarativeBase):
    def __repr__(self):
        values = ", ".join(
            f"{col}={getattr(self,col)!r}"
            for col in self.__table__.columns.keys()
        )
        return f"{self.__class__.__name__}({values})"



all_id = Annotated[int,mapped_column(primary_key=True,autoincrement=True)]
user_tg_id = Annotated[int, mapped_column(BigInteger)]
time_now = Annotated[datetime,mapped_column(server_default=func.now())]

class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    username: Mapped[str | None]
    full_name: Mapped[str]
    registered_at: Mapped[time_now]
    balance: Mapped[Decimal] = mapped_column(Numeric(10,2),default=Decimal('0.00'))

class Categories(Base):
    __tablename__ = 'categories'

    id: Mapped[all_id]
    name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)


class Items(Base):
    __tablename__ = 'items'

    id: Mapped[all_id]
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    title: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10,2))
    data: Mapped[str] = mapped_column(Text)
    is_sold: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[time_now]

class Orders(Base):
    __tablename__ = 'orders'

    id: Mapped[all_id]
    user_id: Mapped[user_tg_id] = mapped_column(ForeignKey('users.id'))
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'))
    price: Mapped[Decimal] = mapped_column(Numeric(10,2))
    purchased_at: Mapped[time_now]

class Payments(Base):
    __tablename__ = 'payments'

    id: Mapped[all_id]
    user_id: Mapped[user_tg_id] = mapped_column(BigInteger, ForeignKey('users.id'))
    amount: Mapped[Decimal] = mapped_column(Numeric(10,2))
    payment_system: Mapped[str]
    status: Mapped[str] = mapped_column(default='pending')
    created_at: Mapped[time_now]