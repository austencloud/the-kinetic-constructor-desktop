"""
Test Viewport Calculation

This test simulates the viewport calculation to identify the issue.
"""

import sys
import math

# Add current directory to path
sys.path.insert(0, '.')

print("🧮 VIEWPORT CALCULATION TEST")

# Simulate the values from the log
scroll_value = 1680
viewport_height = 976
card_height = 340  # Typical card height
spacing = 20  # Typical spacing
columns = 4  # Typical column count
total_items = 372

print(f"Input values:")
print(f"  scroll_value: {scroll_value}")
print(f"  viewport_height: {viewport_height}")
print(f"  card_height: {card_height}")
print(f"  spacing: {spacing}")
print(f"  columns: {columns}")
print(f"  total_items: {total_items}")

# Calculate visible row range (same logic as in the code)
row_height = card_height + spacing
start_row = max(0, scroll_value // row_height)
end_row = min(
    math.ceil(total_items / columns),
    (scroll_value + viewport_height) // row_height + 2,  # Small buffer
)

print(f"\nCalculations:")
print(f"  row_height: {row_height}")
print(f"  start_row: {start_row}")
print(f"  end_row: {end_row}")
print(f"  total_rows: {math.ceil(total_items / columns)}")

# Convert to item indices
new_start = int(start_row * columns)
new_end = min(total_items, int(end_row * columns))

print(f"\nResult:")
print(f"  new_start: {new_start}")
print(f"  new_end: {new_end}")

# Test with different scroll values
print(f"\nTesting different scroll values:")
for test_scroll in [0, 360, 720, 1080, 1440, 1800]:
    test_start_row = max(0, test_scroll // row_height)
    test_end_row = min(
        math.ceil(total_items / columns),
        (test_scroll + viewport_height) // row_height + 2,
    )
    test_new_start = int(test_start_row * columns)
    test_new_end = min(total_items, int(test_end_row * columns))
    print(f"  scroll={test_scroll} -> range {test_new_start}-{test_new_end}")

print("\n🧮 VIEWPORT CALCULATION TEST COMPLETE")
