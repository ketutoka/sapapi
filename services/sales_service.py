from models import db, SalesData
from datetime import datetime
from sqlalchemy import and_

class SalesService:
    """Service class untuk menangani logic bisnis sales data"""
    
    def __init__(self):
        pass
    
    def validate_sales_data(self, data):
        """
        Validasi data sales yang masuk
        """
        required_fields = ['vkorg', 'erdat']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Field '{field}' is required")
        
        # Validate vkorg (sales organization) format
        if not isinstance(data['vkorg'], str) or len(data['vkorg']) > 4:
            raise ValueError("vkorg must be a string with maximum 4 characters")
        
        # Validate erdat (entry date) format
        if isinstance(data['erdat'], str):
            try:
                datetime.strptime(data['erdat'], '%Y-%m-%d')
            except ValueError:
                raise ValueError("erdat must be in YYYY-MM-DD format")
        
        # Optional field validations
        if data.get('audat') and isinstance(data['audat'], str):
            try:
                datetime.strptime(data['audat'], '%Y-%m-%d')
            except ValueError:
                raise ValueError("audat must be in YYYY-MM-DD format")
        
        # Validate numeric fields
        numeric_fields = ['kwmeng', 'netwr']
        for field in numeric_fields:
            if data.get(field) is not None:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    raise ValueError(f"Field '{field}' must be a valid number")
        
        return True
    
    def delete_existing_records(self, vkorg, erdat):
        """
        Delete existing records berdasarkan vkorg (company_id) dan erdat (entry_date)
        """
        try:
            # Convert string date to date object if needed
            if isinstance(erdat, str):
                erdat = datetime.strptime(erdat, '%Y-%m-%d').date()
            
            # Delete existing records
            deleted_count = db.session.query(SalesData).filter(
                and_(
                    SalesData.vkorg == vkorg,
                    SalesData.erdat == erdat
                )
            ).delete()
            
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error deleting existing records: {str(e)}")
    
    def insert_new_records(self, data_list):
        """
        Insert new records ke database
        """
        try:
            inserted_records = []
            
            for data in data_list:
                # Create new SalesData instance
                sales_record = SalesData.from_dict(data)
                db.session.add(sales_record)
                inserted_records.append(sales_record)
            
            # Commit all insertions
            db.session.commit()
            
            return inserted_records
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error inserting new records: {str(e)}")
    
    def process_sales_data_batch(self, data_list):
        """
        Process batch data sales dengan logic delete-insert
        """
        if not data_list:
            raise ValueError("No data provided")
        
        # Validate all data first
        for i, data in enumerate(data_list):
            try:
                self.validate_sales_data(data)
            except ValueError as e:
                raise ValueError(f"Validation error in record {i+1}: {str(e)}")
        
        # Group data by vkorg and erdat untuk delete-insert logic
        grouped_data = {}
        for data in data_list:
            key = (data['vkorg'], data['erdat'])
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(data)
        
        total_deleted = 0
        processed_records = []
        
        try:
            # Process each group
            for (vkorg, erdat), records in grouped_data.items():
                # Delete existing records for this vkorg and erdat
                deleted_count = self.delete_existing_records(vkorg, erdat)
                total_deleted += deleted_count
                
                # Insert new records
                inserted_records = self.insert_new_records(records)
                processed_records.extend(inserted_records)
            
            return {
                'processed_records': len(processed_records),
                'deleted_records': total_deleted,
                'groups_processed': len(grouped_data)
            }
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error processing sales data batch: {str(e)}")
    
    def get_sales_data(self, vkorg=None, erdat=None, page=1, per_page=100):
        """
        Get sales data dengan filtering dan pagination
        """
        try:
            query = db.session.query(SalesData)
            
            # Apply filters
            if vkorg:
                query = query.filter(SalesData.vkorg == vkorg)
            
            if erdat:
                if isinstance(erdat, str):
                    erdat = datetime.strptime(erdat, '%Y-%m-%d').date()
                query = query.filter(SalesData.erdat == erdat)
            
            # Apply pagination
            paginated = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return {
                'data': [record.to_dict() for record in paginated.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': paginated.total,
                    'pages': paginated.pages
                }
            }
            
        except Exception as e:
            raise Exception(f"Error retrieving sales data: {str(e)}")