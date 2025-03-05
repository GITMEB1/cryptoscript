from decimal import Decimal, ROUND_HALF_UP

def normalize_decimal(value):
    """Convert a value to a Decimal with 8 decimal places."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Use quantize with ROUND_HALF_UP for proper rounding
    result = value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    return result

# Test cases
test_values = [
    '0.123456785',  # Should round up to 0.12345679
    '0.123456784',  # Should round down to 0.12345678
    '0.12345675',   # Should round up to 0.12345675
    '0.12345674',   # Should round down to 0.12345674
    '1.23456789',   # Should round to 1.23456789
    '0.00000001',   # Smallest representable value
    '0.000000001'   # Should round to 0.00000000
]

print("Testing normalize_decimal function with ROUND_HALF_UP:")
print("-" * 50)

for value in test_values:
    result = normalize_decimal(value)
    print(f"Input: {value} -> Result: {result}")

print("-" * 50)
print("All tests completed.") 