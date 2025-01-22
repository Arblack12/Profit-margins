import customtkinter as ctk
from data_utils import ensure_csv_headers
from month_status import ensure_month_status_csv

# CSV constants
EBAY_SKU_CSV = "ebay_sku.csv"
EBAY_SALES_CSV = "ebay_sales.csv"
WOO_SKU_CSV = "woo_sku.csv"
WOO_SALES_CSV = "woo_sales.csv"
B2B_CSV      = "b2b_data.csv"
COSTS_CSV    = "costs_data.csv"

# Import tab classes
from ebay_tab import EbayTab
from woo_tab import WooTab
from b2b_tab import B2BTab
from costs_tab import CostsTab
from summary_tab import SummaryTab

class ProfitTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Profit Tracker Application")
        self.geometry("1300x900")

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Ensure CSV headers
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
        ensure_csv_headers(EBAY_SALES_CSV, ["month", "year", "sku", "units_sold"])
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
        ensure_csv_headers(WOO_SALES_CSV, ["month", "year", "sku", "units_sold"])
        ensure_csv_headers(B2B_CSV, ["month", "year", "business_name", "expense", "profit"])
        ensure_csv_headers(COSTS_CSV, ["month", "year", "cost_name", "cost_value"])
        ensure_month_status_csv()

        # Create the Tab View
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True)

        # Create 5 tabs
        # We can pass the newly-created "tab" to each specialized tab class
        self.ebay_tab_frame     = self.tabview.add("eBay")
        self.woo_tab_frame      = self.tabview.add("WooCommerce")
        self.b2b_tab_frame      = self.tabview.add("B2B")
        self.costs_tab_frame    = self.tabview.add("Costs")
        self.summary_tab_frame  = self.tabview.add("Summary")

        # Instantiate each tab
        self.ebay_tab    = EbayTab(self.ebay_tab_frame, self)
        self.woo_tab     = WooTab(self.woo_tab_frame, self)
        self.b2b_tab     = B2BTab(self.b2b_tab_frame, self)
        self.costs_tab   = CostsTab(self.costs_tab_frame, self)
        self.summary_tab = SummaryTab(self.summary_tab_frame, self)


def main():
    app = ProfitTrackerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
