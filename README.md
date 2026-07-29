# Olist Data Warehouse — System Architecture

This document describes the complete architecture of the pipeline, from
raw source data to business-ready analytics tables, including every
identity, permission boundary, and infrastructure component involved. It's
written to be read by someone evaluating the engineering decisions behind
the project, not just the end result.

Two diagrams accompany this document:
- **End-to-end pipeline flow** — the path data takes from source CSVs to a BI dashboard
- **IAM and security model** — the three distinct identities used throughout the system and what each can and cannot touch

---

## 1. Project summary

A batch data warehouse built on the Brazilian E-Commerce (Olist) public
dataset, implementing a Medallion architecture (Bronze → Silver → Gold) on
AWS, modeled as a Kimball-style star schema, transformed with dbt,
orchestrated with Airflow, and validated with automated data quality
checks at every layer boundary.

**Business questions answered:**
1. Delivery performance — on-time vs late rate, by region and by seller
2. Sales trends — revenue and order volume over time, by category and region
3. Customer satisfaction vs delivery delay correlation
4. Seller performance — revenue, delivery time, order volume per seller
5. Payment behavior — payment method mix, installment trends, average order value

---

## 2. Identity and access model

Three distinct identities exist in this system, each scoped to exactly
what it needs and nothing more. This separation mirrors how real
production AWS environments separate human/provisioning access from
application/runtime access from service-to-service access.

### `terraform-admin` — human-operated, infrastructure provisioning
- **Who uses it:** the project owner, manually, only to run `terraform
  plan`/`apply`/`destroy`
- **Permissions:** `AdministratorAccess` — justified because this identity
  is never embedded in any script or application, is protected by MFA, and
  is used interactively by a human who reviews every `terraform plan`
  output before applying
- **Never used for:** running any pipeline code, ingestion, transforms, or
  application logic

### `olist-dw-dev` — scoped IAM user, pipeline runtime identity
- **Who uses it:** the ingestion script, the Python Bronze→Silver
  transforms, and (in the Airflow DAG) every task that calls AWS APIs on
  the pipeline's behalf
- **Permissions:** a custom least-privilege policy granting only:
  - `s3:ListBucket`, `s3:GetBucketLocation` on exactly three bucket ARNs (bronze, silver, gold)
  - `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on objects within those same three buckets
  - Versioning-related read permissions scoped to the Bronze bucket specifically
- **Explicitly excluded:** no IAM permissions (can't create users/roles/policies), no permissions on any bucket or resource outside this project, no `s3:*` wildcard actions
- **Why a user and not a role here:** this identity is used by scripts run
  from a developer's own machine and, later, containerized Airflow tasks —
  both scenarios that need long-lived (though still narrowly scoped)
  credentials rather than a role assumed by an AWS service

### `redshift-s3-role` — IAM role, assumed by the Redshift service
- **Who uses it:** Redshift Serverless itself, automatically, whenever a
  `COPY` command or a Spectrum query needs to read S3 or the Glue Data
  Catalog
- **Trust policy:** only `redshift.amazonaws.com` may assume this role —
  no IAM user, including the admin user, can assume it directly
- **Permissions:**
  - S3 read/write scoped to the same three project buckets (read on
    Bronze/Silver, read/write on Gold for future `UNLOAD` use cases)
  - Glue Data Catalog permissions scoped specifically to the
    `olist_silver` database and its tables — not account-wide Glue access
- **Why a role instead of embedding access keys in Redshift:** this is the
  standard AWS pattern for service-to-service access — Redshift receives
  short-lived, automatically-rotated credentials behind the scenes,
  meaning there are no long-lived secrets sitting inside the warehouse
  itself that could be extracted or leaked

**The unifying principle across all three:** every IAM policy in this
project references exact resource ARNs — never a wildcard (`*`) in the
`Resource` field. If any credential set were ever compromised, the blast
radius is provably limited to this project's own three S3 buckets and one
Glue database, not the wider AWS account.

---

## 3. Infrastructure as Code

All AWS infrastructure — S3 buckets, IAM users/roles/policies, the
Redshift Serverless namespace and workgroup — is provisioned via
**Terraform**, not manual console clicks. Every resource name is
parameterized by `project_name`, `project_owner`, and `project_version`
(e.g. `dev`/`prod`), so the entire environment could be duplicated for a
staging or production deployment by changing one variable and re-running
`terraform apply`, without touching any resource definition.

Public access is explicitly blocked on all three S3 buckets, and the
Bronze bucket has object versioning enabled — protecting the one layer of
the system meant to be immutable from accidental overwrite.

---

## 4. Bronze layer — raw ingestion

**Storage:** S3, one bucket, Hive-style partitioned by
`{entity}/ingestion_date={date}/{filename}.csv` — CSV format preserved
exactly as sourced, no transformation applied at this stage.

**Ingestion:** a Python script (boto3) uploads each of the 9 source CSVs,
computes row counts and file sizes, and writes a JSON manifest documenting
exactly what was uploaded and when — a lightweight audit trail rather than
a silent file copy.

**Why immutable and untouched:** if a downstream transformation bug is
ever discovered, the pipeline can be re-run from Bronze without needing to
re-acquire the source data — a principle borrowed directly from how
production systems protect against irreversible data loss upstream.

---

## 5. Data quality gate — Great Expectations

Before any Bronze data is trusted enough to transform, it passes through
an automated validation suite (Great Expectations) checking column-level
rules derived directly from data profiling: not-null constraints,
uniqueness (including composite-key uniqueness where a single column
isn't a true natural key), accepted value sets, and numeric range bounds.

**Why this exists as a distinct, automated gate:** in the orchestrated
pipeline (Section 9), this check runs before any Silver or Gold work
begins — if Bronze data ever fails validation, the entire downstream
pipeline halts rather than propagating bad data silently into the
warehouse.

---

## 6. Silver layer — cleaning and standardization

**Tooling:** Python/Pandas — chosen because this stage's transformations
are row-level and imperative (deduplication, text normalization, type
casting, conditional logic), which Pandas expresses more naturally than
SQL at this data volume (largest table is ~1M rows, comfortably an
in-memory workload).

**Representative transformations:**
- Geolocation: ~1,000,163 raw coordinate rows deduplicated and aggregated
  down to ~19,011 rows (one per ZIP prefix), with accented-character
  normalization (`São Paulo` → `sao paulo`) to prevent silent join/grouping
  failures downstream
- Products: 610 rows with a missing category filled as `"unknown"`; 623
  products with no English category translation fall back to their
  original Portuguese name rather than becoming null and disappearing
  from category-based analysis
- Orders: all date columns cast from string to proper timestamp types;
  a `delivery_delay_days` measure derived once, upstream, rather than
  recomputed inconsistently in every downstream query

**Storage:** S3, Parquet format (columnar, compressed, schema-preserving)
— chosen over continuing with CSV specifically because the next layer
(Redshift Spectrum) reads this data far more efficiently in a columnar
format, and because Parquet retains type information that CSV silently
loses.

---

## 7. Making Silver queryable — Redshift Spectrum + Glue Data Catalog

Rather than copying Silver data into Redshift's own storage, the pipeline
uses **Redshift Spectrum** to query the Silver Parquet files directly in
place, using the **AWS Glue Data Catalog** as the metadata layer mapping
S3 locations and schemas to queryable table names.

**Why this approach instead of loading Silver into native Redshift
tables:** Spectrum keeps S3 as the single source of truth for Silver data
— no duplicate storage, no separate load step to keep in sync every time
a transform reruns. Redshift compute is reserved for the layer that
actually needs it: building the Gold star schema.

---

## 8. Gold layer — star schema via dbt

**Tooling:** dbt (data build tool) — chosen because this layer's work is
set-based and declarative (joins, aggregations, grain transformations),
which SQL expresses more naturally than Python, and because dbt provides
dependency-aware build ordering, built-in testing, and automatic lineage
documentation as first-class features rather than something to build by
hand.

### Schema design (Kimball dimensional modeling)

**Fact tables**, each with an explicitly declared grain:
- `fact_order_items` — one row per order line item (transaction grain)
- `fact_orders` — one row per order (accumulating snapshot, tracking the
  order lifecycle from purchase through delivery), carrying pre-aggregated
  rollup measures (`total_payment_value`, `avg_review_score`) computed via
  `GROUP BY` before joining, specifically to prevent fan-out bias
- `fact_payments` — one row per payment transaction (an order can have
  multiple split payments)
- `fact_reviews` — one row per review, keyed on the composite
  `(review_id, order_id)` after data profiling revealed `review_id` alone
  is not globally unique in this dataset

**Dimension tables:**
- `dim_date` — conformed across every fact table, including a reserved
  sentinel row (`date_key = -1`) so no foreign key is ever left null
- `dim_customers` — grain deliberately set at `customer_unique_id` (the
  real person), not `customer_id` (an order-scoped identifier), after
  profiling revealed the same customer can have multiple `customer_id`
  values across orders
- `dim_products`, `dim_sellers` — enriched with geolocation coordinates
  joined in from Silver, with documented handling for the small number of
  ZIP prefixes with no geolocation match

**Design principles applied throughout, derived from working through
specific data issues rather than applied as abstract textbook rules:**
never join fact table to fact table directly (shared IDs are used for
traceability only); detail-grain fact tables are paired with
pre-aggregated rollup measures on the order-level snapshot, rather than
forcing every analyst to remember to aggregate correctly themselves;
foreign keys are never left null.

### Testing

dbt's built-in test framework (`unique`, `not_null`, `relationships`,
`accepted_values`) encodes the schema's structural contracts directly, and
two custom SQL tests specifically assert the composite-key uniqueness
findings from data profiling — most notably a test asserting
`(review_id, order_id)` uniqueness rather than `review_id` alone, directly
encoding a non-obvious data quality finding as a permanent, automated
safeguard against future regression.

---

## 9. Orchestration — Airflow

The entire pipeline — ingestion, data quality gate, 8 parallel Silver
transforms, `dbt run`, `dbt test` — is expressed as a single Airflow DAG
with explicit dependency ordering: ingestion must complete before quality
checks run; quality checks must pass before any Silver transform runs; all
8 Silver transforms (which have no dependencies on each other) run in
parallel; the Gold-layer dbt build only runs once every transform
succeeds; tests run as a distinct, separately-visible step after the
build.

**Why data quality gates the pipeline structurally, not just by
convention:** if Bronze data fails validation, the DAG halts before
Silver/Gold are ever touched — bad data is stopped at the door rather than
silently propagating into the warehouse.

**Deployment:** run locally via Docker Compose rather than Amazon MWAA
(AWS's managed Airflow service) — a deliberate cost tradeoff for a
self-funded project rather than a capability gap. Connections and
credentials are structured (via Airflow's Connections feature, referencing
the same scoped `olist-dw-dev` identity used everywhere else in the
pipeline) so that migrating to MWAA in a production context would be a
configuration change, not a code rewrite.

---

## 10. Known limitations and deliberate scope decisions

Documented explicitly, rather than left implicit, because acknowledging
scope tradeoffs is itself part of demonstrating engineering judgment:

- **SCD (Slowly Changing Dimension) handling:** dimensions currently use
  Type 1 (full overwrite) behavior via dbt's table materialization. This
  is appropriate because Olist is a static, one-time historical export,
  not a live system with observable attribute changes over time — a Type
  2 (historized) approach would solve a problem this dataset doesn't
  present, though `dim_customers` would be the natural candidate if this
  pipeline ever ingested live incremental data.
- **Daily scheduling on static data:** the Airflow DAG runs on a daily
  schedule to demonstrate scheduling capability, even though the
  underlying dataset doesn't produce genuinely new daily data — a
  deliberate demonstration choice, not a claim of ongoing business value
  from the schedule itself.
- **Local Airflow instead of MWAA:** a cost-driven choice for a
  self-funded portfolio project, with the architecture structured so the
  migration path to managed Airflow is clear.

---

## Tech stack summary

| Layer | Technology | Chosen over |
|---|---|---|
| Infrastructure as Code | Terraform | CloudFormation (AWS-only), Pulumi, manual console |
| Object storage | Amazon S3 | HDFS (legacy), local filesystem |
| Data warehouse | Redshift Serverless | Provisioned Redshift cluster, Athena-only, Snowflake |
| Query federation | Redshift Spectrum + Glue Data Catalog | Loading Silver into native Redshift tables |
| Bronze→Silver transformation | Python / Pandas | PySpark (unjustified at this data volume), SQL |
| Silver→Gold transformation | dbt | Plain SQL scripts, stored procedures |
| Data quality | Great Expectations | dbt tests alone, manual assertions |
| Orchestration | Apache Airflow (local Docker) | Cron, AWS Step Functions, Dagster/Prefect |
| Data modeling | Kimball star schema | One-big-table, snowflake schema |

---