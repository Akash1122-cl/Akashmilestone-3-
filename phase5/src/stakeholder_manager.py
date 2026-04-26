"""
Stakeholder Management System for Phase 5
Handles recipient lists, delivery rules, and scheduling
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class DeliveryStatus(Enum):
    """Email delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"


class DeliveryFrequency(Enum):
    """Report delivery frequency"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


@dataclass
class Stakeholder:
    """Stakeholder information"""
    email: str
    name: str
    role: str
    products: List[str]
    frequency: DeliveryFrequency
    active: bool = True
    preferred_format: str = 'html'  # html, markdown, pdf
    timezone: str = 'UTC'
    last_delivery: Optional[datetime] = None
    next_delivery: Optional[datetime] = None
    delivery_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.delivery_history is None:
            self.delivery_history = []


@dataclass
class DeliveryRule:
    """Delivery rule configuration"""
    product_id: str
    stakeholders: List[str]  # Email addresses
    frequency: DeliveryFrequency
    delivery_day: Optional[str] = None  # e.g., "Monday"
    delivery_time: str = "09:00"  # HH:MM format
    include_attachments: bool = True
    custom_subject: Optional[str] = None
    conditions: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}


@dataclass
class DeliveryRecord:
    """Record of email delivery"""
    stakeholder_email: str
    product_id: str
    report_id: str
    message_id: str
    thread_id: str
    sent_at: datetime
    status: DeliveryStatus
    error_message: Optional[str] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None


class StakeholderManager:
    """Manages stakeholders and delivery rules"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stakeholders: Dict[str, Stakeholder] = {}  # email -> Stakeholder
        self.delivery_rules: Dict[str, DeliveryRule] = {}  # product_id -> DeliveryRule
        self.delivery_records: List[DeliveryRecord] = []
        
        # Load initial data
        self._load_stakeholders()
        self._load_delivery_rules()
    
    def _load_stakeholders(self):
        """Load stakeholders from configuration or database"""
        # Example stakeholders - in production, load from database
        example_stakeholders = [
            Stakeholder(
                email="product.manager@company.com",
                name="Product Manager",
                role="manager",
                products=["TestApp", "FinanceApp"],
                frequency=DeliveryFrequency.WEEKLY
            ),
            Stakeholder(
                email="engineering.lead@company.com",
                name="Engineering Lead",
                role="engineering",
                products=["TestApp"],
                frequency=DeliveryFrequency.WEEKLY
            ),
            Stakeholder(
                email="ux.designer@company.com",
                name="UX Designer",
                role="design",
                products=["TestApp", "FinanceApp"],
                frequency=DeliveryFrequency.BIWEEKLY
            )
        ]
        
        for stakeholder in example_stakeholders:
            self.stakeholders[stakeholder.email] = stakeholder
    
    def _load_delivery_rules(self):
        """Load delivery rules from configuration"""
        # Example delivery rules
        example_rules = [
            DeliveryRule(
                product_id="TestApp",
                stakeholders=["product.manager@company.com", "engineering.lead@company.com"],
                frequency=DeliveryFrequency.WEEKLY,
                delivery_day="Monday",
                delivery_time="09:00"
            ),
            DeliveryRule(
                product_id="FinanceApp",
                stakeholders=["product.manager@company.com", "ux.designer@company.com"],
                frequency=DeliveryFrequency.WEEKLY,
                delivery_day="Tuesday",
                delivery_time="10:00"
            )
        ]
        
        for rule in example_rules:
            self.delivery_rules[rule.product_id] = rule
    
    def add_stakeholder(self, stakeholder: Stakeholder) -> bool:
        """Add new stakeholder"""
        try:
            self.stakeholders[stakeholder.email] = stakeholder
            
            # Update delivery rules if needed
            for product_id in stakeholder.products:
                if product_id in self.delivery_rules:
                    rule = self.delivery_rules[product_id]
                    if stakeholder.email not in rule.stakeholders:
                        rule.stakeholders.append(stakeholder.email)
            
            logger.info(f"Added stakeholder: {stakeholder.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add stakeholder: {e}")
            return False
    
    def remove_stakeholder(self, email: str) -> bool:
        """Remove stakeholder"""
        try:
            if email in self.stakeholders:
                stakeholder = self.stakeholders[email]
                stakeholder.active = False
                
                # Remove from delivery rules
                for rule in self.delivery_rules.values():
                    if email in rule.stakeholders:
                        rule.stakeholders.remove(email)
                
                logger.info(f"Removed stakeholder: {email}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove stakeholder: {e}")
            return False
    
    def get_stakeholders_for_product(self, product_id: str) -> List[Stakeholder]:
        """Get active stakeholders for a specific product"""
        stakeholders = []
        
        # Get stakeholders from delivery rules
        if product_id in self.delivery_rules:
            rule = self.delivery_rules[product_id]
            for email in rule.stakeholders:
                if email in self.stakeholders and self.stakeholders[email].active:
                    stakeholders.append(self.stakeholders[email])
        
        return stakeholders
    
    def get_pending_deliveries(self, product_id: str) -> List[Stakeholder]:
        """Get stakeholders pending delivery for a product"""
        stakeholders = self.get_stakeholders_for_product(product_id)
        pending = []
        
        now = datetime.now()
        
        for stakeholder in stakeholders:
            should_deliver = False
            
            # Check if delivery is due based on frequency
            if stakeholder.frequency == DeliveryFrequency.WEEKLY:
                if not stakeholder.last_delivery:
                    should_deliver = True
                else:
                    days_since = (now - stakeholder.last_delivery).days
                    should_deliver = days_since >= 7
            
            elif stakeholder.frequency == DeliveryFrequency.BIWEEKLY:
                if not stakeholder.last_delivery:
                    should_deliver = True
                else:
                    days_since = (now - stakeholder.last_delivery).days
                    should_deliver = days_since >= 14
            
            elif stakeholder.frequency == DeliveryFrequency.MONTHLY:
                if not stakeholder.last_delivery:
                    should_deliver = True
                else:
                    days_since = (now - stakeholder.last_delivery).days
                    should_deliver = days_since >= 30
            
            elif stakeholder.frequency == DeliveryFrequency.ON_DEMAND:
                # Manual delivery only
                should_deliver = False
            
            if should_deliver:
                pending.append(stakeholder)
        
        return pending
    
    def record_delivery(self, record: DeliveryRecord):
        """Record email delivery"""
        self.delivery_records.append(record)
        
        # Update stakeholder's last delivery
        if record.stakeholder_email in self.stakeholders:
            self.stakeholders[record.stakeholder_email].last_delivery = record.sent_at
            self.stakeholders[record.stakeholder_email].delivery_history.append({
                'report_id': record.report_id,
                'sent_at': record.sent_at.isoformat(),
                'status': record.status.value,
                'message_id': record.message_id
            })
        
        logger.info(f"Recorded delivery: {record.stakeholder_email} -> {record.product_id}")
    
    def update_delivery_status(self, message_id: str, status: DeliveryStatus, 
                             error_message: Optional[str] = None):
        """Update delivery status"""
        for record in self.delivery_records:
            if record.message_id == message_id:
                record.status = status
                if error_message:
                    record.error_message = error_message
                
                logger.info(f"Updated delivery status: {message_id} -> {status.value}")
                break
    
    def get_delivery_statistics(self, product_id: Optional[str] = None, 
                             days: int = 30) -> Dict[str, Any]:
        """Get delivery statistics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        records = self.delivery_records
        if product_id:
            records = [r for r in records if r.product_id == product_id]
        
        recent_records = [r for r in records if r.sent_at >= cutoff_date]
        
        stats = {
            'total_sent': len([r for r in recent_records if r.status == DeliveryStatus.SENT]),
            'total_delivered': len([r for r in recent_records if r.status == DeliveryStatus.DELIVERED]),
            'total_bounced': len([r for r in recent_records if r.status == DeliveryStatus.BOUNCED]),
            'total_failed': len([r for r in recent_records if r.status == DeliveryStatus.FAILED]),
            'delivery_rate': 0.0,
            'bounce_rate': 0.0,
            'period_days': days
        }
        
        if recent_records:
            stats['delivery_rate'] = (stats['total_delivered'] / len(recent_records)) * 100
            stats['bounce_rate'] = (stats['total_bounced'] / len(recent_records)) * 100
        
        return stats
    
    def export_stakeholders(self) -> List[Dict[str, Any]]:
        """Export stakeholders data"""
        return [asdict(stakeholder) for stakeholder in self.stakeholders.values()]
    
    def import_stakeholders(self, stakeholders_data: List[Dict[str, Any]]) -> int:
        """Import stakeholders data"""
        imported = 0
        
        for data in stakeholders_data:
            try:
                # Convert frequency string to enum
                if 'frequency' in data and isinstance(data['frequency'], str):
                    data['frequency'] = DeliveryFrequency(data['frequency'])
                
                # Convert datetime strings
                if 'last_delivery' in data and data['last_delivery']:
                    data['last_delivery'] = datetime.fromisoformat(data['last_delivery'])
                
                stakeholder = Stakeholder(**data)
                self.add_stakeholder(stakeholder)
                imported += 1
                
            except Exception as e:
                logger.error(f"Failed to import stakeholder: {e}")
                continue
        
        logger.info(f"Imported {imported} stakeholders")
        return imported
    
    def validate_stakeholder_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate stakeholder configuration"""
        errors = []
        
        required_fields = ['email', 'name', 'role', 'products', 'frequency']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate email format
        if 'email' in config:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, config['email']):
                errors.append("Invalid email format")
        
        # Validate frequency
        if 'frequency' in config:
            try:
                DeliveryFrequency(config['frequency'])
            except ValueError:
                errors.append(f"Invalid frequency: {config['frequency']}")
        
        # Validate products
        if 'products' in config:
            if not isinstance(config['products'], list) or not config['products']:
                errors.append("Products must be a non-empty list")
        
        return errors


# Factory function
def create_stakeholder_manager(config: Dict[str, Any]) -> StakeholderManager:
    """Create stakeholder manager instance"""
    return StakeholderManager(config)
