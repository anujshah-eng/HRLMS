import secrets 

@staticmethod
def generate_otp():
    """
    Generate a 6-digit OTP (One-Time Password).

    Returns:
        int: A randomly generated 6-digit OTP.
    """
    try:
        otp = secrets.randbelow(900000) + 100000
        if otp < 100000 or otp > 999999:
            raise RuntimeError("Generated OTP is out of the expected range.")
        return otp
    except Exception as e:
        raise RuntimeError(
            f"An error occurred while generating OTP: {str(e)}"
            ) from e
