import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import customtkinter as ctk
from datetime import datetime

# Local imports from your own modules:
from data_utils import (
    read_csv_dicts,
    overwrite_csv_dicts,
    ensure_csv_headers,
    parse_packaging_input,
    carry_over_data_for_tab
)
from month_status import is_month_archived

# CSV file references
WOO_SKU_CSV   = "woo_sku.csv"
WOO_SALES_CSV = "woo_sales.csv"
COSTS_CSV     = "costs_data.csv"


class WooTab:
    def __init__(self, parent_frame, app):
        """
        parent_frame: the frame (tab) we attach our widgets to
        app: reference to the main ProfitTrackerApp (so we can call shared methods)
        """
        self.app = app
        self.parent = parent_frame

        # 1) Main container
        self.woo_scroll_container = ctk.CTkScrollableFrame(self.parent, label_text="(Scroll Down If Needed)")
        self.woo_scroll_container.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.woo_scroll_container,
            text="All currency below is in £ (GBP).",
            font=("Arial", 14, "bold")
        ).pack(pady=5)

        # 2) Top Buttons: Mark Month Done + Carry Over
        btn_frame = ctk.CTkFrame(self.woo_scroll_container)
        btn_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(btn_frame, text="Click to show Category Table").pack(side="left", padx=5)
        show_cat_btn = ctk.CTkButton(btn_frame, text="Show Category Table", command=self.refresh_woo_category_table)
        show_cat_btn.pack(side="left", padx=5)

        done_btn = ctk.CTkButton(
            btn_frame,
            text="Mark Month as Done",
            command=self._mark_month_done_callback
        )
        done_btn.pack(side="right", padx=5)

        carry_btn = ctk.CTkButton(
            btn_frame,
            text="Carry Over from Previous Month",
            command=self._carry_over_callback
        )
        carry_btn.pack(side="right", padx=5)

        # 3) Month/Year selection
        date_frame = ctk.CTkFrame(self.woo_scroll_container)
        date_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(date_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.woo_month_var = tk.StringVar(value=str(datetime.now().month))
        self.woo_month_cb = ctk.CTkComboBox(
            date_frame,
            values=[str(i) for i in range(1,13)],
            variable=self.woo_month_var
        )
        self.woo_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(date_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.woo_year_var = tk.StringVar(value=str(datetime.now().year))
        self.woo_year_cb = ctk.CTkComboBox(
            date_frame,
            values=[str(y) for y in range(2020, datetime.now().year+3)],
            variable=self.woo_year_var
        )
        self.woo_year_cb.grid(row=0, column=3, padx=5, pady=5)

        # 4) SKU Input
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

        select_packaging_btn = ctk.CTkButton(
            input_frame,
            text="Select Packaging",
            command=self._select_packaging_costs_woo
        )
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

        # 5) MASS PASTE sales
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

        # 6) Treeview for SKUs
        bottom_frame = ctk.CTkFrame(self.woo_scroll_container)
        bottom_frame.pack(pady=5, padx=5, fill="both", expand=True)

        ctk.CTkLabel(bottom_frame, text="Filter by Category (Optional):").grid(row=0, column=0, padx=5, pady=5)
        self.woo_filter_var = tk.StringVar(value="All")
        self.woo_filter_cb = ctk.CTkComboBox(
            bottom_frame,
            values=["All"],
            variable=self.woo_filter_var,
            command=self.refresh_woo_sku_table
        )
        self.woo_filter_cb.grid(row=0, column=1, padx=5, pady=5)

        refresh_table_btn = ctk.CTkButton(
            bottom_frame, 
            text="Refresh SKU Table",
            command=self.refresh_woo_sku_table
        )
        refresh_table_btn.grid(row=0, column=2, padx=5, pady=5)

        edit_table_btn = ctk.CTkButton(
            bottom_frame,
            text="Edit Selected SKU",
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

        # 7) Category table
        cat_frame = ctk.CTkFrame(self.woo_scroll_container)
        cat_frame.pack(pady=5, padx=5, fill="both", expand=False)

        ctk.CTkLabel(
            cat_frame,
            text="Woo Categories (SKUs per Category) - Scroll If Not Visible:"
        ).grid(row=0, column=0, columnspan=4, padx=5, pady=5)

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

    # --------------------------------------------------
    # Callbacks for Mark Month Done / Carry Over
    # --------------------------------------------------
    def _mark_month_done_callback(self):
        m = self.woo_month_var.get()
        y = self.woo_year_var.get()
        # If your main app has mark_month_done, call that:
        # self.app.mark_month_done(self.woo_month_var, self.woo_year_var)
        # Or directly do:
        from .month_status import set_month_archived
        set_month_archived(y, m, archived=True)
        messagebox.showinfo("Month Archived", f"Marked {m}/{y} as DONE.")

    def _carry_over_callback(self):
        m = self.woo_month_var.get()
        y = self.woo_year_var.get()
        # If your main app has a method, you could do: self.app.carry_over_previous_month(...)
        # Or call carry_over_data_for_tab directly for each CSV you want.
        if is_month_archived(y, m):
            messagebox.showerror("Error", f"{m}/{y} is archived. Cannot carry over.")
            return

        # Example: carry over the WOO_SKU_CSV
        from .month_status import get_previous_month_year
        carry_over_data_for_tab(
            WOO_SKU_CSV,
            [
                "month","year","sku","category","sold_price_after_vat","sold_price_before_vat",
                "cost_of_item","packaging","transaction_fee","delivery","total_expenses",
                "profit_margin","profit"
            ],
            y, m,
            key_fields=["sku"],
            read_csv_fn=read_csv_dicts,
            overwrite_csv_fn=overwrite_csv_dicts,
            get_previous_month_year_fn=get_previous_month_year
        )
        # carry over B2B, costs, etc. if you like
        messagebox.showinfo("Carry Over Complete", f"Carried over data into {m}/{y}.")
        self.refresh_woo_sku_table()
        self.refresh_woo_category_table()

    # --------------------------------------------------
    # Packaging selection
    # --------------------------------------------------
    def _select_packaging_costs_woo(self):
        month = self.woo_month_var.get()
        year = self.woo_year_var.get()
        data = read_csv_dicts(COSTS_CSV)
        cost_names = []
        for row in data:
            if row["month"] == month and row["year"] == year:
                cost_names.append(row["cost_name"])
        cost_names = sorted(list(set(cost_names)))

        top = tk.Toplevel()
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

        tk.Button(top, text="Confirm", command=on_confirm).pack(pady=5)

    # --------------------------------------------------
    # Add / Update SKU
    # --------------------------------------------------
    def add_woo_sku(self):
        month = self.woo_month_var.get()
        year = self.woo_year_var.get()

        if is_month_archived(year, month):
            messagebox.showerror("Error", f"{month}/{year} is archived. Cannot add/update SKU.")
            return

        category = self.woo_category_entry.get().strip()
        sku = self.woo_sku_entry.get().strip()
        if not sku:
            messagebox.showerror("Error", "SKU cannot be empty.")
            return

        # parse float fields
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

        # read costs for this month/year to parse packaging
        cost_data = {}
        for row in read_csv_dicts(COSTS_CSV):
            if row["month"] == month and row["year"] == year:
                cost_data[row["cost_name"]] = float(row["cost_value"])

        packaging_sum = parse_packaging_input(packaging_str, cost_data)
        total_expenses = cost + trans_fee + packaging_sum + delivery
        profit = before_vat - total_expenses
        profit_margin = (profit / before_vat)*100 if before_vat != 0 else 0.0

        # display them
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
            if row["month"] == month and row["year"] == year and row["sku"] == sku:
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

    # --------------------------------------------------
    # MASS PASTE Sales
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Refresh UI
    # --------------------------------------------------
    def refresh_woo_sku_table(self, *args):
        for row in self.woo_tree.get_children():
            self.woo_tree.delete(row)

        chosen_month = self.woo_month_var.get()
        chosen_year  = self.woo_year_var.get()
        data = read_csv_dicts(WOO_SKU_CSV)

        # Build category set for this month/year
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
        chosen_year  = self.woo_year_var.get()
        data = read_csv_dicts(WOO_SKU_CSV)
        cat_map = {}
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
            self.woo_cat_tree.insert("", tk.END, values=(cat, sku_list))

    def edit_selected_woo_sku(self):
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
                # populate fields
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

    # --------------------------------------------------
    # Category-based Edit/Delete/Move
    # --------------------------------------------------
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
                self.add_woo_sku()  # calls the logic to update
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
