# ══════════════════════════════════════════════════════════════════════════════
# ALEMBIC — Reference Guide
# ══════════════════════════════════════════════════════════════════════════════
#
# What is it?
# ───────────
# Alembic is the "Git for your database". It keeps a history of all the 
# changes you have made to the tables and allows you to move forward or 
# roll back to any previous version.
#
# How does it do it?
# ──────────────────
# Each change in your models generates a file in alembic/versions/. 
# That file has two functions: upgrade() (applies the change) and 
# downgrade() (reverts it). Files are chained in order:
#
#   [None] ← a1b2c3_initial_schema.py ← d4e5f6_add_email.py ← [HEAD]
#
# Alembic knows which version your DB is in because it stores its ID in an 
# internal table called alembic_version. You never touch it.
#
#
# ══════════════════════════════════════════════════════════════════════════════
# TYPICAL WORKFLOW
# (all commands are executed from the project root)
# ══════════════════════════════════════════════════════════════════════════════
#
#  1. Edit models.py  →  add a column, a table, change a type...
#
#  2. Generate the migration:
#
#        alembic revision --autogenerate -m "short description of the change"
#
#      Alembic compares your models with the current DB and writes the 
#      upgrade()/downgrade() file automatically in alembic/versions/.
#      ALWAYS open and review it before applying it — Alembic is smart but 
#      not infallible.
#
#  3. Apply the migration to the DB:
#
#        alembic upgrade head
#
#      Executes all pending upgrade() calls until it reaches the latest one.
#      Your DB becomes synchronized with your models.
#
#
# ══════════════════════════════════════════════════════════════════════════════
# REFERENCE COMMANDS
# ══════════════════════════════════════════════════════════════════════════════
#
#  GENERATE
#  ────────
#  alembic revision --autogenerate -m "message"
#    → Detects differences between models.py and the DB and generates the file.
#
#  alembic revision -m "message"
#    → Creates an empty migration file to be filled in manually.
#      Useful for changes Alembic doesn't detect (data, SQL functions...).
#
#  FORWARD
#  ───────
#  alembic upgrade head
#    → Applies ALL pending migrations. Leaves the DB in the most recent state.
#
#  alembic upgrade +1
#    → Applies only the next migration.
#
#  alembic upgrade a1b2c3
#    → Advances to that specific version (use the first characters of the ID).
#
#  BACKWARD
#  ──────────
#  alembic downgrade -1
#    → Reverts the last migration applied.
#
#  alembic downgrade a1b2c3
#    → Goes back to that specific version.
#
#  alembic downgrade base
#    → Reverts ALL migrations. The DB is left without any managed tables.
#
#  QUERY
#  ─────
#  alembic current
#    → Shows which version the DB is currently in.
#
#  alembic history
#    → Lists all migrations in order, from oldest to newest.
#
#  alembic history --verbose
#    → Same as above but showing the message for each migration.
#
#  SPECIAL CASES
#  ──────────────
#  alembic stamp head
#    → Marks the DB as "already updated" WITHOUT executing any migration.
#      Useful when the DB already exists and you want to start using 
#      Alembic without recreating it from scratch.
#
#  alembic upgrade head --sql
#    → Executes nothing. Only prints the SQL it would execute.
#      Useful for reviewing or auditing changes before applying them.