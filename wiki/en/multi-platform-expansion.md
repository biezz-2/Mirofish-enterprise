---
title: MiroFish 7 Social Media Platforms Specification
type: concept
tags: [multi-platform, social-simulation, algorithms, agent-behavior, ocean-psychology, v3.1]
related:
  - "[[index]]"
  - "[[architecture]]"
  - "[[operational-readiness]]"
  - "[[codemap]]"
sources:
  - backend/app/services/oasis_profile_generator.py
  - backend/app/services/simulation_config_generator.py
  - backend/scripts/run_parallel_simulation.py
---

> 🌐 **Language / Bahasa**: [English](./multi-platform-expansion.md) | [Bahasa Indonesia](../ekspansi-multi-platform.md)

# 7 Social Media Platforms Specification: MiroFish v3.1 Enterprise

This document provides the in-depth technical specifications and quantitative models for expanding MiroFish from a legacy dual-platform setup (Twitter and Reddit) into a **Unified 7 Social Media Platform Ecosystem**: **Twitter**, **X**, **Reddit**, **TikTok**, **Instagram**, **Facebook**, and **Threads**.

Each platform features a distinct algorithmic recommendation model, custom action spaces, information half-life decay parameters, and agent psychological profiles.

---

## 1. Platform Characteristic Analysis

```
+-------------------------------------------------------------------------------------------------------+
|                                  MIROFISH v3.1 7-PLATFORM LANDSCAPE                                   |
+-------------------+--------------------+--------------------+--------------------+--------------------+
| PLATFORM          | CONTENT TYPOLOGY   | ALGORITHM FOCUS    | SOCIAL DYNAMICS    | INTERACTION PATTERN|
+-------------------+--------------------+--------------------+--------------------+--------------------+
| 1. Twitter        | Fast micro-text    | Chronological/Trend| Rapid cascades     | Retweet, Quote     |
| 2. X              | Long-form/Media    | Monetized / For You| High polarization  | Paid subscriptions |
| 3. Reddit         | Threaded trees     | Karma & Subreddits | In-depth debate    | Upvote, Downvote   |
| 4. TikTok         | Short script/Video | Pure Interest/Loop | Viral replication  | Duet, Sound Contag |
| 5. Instagram      | Visual & Aesthetic | Affinity network   | Curated positivity | Like, Save, DM     |
| 6. Facebook       | Multi-format/Groups| Strong Family/Clan | Strong Echo Chamber| Emotional Reactions|
| 7. Threads        | Conversational text| IG Connected/Fedi  | Light discussions  | Repost, Mentions   |
+-------------------+--------------------+--------------------+--------------------+--------------------+
```

### 1.1 Twitter (Legacy Short-Form Microblogging)
- **Focus**: Fast-breaking news distribution, live updates, and hashtag trending waves.
- **Characteristics**: Strict character limit (280 characters), high timeline velocity, strong reliance on follower graph topology.
- **Cascade Dynamics**: A single post from a high-centrality node (*influencer*) can trigger exponential information cascades within the opening simulation rounds.

### 1.2 X (Algorithmic "For You" & Creator Attention Economy)
- **Focus**: Attention monetization, polarized commentary, long-form articles, and controversy-driven engagement.
- **Characteristics**: The "For You" feed prioritizes verified accounts and controversial discourse (*rage-baiting*) to maximize dwell time.
- **Special Dynamics**: *Quote Posts* frequently act as public counter-arguments that bisect opinion networks into adversarial factions.

### 1.3 Reddit (Hierarchical Community & Karma Economy)
- **Focus**: Thematic discussions within specific sub-communities (*subreddits*) structured as nested conversation trees.
- **Characteristics**: High anonymity, strict community rule enforcement, and quantified social capital through *Upvote* and *Downvote* mechanics.
- **Feedback Loops**: Posts diverging from subreddit consensus suffer immediate downvotes and algorithmic suppression (*shadow dampening*).

### 1.4 TikTok (Interest-Graph & Short-Video Script Engine)
- **Focus**: Rapid trend dispersion governed by pure user interest graphs rather than social friendship networks.
- **Characteristics**: Agents simulate 15-60 second micro-scripts with dramatic 3-second opening hooks.
- **Virality Contagion**: The "For You Page" (FYP) grants viral reach even to low-follower accounts when early completion rates are high.

### 1.5 Instagram (Visual Narrative & Social Curation)
- **Focus**: Aesthetic imagery, carousel infomediaries, lifestyle narratives, and controlled comment sections.
- **Characteristics**: Dominant interactions are *Likes*, *Saves*, and private direct shares. Discourse leans aesthetic, professional, or aspirational.

### 1.6 Facebook (Intergenerational Social Graph & High Homophily)
- **Focus**: Real-world relationship networks, extended families, alumni associations, and closed interest groups.
- **Characteristics**: Broader user age demographics; vulnerable to emotional disinformation, conspiracy narratives, and confirmation bias.
- **Affective Reaction Space**: Full emotional spectrum: *Like*, *Love*, *Care*, *Haha*, *Wow*, *Sad*, and *Angry*, each weighting feed placement differently.

### 1.7 Threads (Conversational Decentralized Microblogging)
- **Focus**: Casual text-first conversations without the aggressive competitive metrics of X.
- **Characteristics**: Seamlessly bootstrapped on Instagram's social graph; emphasizes constructive dialogue and de-emphasizes hostile political conflict.

---

## 2. Quantitative Platform Parameter Matrix

The following mathematical parameters govern content curation and agent action probabilities in the simulation runtime:

| Symbolic Parameter | Twitter | X | Reddit | TikTok | Instagram | Facebook | Threads |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Recency Weight (\(\lambda_{rec}\))** | 0.45 | 0.35 | 0.20 | 0.50 | 0.25 | 0.15 | 0.40 |
| **Popularity Weight (\(\beta_{pop}\))** | 0.30 | 0.40 | 0.35 | 0.35 | 0.45 | 0.30 | 0.25 |
| **Echo Chamber Coefficient (\(\gamma_{echo}\))** | 0.15 | 0.30 | 0.40 | 0.10 | 0.25 | 0.45 | 0.15 |
| **Virality Threshold (\(\theta_{viral}\))** | 0.70 | 0.60 | 0.75 | 0.45 | 0.65 | 0.80 | 0.70 |
| **Half-Life Decay (\(t_{half}\) in Rounds)**| 2.5 | 3.5 | 6.0 | 1.8 | 4.5 | 8.0 | 3.0 |
| **Cross-Platform Spillover (\(\sigma_{spill}\))** | 0.35 | 0.40 | 0.25 | 0.50 | 0.30 | 0.20 | 0.30 |
| **Max Content Characters** | 280 | 4,000 | 40,000 | 500 (script)| 2,200 | 10,000 | 500 |

### 2.1 Action Space Enum Definitions

Each platform defines a valid set of legal actions within `simulation_config.json`:

```python
PLATFORM_ACTION_SPACES = {
    "twitter": [
        "CREATE_POST", "LIKE_POST", "REPOST", "QUOTE_POST", "FOLLOW", "DO_NOTHING"
    ],
    "x": [
        "CREATE_POST", "LIKE_POST", "REPOST", "QUOTE_POST", "BOOKMARK", 
        "REPLY_LONG", "FOLLOW", "BLOCK", "DO_NOTHING"
    ],
    "reddit": [
        "CREATE_POST", "CREATE_COMMENT", "LIKE_POST", "DISLIKE_POST",
        "LIKE_COMMENT", "DISLIKE_COMMENT", "SEARCH_POSTS", "SEARCH_USER",
        "TREND", "REFRESH", "FOLLOW", "MUTE", "DO_NOTHING"
    ],
    "tiktok": [
        "CREATE_SCRIPT", "LIKE_VIDEO", "COMMENT", "SHARE_TO_FRIENDS",
        "DUET_REACT", "FOLLOW_CREATOR", "SKIP", "DO_NOTHING"
    ],
    "instagram": [
        "CREATE_POST", "LIKE_POST", "CREATE_COMMENT", "SAVE_POST",
        "SHARE_STORY", "FOLLOW", "DO_NOTHING"
    ],
    "facebook": [
        "CREATE_POST", "REACT_LIKE", "REACT_LOVE", "REACT_HAHA", 
        "REACT_WOW", "REACT_SAD", "REACT_ANGRY", "SHARE_FEED", 
        "CREATE_COMMENT", "JOIN_GROUP", "DO_NOTHING"
    ],
    "threads": [
        "CREATE_POST", "LIKE_POST", "REPOST", "QUOTE_POST", 
        "REPLY", "FOLLOW", "DO_NOTHING"
    ]
}
```

---

## 3. Behavioral Mathematical Formulation

### 3.1 Timeline Content Relevance Scoring (\(Score_{i,j}\))
When Agent \(i\) evaluates post \(j\) on platform \(p\), perceived relevance is modeled as:

\[
Score_{i,j}^{(p)} = \lambda_{rec}^{(p)} \cdot \exp\left(-\frac{\Delta t_{j}}{t_{half}^{(p)}}\right) + \beta_{pop}^{(p)} \cdot \log_{10}(1 + Eng_{j}) + \gamma_{echo}^{(p)} \cdot \text{Sim}(\mathbf{e}_i, \mathbf{e}_j)
\]

Where:
- \(\Delta t_j = t_{now} - t_{created}\) is elapsed time in simulation rounds.
- \(Eng_j = \text{Likes}_j + 2 \cdot \text{Shares}_j + 1.5 \cdot \text{Comments}_j\) represents composite engagement.
- \(\text{Sim}(\mathbf{e}_i, \mathbf{e}_j) \in [-1, 1]\) is the cosine similarity between agent ideological vectors and post content embeddings.

### 3.2 Action Selection via Multinomial Softmax
The probability that Agent \(i\) executes action \(k\) in round \(t\) is governed by:

\[
P(\text{Action}_k \mid i, j, p) = \frac{\exp\left( \mathbf{w}_k^T \mathbf{x}_{i,j} + b_k^{(p)} \right)}{\sum_{m \in \mathcal{A}_p} \exp\left( \mathbf{w}_m^T \mathbf{x}_{i,j} + b_m^{(p)} \right)}
\]

Where \(\mathbf{x}_{i,j}\) encapsulates psychological attributes, author reputation, and content toxicity:

\[
\mathbf{x}_{i,j} = \left[ O_i, C_i, E_i, A_i, N_i, \text{Rep}_j, Score_{i,j}^{(p)}, \text{Toxicity}_j \right]^T
\]

---

## 4. Agent Psychological Profiling

Agents synthesized by `OasisProfileGenerator` (`backend/app/services/oasis_profile_generator.py`) carry standardized cognitive metadata:

```json
{
  "agent_id": 42,
  "name": "Bambang Sudarmono",
  "username": "bambang_analis_id",
  "entity_uuid": "c3a1e9b2-7f8d-4e5a-9a1b-3c4d5e6f7a8b",
  "bio": "Public Policy Observer & Monetary Economics Lecturer. Skeptical of viral instant narratives.",
  "ocean_traits": {
    "openness": 0.85,
    "conscientiousness": 0.90,
    "extraversion": 0.45,
    "agreeableness": 0.60,
    "neuroticism": 0.25
  },
  "archetype": "EXPERT_SKEPTIC",
  "linguistic_style": {
    "dialect": "Formal Standard English / Indonesian PUEBI",
    "tone": "Objective, academic, cites empirical data",
    "slang_tolerance": 0.1
  },
  "platform_affinities": {
    "twitter": 0.8,
    "reddit": 0.9,
    "x": 0.7,
    "tiktok": 0.1,
    "instagram": 0.3,
    "facebook": 0.5,
    "threads": 0.6
  }
}
```

### 4.1 Six Core Social Persona Archetypes
1. **INFLUENCER / PUBLIC_FIGURE**: High follower counts, prolific posting rates, prioritized social validation and reputation enhancement.
2. **LURKER / PASSIVE_OBSERVER**: High likelihood of choosing `DO_NOTHING` or `LIKE_POST`; rarely creates original content but accounts for audience volume.
3. **EXPERT / SKEPTIC**: Highly analytical, debunks rumors, insists on primary factual citations, utilizes structured argumentation.
4. **TROLL / INSTIGATOR**: Elevated *Neuroticism* and low *Agreeableness*; purposefully stokes outrage and comment flame wars.
5. **ECHO_AMPLIFIER / PARTISAN**: Extreme ideological homophily; amplifies in-group narratives indiscriminately without fact verification.
6. **NEUTRAL / PRAGMATIST**: Proportionate reactions, mediatory stance in disputes, high emotional equilibrium.

---

## 5. Cross-Platform Parallel Coordinator

To execute simulations across 7 platforms simultaneously without race conditions, MiroFish utilizes a **Synchronized Multi-Worker Pool**:

```
                              ┌──────────────────────────────────┐
                              │   Cross-Platform Orchestrator    │
                              │ (backend/scripts/coordinator.py) │
                              └─────────────────┬────────────────┘
                                                │
             ┌──────────────┬──────────────┬────┴─────────┬──────────────┬──────────────┐
             ▼              ▼              ▼              ▼              ▼              ▼
       ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
       │  Twitter  │  │     X     │  │  Reddit   │  │  TikTok   │  │ Instagram │  │ Facebook  │
       │  Worker   │  │  Worker   │  │  Worker   │  │  Worker   │  │  Worker   │  │  Worker   │
       └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
             │              │              │              │              │              │
             └──────────────┴──────────────┼──────────────┴──────────────┴──────────────┘
                                           │
                                           ▼
                     ┌───────────────────────────────────────────┐
                     │          Sync Barrier Round t -> t+1      │
                     ├───────────────────────────────────────────┤
                     │ 1. Half-life Decay Evaluation             │
                     │ 2. Cross-Platform Content Spillover       │
                     │ 3. Unified Zep Graph Memory Update        │
                     │ 4. SHA-256 Round Checkpoint Generation    │
                     └───────────────────────────────────────────┘
```

### 5.1 Cross-Platform Spillover Diffusion
In real-world social dynamics, screenshots of viral posts migrate between platforms. This phenomenon is modeled using a probability transfer matrix:

\[
\text{Spillover}(p_{src} \to p_{dst}) = \sigma_{spill}^{(p_{src})} \cdot \mathbf{M}_{trans}[p_{src}, p_{dst}]
\]
