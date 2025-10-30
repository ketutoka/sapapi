from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import and_, or_
from flask import current_app

# Import from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models from app.py instead of models.py to avoid multiple SQLAlchemy instances
try:
    from app import db, DwhSales as SalesData
except ImportError:
    # Fallback for when running standalone
    from models import db, SalesData

class SalesService:
    """Service class untuk menangani logic bisnis sales data dengan CDC yang tepat"""
    
    def __init__(self, db_instance=None, model_class=None):
        # Allow dependency injection for testing and app context
        self.db = db_instance
        self.model_class = model_class
    
    def _get_db(self):
        """Get database instance, with fallback to app context"""
        if self.db:
            return self.db
        
        # Try to get from Flask app context
        try:
            from flask import current_app
            return current_app.extensions['sqlalchemy']
        except:
            # Fallback to imported db
            try:
                from app import db
                return db
            except ImportError:
                from models import db
                return db
    
    def _get_model(self):
        """Get model class, with fallback to app context"""
        if self.model_class:
            return self.model_class
        
        # Try to get from app import
        try:
            from app import DwhSales
            return DwhSales
        except ImportError:
            from models import SalesData
            return SalesData
    
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
    
    def validate_cdc_parameters(self, cdc_params):
        """
        Validasi parameter CDC (Change Data Capture)
        """
        required_fields = ['vkorg', 'start_date', 'end_date']
        
        for field in required_fields:
            if field not in cdc_params or not cdc_params[field]:
                raise ValueError(f"CDC parameter '{field}' is required")
        
        # Validate date formats
        try:
            start_date = datetime.strptime(cdc_params['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(cdc_params['end_date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("start_date and end_date must be in YYYY-MM-DD format")
        
        # Validate date range
        if start_date > end_date:
            raise ValueError("start_date cannot be greater than end_date")
        
        return True
    
    def delete_existing_records_by_range(self, vkorg, start_date, end_date):
        """
        Delete existing records berdasarkan vkorg dan date range (start_date sampai end_date)
        Ini adalah logic CDC yang tepat untuk delete data berdasarkan parameter range
        """
        try:
            db = self._get_db()
            SalesModel = self._get_model()
            
            # Convert string dates to date objects if needed
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Delete existing records in the specified date range
            deleted_count = db.session.query(SalesModel).filter(
                and_(
                    SalesModel.vkorg == vkorg,
                    SalesModel.erdat >= start_date,
                    SalesModel.erdat <= end_date
                )
            ).delete(synchronize_session=False)
            
            return deleted_count
            
        except Exception as e:
            db = self._get_db()
            db.session.rollback()
            raise Exception(f"Error deleting existing records by range: {str(e)}")
    
    def delete_existing_records(self, vkorg, erdat):
        """
        Delete existing records berdasarkan vkorg dan erdat (legacy method)
        """
        try:
            db = self._get_db()
            SalesModel = self._get_model()
            
            # Convert string date to date object if needed
            if isinstance(erdat, str):
                erdat = datetime.strptime(erdat, '%Y-%m-%d').date()
            
            # Delete existing records
            deleted_count = db.session.query(SalesModel).filter(
                and_(
                    SalesModel.vkorg == vkorg,
                    SalesModel.erdat == erdat
                )
            ).delete(synchronize_session=False)
            
            return deleted_count
            
        except Exception as e:
            db = self._get_db()
            db.session.rollback()
            raise Exception(f"Error deleting existing records: {str(e)}")
    
    def insert_new_records(self, data_list):
        """
        Insert new records ke database
        """
        try:
            db = self._get_db()
            SalesModel = self._get_model()
            
            inserted_records = []
            
            for data in data_list:
                # Create new SalesData instance using from_dict if available
                if hasattr(SalesModel, 'from_dict'):
                    sales_record = SalesModel.from_dict(data)
                else:
                    # Manually create instance
                    sales_record = SalesModel(
                        vkorg=data.get('vkorg'),
                        vtext=data.get('vtext'),
                        erdat=datetime.strptime(data['erdat'], '%Y-%m-%d').date() if isinstance(data['erdat'], str) else data['erdat'],
                        audat=datetime.strptime(data['audat'], '%Y-%m-%d').date() if data.get('audat') and isinstance(data['audat'], str) else data.get('audat'),
                        matkl=data.get('matkl'),
                        wgbez=data.get('wgbez'),
                        matnr=data.get('matnr'),
                        maktx=data.get('maktx'),
                        route=data.get('route'),
                        bezei=data.get('bezei'),
                        kunnr=data.get('kunnr'),
                        name1=data.get('name1'),
                        sorlt=data.get('sorlt'),
                        mvgr1=data.get('mvgr1'),
                        mvgtx=data.get('mvgtx'),
                        meins=data.get('meins'),
                        waerk=data.get('waerk'),
                        kwmeng=data.get('kwmeng'),
                        netwr=data.get('netwr')
                    )
                
                db.session.add(sales_record)
                inserted_records.append(sales_record)
            
            # Commit all insertions
            db.session.commit()
            
            return inserted_records
            
        except Exception as e:
            db = self._get_db()
            db.session.rollback()
            raise Exception(f"Error inserting new records: {str(e)}")
    
    def process_sales_data_cdc(self, cdc_params, data_list):
        """
        Process data sales dengan CDC logic yang tepat:
        1. Terima parameter CDC (vkorg, start_date, end_date)
        2. Delete semua data dalam range tersebut
        3. Insert semua data baru
        """
        if not cdc_params:
            raise ValueError("CDC parameters are required")
        
        if not data_list:
            raise ValueError("No data provided for insertion")
        
        # Validate CDC parameters
        self.validate_cdc_parameters(cdc_params)
        
        # Validate all data
        for i, data in enumerate(data_list):
            try:
                self.validate_sales_data(data)
            except ValueError as e:
                raise ValueError(f"Validation error in record {i+1}: {str(e)}")
        
        vkorg = cdc_params['vkorg']
        start_date = cdc_params['start_date']
        end_date = cdc_params['end_date']
        
        try:
            # Step 1: Delete existing records in the specified date range
            deleted_count = self.delete_existing_records_by_range(vkorg, start_date, end_date)
            
            # Step 2: Insert all new records
            inserted_records = self.insert_new_records(data_list)
            
            return {
                'processed_records': len(inserted_records),
                'deleted_records': deleted_count,
                'cdc_parameters': {
                    'vkorg': vkorg,
                    'start_date': start_date,
                    'end_date': end_date
                },
                'date_range_processed': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            db = self._get_db()
            db.session.rollback()
            raise Exception(f"Error processing CDC sales data: {str(e)}")
    
    def process_sales_data_batch(self, data_list):
        """
        Process batch data sales dengan logic delete-insert (legacy method)
        Untuk backward compatibility
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
            db = self._get_db()
            db.session.rollback()
            raise Exception(f"Error processing sales data batch: {str(e)}")
    
    def get_sales_data(self, vkorg=None, erdat=None, start_date=None, end_date=None, page=1, per_page=100):
        """
        Get sales data dengan filtering dan pagination
        """
        try:
            db = self._get_db()
            SalesModel = self._get_model()
            
            query = db.session.query(SalesModel)
            
            # Apply filters
            if vkorg:
                query = query.filter(SalesModel.vkorg == vkorg)
            
            if erdat:
                if isinstance(erdat, str):
                    erdat = datetime.strptime(erdat, '%Y-%m-%d').date()
                query = query.filter(SalesModel.erdat == erdat)
            
            # Date range filter
            if start_date and end_date:
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(
                    and_(
                        SalesModel.erdat >= start_date,
                        SalesModel.erdat <= end_date
                    )
                )
            
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
    
    def get_cdc_statistics(self, vkorg, start_date, end_date):
        """
        Get statistik data untuk CDC range yang akan diproses
        """
        try:
            db = self._get_db()
            SalesModel = self._get_model()
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Count existing records that will be deleted
            existing_count = db.session.query(SalesModel).filter(
                and_(
                    SalesModel.vkorg == vkorg,
                    SalesModel.erdat >= start_date,
                    SalesModel.erdat <= end_date
                )
            ).count()
            
            # Get date range info
            first_record = db.session.query(SalesModel).filter(
                and_(
                    SalesModel.vkorg == vkorg,
                    SalesModel.erdat >= start_date,
                    SalesModel.erdat <= end_date
                )
            ).order_by(SalesModel.erdat.asc()).first()
            
            last_record = db.session.query(SalesModel).filter(
                and_(
                    SalesModel.vkorg == vkorg,
                    SalesModel.erdat >= start_date,
                    SalesModel.erdat <= end_date
                )
            ).order_by(SalesModel.erdat.desc()).first()
            
            return {
                'vkorg': vkorg,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'existing_records_count': existing_count,
                'existing_date_range': {
                    'first_date': first_record.erdat.isoformat() if first_record else None,
                    'last_date': last_record.erdat.isoformat() if last_record else None
                }
            }
            
        except Exception as e:
            raise Exception(f"Error getting CDC statistics: {str(e)}")