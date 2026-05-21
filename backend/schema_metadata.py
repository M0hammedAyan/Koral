"""SQLAlchemy metadata used by Alembic autogenerate."""

from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import BigInteger
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import ForeignKey

metadata = MetaData()

Table(
    "anomalies",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("timestamp", BigInteger),
    Column("pod", Text),
    Column("namespace", Text),
    Column("metric", Text),
    Column("value", Float),
    Column("unit", Text),
    Column("z_score", Float),
    Column("is_anomaly", Integer),
    Column("window_size", Integer),
    Column("source", Text),
    Column("created_at", Text),
)

Table(
    "incidents",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("incident_id", Text, unique=True),
    Column("timestamp", BigInteger),
    Column("namespace", Text),
    Column("severity", Text),
    Column("root_cause", Text),
    Column("summary", Text),
    Column("affected_pods", Text),
    Column("primary_metric", Text),
    Column("confidence", Float),
    Column("evidence_count", Integer),
    Column("created_at", Text),
    Column("ai_explanation", Text),
    Column("ai_action", Text),
    Column("ai_model", Text),
)

Table(
    "fix_history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("incident_id", Text, ForeignKey("incidents.incident_id")),
    Column("fix_type", Text),
    Column("fix_description", Text),
    Column("applied_by", Text),
    Column("success", Integer),
    Column("error_message", Text),
    Column("kubectl_command", Text),
    Column("timestamp", Text),
    Column("created_at", Text),
)

Table(
    "graph_nodes",
    metadata,
    Column("id", Text, primary_key=True),
    Column("label", Text),
    Column("status", Text),
)

Table(
    "graph_edges",
    metadata,
    Column("source", Text, primary_key=True),
    Column("target", Text, primary_key=True),
)

Table(
    "remediation_plans",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("plan_id", Text, unique=True),
    Column("incident_id", Text, ForeignKey("incidents.incident_id"), nullable=False),
    Column("severity", Text),
    Column("root_cause", Text),
    Column("recommended_action", Text),
    Column("confidence", Float),
    Column("affected_pods", Text),
    Column("parameters", Text),
    Column("ai_reasoning", Text),
    Column("status", Text),
    Column("created_at", Text),
    Column("expires_at", Text),
)

Table(
    "approval_history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("approval_id", Text, unique=True),
    Column("plan_id", Text, ForeignKey("remediation_plans.plan_id"), nullable=False),
    Column("incident_id", Text, ForeignKey("incidents.incident_id"), nullable=False),
    Column("requested_by", Text),
    Column("approved_by", Text),
    Column("approval_status", Text),
    Column("approval_reason", Text),
    Column("email_sent_at", Text),
    Column("email_opened_at", Text),
    Column("response_timestamp", Text),
    Column("created_at", Text),
)

Table(
    "execution_log",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("execution_id", Text, unique=True),
    Column("plan_id", Text, ForeignKey("remediation_plans.plan_id"), nullable=False),
    Column("incident_id", Text, ForeignKey("incidents.incident_id"), nullable=False),
    Column("command", Text),
    Column("parameters", Text),
    Column("execution_status", Text),
    Column("start_time", Text),
    Column("end_time", Text),
    Column("duration_ms", Integer),
    Column("stdout", Text),
    Column("stderr", Text),
    Column("exit_code", Integer),
    Column("blast_radius", Integer),
    Column("pod_failures", Text),
    Column("created_at", Text),
)

Table(
    "verification_results",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("verification_id", Text, unique=True),
    Column("execution_id", Text, ForeignKey("execution_log.execution_id"), nullable=False),
    Column("plan_id", Text, ForeignKey("remediation_plans.plan_id"), nullable=False),
    Column("incident_id", Text, ForeignKey("incidents.incident_id"), nullable=False),
    Column("verification_status", Text),
    Column("pre_metrics", Text),
    Column("post_metrics", Text),
    Column("improvement_percent", Float),
    Column("anomaly_resolved", Integer),
    Column("z_score_delta", Float),
    Column("verification_details", Text),
    Column("duration_ms", Integer),
    Column("created_at", Text),
)

# Foundation tables requested for migration validation.
Table(
    "feedback",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("incident_id", Text),
    Column("metric", Text),
    Column("is_correct", Integer),
    Column("old_threshold", Float),
    Column("new_threshold", Float),
    Column("created_at", Text),
)

Table(
    "audit",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_type", String(128)),
    Column("actor", String(128)),
    Column("target", String(128)),
    Column("payload", Text),
    Column("created_at", Text),
)

Table(
    "remediation",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("incident_id", Text),
    Column("action", Text),
    Column("status", String(64)),
    Column("created_at", Text),
)
