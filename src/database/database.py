import abc
import typing

from loguru import logger
from psycopg_pool import AsyncConnectionPool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import DBNAME, HOST, PASSWORD, PORT, USER
from database.models import AsyncSessionLocal, Base, engine


class DBConnect(abc.ABC):
    @staticmethod
    def get_conn() -> typing.Any:
        pass


class DBTablesCreator(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    async def create(*args, **kwargs) -> None:
        pass


class DBFillTable(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    async def fill(*args, **kwargs) -> None:
        pass


class DBCRUD(abc.ABC):
    pass


@typing.final
class PostgreConnect(DBConnect):
    @staticmethod
    async def get_alchemy_conn() -> AsyncSession:
        connection = AsyncSessionLocal()

        return connection

    @staticmethod
    async def get_async_pool():

        logger.info(f"trying to connect with {DBNAME}\t{USER}\t{HOST}\t{PORT}")
        pool = AsyncConnectionPool(
            conninfo=f"""
            dbname={DBNAME}
            user={USER}
            password={PASSWORD}
            host={HOST}
            port={PORT}
            sslmode=disable
            gssencmode=disable""",
            min_size=4,
            max_size=10,
        )

        logger.info("Succes connected")

        return pool


@typing.final
class PostgreDBTablesCreation(DBTablesCreator):
    @staticmethod
    async def create() -> None:
        try:
            logger.info("Creating the tables")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                #
                logger.info("Tables created")
                await conn.commit()
                await conn.close()

        except Exception as e:
            logger.exception("Problem with creating tables", e)


@typing.final
class PostgreFillTablesCreation(DBFillTable):
    @staticmethod
    async def fill(to_insert: list) -> None:
        try:
            for one_group in to_insert:
                one_group.append(False)

            async with engine.begin() as conn:
                await conn.execute(
                    text("""
                        INSERT INTO all_groups(group_id, group_name, faculty_id, course, in_use)
                        VALUES (:group_id, :group_name, :faculty_id, :course, :in_use)
                    """),
                    [
                        {
                            "group_id": row[0],
                            "group_name": row[1],
                            "faculty_id": row[2],
                            "course": row[3],
                            "in_use": row[4],
                        }
                        for row in to_insert
                    ],
                )

                await conn.commit()
                await conn.close()

        except Exception as e:
            logger.opt(exception=e).critical("Cant fill the tables")
