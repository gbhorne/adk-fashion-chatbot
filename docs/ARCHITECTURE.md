# Architecture: ADK Fashion Shopping Chatbot

## System Overview

A multi-agent conversational shopping assistant using Google ADK's `transfer_to_agent` routing pattern. One root orchestrator delegates to three specialist agents, each with focused BigQuery tools.

## Pipeline Flow

| Step | Component | Action | Output |
|------|-----------|--------|--------|
| 1 | Customer | Types natural language message | "I need a red evening dress" |
| 2 | `shopping_orchestrator` | Detects search intent | Routes to `product_finder` |
| 3 | `product_finder` | Calls `search_products(category="dress", color="red", occasion="evening")` | BigQuery results |
| 4 | `product_finder` | If no results, broadens search (drops least critical filter) | Wider results |
| 5 | `product_finder` | Formats results conversationally | Response with names, prices, ratings |
| 6 | Customer | Refines: "What about accessories?" | New intent detected |
| 7 | `shopping_orchestrator` | Detects styling intent | Routes to `style_advisor` |
| 8 | `style_advisor` | Calls `suggest_accessories(product_id)` | Matching accessories with reasoning |

## Architecture Decision Records (ADRs)

### ADR-1: Multi-Agent Specialist Pattern over Monolithic Agent

**Context:** We could build one agent with all 11 tools, or split into specialists.

**Decision:** Three specialist agents (product_finder, style_advisor, availability_checker) under a root orchestrator.

**Rationale:**
- Focused tool sets reduce hallucination — each agent only sees tools relevant to its role
- Agent instructions are shorter and more specific, improving response quality
- Parallel execution possible (ADK can run sub-agents concurrently)
- Same proven pattern from adk-retail-agents project (100% routing accuracy verified)

**Tradeoff:** Slightly more complex agent configuration, but routing overhead is negligible.

### ADR-2: Fixed SQL with Parameters over Text-to-SQL

**Context:** We could let Gemini generate SQL dynamically or use parameterized fixed queries.

**Decision:** All 11 tools use hand-written SQL with Python string formatting for parameters.

**Rationale:**
- Security: No SQL injection risk — parameters are constrained to known values
- Reliability: Fixed SQL always returns predictable schemas
- Cost: No extra LLM calls to generate SQL
- Debuggability: Every query is visible in tools.py, easy to test independently

**Tradeoff:** Adding new query patterns requires code changes (not just a prompt update). Acceptable for a POC with a stable schema.

### ADR-3: Single Denormalized Table over Normalized Schema

**Context:** Traditional relational design would use separate tables for products, sizes, tags, brands, etc.

**Decision:** One `product_catalog` table with 22 columns including ARRAY columns for `size_available` and `tags`.

**Rationale:**
- BigQuery is columnar — it only reads columns referenced in a query, so wide tables have minimal overhead
- ARRAY columns with UNNEST eliminate join tables (`WHERE "backless" IN UNNEST(tags)`)
- No joins means simpler SQL in tools and faster query execution
- 300 products is tiny for BigQuery — no performance concern

**Tradeoff:** Data duplication (brand name stored as string per row, not as FK). Negligible at this scale.

### ADR-4: AI Studio Free Tier over Vertex AI

**Context:** Gemini 2.5 Flash is available through both AI Studio (free tier) and Vertex AI (paid).

**Decision:** AI Studio with `GOOGLE_API_KEY` environment variable.

**Rationale:**
- $0 cost — sufficient for POC development and testing
- Same model quality — Gemini 2.5 Flash is identical on both platforms
- Simpler authentication — API key vs. service account + `aiplatform.googleapis.com`
- Works in sandbox environments where `aiplatform.googleapis.com` may be blocked

**Tradeoff:** Rate limits on free tier (5-15 RPM). Not suitable for production traffic, but fine for development and portfolio demonstration.

### ADR-5: Automatic Search Broadening Strategy

**Context:** With 300 products, exact multi-filter matches can be sparse (e.g., only 1 red evening dress).

**Decision:** Agent instructions direct the product_finder to broaden searches when no results are found by dropping the least critical filter and explaining the change to the customer.

**Rationale:**
- Better customer experience than "no results found"
- Transparent — agent tells the customer what it changed ("I removed the 'flowy' filter")
- Progressive disclosure — start narrow, widen if needed
- Mimics how a real personal shopper would operate

**Tradeoff:** May occasionally show less relevant results. Mitigated by the agent explaining the broadened criteria.

### ADR-6: Dict Return Format with Status Field

**Context:** Tools need a consistent return format that agents can interpret.

**Decision:** All tools return `{"status": "success|no_results|error", "count": N, "data": [...]}`.

**Rationale:**
- Same pattern proven in adk-retail-agents (100% tool selection accuracy)
- Agents can branch on `status` without parsing raw data
- `count` field helps agents decide how to present results (1 item vs. 10)
- `error` status with message enables graceful error handling

**Tradeoff:** Slightly verbose for single-item lookups. Consistency outweighs the overhead.

## Data Architecture

### BigQuery Schema

```
fashion_store.product_catalog (22 columns)
├── Identifiers: product_id, product_name
├── Classification: category, subcategory, style, occasion, season
├── Appearance: color_primary, color_secondary, fabric
├── Sizing: size_available (ARRAY<STRING>)
├── Pricing: price, price_tier
├── Metadata: brand, description, image_url, tags (ARRAY<STRING>)
├── Reviews: rating, review_count
├── Inventory: in_stock, stock_quantity
└── Timestamps: created_at
```

### Data Distribution

- 300 products: 80 dresses, 55 each for tops/pants/jackets/accessories
- 20 unique colors, 8 occasions, 14 fabrics, 5 seasons
- 90% in-stock rate (270/300)
- Price tiers: budget (<$50), mid ($50-120), premium ($120-250), luxury ($250+)
- Ratings: 3.5–5.0 scale, normally distributed

## Production Considerations

For a production deployment, this architecture would need:

1. **Real product images** — Replace placeholder URLs with actual product photography
2. **Cloud Run or GKE deployment** — Containerize with Flask/FastAPI, add load balancing
3. **Vertex AI** — Switch from AI Studio to Vertex AI for higher rate limits and SLA
4. **Authentication** — Add user sessions, OAuth, rate limiting
5. **Caching** — Cache frequent queries (trending, price ranges) to reduce BigQuery cost
6. **Monitoring** — Log agent routing decisions, tool calls, and response latency
7. **A/B testing** — Compare specialist vs. monolithic agent performance
8. **Feedback loop** — Track which recommendations led to purchases, retrain prompts
