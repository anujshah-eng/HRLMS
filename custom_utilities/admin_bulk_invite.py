from io import StringIO
import csv
from typing import List
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from enums.admin_enums import UserType
from config.bulk_invite_download_template import TEMPLATES

def generate_csv(headers: List[str], sample_data: List[List[str]] = None, include_sample: bool = False) -> str:
    """Generate CSV content with headers and optional sample data."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(headers)
    
    # Write sample data if requested
    if include_sample and sample_data:
        writer.writerows(sample_data)
    
    return output.getvalue()

async def download_template(
    user_type: UserType,
    include_sample: bool = False
):
    """
    Download CSV template for bulk user import.
    
    Args:
        user_type: Type of user (student or teacher)
        include_sample: Include sample data rows (default: False)
    
    Returns:
        CSV file with appropriate headers
    """
    try:
        template = TEMPLATES[user_type]
        
        # Generate CSV content
        csv_content = generate_csv(
            headers=template["headers"],
            sample_data=template["sample_data"] if include_sample else None,
            include_sample=include_sample
        )
        
        # Create streaming response
        response = StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{template["filename"]}"',
                "Cache-Control": "no-cache"
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating template: {str(e)}") from e
