from decimal import Decimal, ROUND_HALF_UP

def normalize_decimal(value, precision=8):
    """
    Enforce exact decimal precision using quantization
    
    Args:
        value: The value to normalize (int, float, str, or Decimal)
        precision: Number of decimal places to maintain (default: 8)
        
    Returns:
        Decimal value with exactly 'precision' decimal places
    """
    if not isinstance(value, Decimal):
        # Convert all values to Decimal first (handling float precision issues)
        try:
            value = Decimal(str(value))
        except:
            raise TypeError(f"Cannot convert {value} to Decimal")
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP) 