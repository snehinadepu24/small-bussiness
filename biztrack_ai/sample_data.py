"""
Sample Data Generator for BizTrack AI
Delegates to seed.py for full MVP demo data.
"""

from seed import clear_all_data, seed_all


def generate_sample_data(force=False):
    """Generate all MVP demo data (users, products, sales, expenses, logs)."""
    return seed_all(force=force)
