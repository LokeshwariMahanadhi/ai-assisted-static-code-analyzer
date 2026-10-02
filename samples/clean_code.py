"""
Sample 1: High Quality, Clean, Production-Ready Python Code.
Demonstrates type hints, docstrings, proper error handling, and clean structure.
"""
from typing import List, Optional


class OrderProcessor:
    """Processes customer orders and calculates final invoice values."""

    def __init__(self, discount_rate: float = 0.05) -> None:
        self.discount_rate = discount_rate

    def calculate_total(self, prices: List[float], tax_rate: float = 0.1) -> float:
        """
        Calculate total invoice cost with tax and discount applied.
        
        Args:
            prices: List of item prices in USD.
            tax_rate: Percentage tax to apply.
            
        Returns:
            Final calculated invoice amount.
        """
        if not prices:
            return 0.0

        subtotal = sum(prices)
        discount = subtotal * self.discount_rate
        taxable_amount = subtotal - discount
        total = taxable_amount * (1.0 + tax_rate)
        return round(total, 2)


def process_orders(order_lists: List[List[float]]) -> List[float]:
    """Helper function to batch process order lists."""
    processor = OrderProcessor()
    results: List[float] = []
    for order in order_lists:
        total = processor.calculate_total(order)
        results.append(total)
    return results
