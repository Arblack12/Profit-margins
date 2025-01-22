import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import os
from datetime import datetime
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


# -------------------------------------------------------------------
#                      File Paths (CSV)
# -------------------------------------------------------------------
EBAY_SKU_CSV = "ebay_sku.csv"
EBAY_SALES_CSV = "ebay_sales.csv"
WOO_SKU_CSV = "woo_sku.csv"
WOO_SALES_CSV = "woo_sales.csv"
B2B_CSV = "b2b_data.csv"
COSTS_CSV = "costs_data.csv"

# New file for month archiving
MONTH_STATUS_CSV = "month_status.csv"


# -------------------------------------------------------------------
#            Helper Functions for Reading / Writing CSV
# -------------------------------------------------------------------
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


# -------------------------------------------------------------------
#         Month Archiving / Checking "Done" status
# -------------------------------------------------------------------
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


# -------------------------------------------------------------------
#     Carry-Over Data from Previous Month (SKUs, B2B, Costs)
# -------------------------------------------------------------------
def carry_over_data_for_tab(csv_file, fieldnames, year, month, key_fields):
    """
    Copies rows from (prev_year, prev_month) to (year, month)
    if same 'key_fields' combination is not already present for (year, month).
    """
    data = read_csv_dicts(csv_file)
    prev_year, prev_month = get_previous_month_year(year, month)

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
        overwrite_csv_dicts(csv_file, fieldnames, data)


class ProfitTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Profit Tracker Application")
        # Increased default size for better visibility
        self.geometry("1300x900")
        ctk.set_appearance_mode("System")   # "Light", "Dark", or "System"
        ctk.set_default_color_theme("blue") # "blue", "green", or "dark-blue"

        # Ensure CSV headers exist
        ensure_csv_headers(
            EBAY_SKU_CSV,
            [
                "month", "year", "sku", "category",
                "sold_price_after_vat", "sold_price_before_vat",
                "cost_of_item", "packaging",
                "transaction_fee", "delivery",
                "total_expenses", "profit_margin", "profit"
            ]
        )
        ensure_csv_headers(
            EBAY_SALES_CSV,
            ["month", "year", "sku", "units_sold"]
        )
        ensure_csv_headers(
            WOO_SKU_CSV,
            [
                "month", "year", "sku", "category",
                "sold_price_after_vat", "sold_price_before_vat",
                "cost_of_item", "packaging",
                "transaction_fee", "delivery",
                "total_expenses", "profit_margin", "profit"
            ]
        )
        ensure_csv_headers(
            WOO_SALES_CSV,
            ["month", "year", "sku", "units_sold"]
        )
        ensure_csv_headers(
            B2B_CSV,
            ["month", "year", "business_name", "expense", "profit"]
        )
        ensure_csv_headers(
            COSTS_CSV,
            ["month", "year", "cost_name", "cost_value"]
        )
        ensure_month_status_csv()

        self.chart_data = {}

        # Create the Tab View
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True)

        # Create the 5 tabs
        self.tab_ebay = self.tabview.add("eBay")
        self.tab_woo = self.tabview.add("WooCommerce")
        self.tab_b2b = self.tabview.add("B2B")
        self.tab_costs = self.tabview.add("Costs")
        self.tab_summary = self.tabview.add("Summary")

        # Initialize UI in each tab
        self.init_ebay_tab()
        self.init_woo_tab()
        self.init_b2b_tab()
        self.init_costs_tab()
        self.init_summary_tab()

    # -------------------------------------------------------------------------
    #                           Common UI
    # -------------------------------------------------------------------------
    def get_month_list(self):
        """Return a list of months (1..12) as strings."""
        return [str(i) for i in range(1, 13)]

    def get_year_list(self):
        """Return a list of possible years. Adjust as needed."""
        current_year = datetime.now().year
        return [str(y) for y in range(2020, current_year + 3)]

    def mark_month_done(self, month_var, year_var):
        """Button callback to mark a month as done/archived."""
        m = month_var.get()
        y = year_var.get()
        set_month_archived(y, m, archived=True)
        messagebox.showinfo("Month Archived", f"Marked {m}/{y} as DONE. You can no longer edit data.")

    def carry_over_previous_month(self, month_var, year_var, tab_name=""):
        """Carries over eBay/Woo/B2B/Costs data from previous month if not present."""
        y = year_var.get()
        m = month_var.get()
        if is_month_archived(y, m):
            messagebox.showerror("Error", f"{m}/{y} is archived. Cannot carry over into an archived month.")
            return

        # eBay SKUs
        carry_over_data_for_tab(
            EBAY_SKU_CSV,
            [
                "month","year","sku","category","sold_price_after_vat","sold_price_before_vat",
                "cost_of_item","packaging","transaction_fee","delivery","total_expenses",
                "profit_margin","profit"
            ],
            y,m,
            key_fields=["sku"]  # If SKU doesn't exist yet in current month, carry it over
        )
        # Woo SKUs
        carry_over_data_for_tab(
            WOO_SKU_CSV,
            [
                "month","year","sku","category","sold_price_after_vat","sold_price_before_vat",
                "cost_of_item","packaging","transaction_fee","delivery","total_expenses",
                "profit_margin","profit"
            ],
            y,m,
            key_fields=["sku"]
        )
        # B2B
        carry_over_data_for_tab(
            B2B_CSV,
            ["month","year","business_name","expense","profit"],
            y,m,
            key_fields=["business_name"]
        )
        # COSTS
        carry_over_data_for_tab(
            COSTS_CSV,
            ["month","year","cost_name","cost_value"],
            y,m,
            key_fields=["cost_name"]
        )

        messagebox.showinfo("Carry Over Complete", 
            f"Data from {get_previous_month_year(y,m)[1]}/{get_previous_month_year(y,m)[0]} carried over to {m}/{y} (where not already present)."
        )

        # Refresh tables if the user is in a certain tab
        if tab_name == "eBay":
            self.refresh_ebay_sku_table()
            self.refresh_ebay_category_table()
        elif tab_name == "WooCommerce":
            self.refresh_woo_sku_table()
            self.refresh_woo_category_table()
        elif tab_name == "B2B":
            self.show_b2b_data()
            self.refresh_b2b_table()
        elif tab_name == "Costs":
            self.refresh_costs_table()

    # --- NEW: parse packaging to allow numeric or cost-name lookups ---
    def parse_packaging_input(self, packaging_str, month, year):
        """
        Splits 'packaging_str' by commas. For each chunk:
          - If it's a valid float, add that numeric cost.
          - Otherwise, treat it as a cost_name from COSTS_CSV.
        Returns the total packaging cost.
        """
        total = 0.0
        if not packaging_str.strip():
            return 0.0

        # read all costs from CSV for this month/year
        data = read_csv_dicts(COSTS_CSV)
        cost_map = {}
        for row in data:
            if row["month"] == str(month) and row["year"] == str(year):
                cost_map[row["cost_name"]] = float(row["cost_value"])

        tokens = [t.strip() for t in packaging_str.split(",") if t.strip()]
        for token in tokens:
            # try numeric
            try:
                val = float(token)
                total += val
            except ValueError:
                # if not numeric, see if it's in cost_map
                if token in cost_map:
                    total += cost_map[token]
                else:
                    # fallback: skip but show a warning
                    print(f"[WARNING] Packaging token '{token}' not found in COSTS_CSV for {month}/{year} and is not numeric.")
        return total

    # --- The old sum_packaging_costs_from_csv is still here (untouched) if needed ---
    def sum_packaging_costs_from_csv(self, packaging_str, month, year):
        """
        This was the original approach that looked up cost_name(s) in COSTS_CSV.
        But it won't catch numeric packaging unless it's also a cost_name.

        We'll keep it since we must not remove lines, but now we use 'parse_packaging_input' above.
        """
        data = read_csv_dicts(COSTS_CSV)
        selected_names = [n.strip() for n in packaging_str.split(",") if n.strip()]
        total = 0.0
        for row in data:
            if row["month"] == str(month) and row["year"] == str(year):
                if row["cost_name"] in selected_names:
                    try:
                        total += float(row["cost_value"])
                    except ValueError:
                        pass
        return total

    # --- Toplevel with checkboxes for packaging (eBay) ---
    def select_packaging_costs_ebay(self):
        month = self.ebay_month_var.get()
        year = self.ebay_year_var.get()

        data = read_csv_dicts(COSTS_CSV)
        cost_names = []
        for row in data:
            if row["month"] == month and row["year"] == year:
                cost_names.append(row["cost_name"])
        cost_names = sorted(list(set(cost_names)))

        top = tk.Toplevel(self)
        top.title("Select Packaging Costs (eBay)")
        tk.Label(top, text=f"Select Packaging Costs for {month}/{year}:").pack(pady=5)

        var_dict = {}
        for name in cost_names:
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(top, text=name, variable=var)
            chk.pack(anchor="w")
            var_dict[name] = var

        def on_confirm():
            selected = [name for name, v in var_dict.items() if v.get()]
            self.ebay_packaging_var.set(", ".join(selected))
            top.destroy()

        btn = tk.Button(top, text="Confirm", command=on_confirm)
        btn.pack(pady=5)

    # --- Toplevel with checkboxes for packaging (Woo) ---
    def select_packaging_costs_woo(self):
        month = self.woo_month_var.get()
        year = self.woo_year_var.get()

        data = read_csv_dicts(COSTS_CSV)
        cost_names = []
        for row in data:
            if row["month"] == month and row["year"] == year:
                cost_names.append(row["cost_name"])
        cost_names = sorted(list(set(cost_names)))

        top = tk.Toplevel(self)
        top.title("Select Packaging Costs (Woo)")
        tk.Label(top, text=f"Select Packaging Costs for {month}/{year}:").pack(pady=5)

        var_dict = {}
        for name in cost_names:
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(top, text=name, variable=var)
            chk.pack(anchor="w")
            var_dict[name] = var

        def on_confirm():
            selected = [name for name, v in var_dict.items() if v.get()]
            self.woo_packaging_var.set(", ".join(selected))
            top.destroy()

        btn = tk.Button(top, text="Confirm", command=on_confirm)
        btn.pack(pady=5)


    # -------------------------------------------------------------------------
    #                          TAB: eBay
    # -------------------------------------------------------------------------
    def init_ebay_tab(self):
        self.ebay_scroll_container = ctk.CTkScrollableFrame(self.tab_ebay, label_text="(Scroll Down If Needed)")
        self.ebay_scroll_container.pack(fill="both", expand=True)

        ctk.CTkLabel(self.ebay_scroll_container, text="All currency below is in £ (GBP).", font=("Arial", 14, "bold")).pack(pady=5)

        btn_frame = ctk.CTkFrame(self.ebay_scroll_container)
        btn_frame.pack(pady=5, padx=5, fill="x")
        ctk.CTkLabel(btn_frame, text="Click to show Category Table").pack(side="left", padx=5)
        show_cat_btn = ctk.CTkButton(btn_frame, text="Show Category Table", command=self.refresh_ebay_category_table)
        show_cat_btn.pack(side="left", padx=5)

        # Button to Mark Month as Done
        done_btn = ctk.CTkButton(btn_frame, text="Mark Month as Done", 
                                 command=lambda: self.mark_month_done(self.ebay_month_var, self.ebay_year_var))
        done_btn.pack(side="right", padx=5)

        # Button to Carry Over
        carry_btn = ctk.CTkButton(btn_frame, text="Carry Over from Previous Month",
                                  command=lambda: self.carry_over_previous_month(self.ebay_month_var, self.ebay_year_var, "eBay"))
        carry_btn.pack(side="right", padx=5)

        # === FRAME: Month/Year selection
        date_frame = ctk.CTkFrame(self.ebay_scroll_container)
        date_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(date_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.ebay_month_var = ctk.StringVar(value=str(datetime.now().month))
        self.ebay_month_cb = ctk.CTkComboBox(date_frame,
                                             values=self.get_month_list(),
                                             variable=self.ebay_month_var)
        self.ebay_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(date_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.ebay_year_var = ctk.StringVar(value=str(datetime.now().year))
        self.ebay_year_cb = ctk.CTkComboBox(date_frame,
                                            values=self.get_year_list(),
                                            variable=self.ebay_year_var)
        self.ebay_year_cb.grid(row=0, column=3, padx=5, pady=5)

        # FRAME: SKU Input
        input_frame = ctk.CTkFrame(self.ebay_scroll_container)
        input_frame.pack(pady=5, padx=5, fill="x")

        # New category approach (free entry):
        ctk.CTkLabel(input_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5)
        self.ebay_category_entry = ctk.CTkEntry(input_frame)
        self.ebay_category_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="SKU:").grid(row=1, column=0, padx=5, pady=5)
        self.ebay_sku_entry = ctk.CTkEntry(input_frame)
        self.ebay_sku_entry.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Sold Price (After VAT):").grid(row=2, column=0, padx=5, pady=5)
        self.ebay_price_after_vat_entry = ctk.CTkEntry(input_frame)
        self.ebay_price_after_vat_entry.grid(row=2, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Cost of Item:").grid(row=3, column=0, padx=5, pady=5)
        self.ebay_cost_entry = ctk.CTkEntry(input_frame)
        self.ebay_cost_entry.grid(row=3, column=1, padx=5, pady=5)

        # packaging line now a read-only combo + “Select Packaging”
        ctk.CTkLabel(input_frame, text="Packaging (Selected Costs):").grid(row=4, column=0, padx=5, pady=5)
        self.ebay_packaging_var = tk.StringVar()
        self.ebay_packaging_cb = ctk.CTkComboBox(
            input_frame,
            values=["(Use 'Select Packaging' Button)"],
            variable=self.ebay_packaging_var,
            state="readonly"
        )
        self.ebay_packaging_cb.grid(row=4, column=1, padx=5, pady=5)

        select_packaging_btn = ctk.CTkButton(input_frame, text="Select Packaging", command=self.select_packaging_costs_ebay)
        select_packaging_btn.grid(row=4, column=2, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Transaction Fee / Promotion (%):").grid(row=5, column=0, padx=5, pady=5)
        self.ebay_trans_fee_entry = ctk.CTkEntry(input_frame)
        self.ebay_trans_fee_entry.grid(row=5, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Transaction Flat Fee (e.g. 0.30):").grid(row=5, column=2, padx=5, pady=5)
        self.ebay_trans_fee_flat_entry = ctk.CTkEntry(input_frame)
        self.ebay_trans_fee_flat_entry.grid(row=5, column=3, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Delivery:").grid(row=6, column=0, padx=5, pady=5)
        self.ebay_delivery_entry = ctk.CTkEntry(input_frame)
        self.ebay_delivery_entry.grid(row=6, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Sold Price (Before VAT):").grid(row=7, column=0, padx=5, pady=5)
        self.ebay_before_vat_var = tk.StringVar(value="0.00")
        self.ebay_before_vat_entry = ctk.CTkEntry(input_frame, textvariable=self.ebay_before_vat_var, state="readonly")
        self.ebay_before_vat_entry.grid(row=7, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Total Expenses:").grid(row=8, column=0, padx=5, pady=5)
        self.ebay_total_exp_var = tk.StringVar(value="0.00")
        self.ebay_total_exp_entry = ctk.CTkEntry(input_frame, textvariable=self.ebay_total_exp_var, state="readonly")
        self.ebay_total_exp_entry.grid(row=8, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Profit Margin (%):").grid(row=9, column=0, padx=5, pady=5)
        self.ebay_margin_var = tk.StringVar(value="0.00")
        self.ebay_margin_entry = ctk.CTkEntry(input_frame, textvariable=self.ebay_margin_var, state="readonly")
        self.ebay_margin_entry.grid(row=9, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Profit:").grid(row=10, column=0, padx=5, pady=5)
        self.ebay_profit_var = tk.StringVar(value="0.00")
        self.ebay_profit_entry = ctk.CTkEntry(input_frame, textvariable=self.ebay_profit_var, state="readonly")
        self.ebay_profit_entry.grid(row=10, column=1, padx=5, pady=5)

        add_sku_btn = ctk.CTkButton(input_frame, text="Add/Update SKU", command=self.add_ebay_sku)
        add_sku_btn.grid(row=11, column=0, columnspan=4, pady=10)

        # MASS PASTE Sales
        sales_frame = ctk.CTkFrame(self.ebay_scroll_container)
        sales_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(sales_frame, text="Mass-Paste SKUs (line by line):").grid(row=0, column=0, padx=5, pady=5)
        self.ebay_sales_skus_text = ctk.CTkTextbox(sales_frame, width=250, height=100)
        self.ebay_sales_skus_text.grid(row=1, column=0, padx=5, pady=5)

        ctk.CTkLabel(sales_frame, text="Mass-Paste Units Sold (line by line):").grid(row=0, column=1, padx=5, pady=5)
        self.ebay_sales_units_text = ctk.CTkTextbox(sales_frame, width=250, height=100)
        self.ebay_sales_units_text.grid(row=1, column=1, padx=5, pady=5)

        add_sales_btn = ctk.CTkButton(sales_frame, text="Submit Sales", command=self.add_ebay_sales_mass)
        add_sales_btn.grid(row=2, column=0, columnspan=2, pady=10)

        # Sales Report
        self.ebay_sales_report_text = ctk.CTkTextbox(self.ebay_scroll_container, height=200, width=600, corner_radius=10)
        self.ebay_sales_report_text.pack(pady=5, padx=5)

        show_report_btn = ctk.CTkButton(self.ebay_scroll_container, text="Show eBay Sales Report", command=self.show_ebay_sales_report)
        show_report_btn.pack(pady=5)

        # Treeview for eBay SKUs
        bottom_frame = ctk.CTkFrame(self.ebay_scroll_container)
        bottom_frame.pack(pady=5, padx=5, fill="both", expand=True)

        ctk.CTkLabel(bottom_frame, text="Filter by Category (Optional):").grid(row=0, column=0, padx=5, pady=5)
        self.ebay_filter_var = tk.StringVar(value="All")
        self.ebay_filter_cb = ctk.CTkComboBox(
            bottom_frame, values=["All"], variable=self.ebay_filter_var,
            command=self.refresh_ebay_sku_table
        )
        self.ebay_filter_cb.grid(row=0, column=1, padx=5, pady=5)

        refresh_table_btn = ctk.CTkButton(
            bottom_frame, text="Refresh SKU Table",
            command=self.refresh_ebay_sku_table
        )
        refresh_table_btn.grid(row=0, column=2, padx=5, pady=5)

        # Edit selected SKU
        edit_table_btn = ctk.CTkButton(
            bottom_frame, text="Edit Selected SKU",
            command=self.edit_selected_ebay_sku
        )
        edit_table_btn.grid(row=0, column=3, padx=5, pady=5)

        columns = (
            "sku", "category", "sold_price_after_vat", "sold_price_before_vat",
            "cost_of_item", "packaging", "transaction_fee", "delivery",
            "total_expenses", "profit_margin", "profit"
        )
        self.ebay_tree = ttk.Treeview(bottom_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.ebay_tree.heading(col, text=col)
            self.ebay_tree.column(col, width=120)

        self.ebay_scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=self.ebay_tree.yview)
        self.ebay_tree.configure(yscrollcommand=self.ebay_scrollbar.set)
        self.ebay_tree.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.ebay_scrollbar.grid(row=1, column=3, sticky="ns")

        bottom_frame.rowconfigure(1, weight=1)
        bottom_frame.columnconfigure(0, weight=1)

        # Category Table
        cat_frame = ctk.CTkFrame(self.ebay_scroll_container)
        cat_frame.pack(pady=5, padx=5, fill="both", expand=False)

        ctk.CTkLabel(cat_frame, text="eBay Categories (SKUs per Category) - Scroll Down If Not Visible:").grid(row=0, column=0, columnspan=4, padx=5, pady=5)

        self.ebay_cat_columns = ("category", "sku_list")
        self.ebay_cat_tree = ttk.Treeview(cat_frame, columns=self.ebay_cat_columns, show="headings", height=6)
        self.ebay_cat_tree.heading("category", text="Category")
        self.ebay_cat_tree.heading("sku_list", text="SKUs in Category")
        self.ebay_cat_tree.column("category", width=150)
        self.ebay_cat_tree.column("sku_list", width=700)
        self.ebay_cat_tree.grid(row=1, column=0, columnspan=4, sticky="nsew")

        cat_frame.rowconfigure(1, weight=1)
        cat_frame.columnconfigure(0, weight=1)

        edit_sku_btn = ctk.CTkButton(cat_frame, text="Edit SKU", command=self.edit_ebay_sku_in_category)
        edit_sku_btn.grid(row=2, column=0, padx=5, pady=5)

        delete_sku_btn = ctk.CTkButton(cat_frame, text="Delete SKU", command=self.delete_ebay_sku_in_category)
        delete_sku_btn.grid(row=2, column=1, padx=5, pady=5)

        # Move SKU to different category
        move_sku_btn = ctk.CTkButton(cat_frame, text="Move SKU to Different Category", command=self.move_ebay_sku_category)
        move_sku_btn.grid(row=2, column=2, padx=5, pady=5)

    #
    # ---------------------- FIXED HERE: now filters by chosen Month/Year ----------------------
    #
    def refresh_ebay_sku_table(self, *args):
        # Clear existing rows
        for row in self.ebay_tree.get_children():
            self.ebay_tree.delete(row)

        # Get chosen month/year
        chosen_month = self.ebay_month_var.get()
        chosen_year = self.ebay_year_var.get()

        data = read_csv_dicts(EBAY_SKU_CSV)

        # Build category set, but only from the chosen month/year
        cat_set = set()
        for r in data:
            if r["month"] == chosen_month and r["year"] == chosen_year:
                cat_set.add(r["category"])

        cat_list = ["All"] + sorted(cat_set)
        current_vals = self.ebay_filter_cb.cget("values")
        if cat_list != list(current_vals):
            self.ebay_filter_cb.configure(values=cat_list)
            if self.ebay_filter_var.get() not in cat_list:
                self.ebay_filter_var.set("All")

        chosen_cat = self.ebay_filter_var.get()

        # Insert rows that match chosen month/year (and category if not "All")
        for r in data:
            if r["month"] == chosen_month and r["year"] == chosen_year:
                if chosen_cat == "All" or r["category"] == chosen_cat:
                    vals = (
                        r["sku"],
                        r["category"],
                        "£" + r["sold_price_after_vat"],
                        "£" + r["sold_price_before_vat"],
                        "£" + r["cost_of_item"],
                        r["packaging"],
                        "£" + r["transaction_fee"],
                        "£" + r["delivery"],
                        "£" + r["total_expenses"],
                        r["profit_margin"],
                        "£" + r["profit"]
                    )
                    self.ebay_tree.insert("", tk.END, values=vals)

    def refresh_ebay_category_table(self):
        for row in self.ebay_cat_tree.get_children():
            self.ebay_cat_tree.delete(row)

        chosen_month = self.ebay_month_var.get()
        chosen_year = self.ebay_year_var.get()

        data = read_csv_dicts(EBAY_SKU_CSV)
        cat_map = {}
        # Only gather categories for the chosen month/year
        for r in data:
            if r["month"] == chosen_month and r["year"] == chosen_year:
                cat = r["category"]
                sku = r["sku"]
                if cat not in cat_map:
                    cat_map[cat] = []
                if sku not in cat_map[cat]:
                    cat_map[cat].append(sku)

        for cat in sorted(cat_map.keys()):
            sku_list = ", ".join(sorted(cat_map[cat]))
            self.ebay_cat_tree.insert("", tk.END, values=(cat, sku_list))

    def edit_selected_ebay_sku(self):
        """Edit the SKU that is selected in the main table (ebay_tree)."""
        selection = self.ebay_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No SKU selected in the table.")
            return
        vals = self.ebay_tree.item(selection[0], "values")
        if not vals or len(vals) < 2:
            return

        chosen_sku = vals[0]
        chosen_category = vals[1].replace("£","")

        # Load from CSV
        data = read_csv_dicts(EBAY_SKU_CSV)
        for row in data:
            if row["sku"] == chosen_sku and row["category"] == chosen_category.replace("£",""):
                self.ebay_sku_entry.delete(0, tk.END)
                self.ebay_sku_entry.insert(0, row["sku"])
                self.ebay_price_after_vat_entry.delete(0, tk.END)
                self.ebay_price_after_vat_entry.insert(0, row["sold_price_after_vat"])
                self.ebay_cost_entry.delete(0, tk.END)
                self.ebay_cost_entry.insert(0, row["cost_of_item"])

                self.ebay_packaging_var.set(row["packaging"])

                self.ebay_trans_fee_entry.delete(0, tk.END)
                self.ebay_trans_fee_entry.insert(0, "0")  
                self.ebay_trans_fee_flat_entry.delete(0, tk.END)
                self.ebay_trans_fee_flat_entry.insert(0, row["transaction_fee"])

                self.ebay_delivery_entry.delete(0, tk.END)
                self.ebay_delivery_entry.insert(0, row["delivery"])

                self.ebay_category_entry.delete(0, tk.END)
                self.ebay_category_entry.insert(0, row["category"])

                self.ebay_month_var.set(row["month"])
                self.ebay_year_var.set(row["year"])
                messagebox.showinfo("Info", f"SKU '{chosen_sku}' loaded for editing.")
                break

    def add_ebay_sku(self):
        month = self.ebay_month_var.get()
        year = self.ebay_year_var.get()

        # Check if archived
        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot add/update SKU.")
            return

        category = self.ebay_category_entry.get().strip()
        sku = self.ebay_sku_entry.get().strip()
        if not sku:
            messagebox.showerror("Error", "SKU cannot be empty.")
            return

        try:
            after_vat = float(self.ebay_price_after_vat_entry.get().strip())
        except ValueError:
            after_vat = 0.0

        try:
            cost = float(self.ebay_cost_entry.get().strip())
        except ValueError:
            cost = 0.0

        packaging_str = self.ebay_packaging_var.get().strip()

        try:
            trans_fee_percent = float(self.ebay_trans_fee_entry.get().strip())
        except ValueError:
            trans_fee_percent = 0.0

        try:
            trans_fee_flat = float(self.ebay_trans_fee_flat_entry.get().strip())
        except ValueError:
            trans_fee_flat = 0.0

        trans_fee = after_vat * (trans_fee_percent / 100.0) + trans_fee_flat

        try:
            delivery = float(self.ebay_delivery_entry.get().strip())
        except ValueError:
            delivery = 0.0

        before_vat = round(after_vat / 1.2, 2) if after_vat != 0 else 0.0

        # handle packaging
        packaging_sum = self.parse_packaging_input(packaging_str, month, year)
        total_expenses = cost + trans_fee + packaging_sum + delivery
        profit = before_vat - total_expenses
        profit_margin = (profit / before_vat) * 100 if before_vat != 0 else 0.0

        self.ebay_before_vat_var.set(f"£{before_vat:.2f}")
        self.ebay_total_exp_var.set(f"£{total_expenses:.2f}")
        self.ebay_margin_var.set(f"{profit_margin:.2f}")
        self.ebay_profit_var.set(f"£{profit:.2f}")

        fieldnames = [
            "month", "year", "sku", "category",
            "sold_price_after_vat", "sold_price_before_vat",
            "cost_of_item", "packaging", "transaction_fee", "delivery",
            "total_expenses", "profit_margin", "profit"
        ]
        existing = read_csv_dicts(EBAY_SKU_CSV)

        found = False
        for row in existing:
            if (row["month"] == month and row["year"] == year and row["sku"] == sku):
                row["category"] = category
                row["sold_price_after_vat"] = f"{after_vat:.2f}"
                row["sold_price_before_vat"] = f"{before_vat:.2f}"
                row["cost_of_item"] = f"{cost:.2f}"
                row["packaging"] = packaging_str
                row["transaction_fee"] = f"{trans_fee:.2f}"
                row["delivery"] = f"{delivery:.2f}"
                row["total_expenses"] = f"{total_expenses:.2f}"
                row["profit_margin"] = f"{profit_margin:.2f}"
                row["profit"] = f"{profit:.2f}"
                found = True
                break

        if not found:
            new_row = {
                "month": month,
                "year": year,
                "sku": sku,
                "category": category,
                "sold_price_after_vat": f"{after_vat:.2f}",
                "sold_price_before_vat": f"{before_vat:.2f}",
                "cost_of_item": f"{cost:.2f}",
                "packaging": packaging_str,
                "transaction_fee": f"{trans_fee:.2f}",
                "delivery": f"{delivery:.2f}",
                "total_expenses": f"{total_expenses:.2f}",
                "profit_margin": f"{profit_margin:.2f}",
                "profit": f"{profit:.2f}"
            }
            existing.append(new_row)

        overwrite_csv_dicts(EBAY_SKU_CSV, fieldnames, existing)
        messagebox.showinfo("Success", f"SKU '{sku}' saved/updated for {month}/{year}.")
        self.refresh_ebay_sku_table()

    def add_ebay_sales_mass(self):
        month = self.ebay_month_var.get()
        year = self.ebay_year_var.get()

        # Check if archived
        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot add/update sales.")
            return

        sku_lines = self.ebay_sales_skus_text.get("1.0", "end").strip().splitlines()
        units_lines = self.ebay_sales_units_text.get("1.0", "end").strip().splitlines()

        count = 0
        fieldnames = ["month", "year", "sku", "units_sold"]
        existing = read_csv_dicts(EBAY_SALES_CSV)

        for i in range(min(len(sku_lines), len(units_lines))):
            sku = sku_lines[i].strip()
            if not sku:
                continue
            try:
                units_sold = int(units_lines[i].strip())
            except ValueError:
                units_sold = 0

            found = False
            for row in existing:
                if (row["month"] == month and row["year"] == year and row["sku"] == sku):
                    row["units_sold"] = str(units_sold)
                    found = True
                    break
            if not found:
                new_row = {
                    "month": month,
                    "year": year,
                    "sku": sku,
                    "units_sold": str(units_sold)
                }
                existing.append(new_row)
            count += 1

        overwrite_csv_dicts(EBAY_SALES_CSV, fieldnames, existing)
        messagebox.showinfo("Success", f"Mass Sales Updated: {count} entries processed.")

    def show_ebay_sales_report(self):
        month = self.ebay_month_var.get()
        year = self.ebay_year_var.get()
        self.ebay_sales_report_text.delete("0.0", "end")

        sku_data = read_csv_dicts(EBAY_SKU_CSV)
        sales_data = read_csv_dicts(EBAY_SALES_CSV)

        profit_dict = {}
        for row in sku_data:
            if row["month"] == month and row["year"] == year:
                sku = row["sku"]
                try:
                    profit_per_item = float(row["profit"])
                except ValueError:
                    profit_per_item = 0.0
                profit_dict[sku] = profit_per_item

        total_profit = 0.0
        report_lines = [f"--- eBay Sales Report for {month}/{year} ---"]

        for row in sales_data:
            if row["month"] == month and row["year"] == year:
                sku = row["sku"]
                try:
                    units_sold = int(row["units_sold"])
                except ValueError:
                    units_sold = 0
                if sku in profit_dict:
                    line_profit = profit_dict[sku] * units_sold
                    total_profit += line_profit
                    report_lines.append(
                        f"SKU: {sku}, Units Sold: {units_sold}, "
                        f"Profit per Item: £{profit_dict[sku]:.2f}, "
                        f"Line Profit: £{line_profit:.2f}"
                    )
                else:
                    report_lines.append(
                        f"SKU: {sku}, Units Sold: {units_sold}, [No matching SKU data found]"
                    )

        report_lines.append(f"Total eBay Profit for {month}/{year}: £{total_profit:.2f}")
        self.ebay_sales_report_text.insert("0.0", "\n".join(report_lines) + "\n")

    def edit_ebay_sku_in_category(self):
        selection = self.ebay_cat_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No category row selected.")
            return

        values = self.ebay_cat_tree.item(selection[0], "values")
        if len(values) < 2:
            return
        category = values[0]
        sku_list_str = values[1]
        sku_list = [s.strip() for s in sku_list_str.split(",") if s.strip()]

        if not sku_list:
            messagebox.showinfo("Info", "No SKUs to edit in this category.")
            return

        chosen_sku = simpledialog.askstring(
            "Edit SKU",
            f"Category: {category}\nSKUs: {', '.join(sku_list)}\n\nEnter one SKU to edit:"
        )
        if not chosen_sku or chosen_sku not in sku_list:
            return

        data = read_csv_dicts(EBAY_SKU_CSV)
        for row in data:
            if row["sku"] == chosen_sku and row["category"] == category:
                self.ebay_sku_entry.delete(0, tk.END)
                self.ebay_sku_entry.insert(0, row["sku"])
                self.ebay_price_after_vat_entry.delete(0, tk.END)
                self.ebay_price_after_vat_entry.insert(0, row["sold_price_after_vat"])
                self.ebay_cost_entry.delete(0, tk.END)
                self.ebay_cost_entry.insert(0, row["cost_of_item"])
                self.ebay_packaging_var.set(row["packaging"])
                self.ebay_trans_fee_entry.delete(0, tk.END)
                self.ebay_trans_fee_entry.insert(0, "0")
                self.ebay_trans_fee_flat_entry.delete(0, tk.END)
                self.ebay_trans_fee_flat_entry.insert(0, row["transaction_fee"])
                self.ebay_delivery_entry.delete(0, tk.END)
                self.ebay_delivery_entry.insert(0, row["delivery"])
                self.ebay_category_entry.delete(0, tk.END)
                self.ebay_category_entry.insert(0, row["category"])
                self.ebay_month_var.set(row["month"])
                self.ebay_year_var.set(row["year"])
                self.add_ebay_sku()
                messagebox.showinfo("Info", f"SKU '{chosen_sku}' loaded for editing.")
                break

    def delete_ebay_sku_in_category(self):
        selection = self.ebay_cat_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No category row selected.")
            return

        values = self.ebay_cat_tree.item(selection[0], "values")
        if len(values) < 2:
            return
        category = values[0]
        sku_list_str = values[1]
        sku_list = [s.strip() for s in sku_list_str.split(",") if s.strip()]

        if not sku_list:
            messagebox.showinfo("Info", "No SKUs to delete in this category.")
            return

        chosen_sku = simpledialog.askstring(
            "Delete SKU",
            f"Category: {category}\nSKUs: {', '.join(sku_list)}\n\nEnter one SKU to delete:"
        )
        if not chosen_sku or chosen_sku not in sku_list:
            return

        data = read_csv_dicts(EBAY_SKU_CSV)
        new_data = []
        deleted_count = 0
        for row in data:
            if row["sku"] == chosen_sku and row["category"] == category:
                deleted_count += 1
            else:
                new_data.append(row)

        if deleted_count > 0:
            fieldnames = [
                "month", "year", "sku", "category",
                "sold_price_after_vat", "sold_price_before_vat",
                "cost_of_item", "packaging",
                "transaction_fee", "delivery",
                "total_expenses", "profit_margin", "profit"
            ]
            overwrite_csv_dicts(EBAY_SKU_CSV, fieldnames, new_data)
            messagebox.showinfo("Success", f"SKU '{chosen_sku}' deleted successfully.")
            self.refresh_ebay_category_table()
            self.refresh_ebay_sku_table()
        else:
            messagebox.showinfo("Info", f"SKU '{chosen_sku}' not found for deletion.")

    def move_ebay_sku_category(self):
        """Allow user to pick an SKU and new category, then update."""
        selection = self.ebay_cat_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No category row selected.")
            return

        values = self.ebay_cat_tree.item(selection[0], "values")
        if len(values) < 2:
            return
        old_category = values[0]
        sku_list_str = values[1]
        sku_list = [s.strip() for s in sku_list_str.split(",") if s.strip()]
        if not sku_list:
            messagebox.showinfo("Info", "No SKUs in this category to move.")
            return

        chosen_sku = simpledialog.askstring(
            "Move SKU",
            f"Current Category: {old_category}\nSKUs: {', '.join(sku_list)}\n\nEnter one SKU to move to a new category:"
        )
        if not chosen_sku or chosen_sku not in sku_list:
            return

        new_cat = simpledialog.askstring("New Category", "Enter new category name:")
        if not new_cat:
            return

        data = read_csv_dicts(EBAY_SKU_CSV)
        changed = 0
        for row in data:
            if row["sku"] == chosen_sku and row["category"] == old_category:
                row["category"] = new_cat
                changed += 1

        if changed:
            fieldnames = [
                "month","year","sku","category","sold_price_after_vat","sold_price_before_vat",
                "cost_of_item","packaging","transaction_fee","delivery","total_expenses",
                "profit_margin","profit"
            ]
            overwrite_csv_dicts(EBAY_SKU_CSV, fieldnames, data)
            messagebox.showinfo("Success", f"Moved SKU '{chosen_sku}' to category '{new_cat}'.")
            self.refresh_ebay_category_table()
            self.refresh_ebay_sku_table()
        else:
            messagebox.showinfo("Info", "No matching SKU found to move.")


    # -------------------------------------------------------------------------
    #                          TAB: WooCommerce
    # -------------------------------------------------------------------------
    def init_woo_tab(self):
        self.woo_scroll_container = ctk.CTkScrollableFrame(self.tab_woo, label_text="(Scroll Down If Needed)")
        self.woo_scroll_container.pack(fill="both", expand=True)

        ctk.CTkLabel(self.woo_scroll_container, text="All currency below is in £ (GBP).", font=("Arial", 14, "bold")).pack(pady=5)

        btn_frame = ctk.CTkFrame(self.woo_scroll_container)
        btn_frame.pack(pady=5, padx=5, fill="x")
        ctk.CTkLabel(btn_frame, text="Click to show Category Table").pack(side="left", padx=5)
        show_cat_btn = ctk.CTkButton(btn_frame, text="Show Category Table", command=self.refresh_woo_category_table)
        show_cat_btn.pack(side="left", padx=5)

        # Mark Month Done
        done_btn = ctk.CTkButton(btn_frame, text="Mark Month as Done", 
                                 command=lambda: self.mark_month_done(self.woo_month_var, self.woo_year_var))
        done_btn.pack(side="right", padx=5)

        # Carry Over
        carry_btn = ctk.CTkButton(btn_frame, text="Carry Over from Previous Month",
                                  command=lambda: self.carry_over_previous_month(self.woo_month_var, self.woo_year_var, "WooCommerce"))
        carry_btn.pack(side="right", padx=5)

        date_frame = ctk.CTkFrame(self.woo_scroll_container)
        date_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(date_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.woo_month_var = tk.StringVar(value=str(datetime.now().month))
        self.woo_month_cb = ctk.CTkComboBox(date_frame,
                                            values=self.get_month_list(),
                                            variable=self.woo_month_var)
        self.woo_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(date_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.woo_year_var = tk.StringVar(value=str(datetime.now().year))
        self.woo_year_cb = ctk.CTkComboBox(date_frame,
                                           values=self.get_year_list(),
                                           variable=self.woo_year_var)
        self.woo_year_cb.grid(row=0, column=3, padx=5, pady=5)

        input_frame = ctk.CTkFrame(self.woo_scroll_container)
        input_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(input_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5)
        self.woo_category_entry = ctk.CTkEntry(input_frame)
        self.woo_category_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="SKU:").grid(row=1, column=0, padx=5, pady=5)
        self.woo_sku_entry = ctk.CTkEntry(input_frame)
        self.woo_sku_entry.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Sold Price (After VAT):").grid(row=2, column=0, padx=5, pady=5)
        self.woo_price_after_vat_entry = ctk.CTkEntry(input_frame)
        self.woo_price_after_vat_entry.grid(row=2, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Cost of Item:").grid(row=3, column=0, padx=5, pady=5)
        self.woo_cost_entry = ctk.CTkEntry(input_frame)
        self.woo_cost_entry.grid(row=3, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Packaging (Selected Costs):").grid(row=4, column=0, padx=5, pady=5)
        self.woo_packaging_var = tk.StringVar()
        self.woo_packaging_cb = ctk.CTkComboBox(
            input_frame,
            values=["(Use 'Select Packaging' Button)"],
            variable=self.woo_packaging_var,
            state="readonly"
        )
        self.woo_packaging_cb.grid(row=4, column=1, padx=5, pady=5)

        select_packaging_btn = ctk.CTkButton(input_frame, text="Select Packaging", command=self.select_packaging_costs_woo)
        select_packaging_btn.grid(row=4, column=2, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Transaction Fee / Promotion (%):").grid(row=5, column=0, padx=5, pady=5)
        self.woo_trans_fee_entry = ctk.CTkEntry(input_frame)
        self.woo_trans_fee_entry.grid(row=5, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Transaction Flat Fee (e.g. 0.30):").grid(row=5, column=2, padx=5, pady=5)
        self.woo_trans_fee_flat_entry = ctk.CTkEntry(input_frame)
        self.woo_trans_fee_flat_entry.grid(row=5, column=3, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Delivery:").grid(row=6, column=0, padx=5, pady=5)
        self.woo_delivery_entry = ctk.CTkEntry(input_frame)
        self.woo_delivery_entry.grid(row=6, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Sold Price (Before VAT):").grid(row=7, column=0, padx=5, pady=5)
        self.woo_before_vat_var = tk.StringVar(value="0.00")
        self.woo_before_vat_entry = ctk.CTkEntry(input_frame, textvariable=self.woo_before_vat_var, state="readonly")
        self.woo_before_vat_entry.grid(row=7, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Total Expenses:").grid(row=8, column=0, padx=5, pady=5)
        self.woo_total_exp_var = tk.StringVar(value="0.00")
        self.woo_total_exp_entry = ctk.CTkEntry(input_frame, textvariable=self.woo_total_exp_var, state="readonly")
        self.woo_total_exp_entry.grid(row=8, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Profit Margin (%):").grid(row=9, column=0, padx=5, pady=5)
        self.woo_margin_var = tk.StringVar(value="0.00")
        self.woo_margin_entry = ctk.CTkEntry(input_frame, textvariable=self.woo_margin_var, state="readonly")
        self.woo_margin_entry.grid(row=9, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Profit:").grid(row=10, column=0, padx=5, pady=5)
        self.woo_profit_var = tk.StringVar(value="0.00")
        self.woo_profit_entry = ctk.CTkEntry(input_frame, textvariable=self.woo_profit_var, state="readonly")
        self.woo_profit_entry.grid(row=10, column=1, padx=5, pady=5)

        add_sku_btn = ctk.CTkButton(input_frame, text="Add/Update SKU", command=self.add_woo_sku)
        add_sku_btn.grid(row=11, column=0, columnspan=4, pady=10)

        # MASS PASTE Sales
        sales_frame = ctk.CTkFrame(self.woo_scroll_container)
        sales_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(sales_frame, text="Mass-Paste SKUs (line by line):").grid(row=0, column=0, padx=5, pady=5)
        self.woo_sales_skus_text = ctk.CTkTextbox(sales_frame, width=250, height=100)
        self.woo_sales_skus_text.grid(row=1, column=0, padx=5, pady=5)

        ctk.CTkLabel(sales_frame, text="Mass-Paste Units Sold (line by line):").grid(row=0, column=1, padx=5, pady=5)
        self.woo_sales_units_text = ctk.CTkTextbox(sales_frame, width=250, height=100)
        self.woo_sales_units_text.grid(row=1, column=1, padx=5, pady=5)

        add_sales_btn = ctk.CTkButton(sales_frame, text="Submit Sales", command=self.add_woo_sales_mass)
        add_sales_btn.grid(row=2, column=0, columnspan=2, pady=10)

        self.woo_sales_report_text = ctk.CTkTextbox(self.woo_scroll_container, height=200, width=600, corner_radius=10)
        self.woo_sales_report_text.pack(pady=5, padx=5)

        show_report_btn = ctk.CTkButton(self.woo_scroll_container, text="Show WooCommerce Sales Report", command=self.show_woo_sales_report)
        show_report_btn.pack(pady=5)

        bottom_frame = ctk.CTkFrame(self.woo_scroll_container)
        bottom_frame.pack(pady=5, padx=5, fill="both", expand=True)

        ctk.CTkLabel(bottom_frame, text="Filter by Category (Optional):").grid(row=0, column=0, padx=5, pady=5)
        self.woo_filter_var = tk.StringVar(value="All")
        self.woo_filter_cb = ctk.CTkComboBox(
            bottom_frame, values=["All"], variable=self.woo_filter_var,
            command=self.refresh_woo_sku_table
        )
        self.woo_filter_cb.grid(row=0, column=1, padx=5, pady=5)

        refresh_table_btn = ctk.CTkButton(
            bottom_frame, text="Refresh SKU Table",
            command=self.refresh_woo_sku_table
        )
        refresh_table_btn.grid(row=0, column=2, padx=5, pady=5)

        # Edit selected SKU
        edit_table_btn = ctk.CTkButton(
            bottom_frame, text="Edit Selected SKU",
            command=self.edit_selected_woo_sku
        )
        edit_table_btn.grid(row=0, column=3, padx=5, pady=5)

        woo_columns = (
            "sku", "category", "sold_price_after_vat", "sold_price_before_vat",
            "cost_of_item", "packaging", "transaction_fee", "delivery",
            "total_expenses", "profit_margin", "profit"
        )
        self.woo_tree = ttk.Treeview(bottom_frame, columns=woo_columns, show="headings", height=8)
        for col in woo_columns:
            self.woo_tree.heading(col, text=col)
            self.woo_tree.column(col, width=120)

        self.woo_scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=self.woo_tree.yview)
        self.woo_tree.configure(yscrollcommand=self.woo_scrollbar.set)

        self.woo_tree.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.woo_scrollbar.grid(row=1, column=3, sticky="ns")

        bottom_frame.rowconfigure(1, weight=1)
        bottom_frame.columnconfigure(0, weight=1)

        cat_frame = ctk.CTkFrame(self.woo_scroll_container)
        cat_frame.pack(pady=5, padx=5, fill="both", expand=False)

        ctk.CTkLabel(cat_frame, text="Woo Categories (SKUs per Category) - Scroll If Not Visible:").grid(row=0, column=0, columnspan=4, padx=5, pady=5)

        self.woo_cat_columns = ("category", "sku_list")
        self.woo_cat_tree = ttk.Treeview(cat_frame, columns=self.woo_cat_columns, show="headings", height=6)
        self.woo_cat_tree.heading("category", text="Category")
        self.woo_cat_tree.heading("sku_list", text="SKUs in Category")
        self.woo_cat_tree.column("category", width=150)
        self.woo_cat_tree.column("sku_list", width=700)
        self.woo_cat_tree.grid(row=1, column=0, columnspan=4, sticky="nsew")

        cat_frame.rowconfigure(1, weight=1)
        cat_frame.columnconfigure(0, weight=1)

        edit_sku_btn = ctk.CTkButton(cat_frame, text="Edit SKU", command=self.edit_woo_sku_in_category)
        edit_sku_btn.grid(row=2, column=0, padx=5, pady=5)

        delete_sku_btn = ctk.CTkButton(cat_frame, text="Delete SKU", command=self.delete_woo_sku_in_category)
        delete_sku_btn.grid(row=2, column=1, padx=5, pady=5)

        move_sku_btn = ctk.CTkButton(cat_frame, text="Move SKU to Different Category", command=self.move_woo_sku_category)
        move_sku_btn.grid(row=2, column=2, padx=5, pady=5)

    #
    # ---------------------- FIXED HERE: now filters by chosen Month/Year ----------------------
    #
    def refresh_woo_sku_table(self, *args):
        for row in self.woo_tree.get_children():
            self.woo_tree.delete(row)

        chosen_month = self.woo_month_var.get()
        chosen_year = self.woo_year_var.get()

        data = read_csv_dicts(WOO_SKU_CSV)

        # Build category set, only from the chosen month/year
        cat_set = set()
        for r in data:
            if r["month"] == chosen_month and r["year"] == chosen_year:
                cat_set.add(r["category"])

        cat_list = ["All"] + sorted(cat_set)
        current_vals = self.woo_filter_cb.cget("values")
        if cat_list != list(current_vals):
            self.woo_filter_cb.configure(values=cat_list)
            if self.woo_filter_var.get() not in cat_list:
                self.woo_filter_var.set("All")

        chosen_cat = self.woo_filter_var.get()
        for r in data:
            if r["month"] == chosen_month and r["year"] == chosen_year:
                if chosen_cat == "All" or r["category"] == chosen_cat:
                    vals = (
                        r["sku"],
                        r["category"],
                        "£" + r["sold_price_after_vat"],
                        "£" + r["sold_price_before_vat"],
                        "£" + r["cost_of_item"],
                        r["packaging"],
                        "£" + r["transaction_fee"],
                        "£" + r["delivery"],
                        "£" + r["total_expenses"],
                        r["profit_margin"],
                        "£" + r["profit"]
                    )
                    self.woo_tree.insert("", tk.END, values=vals)

    def refresh_woo_category_table(self):
        for row in self.woo_cat_tree.get_children():
            self.woo_cat_tree.delete(row)

        chosen_month = self.woo_month_var.get()
        chosen_year = self.woo_year_var.get()

        data = read_csv_dicts(WOO_SKU_CSV)
        cat_map = {}
        for r in data:
            # Only read the chosen month/year
            if r["month"] == chosen_month and r["year"] == chosen_year:
                cat = r["category"]
                sku = r["sku"]
                if cat not in cat_map:
                    cat_map[cat] = []
                if sku not in cat_map[cat]:
                    cat_map[cat].append(sku)

        for cat in sorted(cat_map.keys()):
            sku_list = ", ".join(sorted(cat_map[cat]))
            self.woo_cat_tree.insert("", tk.END, values=(cat, sku_list))

    def edit_selected_woo_sku(self):
        """Edit the SKU that is selected in the main table (woo_tree)."""
        selection = self.woo_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No SKU selected in the table.")
            return
        vals = self.woo_tree.item(selection[0], "values")
        if not vals or len(vals) < 2:
            return

        chosen_sku = vals[0]
        chosen_category = vals[1].replace("£","")

        data = read_csv_dicts(WOO_SKU_CSV)
        for row in data:
            if row["sku"] == chosen_sku and row["category"] == chosen_category:
                self.woo_sku_entry.delete(0, tk.END)
                self.woo_sku_entry.insert(0, row["sku"])
                self.woo_price_after_vat_entry.delete(0, tk.END)
                self.woo_price_after_vat_entry.insert(0, row["sold_price_after_vat"])
                self.woo_cost_entry.delete(0, tk.END)
                self.woo_cost_entry.insert(0, row["cost_of_item"])
                self.woo_packaging_var.set(row["packaging"])
                self.woo_trans_fee_entry.delete(0, tk.END)
                self.woo_trans_fee_entry.insert(0, "0")
                self.woo_trans_fee_flat_entry.delete(0, tk.END)
                self.woo_trans_fee_flat_entry.insert(0, row["transaction_fee"])
                self.woo_delivery_entry.delete(0, tk.END)
                self.woo_delivery_entry.insert(0, row["delivery"])
                self.woo_category_entry.delete(0, tk.END)
                self.woo_category_entry.insert(0, row["category"])
                self.woo_month_var.set(row["month"])
                self.woo_year_var.set(row["year"])
                messagebox.showinfo("Info", f"SKU '{chosen_sku}' loaded for editing.")
                break

    def add_woo_sku(self):
        month = self.woo_month_var.get()
        year = self.woo_year_var.get()

        # Check archive
        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot add/update SKU.")
            return

        category = self.woo_category_entry.get().strip()
        sku = self.woo_sku_entry.get().strip()
        if not sku:
            messagebox.showerror("Error", "SKU cannot be empty.")
            return

        try:
            after_vat = float(self.woo_price_after_vat_entry.get().strip())
        except ValueError:
            after_vat = 0.0

        try:
            cost = float(self.woo_cost_entry.get().strip())
        except ValueError:
            cost = 0.0

        packaging_str = self.woo_packaging_var.get().strip()

        try:
            trans_fee_percent = float(self.woo_trans_fee_entry.get().strip())
        except ValueError:
            trans_fee_percent = 0.0

        try:
            trans_fee_flat = float(self.woo_trans_fee_flat_entry.get().strip())
        except ValueError:
            trans_fee_flat = 0.0

        trans_fee = after_vat * (trans_fee_percent / 100.0) + trans_fee_flat

        try:
            delivery = float(self.woo_delivery_entry.get().strip())
        except ValueError:
            delivery = 0.0

        before_vat = round(after_vat / 1.2, 2) if after_vat != 0 else 0.0

        # parse packaging
        packaging_sum = self.parse_packaging_input(packaging_str, month, year)

        total_expenses = cost + trans_fee + packaging_sum + delivery
        profit = before_vat - total_expenses
        profit_margin = (profit / before_vat) * 100 if before_vat != 0 else 0.0

        self.woo_before_vat_var.set(f"£{before_vat:.2f}")
        self.woo_total_exp_var.set(f"£{total_expenses:.2f}")
        self.woo_margin_var.set(f"{profit_margin:.2f}")
        self.woo_profit_var.set(f"£{profit:.2f}")

        fieldnames = [
            "month", "year", "sku", "category",
            "sold_price_after_vat", "sold_price_before_vat",
            "cost_of_item", "packaging", "transaction_fee", "delivery",
            "total_expenses", "profit_margin", "profit"
        ]
        existing = read_csv_dicts(WOO_SKU_CSV)

        found = False
        for row in existing:
            if (row["month"] == month and row["year"] == year and row["sku"] == sku):
                row["category"] = category
                row["sold_price_after_vat"] = f"{after_vat:.2f}"
                row["sold_price_before_vat"] = f"{before_vat:.2f}"
                row["cost_of_item"] = f"{cost:.2f}"
                row["packaging"] = packaging_str
                row["transaction_fee"] = f"{trans_fee:.2f}"
                row["delivery"] = f"{delivery:.2f}"
                row["total_expenses"] = f"{total_expenses:.2f}"
                row["profit_margin"] = f"{profit_margin:.2f}"
                row["profit"] = f"{profit:.2f}"
                found = True
                break

        if not found:
            new_row = {
                "month": month,
                "year": year,
                "sku": sku,
                "category": category,
                "sold_price_after_vat": f"{after_vat:.2f}",
                "sold_price_before_vat": f"{before_vat:.2f}",
                "cost_of_item": f"{cost:.2f}",
                "packaging": packaging_str,
                "transaction_fee": f"{trans_fee:.2f}",
                "delivery": f"{delivery:.2f}",
                "total_expenses": f"{total_expenses:.2f}",
                "profit_margin": f"{profit_margin:.2f}",
                "profit": f"{profit:.2f}"
            }
            existing.append(new_row)

        overwrite_csv_dicts(WOO_SKU_CSV, fieldnames, existing)
        messagebox.showinfo("Success", f"SKU '{sku}' saved/updated for {month}/{year}.")
        self.refresh_woo_sku_table()

    def add_woo_sales_mass(self):
        month = self.woo_month_var.get()
        year = self.woo_year_var.get()

        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot add/update sales.")
            return

        sku_lines = self.woo_sales_skus_text.get("1.0", "end").strip().splitlines()
        units_lines = self.woo_sales_units_text.get("1.0", "end").strip().splitlines()

        fieldnames = ["month", "year", "sku", "units_sold"]
        existing = read_csv_dicts(WOO_SALES_CSV)

        count = 0
        for i in range(min(len(sku_lines), len(units_lines))):
            sku = sku_lines[i].strip()
            if not sku:
                continue
            try:
                units_sold = int(units_lines[i].strip())
            except ValueError:
                units_sold = 0

            found = False
            for row in existing:
                if (row["month"] == month and row["year"] == year and row["sku"] == sku):
                    row["units_sold"] = str(units_sold)
                    found = True
                    break
            if not found:
                new_row = {
                    "month": month,
                    "year": year,
                    "sku": sku,
                    "units_sold": str(units_sold)
                }
                existing.append(new_row)
            count += 1

        overwrite_csv_dicts(WOO_SALES_CSV, fieldnames, existing)
        messagebox.showinfo("Success", f"Mass Sales Updated: {count} entries processed.")

    def show_woo_sales_report(self):
        month = self.woo_month_var.get()
        year = self.woo_year_var.get()
        self.woo_sales_report_text.delete("0.0", "end")

        sku_data = read_csv_dicts(WOO_SKU_CSV)
        sales_data = read_csv_dicts(WOO_SALES_CSV)

        profit_dict = {}
        for row in sku_data:
            if row["month"] == month and row["year"] == year:
                sku = row["sku"]
                try:
                    profit_per_item = float(row["profit"])
                except ValueError:
                    profit_per_item = 0.0
                profit_dict[sku] = profit_per_item

        total_profit = 0.0
        report_lines = [f"--- WooCommerce Sales Report for {month}/{year} ---"]
        for row in sales_data:
            if row["month"] == month and row["year"] == year:
                sku = row["sku"]
                try:
                    units_sold = int(row["units_sold"])
                except ValueError:
                    units_sold = 0
                if sku in profit_dict:
                    line_profit = profit_dict[sku] * units_sold
                    total_profit += line_profit
                    report_lines.append(
                        f"SKU: {sku}, Units Sold: {units_sold}, "
                        f"Profit per Item: £{profit_dict[sku]:.2f}, "
                        f"Line Profit: £{line_profit:.2f}"
                    )
                else:
                    report_lines.append(
                        f"SKU: {sku}, Units Sold: {units_sold}, [No matching SKU data found]"
                    )

        report_lines.append(f"Total Woo Profit for {month}/{year}: £{total_profit:.2f}")
        self.woo_sales_report_text.insert("0.0", "\n".join(report_lines) + "\n")

    def edit_woo_sku_in_category(self):
        selection = self.woo_cat_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No category row selected.")
            return

        values = self.woo_cat_tree.item(selection[0], "values")
        if len(values) < 2:
            return
        category = values[0]
        sku_list_str = values[1]
        sku_list = [s.strip() for s in sku_list_str.split(",") if s.strip()]

        if not sku_list:
            messagebox.showinfo("Info", "No SKUs to edit in this category.")
            return

        chosen_sku = simpledialog.askstring(
            "Edit SKU",
            f"Category: {category}\nSKUs: {', '.join(sku_list)}\n\nEnter one SKU to edit:"
        )
        if not chosen_sku or chosen_sku not in sku_list:
            return

        data = read_csv_dicts(WOO_SKU_CSV)
        for row in data:
            if row["sku"] == chosen_sku and row["category"] == category:
                self.woo_sku_entry.delete(0, tk.END)
                self.woo_sku_entry.insert(0, row["sku"])
                self.woo_price_after_vat_entry.delete(0, tk.END)
                self.woo_price_after_vat_entry.insert(0, row["sold_price_after_vat"])
                self.woo_cost_entry.delete(0, tk.END)
                self.woo_cost_entry.insert(0, row["cost_of_item"])
                self.woo_packaging_var.set(row["packaging"])
                self.woo_trans_fee_entry.delete(0, tk.END)
                self.woo_trans_fee_entry.insert(0, "0")
                self.woo_trans_fee_flat_entry.delete(0, tk.END)
                self.woo_trans_fee_flat_entry.insert(0, row["transaction_fee"])
                self.woo_delivery_entry.delete(0, tk.END)
                self.woo_delivery_entry.insert(0, row["delivery"])
                self.woo_category_entry.delete(0, tk.END)
                self.woo_category_entry.insert(0, row["category"])
                self.woo_month_var.set(row["month"])
                self.woo_year_var.set(row["year"])
                self.add_woo_sku()
                messagebox.showinfo("Info", f"SKU '{chosen_sku}' loaded for editing.")
                break

    def delete_woo_sku_in_category(self):
        selection = self.woo_cat_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No category row selected.")
            return

        values = self.woo_cat_tree.item(selection[0], "values")
        if len(values) < 2:
            return
        category = values[0]
        sku_list_str = values[1]
        sku_list = [s.strip() for s in sku_list_str.split(",") if s.strip()]

        if not sku_list:
            messagebox.showinfo("Info", "No SKUs to delete in this category.")
            return

        chosen_sku = simpledialog.askstring(
            "Delete SKU",
            f"Category: {category}\nSKUs: {', '.join(sku_list)}\n\nEnter one SKU to delete:"
        )
        if not chosen_sku or chosen_sku not in sku_list:
            return

        data = read_csv_dicts(WOO_SKU_CSV)
        new_data = []
        deleted_count = 0
        for row in data:
            if row["sku"] == chosen_sku and row["category"] == category:
                deleted_count += 1
            else:
                new_data.append(row)

        if deleted_count > 0:
            fieldnames = [
                "month", "year", "sku", "category",
                "sold_price_after_vat", "sold_price_before_vat",
                "cost_of_item", "packaging", "transaction_fee",
                "delivery", "total_expenses", "profit_margin", "profit"
            ]
            overwrite_csv_dicts(WOO_SKU_CSV, fieldnames, new_data)
            messagebox.showinfo("Success", f"SKU '{chosen_sku}' deleted successfully.")
            self.refresh_woo_category_table()
            self.refresh_woo_sku_table()
        else:
            messagebox.showinfo("Info", f"SKU '{chosen_sku}' not found for deletion.")

    def move_woo_sku_category(self):
        selection = self.woo_cat_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No category row selected.")
            return

        values = self.woo_cat_tree.item(selection[0], "values")
        if len(values) < 2:
            return
        old_category = values[0]
        sku_list_str = values[1]
        sku_list = [s.strip() for s in sku_list_str.split(",") if s.strip()]
        if not sku_list:
            messagebox.showinfo("Info", "No SKUs in this category to move.")
            return

        chosen_sku = simpledialog.askstring(
            "Move SKU",
            f"Current Category: {old_category}\nSKUs: {', '.join(sku_list)}\n\nEnter one SKU to move to a new category:"
        )
        if not chosen_sku or chosen_sku not in sku_list:
            return

        new_cat = simpledialog.askstring("New Category", "Enter new category name:")
        if not new_cat:
            return

        data = read_csv_dicts(WOO_SKU_CSV)
        changed = 0
        for row in data:
            if row["sku"] == chosen_sku and row["category"] == old_category:
                row["category"] = new_cat
                changed += 1

        if changed:
            fieldnames = [
                "month","year","sku","category","sold_price_after_vat","sold_price_before_vat",
                "cost_of_item","packaging","transaction_fee","delivery","total_expenses",
                "profit_margin","profit"
            ]
            overwrite_csv_dicts(WOO_SKU_CSV, fieldnames, data)
            messagebox.showinfo("Success", f"Moved SKU '{chosen_sku}' to category '{new_cat}'.")
            self.refresh_woo_category_table()
            self.refresh_woo_sku_table()
        else:
            messagebox.showinfo("Info", "No matching SKU found to move.")


    # -------------------------------------------------------------------------
    #                          TAB: B2B
    # -------------------------------------------------------------------------
    def init_b2b_tab(self):
        self.b2b_scroll_container = ctk.CTkScrollableFrame(self.tab_b2b, label_text="(Scrollable Area)")
        self.b2b_scroll_container.pack(fill="both", expand=True)

        date_frame = ctk.CTkFrame(self.b2b_scroll_container)
        date_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(date_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.b2b_month_var = ctk.StringVar(value=str(datetime.now().month))
        self.b2b_month_cb = ctk.CTkComboBox(date_frame,
                                            values=self.get_month_list(),
                                            variable=self.b2b_month_var)
        self.b2b_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(date_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.b2b_year_var = ctk.StringVar(value=str(datetime.now().year))
        self.b2b_year_cb = ctk.CTkComboBox(date_frame,
                                           values=self.get_year_list(),
                                           variable=self.b2b_year_var)
        self.b2b_year_cb.grid(row=0, column=3, padx=5, pady=5)

        # Mark done / carry over
        action_frame = ctk.CTkFrame(self.b2b_scroll_container)
        action_frame.pack(pady=5, padx=5, fill="x")
        done_btn = ctk.CTkButton(action_frame, text="Mark Month as Done", 
                                 command=lambda: self.mark_month_done(self.b2b_month_var, self.b2b_year_var))
        done_btn.pack(side="right", padx=5)
        carry_btn = ctk.CTkButton(action_frame, text="Carry Over from Previous Month",
                                  command=lambda: self.carry_over_previous_month(self.b2b_month_var, self.b2b_year_var, "B2B"))
        carry_btn.pack(side="right", padx=5)

        input_frame = ctk.CTkFrame(self.b2b_scroll_container)
        input_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(input_frame, text="Business Name:").grid(row=0, column=0, padx=5, pady=5)
        self.b2b_name_entry = ctk.CTkEntry(input_frame)
        self.b2b_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Expense:").grid(row=1, column=0, padx=5, pady=5)
        self.b2b_expense_entry = ctk.CTkEntry(input_frame)
        self.b2b_expense_entry.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Profit:").grid(row=2, column=0, padx=5, pady=5)
        self.b2b_profit_entry = ctk.CTkEntry(input_frame)
        self.b2b_profit_entry.grid(row=2, column=1, padx=5, pady=5)

        add_b2b_btn = ctk.CTkButton(input_frame, text="Add/Update B2B", command=self.add_b2b_record)
        add_b2b_btn.grid(row=3, column=0, columnspan=2, pady=10)

        self.b2b_report_text = ctk.CTkTextbox(self.b2b_scroll_container, height=300, width=600, corner_radius=10)
        self.b2b_report_text.pack(pady=5, padx=5)

        show_data_btn = ctk.CTkButton(self.b2b_scroll_container, text="Show B2B Data (Current Month)", command=self.show_b2b_data)
        show_data_btn.pack(pady=5)

        # B2B Table. We keep columns=(business_name, expense, profit) in the code
        # but we will hide 'expense' and 'profit' so only 'business_name' appears.
        b2b_table_frame = ctk.CTkFrame(self.b2b_scroll_container)
        b2b_table_frame.pack(pady=5, padx=5, fill="both", expand=True)

        columns = ("business_name","expense","profit")
        self.b2b_tree = ttk.Treeview(b2b_table_frame, columns=columns, show="headings", height=8)
        self.b2b_tree.heading("business_name", text="Business Name")
        self.b2b_tree.column("business_name", width=200)
        self.b2b_tree.heading("expense", text="Hidden Expense Column")
        self.b2b_tree.column("expense", width=100)
        self.b2b_tree.heading("profit", text="Hidden Profit Column")
        self.b2b_tree.column("profit", width=100)
        self.b2b_tree.pack(side="left", fill="both", expand=True)

        # Hide expense & profit from display by restricting to "business_name" only
        self.b2b_tree["displaycolumns"] = ("business_name",)

        self.b2b_scrollbar = ttk.Scrollbar(b2b_table_frame, orient="vertical", command=self.b2b_tree.yview)
        self.b2b_tree.configure(yscrollcommand=self.b2b_scrollbar.set)
        self.b2b_scrollbar.pack(side="right", fill="y")

        # Edit / Delete B2B row
        b2b_button_frame = ctk.CTkFrame(self.b2b_scroll_container)
        b2b_button_frame.pack(pady=5)
        edit_b2b_btn = ctk.CTkButton(b2b_button_frame, text="Edit Selected Business", command=self.edit_selected_b2b)
        edit_b2b_btn.pack(side="left", padx=5)
        del_b2b_btn = ctk.CTkButton(b2b_button_frame, text="Delete Selected Business", command=self.delete_selected_b2b)
        del_b2b_btn.pack(side="left", padx=5)
        refresh_b2b_btn = ctk.CTkButton(b2b_button_frame, text="Refresh B2B Table", command=self.refresh_b2b_table)
        refresh_b2b_btn.pack(side="left", padx=5)

        # Call refresh right away
        self.refresh_b2b_table()

    def add_b2b_record(self):
        month = self.b2b_month_var.get()
        year = self.b2b_year_var.get()

        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot add/update B2B.")
            return

        name = self.b2b_name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Business Name cannot be empty.")
            return
        try:
            expense = float(self.b2b_expense_entry.get().strip())
        except ValueError:
            expense = 0.0
        try:
            profit = float(self.b2b_profit_entry.get().strip())
        except ValueError:
            profit = 0.0

        fieldnames = ["month", "year", "business_name", "expense", "profit"]
        existing = read_csv_dicts(B2B_CSV)

        found = False
        for row in existing:
            if (row["month"] == month and row["year"] == year and row["business_name"] == name):
                row["expense"] = str(expense)
                row["profit"] = str(profit)
                found = True
                break
        if not found:
            new_row = {
                "month": month,
                "year": year,
                "business_name": name,
                "expense": str(expense),
                "profit": str(profit)
            }
            existing.append(new_row)

        overwrite_csv_dicts(B2B_CSV, fieldnames, existing)
        messagebox.showinfo("Success", f"B2B record for '{name}' updated.")
        self.show_b2b_data()
        self.refresh_b2b_table()

    def show_b2b_data(self):
        month = self.b2b_month_var.get()
        year = self.b2b_year_var.get()
        data = read_csv_dicts(B2B_CSV)
        self.b2b_report_text.delete("0.0", "end")

        lines = [f"--- B2B Data for {month}/{year} ---"]
        found_any = False
        for row in data:
            if row["month"] == month and row["year"] == year:
                found_any = True
                lines.append(
                    f"Name: {row['business_name']}, "
                    f"Expense: £{row['expense']}, "
                    f"Profit: £{row['profit']}"
                )
        if not found_any:
            lines.append("No B2B data for this month/year.")

        self.b2b_report_text.insert("0.0", "\n".join(lines) + "\n")

    def refresh_b2b_table(self):
        """Refresh the TreeView in B2B tab."""
        month = self.b2b_month_var.get()
        year = self.b2b_year_var.get()
        for row in self.b2b_tree.get_children():
            self.b2b_tree.delete(row)

        data = read_csv_dicts(B2B_CSV)
        for r in data:
            if r["month"] == month and r["year"] == year:
                vals = (r["business_name"], r["expense"], r["profit"])
                self.b2b_tree.insert("", tk.END, values=vals)

    def edit_selected_b2b(self):
        """Load selected business into the input fields for editing."""
        month = self.b2b_month_var.get()
        year = self.b2b_year_var.get()
        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot edit.")
            return

        selection = self.b2b_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No business selected in the table.")
            return
        vals = self.b2b_tree.item(selection[0], "values")
        if not vals or len(vals) < 1:
            return
        business_name = vals[0]
        expense_str = vals[1]
        profit_str = vals[2]

        self.b2b_name_entry.delete(0, tk.END)
        self.b2b_name_entry.insert(0, business_name)
        self.b2b_expense_entry.delete(0, tk.END)
        self.b2b_expense_entry.insert(0, expense_str)
        self.b2b_profit_entry.delete(0, tk.END)
        self.b2b_profit_entry.insert(0, profit_str)

        messagebox.showinfo("Edit B2B", f"Loaded '{business_name}' for editing. Change the fields above and click 'Add/Update B2B'.")

    def delete_selected_b2b(self):
        """Delete the selected business from the CSV for the current month/year."""
        month = self.b2b_month_var.get()
        year = self.b2b_year_var.get()
        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot delete.")
            return

        selection = self.b2b_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No business selected in the table.")
            return
        vals = self.b2b_tree.item(selection[0], "values")
        if not vals or len(vals) < 1:
            return
        business_name = vals[0]

        data = read_csv_dicts(B2B_CSV)
        new_data = []
        deleted_count = 0
        for row in data:
            if (row["month"] == month and row["year"] == year and 
                row["business_name"] == business_name):
                deleted_count += 1
            else:
                new_data.append(row)

        if deleted_count > 0:
            fieldnames = ["month","year","business_name","expense","profit"]
            overwrite_csv_dicts(B2B_CSV, fieldnames, new_data)
            messagebox.showinfo("Success", f"Business '{business_name}' deleted for {month}/{year}.")
            self.refresh_b2b_table()
            self.show_b2b_data()
        else:
            messagebox.showinfo("Info", f"No matching business '{business_name}' found for this month/year.")


    # -------------------------------------------------------------------------
    #                          TAB: Costs
    # -------------------------------------------------------------------------
    def init_costs_tab(self):
        self.costs_scroll_container = ctk.CTkScrollableFrame(self.tab_costs, label_text="(Scrollable Area)")
        self.costs_scroll_container.pack(fill="both", expand=True)

        date_frame = ctk.CTkFrame(self.costs_scroll_container)
        date_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(date_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.costs_month_var = ctk.StringVar(value=str(datetime.now().month))
        self.costs_month_cb = ctk.CTkComboBox(date_frame,
                                              values=self.get_month_list(),
                                              variable=self.costs_month_var,
                                              command=self.refresh_costs_table)
        self.costs_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(date_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.costs_year_var = ctk.StringVar(value=str(datetime.now().year))
        self.costs_year_cb = ctk.CTkComboBox(date_frame,
                                             values=self.get_year_list(),
                                             variable=self.costs_year_var,
                                             command=self.refresh_costs_table)
        self.costs_year_cb.grid(row=0, column=3, padx=5, pady=5)

        action_frame = ctk.CTkFrame(self.costs_scroll_container)
        action_frame.pack(pady=5, padx=5, fill="x")

        done_btn = ctk.CTkButton(action_frame, text="Mark Month as Done", 
                                 command=lambda: self.mark_month_done(self.costs_month_var, self.costs_year_var))
        done_btn.pack(side="right", padx=5)

        carry_btn = ctk.CTkButton(action_frame, text="Carry Over from Previous Month",
                                  command=lambda: self.carry_over_previous_month(self.costs_month_var, self.costs_year_var, "Costs"))
        carry_btn.pack(side="right", padx=5)

        input_frame = ctk.CTkFrame(self.costs_scroll_container)
        input_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(input_frame, text="Cost Name:").grid(row=0, column=0, padx=5, pady=5)
        self.cost_name_entry = ctk.CTkEntry(input_frame)
        self.cost_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Cost Value:").grid(row=1, column=0, padx=5, pady=5)
        self.cost_value_entry = ctk.CTkEntry(input_frame)
        self.cost_value_entry.grid(row=1, column=1, padx=5, pady=5)

        add_cost_btn = ctk.CTkButton(input_frame, text="Add/Update Cost", command=self.add_cost_record)
        add_cost_btn.grid(row=2, column=0, columnspan=2, pady=10)

        table_frame = ctk.CTkFrame(self.costs_scroll_container)
        table_frame.pack(pady=5, padx=5, fill="both", expand=True)

        columns = ("cost_name", "cost_value")
        self.costs_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)  # bigger height
        self.costs_tree.heading("cost_name", text="Cost Name")
        self.costs_tree.heading("cost_value", text="Cost Value")
        self.costs_tree.column("cost_name", width=300)
        self.costs_tree.column("cost_value", width=150)
        self.costs_tree.pack(fill="both", expand=True)

        # Add Edit & Delete buttons for selected cost
        button_frame = ctk.CTkFrame(self.costs_scroll_container)
        button_frame.pack(pady=5)

        edit_btn = ctk.CTkButton(button_frame, text="Edit Selected Cost", command=self.edit_selected_cost)
        edit_btn.pack(side="left", padx=5)

        del_btn = ctk.CTkButton(button_frame, text="Delete Selected Cost", command=self.delete_selected_cost)
        del_btn.pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(self.costs_scroll_container, text="Refresh Costs Table", command=self.refresh_costs_table)
        refresh_btn.pack(pady=5)

        self.refresh_costs_table()

    def add_cost_record(self):
        month = self.costs_month_var.get()
        year = self.costs_year_var.get()

        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot add/update costs.")
            return

        cost_name = self.cost_name_entry.get().strip()
        if not cost_name:
            messagebox.showerror("Error", "Cost Name cannot be empty.")
            return
        try:
            cost_value = float(self.cost_value_entry.get().strip())
        except ValueError:
            cost_value = 0.0

        fieldnames = ["month", "year", "cost_name", "cost_value"]
        existing = read_csv_dicts(COSTS_CSV)

        found = False
        for row in existing:
            if (row["month"] == month and row["year"] == year and row["cost_name"] == cost_name):
                row["cost_value"] = str(cost_value)
                found = True
                break
        if not found:
            new_row = {
                "month": month,
                "year": year,
                "cost_name": cost_name,
                "cost_value": str(cost_value)
            }
            existing.append(new_row)

        overwrite_csv_dicts(COSTS_CSV, fieldnames, existing)
        messagebox.showinfo("Success", f"Cost '{cost_name}' updated for {month}/{year}.")
        self.refresh_costs_table()

    def refresh_costs_table(self, *args):
        month = self.costs_month_var.get()
        year = self.costs_year_var.get()
        data = read_csv_dicts(COSTS_CSV)
        for row in self.costs_tree.get_children():
            self.costs_tree.delete(row)

        for row in data:
            if row["month"] == month and row["year"] == year:
                cost_name = row["cost_name"]
                cost_value = row["cost_value"]
                self.costs_tree.insert("", tk.END, values=(cost_name, "£" + cost_value))

    def edit_selected_cost(self):
        """Load selected cost into the input fields for editing."""
        selection = self.costs_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No cost selected in the table.")
            return
        vals = self.costs_tree.item(selection[0], "values")
        if not vals or len(vals) < 2:
            return
        cost_name = vals[0]
        cost_value_str = vals[1].replace("£","")

        self.cost_name_entry.delete(0, tk.END)
        self.cost_name_entry.insert(0, cost_name)
        self.cost_value_entry.delete(0, tk.END)
        self.cost_value_entry.insert(0, cost_value_str)

        messagebox.showinfo("Edit Cost", f"Loaded cost '{cost_name}' for editing. Update fields and click 'Add/Update Cost'.")

    def delete_selected_cost(self):
        """Delete the selected cost from the CSV."""
        month = self.costs_month_var.get()
        year = self.costs_year_var.get()

        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot delete costs.")
            return

        selection = self.costs_tree.selection()
        if not selection:
            messagebox.showerror("Error", "No cost selected in the table.")
            return
        vals = self.costs_tree.item(selection[0], "values")
        if not vals or len(vals) < 1:
            return
        cost_name = vals[0]

        data = read_csv_dicts(COSTS_CSV)
        new_data = []
        removed = 0
        for row in data:
            if row["month"] == month and row["year"] == year and row["cost_name"] == cost_name:
                removed += 1
            else:
                new_data.append(row)

        if removed > 0:
            fieldnames = ["month","year","cost_name","cost_value"]
            overwrite_csv_dicts(COSTS_CSV, fieldnames, new_data)
            messagebox.showinfo("Success", f"Cost '{cost_name}' deleted for {month}/{year}.")
            self.refresh_costs_table()
        else:
            messagebox.showinfo("Info", f"No matching cost '{cost_name}' found for this month/year.")


    # -------------------------------------------------------------------------
    #                          TAB: Summary
    # -------------------------------------------------------------------------
    def init_summary_tab(self):
        self.summary_scroll_container = ctk.CTkScrollableFrame(self.tab_summary, label_text="(Scrollable Area)")
        self.summary_scroll_container.pack(fill="both", expand=True)

        summary_frame = ctk.CTkFrame(self.summary_scroll_container)
        summary_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(summary_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.summary_month_var = ctk.StringVar(value=str(datetime.now().month))
        self.summary_month_cb = ctk.CTkComboBox(summary_frame,
                                               values=["All"] + self.get_month_list(),
                                               variable=self.summary_month_var)
        self.summary_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(summary_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.summary_year_var = ctk.StringVar(value=str(datetime.now().year))
        self.summary_year_cb = ctk.CTkComboBox(summary_frame,
                                              values=self.get_year_list(),
                                              variable=self.summary_year_var)
        self.summary_year_cb.grid(row=0, column=3, padx=5, pady=5)

        gen_btn = ctk.CTkButton(summary_frame, text="Generate Summary", command=self.generate_monthly_summary)
        gen_btn.grid(row=0, column=4, padx=10, pady=5)

        self.summary_report_text = ctk.CTkTextbox(self.summary_scroll_container, height=200, corner_radius=10)
        self.summary_report_text.pack(pady=5, fill="x")

        self.fig, self.ax = plt.subplots(figsize=(7, 3), dpi=100)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.summary_scroll_container)
        self.chart_canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)

    def generate_monthly_summary(self):
        self.summary_report_text.delete("0.0", "end")
        chosen_month = self.summary_month_var.get()
        chosen_year = self.summary_year_var.get()

        eBay_skus = read_csv_dicts(EBAY_SKU_CSV)
        eBay_sales = read_csv_dicts(EBAY_SALES_CSV)
        Woo_skus = read_csv_dicts(WOO_SKU_CSV)
        Woo_sales = read_csv_dicts(WOO_SALES_CSV)
        b2b_data = read_csv_dicts(B2B_CSV)
        costs_data = read_csv_dicts(COSTS_CSV)

        monthly_aggregates = {}

        def add_monthly_values(y, m, profit_delta, expense_delta):
            key = (y, m)
            if key not in monthly_aggregates:
                monthly_aggregates[key] = {"profit": 0.0, "expense": 0.0}
            monthly_aggregates[key]["profit"] += profit_delta
            monthly_aggregates[key]["expense"] += expense_delta

        # eBay profit
        ebay_profit_map = {}
        for row in eBay_skus:
            try:
                p = float(row["profit"])
            except ValueError:
                p = 0.0
            ebay_profit_map[(row["year"], row["month"], row["sku"])] = p

        for s_row in eBay_sales:
            y = s_row["year"]
            m = s_row["month"]
            sku = s_row["sku"]
            try:
                units_sold = int(s_row["units_sold"])
            except ValueError:
                units_sold = 0
            key = (y, m, sku)
            if key in ebay_profit_map:
                total_line_profit = ebay_profit_map[key] * units_sold
                add_monthly_values(y, m, total_line_profit, 0.0)

        # Woo profit
        woo_profit_map = {}
        for row in Woo_skus:
            try:
                p = float(row["profit"])
            except ValueError:
                p = 0.0
            woo_profit_map[(row["year"], row["month"], row["sku"])] = p

        for s_row in Woo_sales:
            y = s_row["year"]
            m = s_row["month"]
            sku = s_row["sku"]
            try:
                units_sold = int(s_row["units_sold"])
            except ValueError:
                units_sold = 0
            key = (y, m, sku)
            if key in woo_profit_map:
                total_line_profit = woo_profit_map[key] * units_sold
                add_monthly_values(y, m, total_line_profit, 0.0)

        # B2B
        for row in b2b_data:
            y = row["year"]
            m = row["month"]
            try:
                e = float(row["expense"])
            except ValueError:
                e = 0.0
            try:
                p = float(row["profit"])
            except ValueError:
                p = 0.0
            add_monthly_values(y, m, p, e)


        lines = []
        if chosen_month != "All":
            key = (chosen_year, chosen_month)
            if key not in monthly_aggregates:
                lines.append(f"No data for {chosen_month}/{chosen_year}.")
                self.summary_report_text.insert("0.0", "\n".join(lines))
                self.update_line_chart(monthly_aggregates)
                return
            prof = monthly_aggregates[key]["profit"]
            exp = monthly_aggregates[key]["expense"]
            lines.append(f"--- Summary for {chosen_month}/{chosen_year} ---")
            lines.append(f"Total Profit:  £{prof:.2f}")
            lines.append(f"Total Expenses: £{exp:.2f}")
            lines.append(f"Realized Profit (Profit - Expenses): £{prof - exp:.2f}")
        else:
            lines.append(f"--- Summary for Year {chosen_year} (All Months) ---")
            grand_profit = 0.0
            grand_expense = 0.0
            for m in range(1, 13):
                key = (chosen_year, str(m))
                p = monthly_aggregates[key]["profit"] if key in monthly_aggregates else 0.0
                e = monthly_aggregates[key]["expense"] if key in monthly_aggregates else 0.0
                grand_profit += p
                grand_expense += e
            lines.append(f"Total Profit:  £{grand_profit:.2f}")
            lines.append(f"Total Expenses: £{grand_expense:.2f}")
            lines.append(f"Realized Profit: £{grand_profit - grand_expense:.2f}")

        self.summary_report_text.insert("0.0", "\n".join(lines) + "\n")
        self.update_line_chart(monthly_aggregates)

    def update_line_chart(self, monthly_aggregates):
        self.ax.clear()
        self.ax.set_title("Profit vs. Expenses per Month")
        self.ax.set_xlabel("Month")
        self.ax.set_ylabel("Amount")

        data_by_year = {}
        for (y, m), vals in monthly_aggregates.items():
            if y not in data_by_year:
                data_by_year[y] = {}
            data_by_year[y][m] = (vals["profit"], vals["expense"])

        colors = ["blue", "orange", "green", "red", "purple", "brown"]
        year_list = sorted(data_by_year.keys())
        for idx, yr in enumerate(year_list):
            months_sorted = sorted(int(mm) for mm in data_by_year[yr].keys())
            profit_values = []
            expense_values = []
            for mm in months_sorted:
                mm_str = str(mm)
                p, e = data_by_year[yr][mm_str]
                profit_values.append(p)
                expense_values.append(e)

            self.ax.plot(months_sorted, profit_values, 
                         label=f"Profit {yr}", 
                         color=colors[idx % len(colors)], 
                         linestyle="-")
            self.ax.plot(months_sorted, expense_values, 
                         label=f"Expenses {yr}", 
                         color=colors[idx % len(colors)], 
                         linestyle="--")

        self.ax.legend()
        self.ax.grid(True)
        self.chart_canvas.draw()


def packaging_cost(packaging_value):
    """
    Optionally parse the packaging Value if you want to treat "Box S" or "Box M" 
    as different cost. For now we just return 0. 
    If you want a real cost, define a dict below:
    """
    # Example:  
    packaging_map = {
        "Box S": 0.25,
        "Box M": 0.40,
        "Box L": 0.60,
        "Bubble Mailer": 0.20,
        "Poly Bag": 0.10,
        "Other/Multiple": 0.30
    }
    return packaging_map.get(packaging_value, 0.0)


# -------------------------------------------------------------------
#                        MAIN ENTRY POINT
# -------------------------------------------------------------------
if __name__ == "__main__":
    app = ProfitTrackerApp()
    app.mainloop()
