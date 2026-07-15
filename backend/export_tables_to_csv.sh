#!/usr/bin/env bash
# Dump every application table to its own CSV file via psql's \copy.
#
# Usage:
#   ./export_tables_to_csv.sh "postgresql://user:pass@host:port/dbname" [output_dir]
#
# The psql binary on your PATH must be >= the server's Postgres version (same
# constraint as pg_dump). Override it with PSQL_BIN if needed, e.g.:
#   PSQL_BIN="$(brew --prefix libpq)/bin/psql" ./export_tables_to_csv.sh "..."

set -euo pipefail

CONN_STRING="${1:?Usage: $0 <connection_string> [output_dir]}"
OUT_DIR="${2:-./mlm_csv_export_$(date +%Y%m%d_%H%M%S)}"
PSQL_BIN="${PSQL_BIN:-psql}"

# Keep in sync with the tables defined in app/models.py.
TABLES=(
  sales_teams
  team_memberships
  affiliates
  commissions
  webhook_failures
  payout_requests
)

mkdir -p "$OUT_DIR"

for table in "${TABLES[@]}"; do
  csv_path="$OUT_DIR/${table}.csv"
  echo "Exporting $table -> $csv_path"
  "$PSQL_BIN" "$CONN_STRING" -c "\copy (SELECT * FROM $table) TO '$csv_path' WITH CSV HEADER"
done

echo "Done. CSVs written to $OUT_DIR/"
