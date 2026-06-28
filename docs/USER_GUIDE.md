# HeartCompass (Digital Immortality) -- User Guide

**Version:** v1.0.0 | **Last Updated:** June 2026

---

## Table of Contents

1. [Introduction to HeartCompass](#1-introduction-to-heartcompass)
   - [What Is HeartCompass?](#11-what-is-heartcompass)
   - [Core Concepts](#12-core-concepts)
   - [Use Cases](#13-use-cases)
2. [Getting Started](#2-getting-started)
   - [Prerequisites](#21-prerequisites)
   - [Installation](#22-installation)
   - [First-Time Setup](#23-first-time-setup)
   - [Account Registration](#24-account-registration)
   - [Logging In](#25-logging-in)
   - [Binding Your Lark Account](#26-binding-your-lark-account)
   - [Starting the Lark Service](#27-starting-the-lark-service)
3. [Managing Digital Personas](#3-managing-digital-personas)
   - [What Is a Persona?](#31-what-is-a-persona)
   - [Creating a Persona](#32-creating-a-persona)
   - [Listing Your Personas](#33-listing-your-personas)
   - [Viewing Persona Details](#34-viewing-persona-details)
   - [Syncing Feeds to Persona Core](#35-syncing-feeds-to-persona-core)
4. [Conversing with Personas (Lark Bot)](#4-conversing-with-personas-lark-bot)
   - [Starting a Conversation](#41-starting-a-conversation)
   - [Natural Conversation Tips](#42-natural-conversation-tips)
   - [Understanding Persona Responses](#43-understanding-persona-responses)
   - [Viewing Persona Info with /show_persona](#44-viewing-persona-info-with-show_persona)
   - [Switching Personas](#45-switching-personas)
   - [Clearing Conversation Context](#46-clearing-conversation-context)
   - [Listing Available Personas](#47-listing-available-personas)
   - [Getting Help with /menu](#48-getting-help-with-menu)
5. [Building and Enriching Personas](#5-building-and-enriching-personas)
   - [The /build_persona Command](#51-the-build_persona-command)
   - [What Information to Provide](#52-what-information-to-provide)
   - [How the System Extracts and Updates Persona Knowledge](#53-how-the-system-extracts-and-updates-persona-knowledge)
   - [Understanding Build Reports](#54-understanding-build-reports)
   - [Best Practices for Providing Quality Information](#55-best-practices-for-providing-quality-information)
6. [Understanding Persona Dimensions](#6-understanding-persona-dimensions)
   - [Personality Traits](#61-personality-traits)
   - [Interaction Style](#62-interaction-style)
   - [Procedural Information](#63-procedural-information)
   - [Memory](#64-memory)
   - [How Dimensions Affect Conversation](#65-how-dimensions-affect-conversation)
7. [Tips and Best Practices](#7-tips-and-best-practices)
   - [Providing Effective Persona-Building Information](#71-providing-effective-persona-building-information)
   - [Conversation Tips for Natural Interaction](#72-conversation-tips-for-natural-interaction)
   - [Understanding Limitations](#73-understanding-limitations)
   - [Privacy and Data Considerations](#74-privacy-and-data-considerations)
8. [Troubleshooting](#8-troubleshooting)
   - [Common Error Messages and Their Meanings](#81-common-error-messages-and-their-meanings)
   - [What to Do When the Bot Does Not Respond](#82-what-to-do-when-the-bot-does-not-respond)
   - [Account and Binding Issues](#83-account-and-binding-issues)
   - [Service and Environment Issues](#84-service-and-environment-issues)
9. [Appendix: Complete Command Reference](#9-appendix-complete-command-reference)
   - [CLI Commands](#91-cli-commands)
   - [Lark Bot Commands](#92-lark-bot-commands)

---

## 1. Introduction to HeartCompass

### 1.1 What Is HeartCompass?

HeartCompass (also known as Digital Immortality) is an AI-powered digital persona system. It lets you create virtual representations of real people -- called **figures** -- and have natural conversations with them through a Lark (Feishu) bot interface.

Unlike generic chatbots, HeartCompass does not simply ask an AI to "pretend to be someone." Instead, it builds a structured, multi-dimensional understanding of each person: their personality, how they communicate, their life experiences, and how they approach problems. This structured knowledge is stored in a database and retrieved intelligently during conversations, so the AI can respond in a way that genuinely reflects the person you are talking to.

HeartCompass has two primary interfaces:

- **CLI (Command Line Interface):** For account management, persona creation, health checks, and service administration.
- **Lark/Feishu Bot:** For everyday conversations with your digital personas.

### 1.2 Core Concepts

Before diving in, it helps to understand the key concepts that HeartCompass uses:

**Figure**

A "figure" is the real person you want to create a digital representation of. This could be a family member, a close friend, a mentor, a colleague, a partner, a public figure, or even yourself. Each figure has a name, gender, and other basic attributes that describe them.

**FigureRole**

The role defines the relationship between you (the user) and the figure. HeartCompass supports the following roles:

| Role | Description |
|---|---|
| `self` | A digital version of yourself |
| `family` | A family member |
| `friend` | A close or casual friend |
| `mentor` | A teacher, advisor, or mentor |
| `colleague` | A coworker or professional peer |
| `partner` | A romantic partner or spouse |
| `public_figure` | A public personality (author, artist, etc.) |
| `stranger` | Someone you do not yet know well |

The role matters because it shapes how the AI communicates: a conversation with a "partner" persona feels warm and intimate, while one with a "colleague" is more professional yet friendly.

**FigureAndRelation (FR)**

Shortened to "FR" throughout the system, this is the central data entity that ties a figure, its role, and all related knowledge together. Each FR has a unique numeric ID (e.g., `1`, `2`, `3`) that you use to reference it.

**Persona**

A persona is the complete digital portrait of a figure. It includes:

- **Core personality:** What the person is fundamentally like -- their values, temperament, and worldview.
- **Core interaction style:** How they communicate -- their tone, formality level, and conversational habits.
- **Core procedural information:** How they do things -- their approach to work, decision-making style, and habits.
- **Core memory:** Key life events, stories, and experiences that shape who they are.

**FineGrainedFeed (Feed)**

Feeds are granular pieces of information about a figure, organized by dimension (personality, interaction style, procedural info, memory). Each feed is vectorized and stored in the database so the system can semantically search for the most relevant memories and facts during a conversation.

**Dimension**

Dimensions are the categories that feeds are organized into. There are four main dimensions:

- `personality` -- character traits and values
- `interaction_style` -- communication patterns and style
- `procedural_info` -- how the person works and makes decisions
- `memory` -- specific life events and experiences

### 1.3 Use Cases

HeartCompass can serve many purposes. Here are some of the most common use cases our users have found:

**Preserving Relationships.** Stay connected with loved ones by capturing their unique personality and communication style. Whether it is a family member who lives far away, a mentor whose wisdom you want to keep accessible, or a partner you want to feel close to even when apart, HeartCompass helps you maintain a meaningful connection.

**Remembering and Honoring.** Create a digital legacy for someone important to you. By providing stories, memories, and descriptions of a person, you build a representation that others can interact with -- a way of keeping their memory alive.

**Self-Reflection.** Build a persona of yourself. By providing your own writings, thoughts, and descriptions of how others see you, you can have conversations with your own digital self. This can be a powerful tool for self-understanding and personal growth.

**Learning from Mentors.** Capture the knowledge, wisdom, and communication style of a mentor. Even when they are not available, you can have reflective conversations that draw on their way of thinking.

**Creative and Literary Exploration.** Use HeartCompass to bring fictional characters or historical figures to life by feeding in written material and exploring how they might respond in conversation.

---

## 2. Getting Started

### 2.1 Prerequisites

Before installing HeartCompass, you need:

- **Python 3.11 or later** installed on your system
- **Docker** (recommended) for automatic database setup, or a **PostgreSQL 16+** database with the `pgvector` extension if you prefer manual setup
- A **Lark/Feishu account** (for the bot interface)
- A **Volcano Ark (火山方舟) account** with an API key (for the AI model)

### 2.2 Installation

HeartCompass is distributed as a Python package called `digital-immortality`. You can install it using `uv` (recommended) or `pip`.

**Using uv (recommended):**

First, install `uv` if you have not already:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install the CLI tool:

```bash
uv tool install digital-immortality --default-index https://pypi.org/simple
```

**Using pip:**

```bash
pip install digital-immortality -i https://pypi.org/simple
```

After installation, restart your terminal and verify the command is available:

```bash
immortality --help
```

You should see a help message listing all available commands.

### 2.3 First-Time Setup

The `setup` command guides you through configuring HeartCompass for the first time. It handles database configuration, environment variables, and model settings.

```bash
immortality setup
```

The setup wizard will ask you a series of questions:

**Database configuration:**

You will first choose between two database setup modes:

- **Docker setup (recommended):** The CLI automatically pulls the `pgvector/pgvector:pg16` Docker image, starts a PostgreSQL container, creates the required databases (`immortality` and `immortality_checkpoint`), and initializes the vector extension. This is the easiest option.
- **Manual setup:** You provide connection details for an existing PostgreSQL 16+ database with the `pgvector` extension. You will need to enter the host, port, username, and password.

**Model configuration (Volcano Ark):**

You need a Volcano Ark API key and model endpoints. The setup will ask for:

- `ark_api_key`: Your API key from the Volcano Ark console.
- `lite_model_endpoint_or_model_id`: The primary model for conversation and persona building. Recommended: `doubao-seed-2-0-lite-260215`.
- `mini_model_endpoint_or_model_id`: A smaller, faster model for lightweight tasks like field comparison and summarization. Recommended: `doubao-seed-2-0-mini-260215`.
- `embedding_model_endpoint_or_model_id`: The model for vector embeddings (semantic search). Recommended: `doubao-embedding-vision-251215`.

For higher stability, you can create dedicated inference endpoints for each model in the Volcano Ark console and use the endpoint IDs instead of model names.

**Lark bot configuration:**

You will need:

- `lark_bot_app_id`: Your Lark application's App ID.
- `lark_bot_app_secret`: Your Lark application's App Secret.
- `lark_card_template_id`: A card template ID for rich message formatting in Lark.

Refer to the main README for detailed instructions on setting up a Lark bot application and card template.

**After setup:**

All configuration is written to `~/.immortality/.env`. Logs are stored in `~/.immortality/logs/`. Docker compose files (if using Docker mode) are placed in `~/.immortality/docker-compose.yml`.

### 2.4 Account Registration

Create your HeartCompass user account using the CLI:

```bash
immortality auth register
```

You will be prompted for:

- **Username:** A unique username for login.
- **Nickname:** A display name (shown to personas during conversation).
- **Gender:** Choose from `male`, `female`, or `other`.
- **Email:** A valid email address.
- **Password:** Your account password.
- **Confirm password:** Re-enter for confirmation.

You may also provide all information as command-line arguments:

```bash
immortality auth register \
  --username yourname \
  --nickname "Your Nickname" \
  --gender male \
  --email you@example.com \
  --password yourpassword \
  --confirm-password yourpassword
```

### 2.5 Logging In

Once registered, log in to activate your local session:

```bash
immortality auth login
```

You will be prompted for your username (or email) and password. On success, an access token is saved locally in `~/.immortality/`, and you are ready to use all CLI features.

You can also provide credentials directly:

```bash
immortality auth login --username yourname --password yourpassword
```

**Checking your login status:**

```bash
immortality auth whoami
```

This displays your user ID, username, nickname, email, gender, and account level.

**Logging out:**

```bash
immortality auth logout
```

This clears your local session. You will need to log in again before using other commands.

**Changing your password:**

```bash
immortality auth modify-password
```

You will be prompted for your old password and new password.

### 2.6 Binding Your Lark Account

To use the Lark bot, you must link your Lark account to your HeartCompass user account. This tells the system which Lark user corresponds to which HeartCompass user.

**Step 1: Find your Lark Open ID.**

Visit the Lark open platform API debug console and locate your `open_id`. The exact steps are documented in the main README under "Bind Feishu open_id."

**Step 2: Bind using the CLI.**

```bash
immortality auth bind-lark --lark-open-id <your_lark_open_id>
```

Example:

```bash
immortality auth bind-lark --lark-open-id ou_abc123def456
```

On success, your Lark account is linked. You only need to do this once.

### 2.7 Starting the Lark Service

The Lark service connects HeartCompass to the Lark platform via WebSocket, enabling the bot to receive and respond to messages.

**Health check first:**

Before starting, run a health check to verify everything is configured correctly:

```bash
immortality doctor
```

This checks Python version, required environment variables, dependency completeness, and database connectivity. If anything is wrong, it tells you exactly what to fix.

**Starting the service (foreground, for debugging):**

```bash
immortality lark-service start
```

The service runs in the foreground, so you can see log output directly. Press `Ctrl+C` to stop.

**Starting the service (background, for production):**

For long-running use, start the service in the background:

```bash
nohup immortality lark-service start &
```

To find the running process:

```bash
pgrep -af immortality
```

To stop the service:

```bash
kill <pid>
```

**Viewing logs:**

```bash
immortality logs [--date YYYYMMDD]
```

If `--date` is omitted, today's logs are shown.

---

## 3. Managing Digital Personas

### 3.1 What Is a Persona?

A persona is a digital representation of a real person. When you create a persona, you are telling HeartCompass: "I want to talk to this specific person." Every persona is uniquely yours -- it is tied to your user account and represents your personal relationship with that figure.

A persona is identified by a numeric **FR ID** (e.g., `1`, `2`, `3`). You will use this ID throughout the system to reference specific personas.

### 3.2 Creating a Persona

Use the `immortality fr add` command to create a new digital persona:

```bash
immortality fr add
```

You will be prompted for several pieces of information:

**Required fields:**

- **Name:** The figure's real name (e.g., "Zhang Wei").
- **Gender:** `male`, `female`, or `other`.
- **Role:** The figure's relationship to you. Choose from:
  - `self` -- yourself
  - `family` -- family member
  - `friend` -- friend
  - `mentor` -- teacher or advisor
  - `colleague` -- coworker
  - `partner` -- romantic partner
  - `public_figure` -- public personality
  - `stranger` -- someone you do not know well yet

**Optional fields:**

- **Exact Relation:** A more detailed description of the relationship (e.g., "college roommate from 2018-2022" or "my direct manager at Acme Corp").
- **MBTI:** The figure's Myers-Briggs personality type (e.g., `INTJ`, `ENFP`).
- **Birthday:** The figure's birthday.
- **Occupation:** Their job or profession.
- **Education:** Their educational background.
- **Residence:** Where they currently live.
- **Hometown:** Where they are originally from.

You can also provide the required fields directly as arguments:

```bash
immortality fr add --name "Zhang Wei" --gender male --role friend
```

**Important:** At this point, the persona has basic metadata but no personality information yet. The persona will not be very lifelike until you build it up using the `/build_persona` command (covered in Section 5).

### 3.3 Listing Your Personas

To see all the personas you have created:

```bash
immortality fr list
```

This displays a table showing each persona's ID, role, and name. Example output:

```
+----+--------------+-------------+
| id | figure_role  | figure_name |
+----+--------------+-------------+
|  1 | FAMILY       | Mom         |
|  2 | FRIEND       | Zhang Wei   |
|  3 | MENTOR       | Dr. Chen    |
+----+--------------+-------------+
```

For machine-readable output, add the `--json` flag:

```bash
immortality fr list --json
```

### 3.4 Viewing Persona Details

To see the complete portrait of a specific persona:

```bash
immortality fr show --id <fr_id>
```

Example:

```bash
immortality fr show --id 1
```

This displays the persona's core personality, interaction style, procedural information, and memory -- all in markdown format. If no information has been added yet, you will see a message indicating that the persona is empty.

**Semantic search within a persona:**

You can also provide a query to retrieve specific, semantically relevant information:

```bash
immortality fr show --id 1 --query "communication style and conflict handling"
```

This searches the persona's fine-grained feeds for information related to your query and returns the most relevant results. This is especially useful for large personas with many stored memories and details.

### 3.5 Syncing Feeds to Persona Core

As you build up your persona with fine-grained information (feeds), the system can synthesize that information into the persona's core fields (core personality, core interaction style, core procedural info, core memory). This is done with the sync command:

```bash
# Sync a specific persona
immortality fr sync-feeds --id <fr_id>

# Sync all of your personas
immortality fr sync-feeds
```

This process can take a while because it involves comparing, merging, and condensing many individual feeds into coherent summaries. It is recommended to run this periodically (e.g., daily or every other day) as a cron job, rather than after every single persona update.

---

## 4. Conversing with Personas (Lark Bot)

The Lark bot is where HeartCompass comes alive. Once your Lark service is running, you can open a direct message with your bot in the Lark/Feishu app and start conversing with any of your personas.

### 4.1 Starting a Conversation

Before you can chat, you need to tell the bot which persona you want to talk to. Send the FR ID prefixed with a slash:

```
/1
```

If the persona exists and belongs to you, the bot responds with a confirmation card:

```
Dialogue Partner Switched Successfully
I am Zhang Wei
```

From this point on, every message you send will be treated as a message to Zhang Wei, and the bot will respond as Zhang Wei would.

**If you have not selected a persona yet**, the bot will prompt you:

```
Please send `/<fr_id>` to switch to a dialogue partner first, for example `/1`
```

### 4.2 Natural Conversation Tips

HeartCompass is designed to feel like chatting with a real person, not a customer service bot. Here are some tips for natural conversation:

**Talk like you normally would.** Do not feel like you need to ask perfect questions. Real conversations are messy -- you can joke, complain, share random thoughts, or just say hi.

**Send multiple short messages.** Real people do not write essays in chat. You can send several short messages in a row. The bot batches messages that arrive within a 15-second window and processes them together, just as a real person reads a burst of messages.

**You do not need to reply to everything.** Just like in a real conversation, the persona might mention multiple things. You can pick up on what interests you and ignore the rest.

**Change topics naturally.** You can shift the conversation to a new topic without warning. The system retrieves relevant memories for each new context, so the persona can follow along.

**Be patient with the response time.** The system processes messages in batches (default 15-second window), so there may be a short delay between your last message and the response. This is by design -- it allows the system to gather a cluster of messages before processing, which leads to better conversation flow.

### 4.3 Understanding Persona Responses

The AI persona's response is shaped by several factors:

**Role-specific tone (formality):**

The system adjusts the tone of responses based on the figure's role:

| Role | Tone |
|---|---|
| `family` | Very casual and warm. Uses colloquial language freely. |
| `friend` | Casual and familiar. Feels like texting a close friend. |
| `partner` | Warm and intimate. Emotionally expressive. |
| `mentor` | Professional but approachable. Balanced between warmth and authority. |
| `colleague` | Professional and friendly. Appropriate for a workplace. |
| `self` | Reflects your own documented communication style. |
| `public_figure` | Context-dependent, based on the information provided. |
| `stranger` | Polite and somewhat restrained. |

**Language consistency:**

The persona will always respond in the same language you use. If you write in Chinese, the persona responds in Chinese. If you mix languages, the persona follows your pattern.

**Anti-repetition:**

The system actively avoids repeating the same phrases and sentence structures across consecutive turns. This keeps conversations feeling fresh and natural rather than robotic.

**Message splitting:**

Personas typically send 1 to 3 short messages per turn rather than one long block of text. This mimics real messaging behavior, where people often send a few quick messages in succession.

### 4.4 Viewing Persona Info with /show_persona

You can view the current state of any persona's profile directly in Lark:

```
/show_persona:1
```

This shows the persona's core personality, interaction style, procedural information, and memory.

You can also add a query for semantic search:

```
/show_persona:1
communication style and conflict handling
```

Note: the query goes on the second line, after the command. This retrieves the most relevant fine-grained feeds that match your query.

**What you will see:**

The response is a card containing the persona's structured profile. If a field has not been populated yet, you will see a placeholder like "Collecting personality information..." or "Analyzing interaction patterns..."

### 4.5 Switching Personas

You can switch between personas at any time:

```
/2
```

This immediately switches the conversation to persona ID 2. The previous conversation context is preserved so you can switch back and pick up where you left off.

Each persona maintains its own conversation history and short-term memory, so switching between them is seamless.

### 4.6 Clearing Conversation Context

If the conversation with a persona feels like it is getting stuck on old topics, or if you want a completely fresh start, you can clear the context:

```
/clear_current_person
```

This removes the currently active persona from your session. After clearing, you will need to select a persona again with `/<fr_id>` before you can chat.

Note that clearing context only affects your current session state. It does not delete any stored persona data or conversation history.

### 4.7 Listing Available Personas

To see all personas available to you:

```
/list_available_persons
```

The bot responds with a formatted list showing each persona's name, role, and FR ID:

```
Available Dialogue Partners:

- Mom - FAMILY
  fr_id: 1
- Zhang Wei - FRIEND
  fr_id: 2
- Dr. Chen - MENTOR
  fr_id: 3

Send `/<fr_id>` to switch
```

### 4.8 Getting Help with /menu

At any time, you can ask the bot for the full list of available commands:

```
/menu
```

The bot displays all supported commands with usage hints:

1. `/menu` -- Show this menu
2. `/list_available_persons` -- List all available dialogue partners
3. `/<fr_id>` -- Switch to a specific dialogue partner
4. `/clear_current_person` -- Clear the current dialogue partner
5. `/show_persona:<fr_id>` -- View a persona's full profile
6. `/build_persona:<fr_id>` -- Build or enrich a persona's profile

---

## 5. Building and Enriching Personas

A newly created persona is an empty shell -- it has a name and a role, but no personality, no memories, and no communication style. The real magic of HeartCompass happens when you **build** the persona by providing information about the figure.

### 5.1 The /build_persona Command

The primary way to enrich a persona is through the `/build_persona` command in Lark:

```
/build_persona:1
Zhang Wei is my best friend from college. We met in 2018 during freshman orientation. He has a very dry sense of humor and often makes deadpan jokes that take a moment to land. He works as a software engineer and is deeply passionate about open-source projects. When he is stressed, he tends to go quiet rather than talk about it. He loves hiking and has a tradition of doing a big hike every year on his birthday in October.
```

**Format:**

```
/build_persona:<fr_id>
<your text here>
```

The FR ID goes on the first line (after the colon), and the information you want to provide goes on subsequent lines.

**What happens when you send this:**

1. The bot immediately acknowledges the task: "Task started -- now building Zhang Wei's persona profile. You will be notified when complete."
2. The system processes your text in the background using a multi-step pipeline (the FRBuildingGraph).
3. When complete, you receive a success confirmation and a **build report** summarizing what was learned and updated.

**Processing time:** The build process typically takes a few seconds to tens of seconds, depending on the length of your input and the complexity of the persona being updated.

**Cannot run two builds at once:** If a persona build is already in progress, sending another `/build_persona` command for the same persona will result in a "Please try again later" message. Wait for the current build to finish.

### 5.2 What Information to Provide

The quality of your persona depends heavily on the quality of information you provide. The system is designed to handle many different types of input:

**Personal descriptions and narratives.** The most common and flexible type. Simply describe the person in your own words. Talk about their personality, habits, stories, quirks, and how they interact with you and others.

Example:

```
/build_persona:1
Mom is the most patient person I know. She taught elementary school for 30 years before retiring. She has this way of listening that makes you feel like you are the only person in the world. Her advice is never pushy -- she asks questions that help you figure things out yourself. She loves gardening and can name every plant in her neighborhood. Her cooking is legendary among our family, especially her dumplings which she learned from her own mother.
```

**Chat logs and conversation records.** If you have real chat histories with the person, you can paste them in. This is incredibly valuable because it captures the person's authentic communication style: word choice, sentence length, emoji usage, and conversational rhythm.

Example:

```
/build_persona:2
Here are some messages Zhang Wei sent me:

Zhang Wei: lol that meeting was a complete waste of time
Zhang Wei: the PM spent 20 minutes explaining something that could have been a slack message
Zhang Wei: anyway you free for lunch? new ramen place opened

Zhang Wei: honestly i think you should just go for it
Zhang Wei: worst case it doesn't work out and you learn something
Zhang Wei: best case... well, you know
```

**Long-form writings by the person.** If the figure has written blog posts, journal entries, letters, articles, or any other substantial text, provide it. This reveals their thinking style, vocabulary, and how they structure ideas.

**Social media content.** Public posts, tweets, or status updates capture the person's public voice and the topics they care about.

**Work artifacts.** For colleagues and mentors, you can provide code reviews, design documents, project reports, or meeting notes that show how they approach problems and communicate in a professional context.

**Interviews and transcripts.** For public figures, transcripts of interviews or speeches are excellent sources of authentic speech patterns and viewpoints.

**Creative works.** Art, fiction, poetry, or music created by the person can reveal their inner world, values, and aesthetic sensibilities.

### 5.3 How the System Extracts and Updates Persona Knowledge

When you submit information via `/build_persona`, the system runs a sophisticated multi-step pipeline (the **FRBuildingGraph**). Here is what happens behind the scenes:

**Step 1: Load and validate.** The system checks that the FR ID is valid and belongs to you.

**Step 2: Preprocess the input.** An AI model cleans and structures your raw text. It identifies:
- **Source type:** Is this a personal narrative, a chat log, a published article, etc.?
- **Confidence level:** How reliable is this information? Options are `verbatim` (direct quote), `artifact` (from a document or public content), or `impression` (your subjective impression).
- **Involved dimensions:** Which aspects of the persona does this information touch on (personality, interaction style, procedural info, memory)?
- **Approximate date:** When did the described events or observations occur?

**Step 3: Save original source.** The preprocessed content is saved as an `OriginalSource` record, preserving the raw material for future reference and traceability.

**Step 4: Extract persona core fields.** The system attempts to extract basic information about the figure that can be stored directly in the persona record: things like occupation, MBTI type, likes/dislikes, appearance, and characteristic phrases (words the figure says to you, and words you say to the figure).

**Step 5: Compare and update.** For each extracted field, the system compares the new value against the existing value:
- If the field is empty, the new value is adopted directly.
- If the new value matches the old, nothing changes.
- If they differ, an AI model compares them and decides whether to merge, replace, or flag as a conflict.

**Step 6: Extract fine-grained feeds.** The system extracts detailed, dimension-specific information from your input. Each feed is tagged with its dimension (personality, interaction style, procedural info, memory), a sub-dimension for finer categorization, and a confidence level.

**Step 7: Plan upserts.** Each new feed is compared against existing feeds using semantic search. The system decides whether to:
- **Add** a new feed (no similar feed exists)
- **Update** an existing feed (new information supplements or improves old)
- **Skip** (the new feed is equivalent to an existing one)
- **Flag a conflict** (the new information contradicts existing knowledge)

**Step 8: Persist changes.** All decisions are written to the database. Conflicts are recorded in a dedicated conflict table for potential human review.

**Step 9: Generate the build report.** An AI model summarizes all changes into a readable report, which is saved and sent back to you in Lark.

### 5.4 Understanding Build Reports

After a successful build, the bot sends you a **persona build report**. This report summarizes what the system learned and how it updated the persona. Reading these reports helps you understand:

- **What new information was added.** New facts, traits, memories, or stylistic observations that the system incorporated.
- **What existing information was updated.** Details that were enriched or refined based on your new input.
- **What was skipped.** Information that was already present in the persona.
- **Any conflicts detected.** Contradictions between new and old information that the system flagged for attention.

The report is informational -- no action is required from you. However, reviewing reports periodically helps you ensure the persona is developing accurately and gives you insight into what kind of additional information might be most valuable.

### 5.5 Best Practices for Providing Quality Information

**Be specific, not generic.** "She is a nice person" is less useful than "She always remembers everyone's birthday and sends handwritten cards." Specific details create a vivid, recognizable persona.

**Provide varied types of information.** Mix narratives with chat logs, mix stories with observations. Each type reveals different dimensions of the person.

**Include concrete examples.** Instead of saying "He is funny," share a specific joke he made or a situation where his humor shone. Instead of "She is a good leader," describe a specific incident where her leadership made a difference.

**Capture the full person.** Include strengths and weaknesses, good habits and bad. A realistic persona includes imperfections -- they make the person feel real.

**Keep building over time.** A persona gets better with each build. Do not try to capture everything in one go. Add information as you think of it. Regular, incremental building produces the richest results.

**Use /show_persona to check progress.** After a few builds, use `/show_persona:<id>` to review the current state of the persona. This helps you identify gaps -- what aspects of the person are still missing?

**Run sync-feeds periodically.** The fine-grained feeds you build up are valuable, but they become even more powerful when condensed into the persona's core fields. Run `immortality fr sync-feeds` regularly to synthesize feeds into the core profile.

---

## 6. Understanding Persona Dimensions

HeartCompass organizes all knowledge about a figure into four dimensions. Understanding these dimensions helps you provide better information and understand how the system works.

### 6.1 Personality Traits

**What it covers:** The figure's fundamental character -- their values, temperament, worldview, emotional patterns, and core beliefs.

**Examples of personality information:**
- "She is an optimist who always finds the silver lining, even in genuinely difficult situations."
- "He has a strong sense of justice and will speak up when he sees unfairness, even if it makes things awkward."
- "Deeply introverted. She recharges by being alone and finds large social gatherings exhausting."

**How it is used in conversation:** The persona's personality shapes the emotional tone, values expressed, and overall demeanor of responses. A fundamentally optimistic persona will tend to find positive angles, while a more cynical one might express skepticism.

### 6.2 Interaction Style

**What it covers:** How the figure communicates -- their tone, pace, word choice, conversational habits, and relationship dynamics.

**Examples of interaction style information:**
- "He uses a lot of emojis in text, especially the crying-laughing one."
- "She tends to ask a lot of questions rather than making statements. Conversations with her feel like gentle interviews."
- "His humor is very dry and deadpan. He rarely signals jokes with tone or emoji, so you have to pay attention to know he is kidding."

**How it is used in conversation:** This is one of the most visible dimensions. The interaction style directly shapes how the persona structures messages, what kind of language it uses, and the rhythm of the conversation. The system also captures `words_figure2user` (characteristic things the figure says to you) and `words_user2figure` (characteristic things you say to the figure) to make the conversation feel authentic.

### 6.3 Procedural Information

**What it covers:** How the figure does things -- their approach to work, decision-making process, problem-solving style, habits, routines, and methods.

**Examples of procedural information:**
- "She always makes pro-con lists before big decisions. She taught me to do the same."
- "At work, he is known for writing incredibly detailed design docs before writing any code."
- "His morning routine is sacred -- coffee, 30 minutes of reading, then a walk. He gets irritable if anything disrupts this."

**How it is used in conversation:** Procedural information is retrieved contextually. When you ask the persona for advice, discuss work, or talk about plans, the system pulls in relevant procedural knowledge. This makes the persona's advice and perspectives feel grounded in their actual approach to life.

### 6.4 Memory

**What it covers:** Specific events, experiences, stories, and shared history. This is the narrative dimension of the persona.

**Examples of memory information:**
- "In 2019, we took a road trip to Yunnan. The car broke down near Dali and we spent an unexpected night in a tiny village guesthouse, which turned out to be the highlight of the trip."
- "She won a national calligraphy competition when she was 16. Her parents still have the winning piece framed in their living room."
- "He once gave a talk at a conference and the projector failed. He delivered the entire presentation from memory using a whiteboard, and got a standing ovation."

**How it is used in conversation:** Memories are retrieved based on semantic similarity to the current conversation. If you mention travel, the road trip memory might surface. If you discuss achievements, the calligraphy memory could appear. The persona uses memories to enrich conversation naturally -- mentioning relevant shared experiences, drawing on past lessons, or telling stories when they fit the context.

### 6.5 How Dimensions Affect Conversation

During a conversation, the system does not dump all persona information into the AI's context window. Instead, it takes a targeted approach:

**Always loaded:**
- The persona's core personality and interaction style (these are fundamental to every response)
- The figure's characteristic phrases (`words_figure2user`)

**Semantically retrieved (as needed):**
- Relevant procedural information (matched to the conversation topic)
- Relevant memories (matched to the conversation context)

**Short-term conversation memory:**
- Recent messages in the current conversation (up to a character and message count limit)
- A rolling summary of older messages that have been trimmed from the active context

This layered approach keeps the AI's responses grounded in the figure's personality while staying relevant to the current conversation, without overwhelming the system with irrelevant details.

---

## 7. Tips and Best Practices

### 7.1 Providing Effective Persona-Building Information

**Quality over quantity.** One well-chosen paragraph that captures something distinctive about a person is worth more than five paragraphs of generic description.

**Use the person's own voice.** Whenever possible, include content written or spoken by the actual person. Chat logs, emails, social media posts, and recorded conversations are goldmines of authentic communication data.

**Build incrementally.** Start with the most important or distinctive aspects of the person, then add more detail over time. Each build adds to and refines the persona -- it is a cumulative process.

**Cover all dimensions.** A persona with only personality information will feel one-dimensional. Try to provide information across all four dimensions (personality, interaction style, procedural info, memory) for the richest results.

**Include shared history.** Your relationship with the figure matters. Include stories about things you experienced together, inside jokes, and shared references. This makes the conversation feel personal and intimate.

**Do not worry about contradictions.** Real people are complex and sometimes contradictory. If you provide information that conflicts with existing knowledge, the system flags it rather than silently overwriting. You can review these conflicts later if needed.

**Be honest.** It can be tempting to idealize a person, but an honest portrayal -- including flaws, quirks, and imperfections -- produces a much more realistic and compelling persona.

### 7.2 Conversation Tips for Natural Interaction

**Start naturally.** Just say hi. Ask how they are doing. Mention something that happened today. The more you treat the conversation like a real chat, the more natural the responses will feel.

**Share context.** If you want to discuss something specific, provide a bit of context: "I just got out of a really frustrating meeting" gives the persona something to respond to meaningfully.

**Do not test the persona.** Asking "Do you remember X?" or "What is my name?" can break the illusion. The persona uses semantic memory retrieval, not exact factual lookup. It remembers stories, feelings, and patterns better than it remembers specific dates or names.

**Let the conversation flow.** Do not overthink your messages. Real conversations meander, change topics, and include non-sequiturs. The persona is designed to follow your lead naturally.

**Use the batch window.** Because messages within 15 seconds are batched together, you can send a quick series of related thoughts -- just like texting a real person. The persona will process them together and respond to the whole cluster.

**Respect the pauses.** The system intentionally batches messages, so do not expect instant replies. The slight delay is normal and actually makes the conversation feel more like real asynchronous messaging.

### 7.3 Understanding Limitations

**The persona is a representation, not the real person.** No matter how much information you provide, the AI is generating responses based on patterns. It will sometimes say things the real person would not say. Use the build command to refine when you notice inaccuracies.

**Factual precision is limited.** The system is optimized for personality and conversation style, not factual recall. If you ask about highly specific details (exact dates, addresses, phone numbers), the persona may not have precise answers, even if that information was provided.

**Emotional depth varies.** While the system produces emotionally nuanced responses, it is still an AI simulation. Deep emotional conversations may sometimes feel slightly off or miss subtle emotional cues that the real person would catch.

**The system improves with use.** The more you build and converse, the better the persona becomes. Early conversations with a newly created persona will be less convincing than conversations with a well-developed one.

**One persona per figure per user.** Each persona represents your unique relationship with that figure. If two users each create a persona for the same real person, the personas will develop differently based on what each user shares and how they interact.

**Short-term memory has limits.** The system maintains a rolling summary of older conversation, but very long conversations may lose some earlier context. If the conversation feels like it is drifting, use `/clear_current_person` and `/1` (or the relevant ID) to start fresh.

### 7.4 Privacy and Data Considerations

**Your data is yours.** All persona data is stored in your own database. The system does not share or transmit persona data to any third party beyond the AI model provider (Volcano Ark), which processes the data to generate responses and build personas.

**Sensitive information.** Be mindful of what you share, especially for real people who have not consented to having their persona created. The system does not automatically detect or filter sensitive personal information beyond basic email address masking in Lark card outputs.

**Account security.** Your CLI login session is stored locally. Keep your computer secure. Use strong passwords and change them periodically with `immortality auth modify-password`.

---

## 8. Troubleshooting

### 8.1 Common Error Messages and Their Meanings

**"Current Feishu account is not authorized. Please bind your account first."**

Your Lark account is not linked to a HeartCompass user. Run `immortality auth bind-lark --lark-open-id <your_id>` in the CLI.

**"Please send `/<fr_id>` to switch to a dialogue partner first."**

You have not selected a persona to talk to. Send `/<fr_id>` (e.g., `/1`) to choose one.

**"The current dialogue partner is unavailable. Please re-send `/<fr_id>` to switch."**

The selected persona no longer exists or no longer belongs to you. Use `/list_available_persons` to find available personas and switch.

**"Current account is not bound to any dialogue partner (FR)."**

You have not created any personas yet. Use `immortality fr add` in the CLI to create one.

**"No information found for this FR."**

The persona exists but has no content yet. Use `/build_persona:<id>` to add information, or check whether any build operations have completed successfully.

**"FRBuildingGraph is running, please wait until it finishes."**

A persona build operation is already in progress for this FR. Wait for it to complete before starting a new one. Only one build can run per persona at a time.

**"FR not found" or "Figure and relation not found."**

The FR ID you specified does not exist. Use `immortality fr list` or `/list_available_persons` to see valid IDs.

**"raw_content is too short."**

The information you provided via `/build_persona` is too short (fewer than 10 characters). Provide more substantial content for the system to work with.

### 8.2 What to Do When the Bot Does Not Respond

**Check if the Lark service is running.**

```bash
pgrep -af immortality
```

If no process is found, restart the service:

```bash
nohup immortality lark-service start &
```

**Check the logs for errors.**

```bash
immortality logs
```

Look for error messages or warnings that might explain the silence. Common issues include model API failures, database connection problems, or expired Lark tokens.

**Verify your Lark bot application is published.**

Log into the Lark open platform and check that your bot application has a published version. If the version was recently updated, you may need to re-publish.

**Check for duplicate messages being filtered.**

The system filters identical messages sent within 30 seconds (10 seconds for slash commands). If you keep sending the same message, it may be silently deduplicated. Try sending something different.

**Wait for the batch window.**

Messages are processed in batches with a 15-second delay. If you just sent a message, wait at least 15-20 seconds before concluding the bot is not responding.

### 8.3 Account and Binding Issues

**"Login failed" or incorrect credentials.**

Verify your username and password. If you have forgotten your password, you currently need to re-register with a different username. Password reset functionality is planned for a future release.

**"Access token is missing" after login.**

This indicates a server-side issue. Try logging out and logging back in:

```bash
immortality auth logout
immortality auth login
```

**Cannot bind Lark account.**

Make sure you are logged in first (`immortality auth whoami`). Then verify your Lark open ID is correct. The open ID should look something like `ou_xxxxxxxxxxxxx`.

**"User not found" when using CLI commands.**

Your local session may be invalid. Log out and log back in:

```bash
immortality auth logout
immortality auth login
```

### 8.4 Service and Environment Issues

**"Doctor" check fails.**

Run `immortality doctor` to see which checks are failing. The output includes specific guidance for each failure. Common failures:

- Missing environment variables: Re-run `immortality setup` to configure.
- Database unreachable: Check that PostgreSQL (or Docker container) is running.
- Python version too old: Upgrade to Python 3.11 or later.
- Dependencies incomplete: Reinstall the package.

**Database collation version mismatch.**

If you see "collation version mismatch" errors (especially after a Docker image update), your PostgreSQL volume may be from an older image. Reset it:

```bash
docker compose -f ~/.immortality/docker-compose.yml down -v
docker compose -f ~/.immortality/docker-compose.yml up -d postgres
immortality setup
immortality doctor
```

**Model API errors.**

If the persona responds with errors or fails to process, the Volcano Ark API may be experiencing issues. Check:
- Your API key is valid and has not expired.
- Your model endpoints are correctly configured.
- You have not exceeded your TPM (Tokens Per Minute) limit.

**"LARK_CARD_TEMPLATE_ID is not set."**

The card template ID is missing from your configuration. Run `immortality setup` again to configure it, or set it manually in `~/.immortality/.env`. The system will fall back to plain text messages if the card template is unavailable.

**Service crashes or hangs.**

Check the logs for unhandled exceptions:

```bash
immortality logs
```

If the service consistently crashes, try running it in the foreground to see live error output:

```bash
immortality lark-service start
```

---

## 9. Appendix: Complete Command Reference

### 9.1 CLI Commands

All CLI commands use the `immortality` prefix.

**Health and Setup:**

| Command | Description |
|---|---|
| `immortality doctor` | Run health checks on the environment |
| `immortality setup` | Interactive first-time configuration wizard |
| `immortality logs [--date YYYYMMDD]` | View service logs |

**Authentication:**

| Command | Description |
|---|---|
| `immortality auth register` | Create a new user account |
| `immortality auth login` | Log in to your account |
| `immortality auth logout` | Log out and clear local session |
| `immortality auth whoami` | Display current user information |
| `immortality auth modify-password` | Change your password |
| `immortality auth bind-lark --lark-open-id <id>` | Link your Lark account |

**Persona Management:**

| Command | Description |
|---|---|
| `immortality fr add` | Create a new persona (figure) |
| `immortality fr list` | List all your personas |
| `immortality fr show --id <id> [--query <text>]` | View a persona's full profile |
| `immortality fr sync-feeds [--id <id>]` | Synthesize feeds into persona core |

**Service:**

| Command | Description |
|---|---|
| `immortality lark-service start` | Start the Lark bot WebSocket service |

All CLI commands support `--json` for machine-readable output.

### 9.2 Lark Bot Commands

All bot commands are sent as messages in a direct chat with your Lark bot.

| Command | Description | Example |
|---|---|---|
| `/menu` | Show the help menu with all commands | `/menu` |
| `/list_available_persons` | List all personas you can talk to | `/list_available_persons` |
| `/<fr_id>` | Switch to a specific persona | `/1` |
| `/clear_current_person` | Clear the current conversation session | `/clear_current_person` |
| `/show_persona:<fr_id>` | View a persona's complete profile | `/show_persona:1` |
| `/show_persona:<fr_id>` + query | Search a persona's profile semantically | `/show_persona:1` (then on next line:) `communication style` |
| `/build_persona:<fr_id>` + text | Add information to build a persona | `/build_persona:1` (then on next line:) `Zhang Wei is...` |

---

HeartCompass is an evolving project. As you use it, you will discover your own best practices for building personas and having meaningful conversations. The system is designed to improve with every interaction -- both yours and the personas you create.

For technical documentation, architecture details, and contribution guidelines, see the other documents in the `docs/` directory. For questions or issues, refer to the project repository.
