"""
Realistic enterprise tool datasets and query suites for ToolRx benchmarking.
Includes 50, 100, and 500 tool catalogs across CRM, Cloud, SQL, Payment, and Messaging domains.
"""

from typing import List, Dict, Any

CORE_DOMAINS = [
    {
        "domain": "stripe_payments",
        "templates": [
            ("create_payment_intent", "Create a new Stripe payment intent with amount, currency, and customer.", ["amount", "currency", "customer_id"]),
            ("refund_charge", "Issue a full or partial refund for a specific charge or payment intent.", ["charge_id", "amount", "reason"]),
            ("cancel_subscription", "Immediately or period-end cancel a recurring customer subscription.", ["subscription_id", "at_period_end"]),
            ("create_invoice", "Draft a new customer invoice with line items, tax rates, and due date.", ["customer_id", "due_date", "items"]),
            ("retrieve_balance", "Retrieve current available and pending account balances across currencies.", ["currency"]),
        ]
    },
    {
        "domain": "database_sql",
        "templates": [
            ("execute_sql_query", "Run a read-only SQL query against the production analytical database.", ["query", "database", "timeout_sec"]),
            ("explain_query_plan", "Analyze execution plan and bottleneck costs for an index or SQL query.", ["query", "analyze"]),
            ("list_table_schemas", "List tables, column definitions, types, and foreign keys in database.", ["database", "schema_name"]),
            ("fetch_table_row_count", "Get row count estimates and table storage stats from information schema.", ["table_name"]),
            ("invalidate_redis_cache", "Evict specific key patterns or cache namespaces from Redis cluster.", ["pattern", "ttl"]),
        ]
    },
    {
        "domain": "crm_salesforce",
        "templates": [
            ("search_crm_contacts", "Search CRM contacts by email, phone, name, or company domain.", ["query", "limit", "email"]),
            ("update_lead_stage", "Update sales pipeline stage for a lead (MQL, SQL, Opportunity, Closed).", ["lead_id", "stage", "notes"]),
            ("log_customer_call", "Record details, sentiment, and follow-up tasks from a client call.", ["contact_id", "summary", "duration"]),
            ("create_deal_opportunity", "Create a new sales opportunity with deal value, stage, and close date.", ["account_id", "amount", "stage"]),
            ("export_pipeline_report", "Generate CSV export of quarterly revenue pipeline by sales rep.", ["quarter", "year", "rep_id"]),
        ]
    },
    {
        "domain": "cloud_infrastructure",
        "templates": [
            ("restart_kubernetes_pod", "Perform a rolling restart of pods in a deployment namespace.", ["deployment", "namespace"]),
            ("fetch_cloudwatch_metrics", "Query CPU, memory, error rates, and p99 latency from CloudWatch.", ["metric_name", "dimension", "timeframe"]),
            ("rotate_iam_access_key", "Deactivate old AWS IAM access key and generate a new keypair.", ["user_name", "key_id"]),
            ("scale_container_cluster", "Update replica count for worker autoscaling node group.", ["cluster_name", "desired_replicas"]),
            ("purge_cloudflare_cache", "Purge CDN cache tags or specific URLs across global edge.", ["zone_id", "urls", "tags"]),
        ]
    },
    {
        "domain": "communication_email",
        "templates": [
            ("send_transactional_email", "Send transactional template email to user with dynamic variables.", ["recipient", "template_id", "data"]),
            ("post_slack_alert", "Post rich formatted alert message into internal Ops Slack channel.", ["channel", "message", "severity"]),
            ("schedule_calendar_event", "Schedule a meeting with attendees, calendar invites, and video link.", ["title", "start_time", "attendees"]),
            ("search_support_tickets", "Search Zendesk customer tickets by requester email or keyword.", ["query", "status", "priority"]),
            ("resolve_ticket", "Close or resolve a customer support ticket with internal resolution note.", ["ticket_id", "resolution_note"]),
        ]
    }
]

def generate_tool_catalog(count: int = 50) -> List[Dict[str, Any]]:
    """Generate realistic tool catalog of size 50, 100, or 500."""
    tools = []
    generated = 0
    multiplier = (count // 25) + 2

    for cycle in range(multiplier):
        for domain_idx, group in enumerate(CORE_DOMAINS):
            domain_name = group["domain"]
            for name, desc, params in group["templates"]:
                if generated >= count:
                    return tools
                tool_name = f"{name}_{cycle}" if cycle > 0 else name
                properties = {p: {"type": "string", "description": f"The {p} parameter"} for p in params}
                tools.append({
                    "name": tool_name,
                    "description": f"{desc} (Domain: {domain_name})",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": [params[0]] if params else []
                    },
                    "tags": [domain_name, name.split("_")[0]]
                })
                generated += 1
    return tools

BENCHMARK_QUERIES = [
    {
        "query": "Can you issue a refund for charge ch_3MbwQ2Lkd81 for $45.00 due to duplicate billing?",
        "expected_tool": "refund_charge",
        "domain": "payments"
    },
    {
        "query": "SELECT count(*) FROM user_orders WHERE created_at > '2026-01-01';",
        "expected_tool": "execute_sql_query",
        "domain": "database"
    },
    {
        "query": "Look up the contact details and sales stage for client alice@acmecorp.com",
        "expected_tool": "search_crm_contacts",
        "domain": "crm"
    },
    {
        "query": "Kubernetes pods in deployment 'auth-service' in namespace 'prod' are crashing, restart them",
        "expected_tool": "restart_kubernetes_pod",
        "domain": "cloud"
    },
    {
        "query": "Send an email to john.doe@company.com with the welcome template",
        "expected_tool": "send_transactional_email",
        "domain": "email"
    },
    {
        "query": "Purge the CDN cache for https://cdn.example.com/assets/app.js",
        "expected_tool": "purge_cloudflare_cache",
        "domain": "cloud"
    },
    {
        "query": "Cancel the subscription sub_99812 immediately without waiting for billing cycle",
        "expected_tool": "cancel_subscription",
        "domain": "payments"
    },
    {
        "query": "Explain the query plan and index usage for the slow query on table transactions",
        "expected_tool": "explain_query_plan",
        "domain": "database"
    },
    {
        "query": "Post a high severity alert message to #incident-room about database latency spikes",
        "expected_tool": "post_slack_alert",
        "domain": "slack"
    },
    {
        "query": "Create a new sales opportunity for account_883 valued at $50,000 closing this quarter",
        "expected_tool": "create_deal_opportunity",
        "domain": "crm"
    }
]
