from sqlalchemy.sql.functions import grouping_sets
from config import DBNAME, USER, PASSWORD, HOST, PORT

from sqlalchemy import BigInteger, Nullable, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import DATABASE_URL



engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)



#DeclarativeBase in Alchemy 2.0+ is abc class, so we cant use it directly
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    db_id:   Mapped   [int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped   [int] = mapped_column(BigInteger, unique=True, nullable=False)
    course:  Mapped   [int] = mapped_column(nullable=False) 
    faculty: Mapped   [str] = mapped_column(nullable=False)
    group_id: Mapped  [int] = mapped_column(nullable=False)
    last_time_active: Mapped[str] = mapped_column()


