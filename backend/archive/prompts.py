from backend.trends.models import TrendResult

PROMPT_VERSION = "archive-editorial-v1"


def build_archive_metadata_prompt(trend: TrendResult) -> str:
    companies = ", ".join(trend.early_mover_companies) if trend.early_mover_companies else "unattributed companies"
    return f"""
You are writing structured editorial metadata for Job Title Archaeology, a visual archive of emerging job titles.
Return only valid JSON. Do not use markdown. Do not include extra keys.

Job title: {trend.display_title}
Recent postings: {trend.recent_count}
Prior postings: {trend.prior_count}
Trend score: {trend.trend_score:.2f}
Velocity score: {trend.scores.velocity:.2f}
Early mover companies: {companies}

JSON schema:
{{
  "category": "one concise archive category, e.g. Tech / Automation, FINANCE, HEALTHCARE, MANUFACTURING, PUBLIC SECTOR",
  "sector": "one sector label, e.g. Technology, Financial Services, Healthcare, Manufacturing, Public Sector, Other",
  "lead_paragraph": "35-45 words, one paragraph, publication style, no bullet points",
  "pull_quote": "12-18 words, quotable sentence, no quotation marks",
  "preceding_titles": ["exactly 3 earlier job titles this role likely evolved from"],
  "competencies": ["exactly 4 short competency phrases"],
  "outlook": "25-35 words, one sentence about likely adoption trajectory"
}}

Style constraints:
- Sound like an archival magazine note, not marketing copy.
- Base claims only on the title, counts, velocity, and companies above.
- Keep language concrete enough for a frontend card.
""".strip()
