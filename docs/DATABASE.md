# HeartCompass Database Schema Documentation

## Table of Contents

1. [Database Overview](#1-database-overview)
2. [Entity-Relationship Diagram](#2-entity-relationship-diagram)
3. [Core Models](#3-core-models)
   - [3.1 User](#31-user)
   - [3.2 FigureAndRelation](#32-figureandrelation)
   - [3.3 FineGrainedFeed](#33-finegrainedfeed)
   - [3.4 OriginalSource](#34-originalsource)
   - [3.5 FineGrainedFeedConflict](#35-finegrainedfeedconflict)
   - [3.6 FROverallUpdateLog](#36-froverallupdatelog)
   - [3.7 FRBuildingGraphReport](#37-frbuildinggraphreport)
   - [3.8 Knowledge](#38-knowledge)
   - [3.9 Analysis](#39-analysis)
4. [Enum Types](#4-enum-types)
5. [Vector Indexing](#5-vector-indexing)
6. [Database Migrations](#6-database-migrations)
7. [Query Patterns](#7-query-patterns)

---

## 1. Database Overview

### 1.1 Technology Stack

| Component       | Version / Detail                                    |
|-----------------|-----------------------------------------------------|
| RDBMS           | PostgreSQL 16                                       |
| Vector Extension| pgvector (with HNSW index support)                  |
| ORM             | SQLAlchemy 2.0 (declarative mapping, `declarative_base`) |
| Migration Tool  | Alembic (autogenerate support)                      |
| Password Hashing| bcrypt                                              |
| Serialization   | Custom `SerializableMixin.toJson()`                 |
| Embedding Dim   | 1024 (cosine distance)                              |

### 1.2 Connection Configuration

The database engine is built from the `DATABASE_URI` environment variable. No default is provided — the application will fail fast if this variable is unset.

**Configuration source:** `src/database/index.py`

**Engine parameters:**

| Parameter      | Env Variable       | Default | Purpose                                  |
|----------------|--------------------|---------|------------------------------------------|
| `url`          | `DATABASE_URI`     | (none)  | PostgreSQL connection string             |
| `pool_size`    | `DB_POOL_SIZE`     | `5`     | Number of persistent connections         |
| `max_overflow` | `DB_MAX_OVERFLOW`  | `10`    | Additional connections beyond pool_size  |
| `pool_timeout` | `DB_POOL_TIMEOUT`  | `60`    | Seconds to wait for a connection         |
| `pool_recycle` | `DB_POOL_RECYCLE`  | `3600`  | Seconds before a connection is recycled  |
| `pool_pre_ping`| (hardcoded)        | `True`  | Verify connection liveness before use    |

**Session factory behavior:**

- Sessions are created with `autocommit=False` and `autoflush=False`.
- The engine and session factory are per-process: when `os.getpid()` changes (e.g., after a fork), the old engine is disposed and a new one is rebuilt. This is critical for multi-worker deployment scenarios.
- Use `session()` from `src.database.index` to obtain a scoped session.

**Example connection URI:**

```
postgresql://user:password@localhost:5432/heartcompass
```

### 1.3 Naming Convention

All database constraint names follow a deterministic pattern defined in `Base.metadata.naming_convention`:

| Constraint Type | Pattern                                      | Example                                 |
|-----------------|----------------------------------------------|-----------------------------------------|
| Primary Key     | `pk_%(table_name)s`                          | `pk_user`                              |
| Foreign Key     | `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s` | `fk_fine_grained_feed_fr_id_figure_and_relation` |
| Unique          | `uq_%(table_name)s_%(column_0_name)s`        | `uq_user_username`                     |
| Check           | `ck_%(table_name)s_%(column_0_name)s`        | (generated for Enum columns)           |
| Index           | `ix_%(column_0_label)s`                      | `ix_username`                          |

### 1.4 Database Initialization

The function `initDatabaseIfNeeded()` in `src/database/models.py` performs one-shot schema creation:

1. Creates the `pgvector` extension via raw SQL: `CREATE EXTENSION IF NOT EXISTS vector;`
2. Checks whether any tables exist via the SQLAlchemy inspector.
3. If the database is empty, calls `Base.metadata.create_all()` to create all tables, indexes, and constraints.

### 1.5 Soft Deletion Pattern

Several models use an `is_deleted` boolean flag rather than physical row deletion. This preserves referential integrity and enables audit trails. The models using soft deletion are:

- `FigureAndRelation`
- `FineGrainedFeed`
- `OriginalSource`
- `FRBuildingGraphReport`
- `Knowledge`

Application queries must filter `is_deleted = False` to exclude logically deleted records.

---

## 2. Entity-Relationship Diagram

```
+-------------------+          +-----------------------------------+
|      User         |          |        FigureAndRelation           |
|===================|          |===================================|
| PK id             |<---------| FK user_id                        |
| username (UQ)     |    1    | PK id                              |
| password          |          | figure_role            (Enum)     |
| nickname          |          | figure_name                       |
| gender (Enum)     |          | figure_gender         (Enum)     |
| email (UQ)        |          | figure_mbti           (Enum)     |
| level (Enum)      |          | figure_birthday                   |
| lark_open_id (UQ) |          | figure_occupation                 |
| created_at        |          | figure_education                  |
+-------------------+          | figure_residence                  |
           |                   | figure_hometown                    |
           |                   | figure_appearance                  |
           | 1                 | figure_likes          (ARRAY)      |
           |                   | figure_dislikes       (ARRAY)      |
           v                   | words_figure2user     (ARRAY)      |
+-------------------+          | words_user2figure     (ARRAY)      |
|    Knowledge      |          | exact_relation                     |
|===================|          | core_personality                   |
| PK id             |          | core_interaction_style             |
| FK user_id        |          | core_procedural_info               |
| content           |          | core_memory                        |
| weight (Float)    |          | is_deleted                         |
| embedding_model   |          | created_at                         |
| embedding (VECTOR)|          | updated_at                         |
| is_deleted        |          +-----------------------------------+            +-----------------------------+
| created_at (IX)   |                     | 1                                |     FineGrainedFeedConflict  |
| updated_at        |                     |                                  |=============================|
+-------------------+                     |                                  | PK id                        |
                                          |                                  | FK fr_id                     |
                                          |                                  | dimension         (Enum)    |
                                          |                                  | feed_ids          (ARRAY)   |
                                          |                                  | old_value                    |
                                          |                                  | new_value                    |
                                          |                                  | conflict_detail              |
                                          |                                  | status            (Enum)    |
                                          |                                  | created_at                   |
                                          |                                  +-----------------------------+
                                          |
                                          |
                                          | 1
          +-------------------------------+-------------------------------+
          |                               |                               |
          |                               |                               |
          v                               v                               v
+-----------------------------+  +-----------------------------+  +-----------------------------+
|     OriginalSource          |  |     FineGrainedFeed         |  |   FRBuildingGraphReport     |
|=============================|  |=============================|  |=============================|
| PK id                       |  | PK id                       |  | PK id                       |
| FK fr_id                    |  | FK fr_id                    |  | FK fr_id                    |
| type             (Enum)     |  | FK original_source_id       |  | report                      |
| approx_date                 |  | dimension        (Enum)     |  | is_deleted                  |
| confidence       (Enum)     |  | sub_dimension               |  | created_at                  |
| included_dimensions(ARRAY)  |  | confidence       (Enum)     |  +-----------------------------+
| content                     |  | content                     |
| is_deleted                  |  | embedding_model_name        |
| created_at                  |  | embedding        (VECTOR)   |
| updated_at                  |  | is_deleted                  |  +-----------------------------+
+-----------------------------+  | created_at                  |  |     FROverallUpdateLog       |
           |                     | updated_at                  |  |=============================|
           |                     +-----------------------------+  | PK id                       |
           |                                                      | FK fr_id                    |
           |                                                      | FK original_source_id       |
           +-------+-----------------------------+                | update_field_or_sub_dim     |
                   |                             |                | update_dimension (Enum)     |
                   v                             v                | old_value                   |
      +-----------------------------+  +-----------------------------+ new_value                   |
      |     FineGrainedFeed        |  |   FROverallUpdateLog        | created_at                  |
      |     (via original_source)   |  |   (via original_source)     +-----------------------------+
      +-----------------------------+  +-----------------------------+
                                                                               +-----------------------------+
                                                                               |     Analysis                |
                                                                               |=============================|
                                                                               | PK id                       |
                                                                               | FK fr_id                    |
                                                                               | type            (Enum, IX) |
                                                                               | screenshots     (ARRAY)    |
                                                                               | additional_context          |
                                                                               | narrative                   |
                                                                               | message_candidates(ARRAY)   |
                                                                               | risks           (ARRAY)    |
                                                                               | suggestions     (ARRAY)    |
                                                                               | created_at      (IX)       |
                                                                               +-----------------------------+


Cardinality Summary:
  User 1---* FigureAndRelation          (one user creates many figure profiles)
  User 1---* Knowledge                   (one user owns many knowledge entries)
  FigureAndRelation 1---* OriginalSource (one figure has many source materials)
  FigureAndRelation 1---* FineGrainedFeed(one figure has many extracted facts)
  FigureAndRelation 1---* FineGrainedFeedConflict (one figure has many conflicts)
  FigureAndRelation 1---* FROverallUpdateLog       (one figure has many change logs)
  FigureAndRelation 1---* FRBuildingGraphReport    (one figure has many build reports)
  FigureAndRelation 1---* Analysis                 (one figure has many analyses)
  OriginalSource 1---* FineGrainedFeed             (one source yields many extracted facts)
  OriginalSource 1---* FROverallUpdateLog          (one source triggers many update logs)
```

---

## 3. Core Models

### 3.1 User

**Table:** `user`
**Purpose:** Central identity and authentication store. Every interaction in the system is scoped to a user. Users create figure profiles, upload source materials, manage knowledge, and run analyses.

**Column Definitions:**

| Column       | Type              | Constraints                        | Default                    | Comment                       |
|--------------|-------------------|------------------------------------|----------------------------|-------------------------------|
| `id`         | `Integer`         | PK, autoincrement                  | -                          | Unique user identifier        |
| `username`   | `String(64)`      | UNIQUE, NOT NULL, INDEX            | -                          | Unique login name             |
| `password`   | `Text`            | NOT NULL                           | -                          | bcrypt-hashed password        |
| `nickname`   | `String(64)`      | NULLABLE, INDEX                    | -                          | Display name                  |
| `gender`     | `Enum(Gender)`    | NOT NULL                           | -                          | User gender                   |
| `email`      | `Text`            | NULLABLE, UNIQUE                   | -                          | Contact email                 |
| `level`      | `Enum(UserLevel)` | NOT NULL                           | `UserLevel.L4`             | Permission tier (L0 = highest)|
| `lark_open_id`| `Text`           | NULLABLE, UNIQUE                   | -                          | Feishu/Lark integration ID    |
| `created_at` | `DateTime`        | NOT NULL                           | `datetime.now(timezone.utc)` | Account creation timestamp   |

**Methods:**

| Method                  | Purpose                                              |
|-------------------------|------------------------------------------------------|
| `hashPassword(pw)`      | Static. Hashes a plaintext password with bcrypt.      |
| `checkPassword(pw)`     | Instance. Verifies a plaintext password against hash. |
| `toJson(...)`           | Inherited from `SerializableMixin`. Excludes `password` by default. |

**Indexes:**

| Index Name           | Column    | Type   |
|----------------------|-----------|--------|
| `pk_user`            | `id`      | PK     |
| `ix_username`        | `username`| B-tree |
| `ix_nickname`        | `nickname`| B-tree |
| `uq_user_username`   | `username`| UNIQUE |
| `uq_user_email`      | `email`   | UNIQUE |
| `uq_user_lark_open_id`| `lark_open_id` | UNIQUE |

**Relationships:**

| Target              | Backref               | Type      |
|---------------------|-----------------------|-----------|
| `FigureAndRelation` | `figure_and_relations`| One-to-Many |
| `Knowledge`         | `knowledge_pieces`    | One-to-Many |

**SQL Example:**

```sql
-- Create a new user (application-level, using bcrypt)
INSERT INTO "user" (username, password, nickname, gender, level, email, created_at)
VALUES ('alice', '<bcrypt_hash>', 'Alice', 'female', 'L4', 'alice@example.com', NOW());

-- Lookup by username
SELECT * FROM "user" WHERE username = 'alice';

-- Users with knowledge entries (join example)
SELECT u.username, COUNT(k.id) AS knowledge_count
FROM "user" u
LEFT JOIN knowledge k ON k.user_id = u.id AND k.is_deleted = FALSE
GROUP BY u.id;
```

---

### 3.2 FigureAndRelation

**Table:** `figure_and_relation`
**Purpose:** The core domain entity. Each row represents a person ("figure") that a user has a relationship with, along with all accumulated knowledge about that figure. This table acts as the central hub — nearly all other tables reference it via `fr_id`.

**Column Definitions:**

| Column                   | Type                    | Constraints         | Default                   | Comment                                      |
|--------------------------|-------------------------|---------------------|---------------------------|----------------------------------------------|
| `id`                     | `Integer`               | PK, autoincrement   | -                         | Unique identifier                             |
| `user_id`                | `Integer`               | FK -> `user.id`, NOT NULL | -                     | Owning user                                   |
| `figure_role`            | `Enum(FigureRole)`      | NOT NULL            | `FigureRole.STRANGER`     | Relationship category                         |
| `figure_name`            | `String(64)`            | NOT NULL            | -                         | Figure's name                                 |
| `figure_gender`          | `Enum(Gender)`          | NOT NULL            | -                         | Figure's gender                               |
| `figure_mbti`            | `Enum(MBTI)`            | NULLABLE            | -                         | MBTI personality type (if known)              |
| `figure_birthday`        | `Text`                  | NULLABLE            | -                         | Free-form birthday                            |
| `figure_occupation`      | `Text`                  | NULLABLE            | -                         | Job / profession                              |
| `figure_education`       | `Text`                  | NULLABLE            | -                         | Educational background                        |
| `figure_residence`       | `Text`                  | NULLABLE            | -                         | Current residence                             |
| `figure_hometown`        | `Text`                  | NULLABLE            | -                         | Place of origin                               |
| `figure_appearance`      | `Text`                  | NULLABLE            | -                         | Physical description                          |
| `figure_likes`           | `ARRAY(Text)`           | NOT NULL            | `[]`                      | Things the figure likes                       |
| `figure_dislikes`        | `ARRAY(Text)`           | NOT NULL            | `[]`                      | Things the figure dislikes                    |
| `words_figure2user`      | `ARRAY(Text)`           | NOT NULL            | `[]`                      | Verbatim phrases the figure said to the user  |
| `words_user2figure`      | `ARRAY(Text)`           | NOT NULL            | `[]`                      | Verbatim phrases the user said to the figure  |
| `exact_relation`         | `Text`                  | NULLABLE            | `""`                      | Free-form detailed relationship description   |
| `core_personality`       | `Text`                  | NOT NULL            | `""`                      | Synthesized personality & values (low-context)|
| `core_interaction_style` | `Text`                  | NOT NULL            | `""`                      | Synthesized interaction patterns (low-context)|
| `core_procedural_info`   | `Text`                  | NOT NULL            | `""`                      | How the figure operates (high-context, concise)|
| `core_memory`            | `Text`                  | NOT NULL            | `""`                      | Key life memories (high-context, concise)     |
| `is_deleted`             | `Boolean`               | NOT NULL            | `False`                   | Soft deletion flag                            |
| `created_at`             | `DateTime`              | NOT NULL            | `datetime.now(timezone.utc)` | Creation timestamp                         |
| `updated_at`             | `DateTime`              | NOT NULL            | auto-on-update             | Last modification timestamp                   |

**Indexes:**

| Index Name                        | Column      | Type   |
|-----------------------------------|-------------|--------|
| `pk_figure_and_relation`          | `id`        | PK     |
| `fk_figure_and_relation_user_id_user` | `user_id` | FK     |

**Relationships:**

| Target                     | Backref                          | Type          |
|----------------------------|----------------------------------|---------------|
| `User`                     | `figure_and_relations`           | Many-to-One   |
| `FineGrainedFeed`          | `fine_grained_feeds`             | One-to-Many   |
| `OriginalSource`           | `original_sources`               | One-to-Many   |
| `FineGrainedFeedConflict`  | `fine_grained_feed_conflicts`    | One-to-Many   |
| `FROverallUpdateLog`       | `fr_overall_update_logs`         | One-to-Many   |
| `FRBuildingGraphReport`    | `fr_building_graph_reports`      | One-to-Many   |
| `Analysis`                 | `analyses`                       | One-to-Many   |

**Special Notes:**

- The four `core_*` columns are the synthesized output from the fine-grained feed pipeline. The first two (`core_personality`, `core_interaction_style`) are low-context-dependent and should be detailed. The latter two (`core_procedural_info`, `core_memory`) are high-context-dependent and should be concise.
- The `figure_likes`, `figure_dislikes`, `words_figure2user`, and `words_user2figure` columns use `MutableList.as_mutable(ARRAY(Text))` — a PostgreSQL array wrapped for SQLAlchemy change tracking. This ensures that in-place mutations like `.append()` are detected by the ORM.
- `updated_at` uses `onupdate=datetime.now(timezone.utc)`, so it auto-refreshes on any column change.

**SQL Example:**

```sql
-- Retrieve all non-deleted figures for a user, with relationship role
SELECT id, figure_name, figure_role, core_personality
FROM figure_and_relation
WHERE user_id = 1 AND is_deleted = FALSE
ORDER BY updated_at DESC;

-- Update figure likes (array append)
UPDATE figure_and_relation
SET figure_likes = array_append(figure_likes, 'hiking')
WHERE id = 42;
```

---

### 3.3 FineGrainedFeed

**Table:** `fine_grained_feed`
**Purpose:** Stores individual extracted facts/observations about a figure, each belonging to a dimension (personality, interaction style, procedural info, or memory). Each feed entry is vectorized for semantic similarity search. This is the high-cardinality table in the system — it accumulates many rows per figure over time.

**Column Definitions:**

| Column                | Type                           | Constraints                                | Default                    | Comment                                    |
|-----------------------|--------------------------------|--------------------------------------------|----------------------------|--------------------------------------------|
| `id`                  | `Integer`                      | PK, autoincrement                          | -                          | Unique identifier                           |
| `fr_id`               | `Integer`                      | FK -> `figure_and_relation.id`, NOT NULL   | -                          | Parent figure                               |
| `original_source_id`  | `Integer`                      | FK -> `original_source.id`, NOT NULL       | -                          | Source this fact was extracted from         |
| `dimension`           | `Enum(FineGrainedFeedDimension)`| NOT NULL                                   | -                          | Knowledge dimension                         |
| `sub_dimension`       | `String(64)`                   | NULLABLE                                   | -                          | Granular sub-category                       |
| `confidence`          | `Enum(FineGrainedFeedConfidence)`| NOT NULL                                  | -                          | Evidence quality level                      |
| `content`             | `Text`                         | NOT NULL                                   | -                          | The extracted factual statement             |
| `embedding_model_name`| `Text`                         | NOT NULL                                   | -                          | Model used to generate the embedding        |
| `embedding`           | `Vector(1024)`                 | NOT NULL                                   | -                          | 1024-dimensional vector embedding           |
| `is_deleted`          | `Boolean`                      | NOT NULL                                   | `False`                    | Soft deletion flag                          |
| `created_at`          | `DateTime`                     | NOT NULL                                   | `datetime.now(timezone.utc)` | Creation timestamp                        |
| `updated_at`          | `DateTime`                     | NOT NULL, auto-on-update                   | `datetime.now(timezone.utc)` | Last modification timestamp               |

**Indexes:**

| Index Name                              | Column      | Type          |
|-----------------------------------------|-------------|---------------|
| `pk_fine_grained_feed`                  | `id`        | PK            |
| `fk_fine_grained_feed_fr_id_figure_and_relation` | `fr_id` | FK       |
| `fk_fine_grained_feed_original_source_id_original_source` | `original_source_id` | FK |
| `ix_fine_grained_feed_embedding_hnsw`   | `embedding` | HNSW (cosine) |

**Relationships:**

| Target              | Backref                | Type        |
|---------------------|------------------------|-------------|
| `FigureAndRelation` | `fine_grained_feeds`   | Many-to-One |
| `OriginalSource`    | `fine_grained_feeds`   | Many-to-One |

**Special Notes:**

- The `embedding` column is 1024-dimensional. The comment in the source code notes that the HNSW index requires dimensions to be less than 2000, which is why 1024 is used over 2048.
- The HNSW index (`ix_fine_grained_feed_embedding_hnsw`) is created via `__table_args__` with `postgresql_using="hnsw"` and `vector_cosine_ops`. See [Section 5](#5-vector-indexing) for details.
- Both foreign key relationships use `lazy="select"` to avoid the N+1 query problem: when loading a list of feeds, related figures and sources are loaded via a separate SELECT IN query rather than individual queries per row.

**SQL Example:**

```sql
-- Semantic similarity search: find feeds similar to a query vector
SELECT ff.id, ff.content, ff.dimension, 1 - (ff.embedding <=> :query_vector) AS similarity
FROM fine_grained_feed ff
WHERE ff.fr_id = :figure_id
  AND ff.is_deleted = FALSE
ORDER BY ff.embedding <=> :query_vector
LIMIT 10;
```

---

### 3.4 OriginalSource

**Table:** `original_source`
**Purpose:** Stores the raw (preprocessed) source materials that feeds are extracted from. Each source is classified by type (chat logs, long-form writing, social media posts, etc.) and tagged with the dimensions it covers.

**Column Definitions:**

| Column                | Type                                  | Constraints                           | Default                    | Comment                                |
|-----------------------|---------------------------------------|---------------------------------------|----------------------------|----------------------------------------|
| `id`                  | `Integer`                             | PK, autoincrement                     | -                          | Unique identifier                       |
| `fr_id`               | `Integer`                             | FK -> `figure_and_relation.id`, NOT NULL | -                       | Parent figure                           |
| `type`                | `Enum(OriginalSourceType)`            | NOT NULL                              | -                          | Source material category                |
| `approx_date`         | `String(32)`                          | NULLABLE                              | -                          | Approximate date (e.g., `2025-Q3`, `2026-01-15`) |
| `confidence`          | `Enum(FineGrainedFeedConfidence)`     | NOT NULL                              | -                          | Overall evidence reliability            |
| `included_dimensions` | `ARRAY(Enum(FineGrainedFeedDimension))`| NOT NULL                             | -                          | Which knowledge dimensions this source covers |
| `content`             | `Text`                                | NOT NULL                              | -                          | Full source text (after preprocessing)  |
| `is_deleted`          | `Boolean`                             | NOT NULL                              | `False`                    | Soft deletion flag                      |
| `created_at`          | `DateTime`                            | NOT NULL                              | `datetime.now(timezone.utc)` | Creation timestamp                    |
| `updated_at`          | `DateTime`                            | NOT NULL, auto-on-update              | `datetime.now(timezone.utc)` | Last modification timestamp           |

**Indexes:**

| Index Name                                     | Column   | Type |
|------------------------------------------------|----------|------|
| `pk_original_source`                           | `id`     | PK   |
| `fk_original_source_fr_id_figure_and_relation` | `fr_id`  | FK   |

**Relationships:**

| Target              | Backref              | Type        |
|---------------------|----------------------|-------------|
| `FigureAndRelation` | `original_sources`   | Many-to-One |
| `FineGrainedFeed`   | `fine_grained_feeds` | One-to-Many |
| `FROverallUpdateLog`| `fr_overall_update_logs` | One-to-Many |

**Special Notes:**

- The `included_dimensions` column uses an array of enums (`ARRAY(Enum(FineGrainedFeedDimension))`), providing PostgreSQL-level type safety for the dimension tags.
- The `approx_date` field is deliberately free-form (`String(32)`) to accommodate partial dates like quarter-level precision (`2025-Q3`) or full dates (`2026-01-15`).

**SQL Example:**

```sql
-- Find all sources for a figure that cover the personality dimension
SELECT id, type, approx_date, confidence, content
FROM original_source
WHERE fr_id = :figure_id
  AND is_deleted = FALSE
  AND 'personality' = ANY(included_dimensions)
ORDER BY created_at DESC;
```

---

### 3.5 FineGrainedFeedConflict

**Table:** `fine_grained_feed_conflict`
**Purpose:** Records conflicts between feed entries when new information contradicts existing knowledge. Each conflict captures the old value, the new value, the conflicting feed IDs, and the resolution status. This is the quality-control mechanism that ensures the knowledge graph remains consistent.

**Column Definitions:**

| Column            | Type                       | Constraints                         | Default                    | Comment                                   |
|-------------------|----------------------------|-------------------------------------|----------------------------|-------------------------------------------|
| `id`              | `Integer`                  | PK, autoincrement                   | -                          | Unique identifier                          |
| `fr_id`           | `Integer`                  | FK -> `figure_and_relation.id`, NOT NULL | -                     | Parent figure                              |
| `dimension`       | `Enum(FineGrainedFeedDimension)`| NOT NULL                         | -                          | Dimension where the conflict occurred      |
| `feed_ids`        | `ARRAY(Integer)`           | NOT NULL                            | -                          | IDs of the conflicting `FineGrainedFeed` rows |
| `old_value`       | `Text`                     | NOT NULL                            | -                          | Previously accepted value                  |
| `new_value`       | `Text`                     | NOT NULL                            | -                          | Challenging new value                      |
| `conflict_detail` | `Text`                     | NOT NULL                            | -                          | Human-readable explanation of the conflict |
| `status`          | `Enum(ConflictStatus)`     | NOT NULL                            | `ConflictStatus.PENDING`   | Resolution state                           |
| `created_at`      | `DateTime`                 | NOT NULL                            | `datetime.now(timezone.utc)` | Conflict detection timestamp             |

**Indexes:**

| Index Name                                               | Column  | Type |
|----------------------------------------------------------|---------|------|
| `pk_fine_grained_feed_conflict`                          | `id`    | PK   |
| `fk_fine_grained_feed_conflict_fr_id_figure_and_relation`| `fr_id` | FK   |

**Relationships:**

| Target              | Backref                       | Type        |
|---------------------|-------------------------------|-------------|
| `FigureAndRelation` | `fine_grained_feed_conflicts` | Many-to-One |

**Special Notes:**

- Unlike most other tables, this model does NOT use soft deletion — conflicts are either resolved (status changes) or remain pending indefinitely.
- The `feed_ids` column uses `MutableList.as_mutable(ARRAY(Integer))` for ORM-tracked array mutations.

**SQL Example:**

```sql
-- Find all pending conflicts for a user's figures
SELECT ffc.*
FROM fine_grained_feed_conflict ffc
JOIN figure_and_relation fr ON fr.id = ffc.fr_id
WHERE fr.user_id = :user_id AND ffc.status = 'pending'
ORDER BY ffc.created_at DESC;

-- Resolve a conflict by accepting the new value
UPDATE fine_grained_feed_conflict
SET status = 'resolved_accept_new'
WHERE id = :conflict_id;
```

---

### 3.6 FROverallUpdateLog

**Table:** `fr_overall_update_log`
**Purpose:** Audit trail for every change to a figure's profile. Logs both direct field changes on `FigureAndRelation` (e.g., `figure_name` changed) and feed-level changes (e.g., a new `FineGrainedFeed` was added under a sub-dimension). This enables full traceability of how a figure's knowledge graph evolved over time.

**Column Definitions:**

| Column                       | Type                                | Constraints                            | Default                    | Comment                                       |
|------------------------------|-------------------------------------|----------------------------------------|----------------------------|-----------------------------------------------|
| `id`                         | `Integer`                           | PK, autoincrement                      | -                          | Unique identifier                              |
| `fr_id`                      | `Integer`                           | FK -> `figure_and_relation.id`, NOT NULL | -                       | Parent figure                                  |
| `original_source_id`         | `Integer`                           | FK -> `original_source.id`, NULLABLE   | -                          | Source that triggered the change (NULL for direct edits) |
| `update_field_or_sub_dimension`| `Text`                             | NOT NULL                               | `""`                       | Field name or sub-dimension that changed       |
| `update_dimension`           | `Enum(FineGrainedFeedDimension)`    | NULLABLE                               | -                          | Dimension (only populated for feed changes)    |
| `old_value`                  | `Text`                              | NULLABLE                               | -                          | Value before the change                        |
| `new_value`                  | `Text`                              | NULLABLE                               | -                          | Value after the change                         |
| `created_at`                 | `DateTime`                          | NOT NULL                               | `datetime.now(timezone.utc)` | When the change occurred                     |

**Indexes:**

| Index Name                                                    | Column  | Type |
|---------------------------------------------------------------|---------|------|
| `pk_fr_overall_update_log`                                    | `id`    | PK   |
| `fk_fr_overall_update_log_fr_id_figure_and_relation`          | `fr_id` | FK   |
| `fk_fr_overall_update_log_original_source_id_original_source` | `original_source_id` | FK (NULLABLE) |

**Relationships:**

| Target              | Backref                   | Type        |
|---------------------|---------------------------|-------------|
| `FigureAndRelation` | `fr_overall_update_logs`  | Many-to-One |
| `OriginalSource`    | `fr_overall_update_logs`  | Many-to-One (nullable) |

**Special Notes:**

- The `original_source_id` foreign key is the sole nullable FK in the entire schema. When `NULL`, it indicates a manual or system-initiated change not triggered by a specific source.
- `update_dimension` is only populated when the change is at the feed level; for direct FR field changes it remains `NULL`.
- The pair `(old_value, new_value)` can both be `NULL` for cases where the log entry records the fact of a change without capturing the before/after (e.g., creation of a new field).

**SQL Example:**

```sql
-- Full audit trail for a figure, chronological
SELECT uol.created_at, uol.update_field_or_sub_dimension, uol.old_value, uol.new_value,
       os.type AS source_type
FROM fr_overall_update_log uol
LEFT JOIN original_source os ON os.id = uol.original_source_id
WHERE uol.fr_id = :figure_id
ORDER BY uol.created_at DESC;

-- Changes triggered by a specific source
SELECT * FROM fr_overall_update_log
WHERE original_source_id = :source_id;
```

---

### 3.7 FRBuildingGraphReport

**Table:** `fr_building_graph_report`
**Purpose:** Stores the structured report generated each time the knowledge graph for a figure is built or rebuilt. This provides a human-readable summary of the construction process — what was synthesized, what gaps were found, and what decisions were made.

**Column Definitions:**

| Column       | Type       | Constraints                            | Default                    | Comment                    |
|--------------|------------|----------------------------------------|----------------------------|----------------------------|
| `id`         | `Integer`  | PK, autoincrement                      | -                          | Unique identifier           |
| `fr_id`      | `Integer`  | FK -> `figure_and_relation.id`, NOT NULL | -                       | Parent figure               |
| `report`     | `Text`     | NOT NULL                               | -                          | Full build report (markdown)|
| `is_deleted` | `Boolean`  | NOT NULL                               | `False`                    | Soft deletion flag          |
| `created_at` | `DateTime` | NOT NULL                               | `datetime.now(timezone.utc)` | Report generation timestamp|

**Indexes:**

| Index Name                                                     | Column  | Type |
|----------------------------------------------------------------|---------|------|
| `pk_fr_building_graph_report`                                  | `id`    | PK   |
| `fk_fr_building_graph_report_fr_id_figure_and_relation`        | `fr_id` | FK   |

**Relationships:**

| Target              | Backref                      | Type        |
|---------------------|------------------------------|-------------|
| `FigureAndRelation` | `fr_building_graph_reports`  | Many-to-One |

**SQL Example:**

```sql
-- Most recent build report for a figure
SELECT report, created_at
FROM fr_building_graph_report
WHERE fr_id = :figure_id AND is_deleted = FALSE
ORDER BY created_at DESC
LIMIT 1;
```

---

### 3.8 Knowledge

**Table:** `knowledge`
**Purpose:** A private vector knowledge base scoped to each user. Users can store arbitrary text knowledge entries that are vectorized for semantic retrieval. This is used alongside the figure-specific feed data for context-augmented generation and recommendations.

**Column Definitions:**

| Column                | Type           | Constraints                     | Default                    | Comment                                    |
|-----------------------|----------------|---------------------------------|----------------------------|--------------------------------------------|
| `id`                  | `Integer`      | PK, autoincrement               | -                          | Unique identifier                           |
| `user_id`             | `Integer`      | FK -> `user.id`, NOT NULL       | -                          | Owning user                                 |
| `content`             | `Text`         | NOT NULL                        | -                          | Knowledge text                              |
| `weight`              | `Float`        | NOT NULL, INDEX                 | `1.0`                      | Importance weight for retrieval ranking     |
| `embedding_model_name`| `Text`         | NOT NULL                        | -                          | Model used to generate the embedding        |
| `embedding`           | `Vector(1024)` | NOT NULL                        | -                          | 1024-dimensional vector embedding           |
| `is_deleted`          | `Boolean`      | NOT NULL                        | `False`                    | Soft deletion flag                          |
| `created_at`          | `DateTime`     | NOT NULL, INDEX                 | `datetime.now(timezone.utc)` | Creation timestamp                        |
| `updated_at`          | `DateTime`     | NOT NULL, auto-on-update        | `datetime.now(timezone.utc)` | Last modification timestamp               |

**Indexes:**

| Index Name                     | Column      | Type          |
|--------------------------------|-------------|---------------|
| `pk_knowledge`                 | `id`        | PK            |
| `fk_knowledge_user_id_user`    | `user_id`   | FK            |
| `ix_weight`                    | `weight`    | B-tree        |
| `ix_created_at`                | `created_at`| B-tree        |
| `ix_knowledge_embedding_hnsw`  | `embedding` | HNSW (cosine) |

**Relationships:**

| Target | Backref            | Type      |
|--------|--------------------|-----------|
| `User` | `knowledge_pieces` | Many-to-One |

**Special Notes:**

- The `weight` column allows users to prioritize certain knowledge entries in retrieval results. Heavier weights should rank higher when combining vector similarity with weighted scoring.
- Like `FineGrainedFeed`, this table uses an HNSW index on the `embedding` column with the same 1024-dimensional constraint.
- Both `weight` and `created_at` have B-tree indexes, enabling efficient filtering and sorting when combined with vector search.

**SQL Example:**

```sql
-- Weighted semantic search in user's knowledge base
SELECT k.id, k.content, k.weight,
       1 - (k.embedding <=> :query_vector) AS similarity,
       (1 - (k.embedding <=> :query_vector)) * k.weight AS weighted_score
FROM knowledge k
WHERE k.user_id = :user_id
  AND k.is_deleted = FALSE
ORDER BY weighted_score DESC
LIMIT 10;

-- Insert knowledge with embedding
INSERT INTO knowledge (user_id, content, weight, embedding_model_name, embedding, created_at, updated_at)
VALUES (:user_id, :content, :weight, :model_name, :embedding_vector, NOW(), NOW());
```

---

### 3.9 Analysis

**Table:** `analysis`
**Purpose:** Stores analysis runs performed on conversations or narratives involving a figure. Each analysis produces message candidates (suggested replies), risk flags, and actionable suggestions. Supports two analysis modes: screenshot-based conversation analysis and free-text narrative analysis.

**Column Definitions:**

| Column                | Type                   | Constraints                           | Default                    | Comment                                   |
|-----------------------|------------------------|---------------------------------------|----------------------------|-------------------------------------------|
| `id`                  | `Integer`              | PK, autoincrement                     | -                          | Unique identifier                          |
| `fr_id`               | `Integer`              | FK -> `figure_and_relation.id`, NOT NULL | -                       | Figure being analyzed                      |
| `type`                | `Enum(AnalysisType)`   | NOT NULL, INDEX                       | -                          | Analysis mode (conversation / narrative)   |
| `screenshots`         | `ARRAY(Text)`          | NULLABLE                              | `[]`                       | Screenshot URLs (conversation mode)        |
| `additional_context`  | `Text`                 | NULLABLE                              | -                          | Supplementary context provided by user     |
| `narrative`           | `Text`                 | NULLABLE                              | -                          | Free-text narrative (narrative mode)       |
| `message_candidates`  | `ARRAY(Text)`          | NOT NULL                              | `[]`                       | AI-generated reply suggestions             |
| `risks`               | `ARRAY(Text)`          | NOT NULL                              | `[]`                       | Identified risk warnings                   |
| `suggestions`         | `ARRAY(Text)`          | NOT NULL                              | `[]`                       | Next-step action recommendations           |
| `created_at`          | `DateTime`             | NOT NULL, INDEX                       | `datetime.now(timezone.utc)` | Analysis completion timestamp            |

**Indexes:**

| Index Name                                     | Column      | Type   |
|------------------------------------------------|-------------|--------|
| `pk_analysis`                                  | `id`        | PK     |
| `fk_analysis_fr_id_figure_and_relation`        | `fr_id`     | FK     |
| `ix_type`                                      | `type`      | B-tree |
| `ix_created_at`                                | `created_at`| B-tree |

**Relationships:**

| Target              | Backref     | Type        |
|---------------------|-------------|-------------|
| `FigureAndRelation` | `analyses`  | Many-to-One |

**Special Notes:**

- The `type` column determines which input fields are used: `conversation` mode uses `screenshots` and `additional_context`, while `narrative` mode uses `narrative`. The other fields are left `NULL` or empty.
- All three output array fields (`message_candidates`, `risks`, `suggestions`) use `MutableList.as_mutable(ARRAY(Text))` for ORM-tracked mutations.
- Both `type` and `created_at` are indexed for efficient filtering (e.g., "show me all conversation analyses, newest first").

**SQL Example:**

```sql
-- Recent conversation analyses for a figure
SELECT id, type, message_candidates, risks, suggestions, created_at
FROM analysis
WHERE fr_id = :figure_id AND type = 'conversation'
ORDER BY created_at DESC
LIMIT 5;

-- Analyses with risk flags
SELECT a.id, a.type, a.risks, a.created_at, fr.figure_name
FROM analysis a
JOIN figure_and_relation fr ON fr.id = a.fr_id
WHERE fr.user_id = :user_id
  AND cardinality(a.risks) > 0
ORDER BY a.created_at DESC;
```

---

## 4. Enum Types

All enum types are defined in `src/database/enums.py` as Python `enum.Enum` subclasses. They are used in SQLAlchemy `Column(Enum(...))` definitions, which render as PostgreSQL native ENUM types.

### 4.1 Gender

| Value    | Label  |
|----------|--------|
| `male`   | Male   |
| `female` | Female |
| `other`  | Other  |

Used by: `User.gender`, `FigureAndRelation.figure_gender`

---

### 4.2 UserLevel

| Value | Label | Description       |
|-------|-------|-------------------|
| `0`   | L0    | Highest privilege |
| `1`   | L1    | -                 |
| `2`   | L2    | -                 |
| `3`   | L3    | -                 |
| `4`   | L4    | Default (lowest)  |

Used by: `User.level`

The integer values enable ordered comparison: lower number = higher privilege. The default for new users is `L4`.

---

### 4.3 MBTI

All 16 Myers-Briggs Type Indicator types.

| Analysts       | Diplomats      | Sentinels      | Explorers      |
|----------------|----------------|----------------|----------------|
| `INTJ`         | `INFJ`         | `ESTJ`         | `ISTP`         |
| `INTP`         | `INFP`         | `ESFJ`         | `ISFP`         |
| `ENTJ`         | `ENFJ`         | `ISTJ`         | `ESTP`         |
| `ENTP`         | `ENFP`         | `ISFJ`         | `ESFP`         |

Used by: `FigureAndRelation.figure_mbti` (nullable — not all figures have known MBTI)

---

### 4.4 FigureRole

| Value           | Label        | Description                        |
|-----------------|--------------|------------------------------------|
| `self`          | Self         | The user themselves                |
| `family`        | Family       | Family member                      |
| `friend`        | Friend       | Friend                             |
| `mentor`        | Mentor       | Mentor / teacher                   |
| `colleague`     | Colleague    | Work colleague                     |
| `partner`       | Partner      | Romantic partner                   |
| `public_figure` | Public Figure| Public figure / celebrity          |
| `stranger`      | Stranger     | Default — unknown relationship type|

Used by: `FigureAndRelation.figure_role`

The source type enum (`OriginalSourceType`) is partially organized by `FigureRole`, with role-specific subtypes for work relations, close relations, self, and public figures.

---

### 4.5 FineGrainedFeedDimension

| Value               | Label              | Context Dependency |
|---------------------|--------------------|--------------------|
| `personality`       | Personality & Values| Low — requires detail |
| `interaction_style` | Interaction Style   | Low — requires detail |
| `procedural_info`   | Procedural Knowledge| High — keep concise |
| `memory`            | Life Memory & Stories| High — keep concise |
| `other`             | Other              | -                  |

Used by: `FineGrainedFeed.dimension`, `OriginalSource.included_dimensions`, `FineGrainedFeedConflict.dimension`, `FROverallUpdateLog.update_dimension`

The context dependency distinction is critical for the synthesis pipeline: low-context dimensions need rich, detailed descriptions; high-context dimensions should be sparse and reference-oriented.

---

### 4.6 FineGrainedFeedConfidence

| Value        | Label                                         | Reliability |
|--------------|-----------------------------------------------|-------------|
| `verbatim`   | Verbatim — direct quote from the source       | Highest     |
| `artifact`   | Artifact — objective statement in documents/works | Medium    |
| `impression` | Impression — subjective impression from provider | Lowest    |

Used by: `FineGrainedFeed.confidence`, `OriginalSource.confidence`

---

### 4.7 OriginalSourceType

Categorized by the `FigureRole` context in which the source is typically available:

**General (any role):**

| Value                | Description                        |
|----------------------|------------------------------------|
| `narrative_from_user`| User's own written description     |

**Work relations (colleague / mentor):**

| Value                        | Description                                    |
|------------------------------|------------------------------------------------|
| `work_relation_long_form`    | Long-form writing (design docs, postmortems, on-call records) |
| `work_relation_edit_trace`   | Edit traces (code review comments, doc annotations) |
| `work_relation_guidance`     | Mentorship / guidance records                   |
| `work_relation_artifact`     | Created artifacts (code, design files)          |

**Close relations (family / partner / friend):**

| Value                             | Description                           |
|-----------------------------------|---------------------------------------|
| `close_relation_long_form`        | Long-form writing (letters, articles) |
| `close_relation_private_chat`     | Private chat logs (most direct trace) |
| `close_relation_social_expression`| Social media posts / public expressions|
| `close_relation_artifact`         | Created artifacts                     |

**Self:**

| Value                    | Description                           |
|--------------------------|---------------------------------------|
| `self_long_form`         | Self-authored long-form (blog, diary, notes) |
| `self_chat_message`      | Chat messages sent by self            |
| `self_social_expression` | Social media posts by self            |
| `self_artifact`          | Created artifacts by self             |

**Public figure:**

| Value                                      | Description                       |
|--------------------------------------------|-----------------------------------|
| `public_figure_article_blog`               | Published articles / blog posts   |
| `public_figure_interview_speech_transcript`| Interview / speech transcripts    |
| `public_figure_social_expression`          | Social media expressions          |
| `public_figure_news_report`                | News reports                      |
| `public_figure_artifact`                   | Created artifacts                 |

**Total: 14 types.**

Used by: `OriginalSource.type`

---

### 4.8 ConflictStatus

| Value                 | Description                              |
|-----------------------|------------------------------------------|
| `pending`             | Awaiting resolution                       |
| `resolved_keep_old`   | Original value retained, new value discarded |
| `resolved_accept_new` | New value accepted, old value replaced    |
| `resolved_merge`      | Both values merged into a combined entry  |
| `resolved_rewrite`    | Human rewrote the entry to reconcile both |

Used by: `FineGrainedFeedConflict.status`

The default value is `pending`. Once a conflict is resolved, the status should be updated and the corresponding feed entries should be modified by the application layer.

---

### 4.9 AnalysisType

| Value          | Description                        |
|----------------|------------------------------------|
| `conversation` | Analysis of chat screenshots       |
| `narrative`    | Analysis of free-text narrative    |

Used by: `Analysis.type`

When `type = 'conversation'`, the `screenshots` and `additional_context` fields are expected to be populated. When `type = 'narrative'`, the `narrative` field is populated instead.

---

### 4.10 Enum Parsing Utility

The `parseEnum()` function in `src/database/enums.py` provides flexible enum resolution:

```python
def parseEnum(enum_cls, value: str | None) -> enum.Enum | None:
    """
    Resolves an enum by either its key name (e.g., 'PENDING') or its value (e.g., 'pending').
    Returns None if value is None or cannot be resolved.
    """
```

This is useful for API endpoints that accept enum values as strings without requiring the caller to know whether to send the key or the value.

---

## 5. Vector Indexing

### 5.1 pgvector Extension

The `pgvector` extension must be enabled on the PostgreSQL instance before any vector operations. This is handled automatically by `initDatabaseIfNeeded()`:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The extension provides:
- The `vector(N)` data type for fixed-dimensional embeddings.
- Distance operators: `<->` (L2), `<#>` (inner product), `<=>` (cosine distance).
- HNSW and IVFFlat index types for approximate nearest neighbor search.

### 5.2 HNSW Index Configuration

Two tables use HNSW indexes for vector similarity search:

| Table              | Index Name                              | Dimension | Operator          |
|--------------------|-----------------------------------------|-----------|-------------------|
| `fine_grained_feed`| `ix_fine_grained_feed_embedding_hnsw`   | 1024      | `vector_cosine_ops`|
| `knowledge`        | `ix_knowledge_embedding_hnsw`           | 1024      | `vector_cosine_ops`|

The HNSW (Hierarchical Navigable Small World) index is defined via SQLAlchemy's `Index` with PostgreSQL-specific arguments:

```python
Index(
    "ix_fine_grained_feed_embedding_hnsw",
    "embedding",
    postgresql_using="hnsw",
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
```

This renders as:

```sql
CREATE INDEX ix_fine_grained_feed_embedding_hnsw
ON fine_grained_feed
USING hnsw (embedding vector_cosine_ops);
```

### 5.3 Embedding Dimensions

- **Dimension:** 1024
- **Rationale:** The source code notes that the embedding model supports 1024 and 2048 dimensions, but HNSW indexes require dimensions < 2000. Therefore 1024 is used.
- **Consistency:** Both `fine_grained_feed.embedding` and `knowledge.embedding` use `Vector(1024)`.

### 5.4 Cosine Distance Operator

The cosine distance operator `<=>` returns a value between 0 (identical direction) and 2 (opposite direction). To convert to a similarity score:

```sql
-- Cosine similarity (1 = identical, -1 = opposite)
1 - (embedding <=> :query_vector) AS similarity
```

Ordering by `embedding <=> :query_vector` returns the most similar vectors first (ascending distance = descending similarity).

### 5.5 Performance Characteristics

- **HNSW** is an approximate nearest neighbor (ANN) index. It trades a small amount of recall for large gains in query speed compared to exact search.
- Build time: O(N log N) where N is the number of vectors.
- Query time: O(log N) for typical configurations.
- Memory: The index stores a graph structure alongside the vectors, increasing storage requirements by roughly 20-50% compared to raw vectors.
- **Maintenance:** HNSW indexes are maintained incrementally on INSERT/UPDATE/DELETE. No reindexing is needed for incremental data changes.
- **pgvector defaults** for HNSW parameters (`m` and `ef_construction`) are used unless overridden.

---

## 6. Database Migrations

### 6.1 Alembic Setup

The project uses Alembic for schema migrations. Configuration is split across:

| File                                        | Purpose                                    |
|---------------------------------------------|--------------------------------------------|
| `src/database/alembic/env.py`               | Migration environment (online + offline modes) |
| `src/database/alembic/script.py.mako`       | Template for new migration files           |
| `alembic/versions/`                         | Migration version scripts                  |
| `alembic/alembic.ini` (in BE-HeartCompass)  | Database URL and Alembic configuration     |

The `env.py` file is configured for:
- **Online migrations:** Connects to the database and executes migrations directly.
- **Offline migrations:** Generates SQL scripts without a live connection (for review or DBA execution).
- **Autogenerate support:** Imports `Base.metadata` from `src.database.models`, enabling `--autogenerate` to detect model changes.

### 6.2 Migration Workflow

```bash
# 1. Make changes to models.py (add/remove/modify columns, tables, etc.)

# 2. Generate a new migration
cd BE-HeartCompass
alembic revision --autogenerate -m "describe the change"

# 3. Review the generated migration file in alembic/versions/

# 4. Apply the migration
alembic upgrade head

# 5. Roll back one migration (if needed)
alembic downgrade -1

# 6. View migration history
alembic history

# 7. View current revision
alembic current
```

### 6.3 Common Migration Commands

| Command                              | Purpose                                      |
|--------------------------------------|----------------------------------------------|
| `alembic upgrade head`               | Apply all pending migrations                 |
| `alembic downgrade -1`               | Roll back the most recent migration          |
| `alembic downgrade base`             | Roll back ALL migrations (empty database)    |
| `alembic revision --autogenerate -m "msg"` | Auto-detect model changes and create migration |
| `alembic revision -m "msg"`          | Create empty migration (manual)              |
| `alembic current`                    | Show the current revision                    |
| `alembic history`                    | Show migration history                       |
| `alembic stamp head`                 | Mark the database as up-to-date (no execution)|
| `alembic upgrade head --sql`         | Generate SQL without executing (offline)     |

### 6.4 Migration Caveats

From `src/database/README.md`:

1. **pgvector imports:** Auto-generated migration files do not automatically include `import pgvector`. This must be added manually to the generated version file if the migration references vector operations.

2. **Enum type conflicts:** When a migration creates or modifies an ENUM type that already exists, set `create_type=False` and use `checkfirst=True`:

   ```python
   my_enum = postgresql.ENUM(
       "VALUE1", "VALUE2", "VALUE3",
       name="my_enum",
       create_type=False,
   )
   bind = op.get_bind()
   my_enum.create(bind, checkfirst=True)
   ```

---

## 7. Query Patterns

### 7.1 Vector Similarity Search (FineGrainedFeed)

Retrieve the top-K most semantically similar feed entries for a given query vector, scoped to a specific figure:

```sql
SELECT
    ff.id,
    ff.content,
    ff.dimension,
    ff.confidence,
    1 - (ff.embedding <=> :query_vector) AS similarity
FROM fine_grained_feed ff
WHERE ff.fr_id = :figure_id
  AND ff.is_deleted = FALSE
ORDER BY ff.embedding <=> :query_vector
LIMIT :k;
```

Python (SQLAlchemy):

```python
from sqlalchemy import func, text

results = (
    session.query(
        FineGrainedFeed,
        (1 - FineGrainedFeed.embedding.cosine_distance(query_vector)).label("similarity"),
    )
    .filter(
        FineGrainedFeed.fr_id == figure_id,
        FineGrainedFeed.is_deleted == False,
    )
    .order_by(FineGrainedFeed.embedding.cosine_distance(query_vector))
    .limit(k)
    .all()
)
```

### 7.2 Vector Similarity Search (Knowledge)

Weighted retrieval from the user's knowledge base:

```sql
SELECT
    k.id,
    k.content,
    k.weight,
    1 - (k.embedding <=> :query_vector) AS similarity,
    (1 - (k.embedding <=> :query_vector)) * k.weight AS weighted_score
FROM knowledge k
WHERE k.user_id = :user_id
  AND k.is_deleted = FALSE
ORDER BY weighted_score DESC
LIMIT :k;
```

### 7.3 Ownership Verification

Every figure belongs to a user. Always verify ownership before mutating data:

```sql
-- Check if user owns a figure
SELECT 1 FROM figure_and_relation
WHERE id = :figure_id AND user_id = :user_id AND is_deleted = FALSE;

-- Check if user owns a knowledge entry
SELECT 1 FROM knowledge
WHERE id = :knowledge_id AND user_id = :user_id AND is_deleted = FALSE;
```

A common pattern: verify figure ownership before inserting related records:

```python
figure = (
    session.query(FigureAndRelation)
    .filter(
        FigureAndRelation.id == fr_id,
        FigureAndRelation.user_id == current_user_id,
        FigureAndRelation.is_deleted == False,
    )
    .first()
)
if not figure:
    raise PermissionError("Figure not found or access denied")
```

### 7.4 Full Figure Profile with Relations

Load a complete figure profile including all feeds, sources, and conflicts:

```sql
-- Figure details
SELECT * FROM figure_and_relation
WHERE id = :figure_id AND is_deleted = FALSE;

-- All non-deleted feeds, grouped by dimension
SELECT dimension, COUNT(*) AS count, ARRAY_AGG(id) AS feed_ids
FROM fine_grained_feed
WHERE fr_id = :figure_id AND is_deleted = FALSE
GROUP BY dimension;

-- All non-deleted sources
SELECT id, type, approx_date, confidence, content
FROM original_source
WHERE fr_id = :figure_id AND is_deleted = FALSE
ORDER BY created_at DESC;

-- Pending conflicts
SELECT id, dimension, conflict_detail, status, created_at
FROM fine_grained_feed_conflict
WHERE fr_id = :figure_id AND status = 'pending'
ORDER BY created_at DESC;

-- Recent analyses
SELECT id, type, message_candidates, risks, suggestions, created_at
FROM analysis
WHERE fr_id = :figure_id
ORDER BY created_at DESC
LIMIT 10;
```

### 7.5 Change History for a Figure

Trace all modifications to a figure's profile over time:

```sql
-- Field-level changes (direct FR edits)
SELECT 'field_update' AS change_type, created_at, update_field_or_sub_dimension AS field,
       old_value, new_value, NULL AS dimension
FROM fr_overall_update_log
WHERE fr_id = :figure_id AND update_dimension IS NULL

UNION ALL

-- Feed-level changes
SELECT 'feed_update' AS change_type, created_at, update_field_or_sub_dimension AS field,
       old_value, new_value, update_dimension::text AS dimension
FROM fr_overall_update_log
WHERE fr_id = :figure_id AND update_dimension IS NOT NULL

ORDER BY created_at DESC
LIMIT 100;
```

### 7.6 Array Operations

PostgreSQL array columns support rich querying:

```sql
-- Figures who like "hiking" (exact match in array)
SELECT id, figure_name FROM figure_and_relation
WHERE 'hiking' = ANY(figure_likes) AND is_deleted = FALSE;

-- Sources that cover both personality AND interaction_style
SELECT id, content FROM original_source
WHERE included_dimensions @> ARRAY['personality', 'interaction_style']::finegrainedfeeddimension[];

-- Analyses that produced at least one risk flag
SELECT id, fr_id, risks FROM analysis
WHERE cardinality(risks) > 0;

-- Append to an array field (use MutableList in ORM for this)
UPDATE figure_and_relation
SET figure_dislikes = array_append(figure_dislikes, 'loud noises')
WHERE id = :figure_id;
```

### 7.7 Soft Deletion Filtering

All queries against soft-deletable tables must include the `is_deleted = FALSE` filter:

```sql
-- Correct: excludes deleted records
SELECT * FROM fine_grained_feed WHERE fr_id = :id AND is_deleted = FALSE;

-- Incorrect: includes deleted records (data leak)
SELECT * FROM fine_grained_feed WHERE fr_id = :id;
```

Tables that do NOT use soft deletion (no `is_deleted` column):
- `FineGrainedFeedConflict` — resolved via status transitions
- `FROverallUpdateLog` — immutable audit trail
- `Analysis` — no deletion concept

### 7.8 Timestamp Conventions

All timestamps use UTC (`datetime.now(timezone.utc)`) to avoid timezone ambiguity. When displaying timestamps to users, convert to the user's local timezone at the application layer.

```python
# All timestamp defaults in models
created_at = Column(DateTime, default=datetime.now(timezone.utc))
updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
```

### 7.9 Session Management Pattern

The `session()` factory from `src/database.index` should be used within context managers:

```python
from src.database.index import session

def get_figure(figure_id: int, user_id: int):
    """Example: fetch a figure with ownership check."""
    db = session()
    try:
        figure = (
            db.query(FigureAndRelation)
            .filter(
                FigureAndRelation.id == figure_id,
                FigureAndRelation.user_id == user_id,
                FigureAndRelation.is_deleted == False,
            )
            .first()
        )
        return figure
    finally:
        db.close()
```

The `session()` factory handles engine lifecycle management including forking support (detects PID changes and rebuilds the engine).

---

## Appendix: Model Summary Matrix

| # | Model                    | Table                       | Soft Delete | Has Vector | FK Targets                    |
|---|--------------------------|-----------------------------|-------------|------------|-------------------------------|
| 1 | User                     | `user`                      | No          | No         | -                             |
| 2 | FigureAndRelation        | `figure_and_relation`       | Yes         | No         | `user`                        |
| 3 | FineGrainedFeed          | `fine_grained_feed`         | Yes         | Yes (HNSW) | `figure_and_relation`, `original_source` |
| 4 | OriginalSource           | `original_source`           | Yes         | No         | `figure_and_relation`         |
| 5 | FineGrainedFeedConflict  | `fine_grained_feed_conflict`| No          | No         | `figure_and_relation`         |
| 6 | FROverallUpdateLog       | `fr_overall_update_log`     | No          | No         | `figure_and_relation`, `original_source` (nullable) |
| 7 | FRBuildingGraphReport    | `fr_building_graph_report`  | Yes         | No         | `figure_and_relation`         |
| 8 | Knowledge                | `knowledge`                 | Yes         | Yes (HNSW) | `user`                        |
| 9 | Analysis                 | `analysis`                  | No          | No         | `figure_and_relation`         |

---

## Appendix: Column Count by Table

| Table                          | Column Count |
|--------------------------------|-------------|
| `user`                         | 9           |
| `figure_and_relation`          | 22          |
| `fine_grained_feed`            | 13          |
| `original_source`              | 10          |
| `fine_grained_feed_conflict`   | 9           |
| `fr_overall_update_log`        | 8           |
| `fr_building_graph_report`     | 5           |
| `knowledge`                    | 9           |
| `analysis`                     | 10          |
| **Total**                      | **95**      |
