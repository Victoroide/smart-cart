import json
import io
from django.core.serializers.json import DjangoJSONEncoder

class JSONFormatter:
    def format_report(self, data, file_name, report_type, reports_dir):
        # Convert complex data types to JSON-serializable format
        serializable_data = self._make_serializable(data)
        
        # Add report metadata
        serializable_data['report_type'] = report_type
        serializable_data['file_name'] = file_name
        
        # Generate JSON content
        json_content = json.dumps(serializable_data, indent=4, cls=DjangoJSONEncoder)
        
        # Create file path
        file_path = f"{file_name}.json"
        
        # Create in-memory file
        content = io.BytesIO(json_content.encode('utf-8'))
        content.seek(0)
        
        return content, file_path
    
    def _make_serializable(self, data):
        if isinstance(data, dict):
            return {key: self._make_serializable(value) for key, value in data.items()}
        elif hasattr(data, 'all') and callable(data.all):
            return [self._make_serializable(item) for item in data.all()]
        elif hasattr(data, '__dict__'):
            if hasattr(data, 'id'):
                result = {'id': data.id}
                
                # Handle common model fields
                for field in ['name', 'email', 'created_at', 'updated_at', 'status', 'total_amount', 'currency']:
                    if hasattr(data, field):
                        result[field] = getattr(data, field)
                
                # Handle specific model relationships
                if hasattr(data, 'user') and data.user:
                    if hasattr(data.user, 'get_full_name'):
                        result['user_name'] = data.user.get_full_name() or data.user.email
                    result['user_id'] = data.user.id
                
                # Handle order items
                if hasattr(data, 'items') and hasattr(data.items, 'all'):
                    result['items'] = [self._make_serializable(item) for item in data.items.all()]
                
                return result
            return str(data)
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        else:
            return data