from sqlalchemy.sql.functions import grouping_sets
from config import DBNAME, USER, PASSWORD, HOST, PORT

from sqlalchemy import BigInteger, ForeignKey, Nullable, String, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedSQLExpression, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import typing
from config import DATABASE_URL



engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def close_db() -> None:
    await engine.dispose()


#DeclarativeBase in Alchemy 2.0+ is abc class, so we cant use it directly
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    db_id:            Mapped [int] = mapped_column(primary_key=True, autoincrement=True)
    user_id:          Mapped [int] = mapped_column(BigInteger, unique=True, nullable=False)
    course:           Mapped [int] = mapped_column(nullable=False) 
    faculty:          Mapped [str] = mapped_column(nullable=False)
    group_id:         Mapped [int] = mapped_column(ForeignKey('all_groups.group_id'), nullable=False)
    last_time_active: Mapped [str] = mapped_column()


class Schedule(Base):
    __tablename__ = "schedule"

    db_id:                Mapped   [int] = mapped_column(primary_key=True, autoincrement=True)
    group_id:             Mapped   [int] = mapped_column(nullable=False)
    week_num:             Mapped   [int] = mapped_column(nullable=False)
    schedule_json:        Mapped   [list[typing.Any]] = mapped_column(JSON, nullable=False)
    to_compare:           Mapped   [str] = mapped_column(nullable=False)
    last_updated:         Mapped   [int] = mapped_column(nullable=False) 
    last_updated_formated:  Mapped   [str] = mapped_column(nullable=False)


class Group(Base):
    __tablename__ = "all_groups"
    
    db_id:       Mapped   [int]  = mapped_column(primary_key=True, autoincrement=True)
    group_id:    Mapped   [int]  = mapped_column(BigInteger, unique=True, nullable=False)
    group_name:  Mapped   [str]  = mapped_column(nullable=False)
    faculty_id:  Mapped   [int]  = mapped_column(nullable=False)
    course:      Mapped   [int]  = mapped_column(nullable=False) 
    in_use:      Mapped   [bool] = mapped_column(nullable=False)



