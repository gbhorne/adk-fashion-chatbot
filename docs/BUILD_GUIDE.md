# Building a Customer-Facing AI Shopping Assistant with Google ADK, Gemini, and BigQuery  -  for $0

## How I built a multi-agent fashion chatbot that searches products, gives styling advice, and checks inventory through natural conversation

---

I've built several AI agents for internal analytics  -  inventory dashboards, anomaly detection, research tools. They all follow the same pattern: analyst asks a question, agent queries a database, returns structured results.

But none of them talked to customers.

Customer-facing AI is a different problem. Customers don't write SQL. They say things like "I need something red and flowy for a dinner party, nothing too expensive." They expect the system to understand intent, handle ambiguity, and respond like a person  -  not a search engine.

So I built a conversational fashion shopping assistant using Google's Agent Development Kit. Four agents, eleven tools, three hundred products, zero dollars.

Here's how it works and what I learned.

---

## The Problem with Single-Agent Chatbots

Most shopping chatbots are glorified search bars. You type "red dress," it returns a filtered list. There's no conversation, no refinement, no styling advice.

The issue is tool overload. Give one agent fifteen tools  -  search, filter, compare, suggest accessories, check stock, find deals  -  and it struggles to pick the right one. It hallucinates parameters. It calls the wrong tool for the intent.

The fix is specialization. Instead of one agent doing everything, I split the work into three specialists, each with a focused set of tools, coordinated by a root orchestrator.

---

## The Architecture

The system has four agents arranged in a hub-and-spoke pattern.

The **shopping orchestrator** is the root agent. It receives every customer message, classifies the intent, and routes to the right specialist. It never queries the database directly  -  its only job is routing.

The **product finder** handles all catalog searches. It has four tools: `search_products` for filtered browsing, `get_product_details` for deep dives, `get_similar_items` for recommendations, and `filter_by_attributes` for specific criteria like fabric or tags. When a customer says "show me evening dresses," this agent handles it.

The **style advisor** handles fashion expertise. It compares products side-by-side, suggests accessories that pair with a chosen item, surfaces trending pieces, and provides occasion-appropriate style tips. When a customer says "which of these would look better for a wedding," this agent handles it.

The **availability checker** handles logistics. Stock levels, size availability, price ranges, and budget-constrained deal finding. When a customer says "do you have that in a medium," this agent handles it.

Each specialist has its own Gemini 2.5 Flash instance, its own instruction prompt, and its own tool set. They share a single BigQuery table but never see each other's tools.

---

## The Data Layer

The product catalog is a single BigQuery table with 22 columns and 300 synthetic fashion products. Dresses, tops, pants, jackets, accessories  -  each with colors, styles, occasions, fabrics, sizes, prices, ratings, and descriptive tags.

Two design decisions shaped the schema.

First, I used ARRAY columns for sizes and tags. Instead of a separate `product_sizes` junction table, the `size_available` column stores `["XS", "S", "M", "L", "XL"]` directly. BigQuery queries these with UNNEST: `WHERE "M" IN UNNEST(size_available)`. Same for tags like "backless" or "v_neck." This eliminates joins and keeps every tool's SQL simple.

Second, I used a single denormalized table instead of normalized relations. BigQuery is columnar  -  it only reads the columns you SELECT, regardless of how wide the table is. A 22-column table where you read 6 columns costs the same as a 6-column table. The simplicity gain from avoiding joins outweighs any theoretical normalization benefit at this scale.

---

## The Search Broadening Strategy

This is the feature I'm most proud of, and it's not a feature in the traditional sense. It's a behavior encoded in the agent's instructions.

When a customer asks for "a red flowy evening dress" and the catalog only has one red evening dress (and it's bodycon, not flowy), most chatbots return "no results found." That's a dead end.

My product finder does something different. It searches with all filters first. When it gets no results, it drops the least critical filter  -  in this case, "flowy"  -  and searches again. Then it tells the customer what happened: "I couldn't find a red flowy evening dress, so I broadened the search to all red evening dresses. Here's what I found."

This is how a real personal shopper operates. Start specific, widen progressively, and be transparent about it.

The behavior isn't hardcoded in SQL or Python. It's in the agent's instruction prompt. Gemini reads the instructions, recognizes the no-results scenario, and decides which filter to drop. The LLM handles the judgment call; the tools handle the data retrieval.

---

## Fixed SQL vs. Text-to-SQL

Every tool in this system uses hand-written SQL with parameterized inputs. No tool generates SQL dynamically from natural language.

This is a deliberate choice. Text-to-SQL is impressive in demos but dangerous in production. The LLM might generate a query that scans the entire table (expensive), returns unexpected columns (confusing for the agent), or includes SQL injection vectors (dangerous if connected to real data).

Fixed SQL means I know exactly what runs. `search_products` always generates the same SELECT with a dynamic WHERE clause. `get_similar_items` always uses the same CTE with attribute-based scoring. Every query is testable, predictable, and safe.

The tradeoff is flexibility  -  a new search pattern requires a code change. But for a bounded product catalog with known attributes, that's the right tradeoff. You don't need infinite SQL flexibility when you have 11 well-designed tools covering every reasonable customer query.

---

## What I Learned About Agent Instructions

The hardest part of this project wasn't the code. tools.py is 300 lines of straightforward SQL. agent.py is 120 lines of agent configuration.

The hard part was writing instructions that produce consistent, high-quality responses across edge cases.

Three examples.

For the product finder, I had to specify "present a maximum of 5 items at a time." Without this, the agent would dump all 10 results in one message  -  overwhelming for a customer. With the limit, it presents 5 and asks "would you like to see more?"

For the style advisor, I had to specify "explain WHY accessories pair well." Without this, it would just list matching accessories. With the instruction, it says things like "the gold hardware will contrast beautifully with the red dress, adding warmth without competing with the bold color." That's the difference between a search result and a styling experience.

For the availability checker, I had to specify "always mention the exact price." Without this, it would say "it's in the mid price range"  -  useless for a buying decision. With the instruction, it says "$100.43"  -  actionable information.

Agent instructions are the product design layer of LLM applications. They deserve the same attention as UI wireframes.

---

## The $0 Stack

The entire project runs at zero cost.

Gemini 2.5 Flash through AI Studio's free tier handles all LLM inference. The rate limit (5-15 RPM) is fine for development and demos. BigQuery's free tier provides 1 TB of queries and 10 GB of storage per month  -  orders of magnitude more than this project needs. ADK is open source. Python is free. The ADK web UI provides the chat interface.

For production, you'd switch to Vertex AI for higher rate limits and SLA guarantees, deploy to Cloud Run for HTTPS and autoscaling, and add monitoring. But the architecture stays the same.

---

## Results

The agent correctly routes queries to the right specialist across all test scenarios. Search queries go to product_finder. Styling questions go to style_advisor. Stock checks go to availability_checker.

When exact matches aren't available, the search broadening behavior kicks in  -  the agent drops filters, explains what it changed, and still delivers useful results.

The accessory suggestions include reasoning: why a gold belt pairs with a red dress, why a black necklace grounds a bold color. The trending results include ratings and descriptions. The deal finder prioritizes quality within a budget, not just the cheapest items.

Three hundred lines of tool code. One hundred twenty lines of agent configuration. Four agents coordinating through natural language routing. A conversational shopping experience that handles ambiguity, broadens searches, and explains its recommendations.

And it cost nothing to build.

---

## What's Next

This is my sixth ADK project, but the first one that faces customers instead of analysts. The next step is a Vertex AI Pipeline project  -  taking a machine learning model from training through registry to endpoint deployment with Kubeflow orchestration and drift monitoring. Different problem space, same principle: build the architecture that production systems actually need.

The repo is on GitHub: [github.com/gbhorne/adk-fashion-chatbot](https://github.com/gbhorne/adk-fashion-chatbot)

---

*Built with Google ADK, Gemini 2.5 Flash, BigQuery, and Python. Architecture diagram and documentation included in the repository.*
