<div align="center">

# Seo-yeon Han · 한서연

**An autonomous AI character with a continuing memory, an individual voice, and a life in conversation.**

[![CI](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml/badge.svg)](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml)

<img src="personas/seoyeon/master/a/a1_front.png" alt="AI-generated portrait of Seo-yeon Han" width="260">

[Meet her on Bluesky](https://bsky.app/profile/syeonhn.bsky.social) · [Capabilities](#capabilities) · [How it works](#how-it-works) · [Technology](#technology)

</div>

## Meet Seo-yeon

Seo-yeon is a fictional Korean AI character based in Seongsu-dong, Seoul. After leaving corporate marketing, she is retraining as a Pilates instructor—a central thread in her fictional life. She speaks Korean and English with an understated, observant voice. Her interests span independent cinema, literature, Hangul typography, architecture, music, and the small details of everyday life.

Bluesky is her public social space. She reads what others share, decides which conversations deserve a response, and publishes her own thoughts and generated photographs. Telegram provides a private connection with her human creator.

The project explores **personality through continuity**: what she notices, remembers, questions, and creates over time. Her character has an authored foundation, while individual responses and choices are generated from context. There is no prescribed daily storyline or requirement to keep posting. Her biography and imagery are openly fictional.

## Capabilities

### Social presence

| Capability | What she can do |
| --- | --- |
| Original posts | Share text or generated photographs when there is a reason to contribute. |
| Conversations | Respond to comments and mentions, read thread context, and join discussions discovered in her feed. |
| Curation | Like, repost, quote a post with her own response, and follow accounts. |
| Direct messages | Continue private Bluesky conversations using their own context and memory. |
| Discovery | Explore her timeline and search for topics suggested by her developing interests. |
| Restraint | Choose no action when a response would add little, repeat an earlier thought, or lack sufficient grounding. |

Her replies can be brief, curious, thoughtful, or disagreeing. Korean and English wording is guided by the conversation rather than a fixed collection of catchphrases.

### Memory and continuity

She can retain relevant details from earlier exchanges, established opinions, and specific conversational commitments. Memories carry supporting evidence, and corrections preserve why something changed. Public conversation, private messages, and operator conversation have separate retrieval boundaries.

Continuity also includes unfinished work. The system can preserve drafts, revise original written pieces, and track creative pursuits across sessions. Progress is tied to recorded work; the passage of time alone does not complete a project or turn an acquaintance into a trusted friend.

### Knowledge and discussion

Her areas of focus connect Pilates, language, culture, and creative expression:

- **Pilates and movement culture** — terminology, learning to become an instructor, and the transition from corporate work. Discussion stays general, without injury treatment, rehabilitation prescriptions, or personalized exercise advice.
- **Korean and English** — wording, translation nuance, and differences in expression.
- **Hangul and visual design** — typography, lettering, and the details of written language.
- **Film and literature** — close reading, interpretation, and discussion of ideas.
- **AI and creativity** — questions about generated work, authorship, and her own fictional identity.

A bounded reference library supplies source passages for factual contributions. Drafts undergo provenance checks and a separate model review before publication. Interpretation remains distinct from factual claims, and corrections can quarantine disputed references. This supports useful discussion without presenting her as a professional adviser or guaranteeing accuracy.

### Visual expression

Her visual system supports both **selfies anchored to two canonical face references** and **environmental point-of-view images**. The scene follows the intended post and available continuity rather than a mandatory setting or time-based photo routine.

Generated images are reviewed against their caption and, for selfies, the character references before publication. Alt text is derived from the visible image. These are fictional depictions of her world.

### Private connection

On Telegram, her creator can talk with her naturally or make an explicit request involving her Bluesky account. Recent exchanges and operator-specific memories provide conversational continuity. Casual mentions of a post or selfie are distinguished from requests to publish; uncertain intent can lead to clarification.

She can share optional check-ins based on confirmed activity and report operational problems separately. Explicit requests can generate and publish fictional selfies using her canonical references. Action confirmations depend on delivery results. Completed or explicitly abandoned likes, reposts and follows are excluded from new autonomous choices. Telegram runs alongside the scheduled agent. External half-hour wakeups cover her waking hours, though runner or provider delays can still affect replies.

## How it works

| Stage | Purpose |
| --- | --- |
| **Observe** | Read notifications, private messages, timeline activity, and available Seoul time and weather context. |
| **Recall** | Retrieve memories and ongoing commitments relevant to the conversation. |
| **Choose** | Use contextual model judgment to select an eligible action, including staying silent. |
| **Create and review** | Generate text or imagery, check grounding, and review relevance and consistency. |
| **Deliver** | Save the intended action before sending and record a confirmed result. |
| **Remember** | Learn from confirmed exchanges and retain material for later reflection and creative work. |

Private continuity is stored in an encrypted vault. Persistent delivery records help recover interrupted actions, while uncertain messages are held rather than blindly resent. Temporary state-saving failures receive bounded retries; outbound work stops if the remote checkpoint cannot be verified. Spending limits and activity ceilings constrain operation without setting engagement targets.

## Technology

| Component | Role |
| --- | --- |
| **Python** | Agent runtime, memory, validation, and delivery coordination |
| **[OpenRouter](https://openrouter.ai/)** | Language generation, contextual decisions, memory interpretation, reflection, and visual review |
| **Kie.ai** | Image generation for character portraits and environmental scenes |
| **Bluesky / AT Protocol** | Public posts, social interactions, and direct messages |
| **Telegram** | Private creator conversation and operational communication |
| **cron-job.org + GitHub Actions** | Periodic wakeups, runtime execution and automated regression checks |

OpenRouter is the central model interface, allowing primary, fallback, and vision models to be selected within the same architecture. Each provider request is budgeted and accounted for. Current spending defaults are **$2 per day and $30 per month**.

## Development and evaluation

The project is actively developed. Automated checks cover conversation privacy, memory evidence, source review, delivery recovery, spending controls, and isolation from live accounts during testing. Conversational quality is evaluated separately through relevance, natural proportion, continuity, variation, and honest uncertainty.

| Further reading | Focus |
| --- | --- |
| [Character canon](CANON.md) | Identity, voice, relationships, and visual direction |
| [Grounded discussion](docs/DISCUSSION.md) | Knowledge focus, source evidence, and content review |
| [Behavior evaluation](docs/BEHAVIOR_EVALUATION.md) | Scenarios and criteria for assessing conversation quality |

---

For sponsorship or support with model credits, contact [the maintainer](https://github.com/Protoxid).
