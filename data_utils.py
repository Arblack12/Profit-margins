import csv
import os


def ensure_csv_headers(filepath, headers):
    """Ensure that a CSV file exists with the given headers.
       If it doesn't exist, create it and write headers.
    """
    if not os.path.isfile(filepath):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


def read_csv_dicts(filepath):
    """Reads a CSV into a list of dicts."""
    if not os.path.isfile(filepath):
        return []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def append_csv_dict(filepath, fieldnames, row_dict):
    """Append a single dict to CSV."""
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row_dict)


def overwrite_csv_dicts(filepath, fieldnames, data):
    """Overwrite CSV with a list of dictionaries."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row_dict in data:
            writer.writerow(row_dict)


def packaging_cost(packaging_value):
    """
    Example placeholder. If you want to treat "Box S", etc. as different costs,
    define them here or in your DB. This is left as an example.
    """
    packaging_map = {
        "Box S": 0.25,
        "Box M": 0.40,
        "Box L": 0.60,
        "Bubble Mailer": 0.20,
        "Poly Bag": 0.10,
        "Other/Multiple": 0.30
    }
    return packaging_map.get(packaging_value, 0.0)


def parse_packaging_input(packaging_str, cost_data_for_month):
    """
    Splits 'packaging_str' by commas. For each chunk:
      - If it's a valid float, add that numeric cost.
      - Otherwise, treat it as a cost_name from COSTS_CSV.
    Returns the total packaging cost.

    cost_data_for_month is a dict: { cost_name -> float(cost_value), ... }
    """
    total = 0.0
    if not packaging_str.strip():
        return 0.0

    tokens = [t.strip() for t in packaging_str.split(",") if t.strip()]
    for token in tokens:
        # try numeric
        try:
            val = float(token)
            total += val
        except ValueError:
            # if not numeric, see if it's in cost_data_for_month
            if token in cost_data_for_month:
                total += cost_data_for_month[token]
            else:
                # fallback: skip but show a warning
                print(f"[WARNING] Packaging token '{token}' not found in COSTS_CSV for this month/year and is not numeric.")
    return total


def carry_over_data_for_tab(csv_file, fieldnames, year, month, key_fields, read_csv_fn, overwrite_csv_fn, get_previous_month_year_fn):
    """
    Copies rows from (prev_year, prev_month) to (year, month)
    if the same 'key_fields' combination is not already present for (year, month).
    """
    data = read_csv_fn(csv_file)
    prev_year, prev_month = get_previous_month_year_fn(year, month)

    # Collect previous-month rows
    prev_rows = [r for r in data if r["year"] == str(prev_year) and r["month"] == str(prev_month)]
    # Collect current-month rows
    curr_rows = [r for r in data if r["year"] == str(year) and r["month"] == str(month)]

    # We'll make sets of key combinations to see if it already exists
    curr_key_set = set()
    for r in curr_rows:
        key_tuple = tuple(r[k] for k in key_fields)
        curr_key_set.add(key_tuple)

    # For each previous row, if that key combination not in current, copy it over
    new_data = []
    appended_any = False
    for r in prev_rows:
        key_tuple = tuple(r[k] for k in key_fields)
        if key_tuple not in curr_key_set:
            # We carry it over as a new row (but with updated month/year)
            new_row = dict(r)
            new_row["year"] = str(year)
            new_row["month"] = str(month)
            new_data.append(new_row)
            appended_any = True

    if appended_any:
        data.extend(new_data)
        overwrite_csv_fn(csv_file, fieldnames, data)
