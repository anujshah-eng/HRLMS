"""
This module contains data transfer object (DTO) classes using Pydantic for managing
user information and response data. These classes facilitate communication between
different layers of the application, ensuring consistency and validation of data being
passed around.

Classes:
    ResponseDto: Represents a general response structure with an optional data payload.
    VerifyUserResponseDto: Represents the response structure for user verification, including
    information about user registration.
    UserManagementResponseDto: Represents a response structure for user management operations.
"""
from pydantic import BaseModel

class ResponseDto(BaseModel):
    """
    Data Transfer Object representing a general response structure with an optional data payload.

    Attributes:
        Data (object, optional): An optional data payload. Defaults to None.
        Success (bool): Indicates whether the operation was successful.
        Message (str): A message describing the operation result.
        Status (int): The status code of the operation.
    """
    Data: object = None
    Success: bool
    Message: str
    Status: int
