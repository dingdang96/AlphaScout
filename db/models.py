from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, BigInteger, Float, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from config import settings

engine = create_async_engine(settings.DB_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class Project(Base):
    """Web3 项目基础表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rootdata_id = Column(String(100), unique=True, index=True)
    name = Column(String(200), nullable=False)
    financing_amount = Column(String(100), default="未披露")
    website_url = Column(String(500))
    twitter_handle = Column(String(100), index=True)
    discord_url = Column(String(500))
    has_token = Column(Boolean, default=False, index=True)  # 是否已发币
    token_symbol = Column(String(50))
    alpha_score = Column(Float, default=0.0, index=True)  # Alpha 匹配得分
    is_priority = Column(Boolean, default=False, index=True)  # 是否标记为重点跟踪
    matched_traits = Column(JSON, nullable=True)  # 匹配到的 Golden Traits 标签
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    monitored_account = relationship("MonitoredAccount", back_populates="project", uselist=False)


class MonitoredAccount(Base):
    """X (Twitter) 账号监控表"""
    __tablename__ = "monitored_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    twitter_handle = Column(String(100), unique=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    source_type = Column(String(50), default="ROOTDATA")
    last_tweet_id = Column(BigInteger, default=0)  # 增量游标
    is_active = Column(Boolean, default=True, index=True)  # 仅未发币且激活状态抓取
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="monitored_account")


class CapturedTweet(Base):
    """抓取到的推文记录"""
    __tablename__ = "captured_tweets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(BigInteger, unique=True, index=True)
    twitter_handle = Column(String(100), index=True)
    content = Column(Text, nullable=False)
    category = Column(String(50))  # AIRDROP, QUEST, ROADMAP, GENERAL
    importance = Column(Integer, default=1)  # 1 - 5 重要程度
    summary_cn = Column(Text)  # LLM 中文摘要
    pushed = Column(Boolean, default=False)  # 推送状态
    tweet_created_at = Column(DateTime)
    captured_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
