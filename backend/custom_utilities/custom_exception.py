class CustomException(Exception):
    """
    Custom exception class for handling specific errors.

    Attributes:
        message (str): The error message to be displayed.
        status_code (int): HTTP status code for the error.
        data (dict): Optional extra data to include in the response.
    """
    def __init__(self, message, status_code, data=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data or {}

    def __str__(self):
        return self.message
