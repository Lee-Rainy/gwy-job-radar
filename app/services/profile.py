from dataclasses import dataclass
import re

from app.config import Settings, get_settings
from app.database import Job


@dataclass(frozen=True)
class UserProfile:
    age: int
    education: str
    major: str
    candidate_status: str
    is_fresh_graduate: bool
    major_aliases: tuple[str, ...]
    major_related: tuple[str, ...]
    fresh_exclude_keywords: tuple[str, ...]
    fresh_include_keywords: tuple[str, ...]
    social_exclude_keywords: tuple[str, ...]
    job_include_keywords: tuple[str, ...]
    job_exclude_keywords: tuple[str, ...]
    enable_relaxed_major: bool


def profile_from_settings(settings: Settings) -> UserProfile:
    return UserProfile(
        age=settings.profile_age,
        education=settings.profile_education,
        major=settings.profile_major,
        candidate_status=settings.profile_candidate_status,
        is_fresh_graduate=settings.profile_is_fresh_graduate,
        major_aliases=tuple(settings.profile_major_aliases),
        major_related=tuple(settings.profile_major_related),
        fresh_exclude_keywords=tuple(settings.profile_fresh_exclude_keywords),
        fresh_include_keywords=tuple(settings.profile_fresh_include_keywords),
        social_exclude_keywords=tuple(settings.profile_social_exclude_keywords),
        job_include_keywords=tuple(settings.profile_job_include_keywords),
        job_exclude_keywords=tuple(settings.profile_job_exclude_keywords),
        enable_relaxed_major=settings.profile_enable_relaxed_major,
    )


def get_user_profile() -> UserProfile:
    return profile_from_settings(get_settings())


def job_matches_profile(job: Job, profile: UserProfile | None = None) -> bool:
    p = profile or get_user_profile()
    haystack = _job_haystack(job)
    if not haystack.strip():
        return False
    if not _keyword_include_exclude(haystack, p):
        return False
    if not _education_matches(haystack, p.education):
        return False
    if not _fresh_graduate_matches(haystack, p):
        return False
    if not _age_matches(haystack, p.age):
        return False
    if not _major_matches(haystack, p):
        return False
    return True


def _job_haystack(job: Job) -> str:
    return " ".join(
        filter(
            None,
            [
                job.education,
                job.degree,
                job.major,
                job.candidate_type,
                job.age_requirement,
                job.job_title,
                job.raw_data,
            ],
        )
    )


def _keyword_include_exclude(text: str, profile: UserProfile) -> bool:
    if profile.job_exclude_keywords and any(k in text for k in profile.job_exclude_keywords):
        return False
    if profile.job_include_keywords and not any(k in text for k in profile.job_include_keywords):
        return False
    return True


def _fresh_graduate_matches(text: str, profile: UserProfile) -> bool:
    if profile.is_fresh_graduate:
        if any(k in text for k in profile.social_exclude_keywords):
            return False
        if "社会人员" in text and "应届" not in text and "应往届" not in text and "不限" not in text:
            return False
        if "应届" in text or "毕业生" in text:
            return any(k in text for k in profile.fresh_include_keywords) or "不限" in text
        return True

    combined = list(profile.fresh_exclude_keywords)
    if profile.candidate_status in ("社会人员", "已毕业", "在职"):
        combined.extend(profile.social_exclude_keywords)
    if any(k in text for k in combined):
        return False
    if "社会人员" in text or "不限" in text or "应往届" in text:
        return True
    if "应届" not in text:
        return True
    return "非应届" in text or "社会" in text


def _education_matches(text: str, education: str) -> bool:
    if re.search(r"研究生|硕士|博士", text) and "本科" not in text and education == "本科":
        if re.search(r"本科及以上|学士及以上|大学本科及以上", text):
            return True
        return False
    if education in text:
        return True
    if education == "本科" and any(k in text for k in ("大学本科", "学士", "本科以上", "本科及以上学历")):
        return True
    return False


def _age_matches(text: str, age: int) -> bool:
    if not text or ("年龄" not in text and "周岁" not in text):
        return True
    for match in re.finditer(r"(\d{1,2})\s*周岁\s*以[下内]", text):
        if age > int(match.group(1)):
            return False
    for match in re.finditer(r"年龄.*?(\d{1,2})\s*周岁", text):
        if age > int(match.group(1)):
            return False
    return True


def _major_matches(text: str, profile: UserProfile) -> bool:
    major = profile.major
    if not major:
        return True
    if major in text:
        return True
    if "不限专业" in text or "专业不限" in text:
        return True
    for alias in profile.major_aliases:
        if alias in major and alias in text:
            return True
        if alias in text and alias in major:
            return True
    if profile.enable_relaxed_major and _major_matches_relaxed(text, profile):
        return True
    return False


def _major_matches_relaxed(text: str, profile: UserProfile) -> bool:
    if "不限专业" in text or "专业不限" in text:
        return True
    if "不限" in text and "专业" in text:
        return True
    major = profile.major
    return any(token in major for token in profile.major_related) and any(
        token in text for token in profile.major_related
    )
