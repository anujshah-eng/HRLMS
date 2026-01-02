from enums.admin_enums import UserType

# Template definitions
TEMPLATES = {
    UserType.STUDENT: {
        "filename": "student_template.csv",
        "headers": ["Name", "Email", "Batch", "Department"],
        "sample_data": [
            ["John Doe", "john.doe@example.com", "Batch A", "MCA"],
            ["Jane Smith", "jane.smith@example.com", "Batch B", "MBA"]
        ]
    },
    UserType.TEACHER: {
        "filename": "teacher_template.csv",
        "headers": ["Honorific", "Name", "Email", "Department", "Designation"],
        "sample_data": [
            ["Dr.", "Sarah Johnson", "sarah.johnson@example.com", "MCA", "Professor"],
            ["Dr.", "Michael Brown", "michael.brown@example.com", "MBA", "Associate Professor"]
        ]
    }
}