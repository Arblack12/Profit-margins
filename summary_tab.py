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

        # Month/Year selection
        summary_frame = ctk.CTkFrame(self.summary_scroll_container)
        summary_frame.pack(pady=5, padx=5, fill="x")

        self.summary_month_var = tk.StringVar(value="All")  # default "All"
        self.summary_year_var = tk.StringVar(value="2025")  # example

        # You might populate these combos from your app
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

        # Report text
        self.summary_report_text = ctk.CTkTextbox(self.summary_scroll_container, height=250, corner_radius=10)
        self.summary_report_text.pack(pady=5, fill="x")

        # Create the figure with 3 subplots
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(nrows=3, ncols=1, figsize=(6, 8), dpi=100)
        self.fig.tight_layout(pad=3.0)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.summary_scroll_container)
        self.chart_canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)

    def generate_monthly_summary(self):
        self.summary_report_text.delete("0.0", "end")
        chosen_month = self.summary_month_var.get()
        chosen_year = self.summary_year_var.get()

        # 1) Build monthly aggregates for Profit & Expenses
        monthly_aggregates = {}  # dict of (year, month) -> { "profit": float, "expense": float }

        # eBay data
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

        # accumulate
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

        # Woo data (same pattern)
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

        # Summaries
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

        # Build 3 separate subplots:
        self._update_summary_charts(monthly_aggregates, chosen_year)

    def _add_monthly_values(self, monthly_aggregates, y, m, profit_delta, expense_delta):
        key = (y,m)
        if key not in monthly_aggregates:
            monthly_aggregates[key] = {"profit":0.0, "expense":0.0}
        monthly_aggregates[key]["profit"] += profit_delta
        monthly_aggregates[key]["expense"] += expense_delta

    def _update_summary_charts(self, monthly_aggregates, chosen_year):
        # Clear the subplots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # We only plot months 1..12 for the chosen_year
        months = range(1,13)
        expenses = []
        profits = []

        total_profit_for_year = 0.0

        for m in months:
            key = (chosen_year, str(m))
            if key in monthly_aggregates:
                e = monthly_aggregates[key]["expense"]
                p = monthly_aggregates[key]["profit"]
            else:
                e = 0.0
                p = 0.0

            expenses.append(e)
            profits.append(p)
            total_profit_for_year += (p - e)

        # 1) AX1: Expenses
        self.ax1.set_title("Monthly Expenses")
        self.ax1.bar(months, expenses, color="orange")
        self.ax1.set_xlabel("Month")
        self.ax1.set_ylabel("Expenses (£)")
        self.ax1.grid(True)

        # 2) AX2: Profit
        self.ax2.set_title("Monthly Profit")
        self.ax2.bar(months, profits, color="green")
        self.ax2.set_xlabel("Month")
        self.ax2.set_ylabel("Profit (£)")
        self.ax2.grid(True)

        # 3) AX3: Total Profit for the year
        # We can just do a single bar:
        self.ax3.set_title("Total Profit for the Year")
        self.ax3.bar(["Year Total"], [total_profit_for_year], color="blue")
        self.ax3.set_ylabel("£")
        self.ax3.grid(True, axis="y")

        # Draw
        self.fig.tight_layout()
        self.chart_canvas.draw()
