# ToolRx Commercial Monetization & Pricing Tiers

ToolRx operates on a **dual-licensing and hosted gateway monetization model**. 

---

## 1. Plan Overview

| Tier | Price | Deployment | Request Allowance | Support & SLA | Licensing |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Community / Developer** | **$0 / mo** | Self-Hosted | Up to 100k req/mo | Community GitHub Issues | BSL 1.1 |
| **Hosted API Pro** | **$99 / mo** + $0.05 / 10k req | Managed Cloud Edge | 500k req/mo included | Standard Email (24h) | Managed SaaS |
| **Enterprise Core** | **$999 / mo** (billed annually) | Self-Hosted / VPC / Airgapped | Unlimited requests | Priority 4h SLA, Slack | Commercial Proprietary |
| **Platform OEM / Custom** | **$3,500+ / mo** | Embedded Binary / OEM | Unlimited seats & apps | Dedicated Engineer, 1h SLA | Full Commercial OEM |

---

## 2. ROI & Value Proposition Breakdown

### The Problem: Massive Token Bloat in Multi-Tool Agents
Every modern agent framework (OpenAI Assistant, LangGraph, CrewAI, AutoGen) sends the entire catalog of tools in every prompt turn.
- A production catalog of **100 tools** consumes **~11,000 prompt tokens** per turn.
- At GPT-4o input rates ($2.50 per 1M tokens), each turn costs **$0.0275** purely for tool definitions.
- At 10,000,000 agent turns per month:
  $$\text{Raw LLM Tool Definition Cost} = 10,000,000 \times \$0.0275 = \mathbf{\$275,000\text{ / month}}$$

### The Solution: ToolRx Deterministic Pruning
ToolRx intercepts the query and dynamically prunes the 100 tools down to the exact **top 3 relevant tools** in **< 1 millisecond** (zero LLM calls).
- 3 tools consume only **~340 prompt tokens**.
- At 10,000,000 turns:
  $$\text{ToolRx Routed LLM Cost} = 10,000,000 \times \$0.00085 = \mathbf{\$8,500\text{ / month}}$$

### Customer Net Savings
- **Gross Monthly LLM Savings**: **$266,500 / month** ($3.19 Million / year)
- **ToolRx Enterprise Cost**: **$999 / month**
- **Net Customer Savings**: **$265,501 / month**
- **Immediate Customer ROI**: **266x Return on Investment**
- **Bonus Benefit**: Time-To-First-Token (TTFT) drops by **40% to 70%** because the LLM processes 97% fewer input tokens.

---

## 3. Product Offerings

### Product A: ToolRx Hosted Edge Gateway
- Global, low-latency edge deployment across 300+ PoPs (Cloudflare Workers / AWS Edge).
- Drop-in API endpoint:
  ```http
  POST https://api.toolrx.io/v1/route
  Authorization: Bearer trx_live_...
  ```
- Transparent OpenAI proxy endpoint:
  ```http
  POST https://api.toolrx.io/v1/chat/completions
  ```
- Automated usage telemetry, live token savings tracking, and Stripe billing integration.

### Product B: ToolRx Enterprise VPC / On-Prem Package
- Zero-external-network requirement for airgapped environments (DoD, HIPAA healthcare, FinTech).
- Native C/Rust accelerator extension compilation for sub-50 microsecond execution.
- IP indemnification and SOC2 Type II audit report access.
- Commercial dual-license clearing all AGPL/BSL obligations.
