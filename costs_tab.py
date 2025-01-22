import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime

# Local imports from your own modules:
from .data_utils import read_csv_dicts, overwrite_csv_dicts
from .month_status import is_month_archived

COSTS_CSV = "costs_data.csv"


class CostsTab:
    def __init__(self, parent_frame, app):
        """
        parent_frame: the frame (tab) we attach our widgets to
        app: reference to the main ProfitTrackerApp
        """
        self.app = app
        self.parent = parent_frame

        self.costs_scroll_container = ctk.CTkScrollableFrame(self.parent, label_text="(Scrollable Area)")
        self.costs_scroll_container.pack(fill="both", expand=True)

        # Month/Year selection
        date_frame = ctk.CTkFrame(self.costs_scroll_container)
        date_frame.pack(pady=5, padx=5, fill="x")

        ctk.CTkLabel(date_frame, text="Select Month:").grid(row=0, column=0, padx=5, pady=5)
        self.costs_month_var = tk.StringVar(value=str(datetime.now().month))
        self.costs_month_cb = ctk.CTkComboBox(
            date_frame,
            values=[str(i) for i in range(1,13)],
            variable=self.costs_month_var,
            command=self.refresh_costs_table
        )
        self.costs_month_cb.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(date_frame, text="Select Year:").grid(row=0, column=2, padx=5, pady=5)
        self.costs_year_var = tk.StringVar(value=str(datetime.now().year))
        self.costs_year_cb = ctk.CTkComboBox(
            date_frame,
            values=[str(y) for y in range(2020, datetime.now().year+3)],
            variable=self.costs_year_var,
            command=self.refresh_costs_table
        )
        self.costs_year_cb.grid(row=0, column=3, padx=5, pady=5)

        # Mark Done / Carry Over
        action_frame = ctk.CTkFrame(self.costs_scroll_container)
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

        # Input frame for cost addition
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

        # Table of costs
        table_frame = ctk.CTkFrame(self.costs_scroll_container)
        table_frame.pack(pady=5, padx=5, fill="both", expand=True)

        columns = ("cost_name", "cost_value")
        self.costs_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        self.costs_tree.heading("cost_name", text="Cost Name")
        self.costs_tree.heading("cost_value", text="Cost Value")
        self.costs_tree.column("cost_name", width=300)
        self.costs_tree.column("cost_value", width=150)
        self.costs_tree.pack(fill="both", expand=True)

        button_frame = ctk.CTkFrame(self.costs_scroll_container)
        button_frame.pack(pady=5)

        edit_btn = ctk.CTkButton(button_frame, text="Edit Selected Cost", command=self.edit_selected_cost)
        edit_btn.pack(side="left", padx=5)

        del_btn = ctk.CTkButton(button_frame, text="Delete Selected Cost", command=self.delete_selected_cost)
        del_btn.pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(
            self.costs_scroll_container,
            text="Refresh Costs Table",
            command=self.refresh_costs_table
        )
        refresh_btn.pack(pady=5)

        # Initial load
        self.refresh_costs_table()

    # --------------------------------------------------
    # Mark month done / Carry Over
    # --------------------------------------------------
    def _mark_month_done_callback(self):
        m = self.costs_month_var.get()
        y = self.costs_year_var.get()
        from .month_status import set_month_archived
        set_month_archived(y, m, archived=True)
        messagebox.showinfo("Month Archived", f"Marked {m}/{y} as DONE.")

    def _carry_over_callback(self):
        m = self.costs_month_var.get()
        y = self.costs_year_var.get()
        if is_month_archived(y, m):
            messagebox.showerror("Error", f"{m}/{y} is archived. Cannot carry over data.")
            return

        # Example if you want to carry over from previous month:
        from .month_status import get_previous_month_year
        from .data_utils import carry_over_data_for_tab

        carry_over_data_for_tab(
            COSTS_CSV,
            ["month","year","cost_name","cost_value"],
            y, m,
            key_fields=["cost_name"],
            read_csv_fn=read_csv_dicts,
            overwrite_csv_fn=overwrite_csv_dicts,
            get_previous_month_year_fn=get_previous_month_year
        )
        messagebox.showinfo("Success", f"Carried over cost data into {m}/{y}.")
        self.refresh_costs_table()

    # --------------------------------------------------
    # Add / Update Cost
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------
    def refresh_costs_table(self, *args):
        month = self.costs_month_var.get()
        year = self.costs_year_var.get()
        data = read_csv_dicts(COSTS_CSV)

        # clear old
        for row in self.costs_tree.get_children():
            self.costs_tree.delete(row)

        for row in data:
            if row["month"] == month and row["year"] == year:
                cost_name  = row["cost_name"]
                cost_value = row["cost_value"]
                self.costs_tree.insert("", tk.END, values=(cost_name, "£" + cost_value))

    def edit_selected_cost(self):
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

        messagebox.showinfo(
            "Edit Cost",
            f"Loaded cost '{cost_name}' for editing. Update fields and click 'Add/Update Cost'."
        )

    def delete_selected_cost(self):
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
