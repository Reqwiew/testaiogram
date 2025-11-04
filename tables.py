from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

from loader import engine

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger)
    username = Column("username", String)
    phone_number = Column("phone_number", String)
    tasks = relationship("Tasks", back_populates="user")



class Tasks(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column("task_name", String)
    description = Column("description", String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("Users", back_populates="tasks")





async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
