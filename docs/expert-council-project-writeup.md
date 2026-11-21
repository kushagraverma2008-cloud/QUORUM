# Expert Council: Project Write-Up
*(Working title. An AI platform that lets anyone get their idea evaluated by the accumulated thinking of hundreds of real industry experts.)*

---

## 1. One-Line Vision

A global web app where a founder submits an idea in any format and receives a brutally honest, multi-expert evaluation, drawn from the published principles, warnings, and predictions of real industry leaders across every major sector.

## 2. The Problem

- Millions of people worldwide have ideas (technical, non-technical, financial, consumer, social), but **no access to experienced people** who can judge them.
- A person launching a cosmetics brand does not know a formulation expert, a retail sales head, a D2C marketer, and a regulatory expert personally.
- Friends and family give polite, uninformed feedback. Consultants are expensive. Incubators are selective and geographically limited.
- Result: ideas die early or fail late for reasons an experienced person would have spotted in ten minutes.

## 3. The Solution

Build a platform with three layers:

1. **Knowledge layer:** a curated library of real experts' public knowledge (books, interviews, podcasts, talks, articles), organised by sector.
2. **Brain layer:** for each expert, a "digital brain": an AI persona built strictly from that expert's documented views, principles, and advice.
3. **Orchestration layer:** an orchestrator that takes the user's idea, routes it to the right brains, collects their evaluations, and merges them into one clear report.

## 4. Target Users

| User | Need |
|---|---|
| First-time founders and students | Reality check before spending money or time |
| Non-technical idea holders | Access to domain knowledge they lack |
| Early-stage startups | Second opinions across functions (sales, finance, legal) |
| Incubators, colleges, accelerators | Scalable first-round screening of many ideas |
| Small business owners | Expansion or pivot feedback |

## 5. Core Concept: Two Axes of Expertise

An idea needs judgment on **what industry it is in** *and* **how the business will run**. Every expert is therefore tagged on two axes:

- **Sector axis:** Cosmetics, AI, Finance, Agriculture, etc.
- **Function axis:** Sales, Marketing, Fundraising, Operations, Legal, Product, Hiring, Unit Economics, Branding.

Example: a cosmetics brand idea gets evaluated by cosmetics/beauty experts (sector) **and** by D2C sales, brand-building, and fundraising experts (function).

## 6. Sector Taxonomy

The first draft listed 19 categories. That number was a starting point, not a fact. Standard classification systems range from about 11 broad sectors (GICS) to about 20 (NAICS) and 21 (ISIC), each with well over 100 sub-industries beneath them. Several real areas were also missing or buried, such as telecom, FMCG, materials and mining, utilities and waste, arts and design, and home, pets and events. This revision uses **25 industry sectors plus 1 cross-sector function layer**.

| # | Sector | Sub-domains (examples) |
|---|---|---|
| 1 | Technology & Software | SaaS, cybersecurity, cloud, mobile/web, developer tools |
| 2 | AI, ML & Data | Generative AI, computer vision, data engineering, AI ethics |
| 3 | Telecom & Connectivity | Telecom operators, networking, IoT, satellite internet |
| 4 | Deep Tech, Space & Defence | Aerospace, quantum, drones, advanced materials, defence |
| 5 | Manufacturing & Hardware | Electronics, robotics, industrial machinery, 3D printing |
| 6 | Finance & Fintech | Payments, lending, investing, insurance, VC/PE, banking, crypto |
| 7 | Professional Services | Consulting, legal, HR and recruitment, accounting, agencies |
| 8 | E-commerce & Retail | Marketplaces, D2C, offline retail, quick commerce |
| 9 | Consumer Goods & FMCG | Household products, packaged goods, appliances, consumer electronics brands |
| 10 | Fashion, Beauty & Personal Care | Apparel, footwear, cosmetics, skincare, luxury |
| 11 | Food & Beverage | Restaurants, cloud kitchens, packaged food, beverages |
| 12 | Agriculture & Agritech | Farming, dairy, fisheries, food processing, farm supply chains |
| 13 | Travel & Hospitality | Hotels, tourism, airlines, travel-tech |
| 14 | Media, Entertainment & Gaming | Content, OTT, music, games, creator economy, publishing |
| 15 | Sports & Fitness | Sports-tech, gyms, athlete brands, wellness studios |
| 16 | Home, Lifestyle & Pets | Home services, interiors, furniture, weddings and events, pet care |
| 17 | Healthcare & Life Sciences | Digital health, pharma, biotech, medical devices, mental health |
| 18 | Education & EdTech | K-12, higher-ed, skilling, tutoring, research |
| 19 | Social Impact & Public Sector | NGOs, govtech, policy, rural development, non-profits |
| 20 | Arts, Design & Creative Industries | Architecture, graphic and product design, film production, crafts |
| 21 | Energy & Climate | Solar, wind, batteries, hydrogen, carbon, sustainability |
| 22 | Real Estate & Construction | Proptech, construction, infrastructure, urban planning |
| 23 | Logistics, Mobility & Automotive | Supply chain, delivery, ride-hailing, EVs, shipping |
| 24 | Materials, Chemicals & Mining | Chemicals, metals, plastics, packaging, raw materials |
| 25 | Utilities, Water & Waste | Power distribution, water, recycling, waste management |
| F | **Function layer (cross-sector)** | Sales, marketing and branding, fundraising, finance and unit economics, operations, legal and compliance, product, hiring and team, strategy and business models, customer success |

**Rules for keeping the taxonomy honest**
- The taxonomy is stored as a tree in the database, so sectors and sub-sectors can be added or split without code changes.
- A sector goes live only when it has enough vetted experts (suggested minimum 30 at launch, growing to 100 to 200).
- Ideas are multi-tagged. A cosmetics brand touches sectors 10, 8, and 9, plus the function layer.
- An "Other / Cross-sector" fallback catches ideas that fit nowhere. Those ideas are logged, and repeated patterns reveal new sectors to add.
- Review the taxonomy every quarter against what users actually submit.

## 7. The Expert Library

### 7.1 Goal
100 to 200 authentic experts per sector (sector-specific experts plus function experts), each with a documented public record.

### 7.2 Who counts as an expert
- Founders, CEOs, and operators who built real companies
- Investors and VCs who have backed and watched many companies
- Domain scientists, engineers, and practitioners
- Authors and researchers with published frameworks
- Regulators or policy figures where relevant

### 7.3 Inclusion criteria (quality gate)
1. Verifiable real-world track record
2. At least 10 hours of primary-source content (long interviews, podcasts, books, letters, talks)
3. Content where they state **principles, warnings, and predictions**, not only anecdotes
4. Geographic and stylistic diversity (global, plus strong India coverage)
5. Balance of optimists and skeptics, so the panel is not an echo chamber

### 7.4 Source types per expert
Books and memoirs · long-form podcasts · YouTube interviews and keynotes · shareholder letters · blogs and essays · newsletters · court/regulatory testimony · biographies written about them.

### 7.5 Expert profile record
- Name, sector tags, function tags, region, era
- Company/ventures and outcomes (including failures)
- Source list with links, dates, and licence/usage status
- Extracted profile (see Section 8)

## 8. The Digital Brain (per expert)

Each brain is not just a chatbot with a name. It has two parts:

**A. Structured Profile** (distilled once, reviewed by you)
- **Core principles:** the rules they repeatedly state
- **Morals and values:** what they refuse to do
- **Decision heuristics:** how they judge opportunities (e.g., "I look for X before Y")
- **Advice to beginners**
- **Warnings:** common mistakes and traps in their field
- **Predictions:** views on the future of the sector
- **Blind spots and biases:** known to keep the panel honest
- **Communication style:** blunt, cautious, data-driven, etc.

**B. Retrieval Knowledge Base**
- All source material transcribed, cleaned, chunked, and embedded in a vector database
- Every chunk tagged with source, date, and topic
- At evaluation time, the brain retrieves the most relevant passages for the idea, so its opinion is **grounded in real statements**

**Behaviour rules for every brain**
- Answer only from the profile and retrieved sources; say "no documented view on this" instead of inventing one
- Every claim carries a citation (source + timestamp/page)
- Be truthful over polite: identify weaknesses first
- Be clearly labelled as an **AI-generated perspective based on public material**, never as the person's actual statement about this idea

## 9. The Orchestrator

### 9.1 Responsibilities
1. Receive the normalised idea
2. Understand it: classify sector(s), functions needed, stage, geography, and missing information
3. Select the relevant brains
4. Dispatch the idea to them in parallel
5. Collect structured responses
6. Detect agreement, disagreement, and duplicate points
7. Produce the final report

### 9.2 Routing: a key design decision
Sending every idea to every brain in every sector would be slow, expensive, and noisy (a fintech expert's opinion on a cosmetics brand is mostly irrelevant). Use **selective routing**:

1. **Sector classifier:** picks the top 1 to 3 relevant sectors (with a "Cross-sector" option for broad ideas)
2. **Expert ranker:** within those sectors, picks the top N experts (say 10 to 30) by relevance, using semantic match between the idea and each expert's profile and source material
3. **Function panel:** always adds a set of function experts (sales, finance, legal, marketing)
4. **Diversity guard:** ensures the panel includes skeptics, optimists, and operators, not only one type
5. **User control:** the user can add or remove experts or sectors before running

An optional "Full Council" mode (all sectors) can exist as a premium or experimental feature.

### 9.3 Aggregation
A synthesis agent reads all expert outputs and produces themes, ranked risks, consensus, and conflicts. It must preserve minority opinions rather than average them away.

## 10. End-to-End User Flow

1. **Submit idea:** upload PDF, Word, or text; or record voice. Optionally answer a short questionnaire (target customer, budget, location, stage).
2. **Conversion:** files parsed and voice transcribed into one text "Idea Brief".
3. **Clarify:** the app shows the brief and asks the user to confirm or fill gaps (a weak brief leads to weak feedback).
4. **Panel selection:** the user sees which sectors and experts were chosen and can adjust.
5. **Evaluation:** brains run in parallel with live progress ("14 of 25 experts have responded").
6. **Report:** the user gets the Council Summary Report with the overall score and pillar ratings (Section 11.2). Clicking any expert opens their individual card (Section 11.4).
7. **Follow-up:** the user can question any single expert ("Why do you think my pricing fails?"), refine the idea, and re-run.

## 11. Evaluation Output: What the User Receives

### 11.1 Two connected layers
When the run finishes, the user receives two things that link to each other:

1. **Council Summary Report** (the core deliverable): the combined essence of everything all experts said, in one place.
2. **Individual Expert Cards** (the drill-down): one card per digital brain, opened by clicking that expert's name anywhere in the summary.

Both are available on screen, as a downloadable PDF, and as plain text (see Section 11.5).

### 11.2 Council Summary Report (Layer 1)
1. **Overall Council Score (out of 10)** with a verdict label (Strong / Promising / Risky / Not viable) and a **confidence indicator** showing how closely the experts agree and how many had grounded evidence.
2. **The Council in one paragraph:** the combined bottom line in plain language.
3. **Pillar ratings (out of 10):** the score broken down by the pillars in the table below.
4. **Top warnings**, ranked by severity, each showing how many experts raised it.
5. **Top tips and advice**, ranked by how many experts recommend them.
6. **Predicted problems** at 6 months, 2 years, and 5 years.
7. **Consensus and disagreement map:** what most experts agree on, and where they split, with the experts on each side named.
8. **Kill questions:** the 5 questions the idea must answer to survive.
9. **30/90/180-day action plan.**
10. **Expert Directory:** a table of every expert on the panel with sector, personal score, and a one-line stance. Each name is a link to that expert's card.
11. Recommended real-world experts to talk to (the Phase 4 marketplace, see Section 16).

| Pillar | What it measures |
|---|---|
| Market Demand | Is there a real, reachable customer need? |
| Differentiation | Why would customers pick this over alternatives? |
| Feasibility | Can it be built or delivered with realistic resources and skills? |
| Financial Viability | Unit economics, margins, funding needs, path to profit |
| Execution Risk | Team, operations, supply, and complexity risks (10 = low risk) |
| Regulatory & Legal Risk | Licences, compliance, IP, liability (10 = low risk) |
| Market Timing | Is now the right time, given trends and competition? |
| Defensibility & Scale | Can it stay ahead and grow beyond the first version? |

Every pillar uses the same direction: **10 is always best**. Risk pillars are inverted so that a higher score means safer.

### 11.3 How the scores are calculated
- Each expert scores every pillar from 0 to 10 and gives an overall score, using only what their profile and sources support. Where they have no documented view, the pillar is marked "no documented view" and never guessed.
- **Council pillar score:** relevance-weighted average of the experts who scored that pillar. Weight reflects how closely the expert's sector and experience match the idea.
- **Overall Council Score:** relevance-weighted average of the experts' overall scores, cross-checked against the pillar average. A large mismatch is flagged.
- The report always shows the **range (lowest to highest score)** and the confidence indicator, so one average never hides a split panel.
- Minority opinions, especially the harshest dissent, stay visible and are never averaged away.
- The weighting method is shown to the user for transparency.

### 11.4 Individual Expert Card (Layer 2)
Clicking any expert opens their card:
- **Identity:** name, photo, sector and function tags, short bio, track record
- **Personal rating out of 10**, with their own pillar ratings and verdict
- **Personal opinion:** their evaluation, written in their documented thinking style
- **Their warnings** specific to this idea
- **Their tips and advice**
- **Their predictions** for this idea and its sector
- **What they would ask the founder first**
- **Sources behind the opinion:** citations to the exact book, interview, timestamp, or page
- **Agreement flag:** where they agree or differ from the council
- **Standing label:** "AI-generated perspective based on public material; not a statement by the person."
- **Actions:** ask this expert a follow-up question, or return to the summary

### 11.5 Delivery formats
| Format | What it is |
|---|---|
| In-app dashboard | Interactive summary. Click any expert to open their card. Sort or filter experts by score, sector, or verdict. |
| PDF export | Same content. Expert names link to their card pages, and every card has a "back to summary" link. |
| Plain text / Markdown | Copy-friendly version of the summary and all cards. |
| Saved history | Every version of the idea keeps its own report, so scores can be compared after edits. |

## 12. Web App: Main Screens

1. Landing page and sign-up
2. Idea submission (text, files, voice) with questionnaire
3. Idea Brief review and edit
4. Panel selector (sector map, expert cards with photo, bio, track record, sources)
5. Live evaluation progress
6. Council Summary dashboard (overall score, pillar ratings, warnings, tips, disagreement map, action plan, expert directory)
7. Individual Expert Card (personal rating, opinion, warnings, tips, sources) with follow-up chat
8. Idea history and version comparison
9. **Admin/curation console** (for you): add experts, upload sources, review extracted profiles, monitor quality

## 13. Technical Architecture

**Frontend:** React/Next.js, with Tailwind CSS for styling.
**Backend:** Python (FastAPI) or Node.js; job queue (Celery/BullMQ + Redis) for parallel expert runs.
**Input processing:** PDF/DOCX parsers; speech-to-text (Whisper or similar) for voice.
**Data layer:**
- PostgreSQL for users, ideas, experts, sectors, reports
- Vector database (pgvector, Qdrant, or Pinecone) for source chunks
- Object storage (S3-compatible) for raw files and transcripts
**AI layer:**
- LLM API for brains, orchestrator, and synthesis
- Embedding model for retrieval
- Retrieval-augmented generation (RAG) plus per-expert profile prompts
- Structured JSON outputs for consistent scoring
**Report generation:** structured JSON from the brains and the synthesis agent feeds the on-screen dashboard, the PDF export (HTML-to-PDF), and the plain-text version.
**Ingestion pipeline:** source URL/file → download/transcribe → clean → chunk → embed → tag → store → profile extraction → human review.
**Infra:** Docker, cloud hosting, caching, rate limiting, cost monitoring, logging of every evaluation for audit.

### Data model (core tables)
`users` · `ideas` · `idea_versions` · `sectors` (tree) · `experts` · `expert_sector_tags` · `sources` · `chunks` · `expert_profiles` · `evaluations` · `expert_responses` · `reports`

## 14. Knowledge Building Workflow (Your Manual Curation Part)

1. Finalise the sector taxonomy
2. For each sector, shortlist 100 to 200 experts using the criteria in Section 7.3
3. Collect and log primary sources per expert
4. Run the ingestion pipeline
5. Generate the structured profile with AI, then **review and correct it manually**
6. Test each brain with sample ideas; check for fabrication and out-of-character answers
7. Publish the brain to the live library

Start with **1 or 2 sectors and 20 to 30 experts each**, prove the quality, then scale. Curation quality, not the number of experts, is the product's real moat.

## 15. Legal, Ethical, and Trust Design (Build In From Day One)

| Risk | Safeguard |
|---|---|
| **Impersonation / personality rights** (using a real person's name and style commercially; India's courts have protected several public figures' personality rights) | Label every output "AI perspective based on public sources"; avoid fake first-person quotes presented as real; seek permission or partnerships with experts where possible; consider consulting a lawyer before launch |
| **Copyright on books, transcripts, and videos** | Prefer licensed or permissioned content; store derived ideas and short cited excerpts, not full text redistribution; check platform terms for scraping YouTube and podcasts |
| **Hallucinated opinions** | Retrieval-grounded answers, mandatory citations, "no documented view" fallback, evaluation tests |
| **Wrong or harmful advice** (financial, medical, legal) | Clear disclaimers; the report is decision support, not professional advice; extra caution in health and finance sectors |
| **Echo chamber and bias** | Diverse panel rules, skeptic quotas, blind-spot fields in each profile |
| **User idea confidentiality** | Encryption, private-by-default, no training on user ideas, clear privacy policy, optional NDA-style terms |
| **Outdated views** | Date-stamp sources; weight recent statements; allow "views changed over time" |

## 16. Roadmap

| Phase | Scope | Outcome |
|---|---|---|
| **0: Research (2 to 4 weeks)** | Finalise sector list, expert criteria, test manual prompt on 5 experts | Proof that persona-grounded feedback is useful |
| **1: Prototype (1 to 2 months)** | 1 to 2 sectors, 20 to 30 experts, text input only, simple report | Working end-to-end demo |
| **2: MVP (2 to 4 months)** | Multi-format and voice input, routing, 5 to 8 sectors, full report, expert chat, accounts | Public beta with real founders |
| **3: Expansion** | All 25 sectors, 100 to 200 experts each, user feedback loop, incubator/college partnerships | Broad coverage |
| **4: Real Human Bridge** | Optional marketplace connecting users to the **real** experts and practitioners for paid sessions | Fulfils your original goal of giving people expert access |

## 17. Success Metrics

- Founder-rated usefulness of the report (target above 4 out of 5)
- Percentage of expert claims traceable to a cited source (target near 100%)
- Blind test: do experienced people agree with the panel's top 3 risks?
- Time from submission to report
- Cost per evaluation
- Repeat usage and idea revisions per user

## 18. Business Model (Options)

Freemium (limited evaluations) · pay-per-evaluation · subscriptions for founders · institutional licences for incubators and universities · revenue share with experts in the human-bridge marketplace.

## 19. Open Decisions to Resolve

1. Sector and function tags: confirm the 25 sectors and 10 functions, and how deep the sub-domains go
2. Expert consent strategy: public-source only, or partnerships
3. Cost model: how many brains per evaluation is affordable
4. Language support (Hindi and other languages alongside English) from the start or later
5. Whether reports are private only or shareable
6. Which sector to launch first (choose one where you can judge output quality yourself)

---

**Summary:** Expert Council converts scattered public wisdom of real industry leaders into an accessible, cited, multi-perspective evaluation engine, so that anyone, anywhere, can pressure-test an idea before betting time and money on it.
