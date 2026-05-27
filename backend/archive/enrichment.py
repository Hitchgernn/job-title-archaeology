import re
from dataclasses import dataclass

from backend.archive.models import AdoptionPoint, ArchiveRecord, DossierResponse, EarlyAdopter, SectorDensity
from backend.trends.models import TrendResult


@dataclass(frozen=True)
class EditorialMetadata:
    category: str
    sector: str
    lead_paragraph: str
    pull_quote: str
    preceding_titles: tuple[str, ...]
    competencies: tuple[str, ...]
    outlook: str


CURATED_METADATA: dict[str, EditorialMetadata] = {
    "AI Workflow Architect": EditorialMetadata(
        category="Tech / Automation",
        sector="Technology",
        lead_paragraph=(
            "Workflow architecture is turning from informal automation work into a named operating discipline. "
            "The title appears where companies need someone to connect AI tools, business processes, and measurable delivery."
        ),
        pull_quote="Workflow architecture is becoming a formal operating layer between strategy and automation.",
        preceding_titles=("AI Program Manager", "Automation Architect", "Business Process Lead"),
        competencies=("Workflow design", "AI tool evaluation", "Process instrumentation", "Change management"),
        outlook="Expect this role to move closer to operations leadership as companies standardize AI-assisted work across teams.",
    ),
    "Agent Operations Lead": EditorialMetadata(
        category="Tech / Operations",
        sector="Technology",
        lead_paragraph=(
            "Agent operations roles appear when prototypes become recurring production systems. "
            "The work is less about model invention and more about supervising reliability, handoffs, and operating controls."
        ),
        pull_quote="Agent operations signals the moment autonomous workflows become infrastructure instead of experiments.",
        preceding_titles=("Operations Manager", "Automation Lead", "AI Program Manager"),
        competencies=("Runbook design", "Agent monitoring", "Escalation policy", "Process QA"),
        outlook="The title should consolidate around teams running AI agents for customer operations, finance, and internal support.",
    ),
    "LLM Reliability Engineer": EditorialMetadata(
        category="Tech / Reliability",
        sector="Technology",
        lead_paragraph=(
            "Reliability language is moving into applied AI job titles as teams confront hallucination, latency, and evaluation drift. "
            "The title borrows from site reliability engineering but points it at model-dependent systems."
        ),
        pull_quote="The reliability problem has moved from servers alone to the behavior of language systems in production.",
        preceding_titles=("Site Reliability Engineer", "ML Engineer", "Platform Engineer"),
        competencies=("Evaluation harnesses", "Incident analysis", "Latency tracing", "Model monitoring"),
        outlook="The role is likely to remain technical and high-signal while AI features enter core production paths.",
    ),
    "Climate Risk Modeler": EditorialMetadata(
        category="FINANCE",
        sector="Financial Services",
        lead_paragraph=(
            "Climate risk modeling is shifting from research desks into operating finance teams. "
            "The title appears where lenders and asset managers need quantifiable exposure views across portfolios."
        ),
        pull_quote="Climate risk is becoming a balance-sheet discipline, not a sustainability side report.",
        preceding_titles=("Risk Analyst", "ESG Analyst", "Quantitative Modeler"),
        competencies=("Scenario modeling", "Portfolio analytics", "Regulatory reporting", "Climate data interpretation"),
        outlook="Expect the title to spread as insurers, banks, and asset managers operationalize climate stress testing.",
    ),
    "Digital Asset Compliance Lead": EditorialMetadata(
        category="FINANCE",
        sector="Financial Services",
        lead_paragraph=(
            "Digital asset compliance roles signal that crypto exposure is moving from experimental desks into formal control environments. "
            "The title appears where firms need policy ownership across custody, reporting, and transaction monitoring."
        ),
        pull_quote="Digital assets become enterprise activity when compliance gets a named owner.",
        preceding_titles=("Compliance Manager", "Financial Crimes Analyst", "Digital Assets Associate"),
        competencies=("Regulatory analysis", "Transaction monitoring", "Custody controls", "Policy design"),
        outlook="The role should grow where institutions keep crypto products while regulators demand clearer accountability.",
    ),
    "Clinical AI Safety Officer": EditorialMetadata(
        category="HEALTHCARE",
        sector="Healthcare",
        lead_paragraph=(
            "Clinical AI safety is emerging as hospitals move model-assisted workflows closer to patient care. "
            "The title marks a need for accountable review of errors, escalation paths, and clinical governance."
        ),
        pull_quote="Clinical AI adoption becomes credible only when safety has an operational owner.",
        preceding_titles=("Clinical Safety Officer", "Health Informatics Lead", "AI Governance Manager"),
        competencies=("Clinical risk review", "Model evaluation", "Patient safety policy", "Workflow governance"),
        outlook="Expect this role to appear first in health systems deploying AI triage, documentation, and care navigation tools.",
    ),
    "Virtual Care Operations Manager": EditorialMetadata(
        category="HEALTHCARE",
        sector="Healthcare",
        lead_paragraph=(
            "Virtual care operations roles reflect telehealth moving from emergency adoption to durable delivery model. "
            "The title appears where providers need to coordinate staffing, tooling, patient routing, and service quality."
        ),
        pull_quote="Virtual care is becoming an operating model rather than a channel experiment.",
        preceding_titles=("Clinic Operations Manager", "Telehealth Coordinator", "Patient Access Manager"),
        competencies=("Capacity planning", "Patient routing", "Care team coordination", "Service quality analytics"),
        outlook="The title should persist as health systems blend in-person, remote, and asynchronous care delivery.",
    ),
    "Robotics Fleet Coordinator": EditorialMetadata(
        category="MANUFACTURING",
        sector="Manufacturing",
        lead_paragraph=(
            "Robotics fleet coordination appears when automation moves from isolated cells to distributed operating assets. "
            "The title signals a need to schedule, monitor, and maintain robot fleets like production infrastructure."
        ),
        pull_quote="Factories are beginning to manage robots as fleets, not machines.",
        preceding_titles=("Maintenance Planner", "Automation Technician", "Production Coordinator"),
        competencies=("Fleet monitoring", "Maintenance scheduling", "Production planning", "Robotics vendor coordination"),
        outlook="Expect the role to grow in warehouses, factories, and logistics networks scaling autonomous equipment.",
    ),
    "Supply Chain Resilience Planner": EditorialMetadata(
        category="MANUFACTURING",
        sector="Manufacturing",
        lead_paragraph=(
            "Supply chain resilience planning titles show companies formalizing disruption readiness after years of volatile logistics. "
            "The work blends scenario planning, supplier visibility, and contingency design."
        ),
        pull_quote="Resilience is becoming a planned capability, not a crisis response.",
        preceding_titles=("Supply Chain Analyst", "Demand Planner", "Operations Planner"),
        competencies=("Scenario planning", "Supplier risk analysis", "Inventory strategy", "Logistics analytics"),
        outlook="The title should remain relevant as manufacturers diversify suppliers and regionalize critical operations.",
    ),
    "Algorithmic Accountability Officer": EditorialMetadata(
        category="PUBLIC SECTOR",
        sector="Public Sector",
        lead_paragraph=(
            "Algorithmic accountability roles emerge as public agencies and regulated institutions face scrutiny over automated decisions. "
            "The title points to governance work around audits, appeals, documentation, and public trust."
        ),
        pull_quote="Algorithmic systems enter public life only after accountability becomes a job, not a principle.",
        preceding_titles=("Policy Analyst", "Data Governance Lead", "Compliance Officer"),
        competencies=("Algorithm audit", "Public policy analysis", "Documentation standards", "Stakeholder review"),
        outlook="Expect demand to rise where governments and vendors deploy AI in benefits, hiring, licensing, and enforcement workflows.",
    ),
}


def stable_record_id(rank: int, title: str) -> str:
    slug = re.sub(r"[^A-Z0-9]+", "-", title.upper()).strip("-")
    return f"JTA-{rank:04d}-{slug}"


def _metadata_for(title: str) -> EditorialMetadata:
    return CURATED_METADATA.get(
        title,
        EditorialMetadata(
            category="Tech / Operations",
            sector="Technology",
            lead_paragraph=(
                f"{title} is appearing as companies translate emerging technical pressure into named operating responsibility. "
                "The title is early, but the pattern suggests a search for ownership around new tools and workflows."
            ),
            pull_quote=f"{title} marks a shift from informal experimentation to accountable organizational practice.",
            preceding_titles=("Program Manager", "Operations Lead", "Technology Strategist"),
            competencies=("Signal analysis", "Operational design", "Vendor evaluation", "Stakeholder coordination"),
            outlook="If adoption spreads beyond early movers, this title may become a durable layer in operating teams.",
        ),
    )


def _velocity_label(trend: TrendResult) -> str:
    if trend.scores.velocity >= 0.85:
        tier = "High"
    elif trend.scores.velocity >= 0.65:
        tier = "Rising"
    else:
        tier = "Emerging"
    return f"{tier} · {round(trend.scores.velocity * 100)}% growth index"


def _adoption_points(trend: TrendResult) -> list[AdoptionPoint]:
    start = max(trend.prior_count, 1)
    midpoint = max(start + 1, round((trend.recent_count + start) / 2))
    return [
        AdoptionPoint(label="Prior window", value=start),
        AdoptionPoint(label="Early signal", value=midpoint),
        AdoptionPoint(label="Current edition", value=max(trend.recent_count, midpoint), annotation="Bright Data peak"),
    ]


def _sector_density(metadata: EditorialMetadata) -> list[SectorDensity]:
    return [
        SectorDensity(sector=metadata.sector, percentage=45),
        SectorDensity(sector="Financial Services", percentage=22),
        SectorDensity(sector="Healthcare", percentage=14),
        SectorDensity(sector="Public Sector", percentage=11),
        SectorDensity(sector="Other", percentage=8),
    ]


def _early_adopters(trend: TrendResult) -> list[EarlyAdopter]:
    companies = trend.early_mover_companies or ["Unattributed early mover"]
    labels = ["MAY 2026", "JUNE 2026", "JULY 2026", "AUGUST 2026", "SEPTEMBER 2026"]
    locations = ["San Francisco, CA", "New York, NY", "London, UK", "Singapore", "Remote"]
    return [
        EarlyAdopter(company=company, date_label=labels[index % len(labels)], location_label=locations[index % len(locations)])
        for index, company in enumerate(companies[:5])
    ]


def build_record_metadata(trend: TrendResult, rank: int) -> ArchiveRecord:
    metadata = _metadata_for(trend.display_title)
    return ArchiveRecord(
        record_id=stable_record_id(rank, trend.display_title),
        title=trend.display_title,
        category=metadata.category,
        first_seen_label="May 2026 · Bright Data Corpus",
        velocity_label=_velocity_label(trend),
        score=trend.trend_score,
        recent_count=trend.recent_count,
        prior_count=trend.prior_count,
        early_mover_companies=trend.early_mover_companies,
        excerpt=metadata.lead_paragraph.split(". ", 1)[0] + ".",
    )


def build_dossier_metadata(trend: TrendResult, rank: int) -> DossierResponse:
    metadata = _metadata_for(trend.display_title)
    record = build_record_metadata(trend, rank)
    return DossierResponse(
        **record.model_dump(),
        subheadline=f"First detected in {metadata.sector} · {len(trend.early_mover_companies)} companies found in the Bright Data corpus",
        lead_paragraph=metadata.lead_paragraph,
        pull_quote=metadata.pull_quote,
        adoption_points=_adoption_points(trend),
        sector_density=_sector_density(metadata),
        early_adopters=_early_adopters(trend),
        preceding_titles=list(metadata.preceding_titles),
        competencies=list(metadata.competencies),
        outlook=metadata.outlook,
    )
