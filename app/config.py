import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def resolve_env_files() -> tuple[str, ...]:
    """
    仅使用 .env.test（本地真实配置）或 ENV_FILE 指向的文件。
    .env.example 为模板，不会被自动加载。
    """
    override = os.getenv("ENV_FILE", "").strip()
    if override:
        path = Path(override)
        if path.is_file():
            return (str(path),)
    if Path(".env.test").is_file():
        return (".env.test",)
    return tuple()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=resolve_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg://radar:radar_secret@localhost:5432/gd_job_radar",
        alias="DATABASE_URL",
    )

    http_timeout_seconds: float = Field(default=30.0, alias="HTTP_TIMEOUT_SECONDS")
    http_user_agent: str = Field(
        default="gd-job-radar/0.1",
        alias="HTTP_USER_AGENT",
    )
    collector_rate_limit_seconds: float = Field(
        default=1.5,
        alias="COLLECTOR_RATE_LIMIT_SECONDS",
    )
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")

    target_cities_csv: str = Field(
        default="广州,东莞,佛山",
        alias="TARGET_CITIES",
    )

    scheduler_timezone: str = Field(default="Asia/Shanghai", alias="SCHEDULER_TIMEZONE")
    morning_digest_hour: int = Field(default=8, alias="MORNING_DIGEST_HOUR")
    morning_digest_minute: int = Field(default=0, alias="MORNING_DIGEST_MINUTE")
    evening_digest_hour: int = Field(default=18, alias="EVENING_DIGEST_HOUR")
    evening_digest_minute: int = Field(default=0, alias="EVENING_DIGEST_MINUTE")

    smtp_host: str = Field(default="smtp.qq.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=465, alias="SMTP_PORT")
    smtp_use_ssl: bool = Field(default=True, alias="SMTP_USE_SSL")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    mail_from: str = Field(default="", alias="MAIL_FROM")
    mail_recipients_csv: str = Field(default="", alias="MAIL_RECIPIENTS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: Path = Field(default=Path("./logs"), alias="LOG_DIR")

    collector_sources_csv: str = Field(default="", alias="COLLECTOR_SOURCES")
    run_job_on_start: bool = Field(default=False, alias="RUN_JOB_ON_START")

    profile_age: int = Field(default=25, alias="PROFILE_AGE")
    profile_education: str = Field(default="本科", alias="PROFILE_EDUCATION")
    profile_major: str = Field(default="信息管理与信息系统", alias="PROFILE_MAJOR")
    profile_candidate_status: str = Field(default="社会人员", alias="PROFILE_CANDIDATE_STATUS")
    profile_is_fresh_graduate: bool = Field(default=False, alias="PROFILE_IS_FRESH_GRADUATE")
    profile_major_aliases_csv: str = Field(
        default="信息管理,管理科学与工程,计算机,电子信息,软件工程",
        alias="PROFILE_MAJOR_ALIASES",
    )
    profile_major_related_csv: str = Field(
        default="计算机,软件,网络,数据,信息,管理,电子商务,统计",
        alias="PROFILE_MAJOR_RELATED_KEYWORDS",
    )
    profile_fresh_exclude_keywords_csv: str = Field(
        default="仅限应届,限应届,仅应届,应届毕业生报考,限应届毕业生",
        alias="PROFILE_FRESH_EXCLUDE_KEYWORDS",
    )
    profile_fresh_include_keywords_csv: str = Field(
        default="应届,应届毕业生,应往届",
        alias="PROFILE_FRESH_INCLUDE_KEYWORDS",
    )
    profile_social_exclude_keywords_csv: str = Field(
        default="仅限应届毕业生,仅面向应届",
        alias="PROFILE_SOCIAL_EXCLUDE_KEYWORDS",
    )
    profile_job_include_keywords_csv: str = Field(
        default="",
        alias="PROFILE_JOB_INCLUDE_KEYWORDS",
    )
    profile_job_exclude_keywords_csv: str = Field(
        default="",
        alias="PROFILE_JOB_EXCLUDE_KEYWORDS",
    )
    profile_enable_relaxed_major: bool = Field(default=True, alias="PROFILE_ENABLE_RELAXED_MAJOR")
    crawl_target_year: str = Field(default="2026", alias="CRAWL_TARGET_YEAR")

    @field_validator(
        "profile_is_fresh_graduate",
        "profile_enable_relaxed_major",
        mode="before",
    )
    @classmethod
    def parse_bool_fields(cls, value: object) -> bool:
        return _parse_bool(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def target_cities(self) -> list[str]:
        return _split_csv(self.target_cities_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mail_recipients(self) -> list[str]:
        return _split_csv(self.mail_recipients_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def collector_sources(self) -> list[str]:
        return _split_csv(self.collector_sources_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_major_aliases(self) -> list[str]:
        return _split_csv(self.profile_major_aliases_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_major_related(self) -> list[str]:
        return _split_csv(self.profile_major_related_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_fresh_exclude_keywords(self) -> list[str]:
        return _split_csv(self.profile_fresh_exclude_keywords_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_fresh_include_keywords(self) -> list[str]:
        return _split_csv(self.profile_fresh_include_keywords_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_social_exclude_keywords(self) -> list[str]:
        return _split_csv(self.profile_social_exclude_keywords_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_job_include_keywords(self) -> list[str]:
        return _split_csv(self.profile_job_include_keywords_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_job_exclude_keywords(self) -> list[str]:
        return _split_csv(self.profile_job_exclude_keywords_csv)


def _split_csv(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


# 公告状态
ANNOUNCEMENT_STATUS_ACTIVE = "正常"
ANNOUNCEMENT_STATUS_INACTIVE = "失效"
ANNOUNCEMENT_STATUS_PARSE_FAILED = "解析失败"

# 岗位类型
JOB_TYPE_CIVIL_SERVICE = "civil_service"
JOB_TYPE_PUBLIC_INSTITUTION = "public_institution"

# 邮件发送
DELIVERY_PERIOD_MORNING = "morning"
DELIVERY_PERIOD_EVENING = "evening"
DELIVERY_STATUS_PENDING = "pending"
DELIVERY_STATUS_SENT = "sent"
DELIVERY_STATUS_FAILED = "failed"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    """更换 ENV_FILE 后调用，避免 lru_cache 仍使用旧配置。"""
    get_settings.cache_clear()
    return get_settings()
