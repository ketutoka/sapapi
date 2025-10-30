from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index

db = SQLAlchemy()

class SalesData(db.Model):
    """
    Model untuk data sales dari SAP
    """
    __tablename__ = 'sales_data'
    
    # Primary key auto increment
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Sales Organization
    vkorg = db.Column(db.String(4), nullable=False, comment='Sales Organization')
    
    # Entry Date (key untuk delete-insert logic)
    erdat = db.Column(db.Date, nullable=False, comment='Entry Date')
    
    # Document Date
    audat = db.Column(db.Date, nullable=True, comment='Document Date')
    
    # Material Group
    matkl = db.Column(db.String(9), nullable=True, comment='Material Group')
    wgbez = db.Column(db.String(20), nullable=True, comment='Material Group Description')
    
    # Material
    matnr = db.Column(db.String(18), nullable=True, comment='Material Number')
    maktx = db.Column(db.String(40), nullable=True, comment='Material Description')
    
    # Route
    route = db.Column(db.String(6), nullable=True, comment='Route')
    bezei = db.Column(db.String(30), nullable=True, comment='Route Description')
    
    # Customer
    kunnr = db.Column(db.String(10), nullable=True, comment='Customer')
    name1 = db.Column(db.String(35), nullable=True, comment='Customer Name')
    sorlt = db.Column(db.String(10), nullable=True, comment='Sort Customer Name')
    
    # Material Group (additional)
    mvgr1 = db.Column(db.String(3), nullable=True, comment='Material Group 1')
    mvgtx = db.Column(db.String(20), nullable=True, comment='Material Group Description')
    
    # Unit and Currency
    meins = db.Column(db.String(3), nullable=True, comment='Unit of Measure')
    waerk = db.Column(db.String(5), nullable=True, comment='Currency')
    
    # Quantities and Amounts
    kwmeng = db.Column(db.Numeric(13, 3), nullable=True, comment='Sales Quantity')
    netwr = db.Column(db.Numeric(15, 2), nullable=True, comment='Sales Amount')
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='Record Creation Time')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Record Update Time')
    
    # Index untuk performance (berdasarkan key delete-insert)
    __table_args__ = (
        Index('idx_sales_vkorg_erdat', 'vkorg', 'erdat'),
        Index('idx_sales_created_at', 'created_at'),
        Index('idx_sales_matnr', 'matnr'),
        Index('idx_sales_kunnr', 'kunnr'),
    )
    
    def __repr__(self):
        return f'<SalesData {self.vkorg}-{self.erdat}-{self.matnr}>'
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'vkorg': self.vkorg,
            'erdat': self.erdat.isoformat() if self.erdat else None,
            'audat': self.audat.isoformat() if self.audat else None,
            'matkl': self.matkl,
            'wgbez': self.wgbez,
            'matnr': self.matnr,
            'maktx': self.maktx,
            'route': self.route,
            'bezei': self.bezei,
            'kunnr': self.kunnr,
            'name1': self.name1,
            'sorlt': self.sorlt,
            'mvgr1': self.mvgr1,
            'mvgtx': self.mvgtx,
            'meins': self.meins,
            'waerk': self.waerk,
            'kwmeng': float(self.kwmeng) if self.kwmeng else None,
            'netwr': float(self.netwr) if self.netwr else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def from_dict(data):
        """Create model instance from dictionary"""
        # Convert string dates to date objects
        erdat = None
        if data.get('erdat'):
            if isinstance(data['erdat'], str):
                erdat = datetime.strptime(data['erdat'], '%Y-%m-%d').date()
            else:
                erdat = data['erdat']
        
        audat = None
        if data.get('audat'):
            if isinstance(data['audat'], str):
                audat = datetime.strptime(data['audat'], '%Y-%m-%d').date()
            else:
                audat = data['audat']
        
        return SalesData(
            vkorg=data.get('vkorg'),
            erdat=erdat,
            audat=audat,
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