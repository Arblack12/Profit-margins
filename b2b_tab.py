import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime

from data_utils import read_csv_dicts, overwrite_csv_dicts
from month_status import is_month_archived

B2B_CSV = "b2b_data.csv"


class B2BTab:
    def __init__(self, parent_frame, app):
        self.app = app
        self.parent = parent_frame

        self.b2b_scroll_container = ctk.CTkScrollableFrame(self.parent, label_text="(Scrollable Area)")
        self.b2b_scroll_container.pack(fill="both", expand=True)

        date_frame = ctk.CTkFrame(self.b2b_scroll_container)
        date_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(date_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.b2b_month_var = tk.StringVar(value=str(datetime.now().month))
        self.b2b_month_cb = ctk.CTkComboBox(
            date_frame,
            values=[str(i) for i in range(1,13)],
            variable=self.b2b_month_var
        )
        self.b2b_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(date_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.b2b_year_var = tk.StringVar(value=str(datetime.now().year))
        self.b2b_year_cb = ctk.CTkComboBox(
            date_frame,
            values=[str(y) for y in range(2020, datetime.now().year+3)],
            variable=self.b2b_year_var
        )
        self.b2b_year_cb.grid(row=0, column=3, padx=5, pady=5)

        # Mark done / carry over
        action_frame = ctk.CTkFrame(self.b2b_scroll_container)
        action_frame.pack(pady=5, padx=5, fill="x")

        done_btn = ctk.CTkButton(
            action_frame,
            text="Mark Month as Done",
            command=self._mark_month_done_callback
        )
        done_btn.pack(side="right", padx=5)

        carry_btn = ctk.CTkButton(
            action_frame,
            text="Carry Over from Previous Month",
            command=self._carry_over_callback
        )
        carry_btn.pack(side="right", padx=5)

        # Input
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

        # Two tables: Profit / Expense
        table_frame = ctk.CTkFrame(self.b2b_scroll_container)
        table_frame.pack(pady=5, padx=5, fill="both", expand=True)

        profit_frame = ctk.CTkFrame(table_frame)
        profit_frame.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkLabel(profit_frame, text="B2B (Profit side)").pack()
        self.profit_tree = ttk.Treeview(profit_frame, columns=("business_name","profit"), show="headings", height=8)
        self.profit_tree.heading("business_name", text="Business Name")
        self.profit_tree.heading("profit", text="Profit")
        self.profit_tree.column("business_name", width=150)
        self.profit_tree.column("profit", width=80)
        self.profit_tree.pack(fill="both", expand=True)

        expense_frame = ctk.CTkFrame(table_frame)
        expense_frame.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkLabel(expense_frame, text="B2B (Expense side)").pack()
        self.expense_tree = ttk.Treeview(expense_frame, columns=("business_name","expense"), show="headings", height=8)
        self.expense_tree.heading("business_name", text="Business Name")
        self.expense_tree.heading("expense", text="Expense")
        self.expense_tree.column("business_name", width=150)
        self.expense_tree.column("expense", width=80)
        self.expense_tree.pack(fill="both", expand=True)

        refresh_b2b_btn = ctk.CTkButton(
            self.b2b_scroll_container,
            text="Refresh B2B Tables",
            command=self.refresh_b2b_tables
        )
        refresh_b2b_btn.pack(pady=5)

    def _mark_month_done_callback(self):
        m = self.b2b_month_var.get()
        y = self.b2b_year_var.get()
        from .month_status import set_month_archived
        set_month_archived(y, m, archived=True)
        messagebox.showinfo("Month Archived", f"Marked {m}/{y} as DONE.")

    def _carry_over_callback(self):
        m = self.b2b_month_var.get()
        y = self.b2b_year_var.get()
        if is_month_archived(y, m):
            messagebox.showerror("Error", f"{m}/{y} is archived. Cannot carry over.")
            return

        from .month_status import get_previous_month_year
        from .data_utils import carry_over_data_for_tab
        carry_over_data_for_tab(
            B2B_CSV,
            ["month","year","business_name","expense","profit"],
            y, m,
            key_fields=["business_name"],
            read_csv_fn=read_csv_dicts,
            overwrite_csv_fn=overwrite_csv_dicts,
            get_previous_month_year_fn=get_previous_month_year
        )
        messagebox.showinfo("Carry Over Complete", f"Carried over B2B data into {m}/{y}.")
        self.refresh_b2b_tables()

    def add_b2b_record(self):
        month = self.b2b_month_var.get()
        year  = self.b2b_year_var.get()

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
            expense=0.0
        try:
            profit = float(self.b2b_profit_entry.get().strip())
        except ValueError:
            profit=0.0

        fieldnames=["month","year","business_name","expense","profit"]
        existing=read_csv_dicts(B2B_CSV)

        found=False
        for row in existing:
            if (row["month"]==month and row["year"]==year and row["business_name"]==name):
                row["expense"] = str(expense)
                row["profit"]  = str(profit)
                found=True
                break
        if not found:
            new_row={
                "month": month,
                "year": year,
                "business_name": name,
                "expense": str(expense),
                "profit": str(profit)
            }
            existing.append(new_row)

        overwrite_csv_dicts(B2B_CSV, fieldnames, existing)
        messagebox.showinfo("Success", f"B2B record for '{name}' updated.")
        self.refresh_b2b_tables()

    def refresh_b2b_tables(self):
        # clear
        for row in self.profit_tree.get_children():
            self.profit_tree.delete(row)
        for row in self.expense_tree.get_children():
            self.expense_tree.delete(row)

        month=self.b2b_month_var.get()
        year=self.b2b_year_var.get()
        data=read_csv_dicts(B2B_CSV)
        for row in data:
            if row["month"]==month and row["year"]==year:
                bname=row["business_name"]
                exp  =row["expense"]
                prof =row["profit"]
                self.profit_tree.insert("", tk.END, values=(bname, "£"+prof))
                self.expense_tree.insert("", tk.END, values=(bname, "£"+exp))
