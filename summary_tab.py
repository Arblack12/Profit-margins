import tkinter as tk
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from data_utils import read_csv_dicts
from month_status import is_month_archived

EBAY_SKU_CSV = "ebay_sku.csv"
EBAY_SALES_CSV = "ebay_sales.csv"
WOO_SKU_CSV = "woo_sku.csv"
WOO_SALES_CSV = "woo_sales.csv"
B2B_CSV      = "b2b_data.csv"
COSTS_CSV    = "costs_data.csv"


class SummaryTab:
    def __init__(self, parent_frame, app):
        self.app = app
        self.parent = parent_frame

        self.summary_scroll_container = ctk.CTkScrollableFrame(self.parent, label_text="(Scrollable Area)")
        self.summary_scroll_container.pack(fill="both", expand=True)

        # -----------------------------------------------------------------
        # 1) Existing "Month/Year" selection for old "Generate Summary"
        # -----------------------------------------------------------------
        summary_frame = ctk.CTkFrame(self.summary_scroll_container)
        summary_frame.pack(pady=5, padx=5, fill="x")

        self.summary_month_var = tk.StringVar(value="All")  # default "All"
        self.summary_year_var = tk.StringVar(value="2025")  # example

        ctk.CTkLabel(summary_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.summary_month_cb = ctk.CTkComboBox(
            summary_frame,
            values=["All"] + [str(i) for i in range(1,13)],
            variable=self.summary_month_var
        )
        self.summary_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(summary_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.summary_year_cb = ctk.CTkComboBox(
            summary_frame,
            values=[str(y) for y in range(2020, 2030)],
            variable=self.summary_year_var
        )
        self.summary_year_cb.grid(row=0, column=3, padx=5, pady=5)

        gen_btn = ctk.CTkButton(summary_frame, text="Generate Summary", command=self.generate_monthly_summary)
        gen_btn.grid(row=0, column=4, padx=10, pady=5)

        # Text box for the old summary
        self.summary_report_text = ctk.CTkTextbox(self.summary_scroll_container, height=250, corner_radius=10)
        self.summary_report_text.pack(pady=5, fill="x")

        # -----------------------------------------------------------------
        # 2) New "From/To Month/Year" selection for a multi-month line chart
        # -----------------------------------------------------------------
        range_frame = ctk.CTkFrame(self.summary_scroll_container)
        range_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(range_frame, text="From Month:").grid(row=0, column=0, padx=5, pady=5)
        self.from_month_var = tk.StringVar(value="9")  # e.g. 9 for September
        self.from_month_cb = ctk.CTkComboBox(
            range_frame,
            values=[str(i) for i in range(1,13)],
            variable=self.from_month_var
        )
        self.from_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(range_frame, text="From Year:").grid(row=0, column=2, padx=5, pady=5)
        self.from_year_var = tk.StringVar(value="2024")
        self.from_year_cb = ctk.CTkComboBox(
            range_frame,
            values=[str(y) for y in range(2020, 2030)],
            variable=self.from_year_var
        )
        self.from_year_cb.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(range_frame, text="To Month:").grid(row=0, column=4, padx=5, pady=5)
        self.to_month_var = tk.StringVar(value="2")  # e.g. 2 for February
        self.to_month_cb = ctk.CTkComboBox(
            range_frame,
            values=[str(i) for i in range(1,13)],
            variable=self.to_month_var
        )
        self.to_month_cb.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkLabel(range_frame, text="To Year:").grid(row=0, column=6, padx=5, pady=5)
        self.to_year_var = tk.StringVar(value="2026")
        self.to_year_cb = ctk.CTkComboBox(
            range_frame,
            values=[str(y) for y in range(2020, 2030)],
            variable=self.to_year_var
        )
        self.to_year_cb.grid(row=0, column=7, padx=5, pady=5)

        line_btn = ctk.CTkButton(range_frame, text="Generate Line Chart", command=self.generate_line_chart)
        line_btn.grid(row=0, column=8, padx=10, pady=5)

        # -----------------------------------------------------------------
        # Matplotlib Figure for charts
        # -----------------------------------------------------------------
        self.fig = plt.Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)  # single subplot for the line chart
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.summary_scroll_container)
        self.chart_canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)

    # ---------------------------------------------------------------------
    # Old summary method (kept intact)
    # ---------------------------------------------------------------------
    def generate_monthly_summary(self):
        self.summary_report_text.delete("0.0", "end")
        chosen_month = self.summary_month_var.get()
        chosen_year = self.summary_year_var.get()

        # 1) Build monthly aggregates for Profit & Expenses
        monthly_aggregates = {}  # dict of (year, month) -> { "profit": float, "expense": float }
        self._build_monthly_aggregates(monthly_aggregates)

        lines = []

        if chosen_month != "All":
            key = (chosen_year, chosen_month)
            if key not in monthly_aggregates:
                lines.append(f"No data for {chosen_month}/{chosen_year}.")
            else:
                prof = monthly_aggregates[key]["profit"]
                exp = monthly_aggregates[key]["expense"]
                lines.append(f"--- Summary for {chosen_month}/{chosen_year} ---")
                lines.append(f"Total Profit:  £{prof:.2f}")
                lines.append(f"Total Expenses: £{exp:.2f}")
                lines.append(f"Realized Profit (Profit - Expenses): £{prof - exp:.2f}")
        else:
            # Summarize entire year
            lines.append(f"--- Summary for Year {chosen_year} (All Months) ---")
            grand_profit = 0.0
            grand_expense = 0.0
            for m in range(1, 13):
                key = (chosen_year, str(m))
                if key in monthly_aggregates:
                    grand_profit += monthly_aggregates[key]["profit"]
                    grand_expense += monthly_aggregates[key]["expense"]
            lines.append(f"Total Profit:  £{grand_profit:.2f}")
            lines.append(f"Total Expenses: £{grand_expense:.2f}")
            lines.append(f"Realized Profit: £{grand_profit - grand_expense:.2f}")

        # Show in the text box
        self.summary_report_text.insert("0.0", "\n".join(lines) + "\n")

    # ---------------------------------------------------------------------
    # New method: generate a line chart from FROM (month/year) to TO (month/year)
    # ---------------------------------------------------------------------
    def generate_line_chart(self):
        # Build monthly aggregates for all available data
        monthly_aggregates = {}
        self._build_monthly_aggregates(monthly_aggregates)

        # parse from/to
        from_y = int(self.from_year_var.get())
        from_m = int(self.from_month_var.get())
        to_y   = int(self.to_year_var.get())
        to_m   = int(self.to_month_var.get())

        # create a list of (year, month) from from_y/from_m up to to_y/to_m
        # inclusive
        ym_list = []
        y, m = from_y, from_m
        while (y < to_y) or (y == to_y and m <= to_m):
            ym_list.append((y, m))
            # increment month
            m += 1
            if m > 12:
                m = 1
                y += 1

        # Build arrays for the line chart
        x_labels = []
        expenses_arr = []
        profits_arr = []

        for (yy, mm) in ym_list:
            str_yy = str(yy)
            str_mm = str(mm)
            if (str_yy, str_mm) in monthly_aggregates:
                e = monthly_aggregates[(str_yy, str_mm)]["expense"]
                p = monthly_aggregates[(str_yy, str_mm)]["profit"]
            else:
                e = 0.0
                p = 0.0

            expenses_arr.append(e)
            profits_arr.append(p)
            x_labels.append(f"{mm}/{yy}")  # e.g. "9/2024"

        # Clear the old plot
        self.ax.clear()

        # Plot lines
        self.ax.plot(x_labels, expenses_arr, marker='o', color='red', label='Expenses')
        self.ax.plot(x_labels, profits_arr, marker='o', color='green', label='Profit')
        self.ax.set_title("Monthly Expenses vs. Profit")
        self.ax.set_xlabel("Month/Year")
        self.ax.set_ylabel("GBP (£)")
        self.ax.legend()
        self.ax.grid(True)

        # Make x-labels more readable (rotate if needed)
        self.ax.set_xticklabels(x_labels, rotation=45, ha='right')

        # Redraw
        self.fig.tight_layout()
        self.chart_canvas.draw()

    # ---------------------------------------------------------------------
    # Helper to fill `monthly_aggregates` with profit & expense
    # ---------------------------------------------------------------------
    def _build_monthly_aggregates(self, monthly_aggregates):
        """
        Fills up the monthly_aggregates dict: 
          (year, month) -> {"profit": float, "expense": float}
        from eBay, Woo, B2B data, etc.
        """

        # eBay
        ebay_skus = read_csv_dicts(EBAY_SKU_CSV)
        ebay_sales = read_csv_dicts(EBAY_SALES_CSV)
        # Convert to (year,month,sku)->profit
        ebay_profit_map = {}
        for row in ebay_skus:
            try:
                p = float(row["profit"])
            except:
                p = 0.0
            ebay_profit_map[(row["year"], row["month"], row["sku"])] = p

        for s_row in ebay_sales:
            y, m, sku = s_row["year"], s_row["month"], s_row["sku"]
            try:
                units_sold = int(s_row["units_sold"])
            except:
                units_sold = 0
            key = (y,m,sku)
            if key in ebay_profit_map:
                total_line_profit = ebay_profit_map[key] * units_sold
                self._add_monthly_values(monthly_aggregates, y, m, profit_delta=total_line_profit, expense_delta=0.0)

        # Woo
        woo_skus = read_csv_dicts(WOO_SKU_CSV)
        woo_sales = read_csv_dicts(WOO_SALES_CSV)
        woo_profit_map = {}
        for row in woo_skus:
            try:
                p = float(row["profit"])
            except:
                p = 0.0
            woo_profit_map[(row["year"], row["month"], row["sku"])] = p

        for s_row in woo_sales:
            y, m, sku = s_row["year"], s_row["month"], s_row["sku"]
            try:
                units_sold = int(s_row["units_sold"])
            except:
                units_sold = 0
            key = (y,m,sku)
            if key in woo_profit_map:
                total_line_profit = woo_profit_map[key] * units_sold
                self._add_monthly_values(monthly_aggregates, y, m, profit_delta=total_line_profit, expense_delta=0.0)

        # B2B
        b2b_rows = read_csv_dicts(B2B_CSV)
        for row in b2b_rows:
            y, m = row["year"], row["month"]
            try:
                e = float(row["expense"])
            except:
                e = 0.0
            try:
                p = float(row["profit"])
            except:
                p = 0.0
            self._add_monthly_values(monthly_aggregates, y, m, profit_delta=p, expense_delta=e)

    def _add_monthly_values(self, monthly_aggregates, y, m, profit_delta, expense_delta):
        key = (y, m)
        if key not in monthly_aggregates:
            monthly_aggregates[key] = {"profit":0.0, "expense":0.0}
        monthly_aggregates[key]["profit"]  += profit_delta
        monthly_aggregates[key]["expense"] += expense_delta
