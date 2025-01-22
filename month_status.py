from data_utils import ensure_csv_headers, read_csv_dicts, overwrite_csv_dicts

MONTH_STATUS_CSV = "month_status.csv"


def ensure_month_status_csv():
    ensure_csv_headers(MONTH_STATUS_CSV, ["year", "month", "archived"])


def is_month_archived(year, month):
    """Check if given year,month is archived (done)."""
    rows = read_csv_dicts(MONTH_STATUS_CSV)
    for r in rows:
        if r["year"] == str(year) and r["month"] == str(month):
            return (r["archived"] == "True")
    return False


def set_month_archived(year, month, archived=True):
    """Mark a month as archived or not."""
    fieldnames = ["year", "month", "archived"]
    rows = read_csv_dicts(MONTH_STATUS_CSV)
    found = False
    for r in rows:
        if r["year"] == str(year) and r["month"] == str(month):
            r["archived"] = str(archived)
            found = True
            break
    if not found:
        rows.append({"year": str(year), "month": str(month), "archived": str(archived)})
    overwrite_csv_dicts(MONTH_STATUS_CSV, fieldnames, rows)


def get_previous_month_year(year, month):
    """Returns (prev_year, prev_month) given a (year, month)."""
    y = int(year)
    m = int(month)
    if m == 1:
        return (y - 1, 12)
    else:
        return (y, m - 1)
