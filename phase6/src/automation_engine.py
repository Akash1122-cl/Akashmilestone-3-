"""
Phase 6 Automation Engine
Handles scheduled report generation, rule processing, and automation workflows
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)

class AutomationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TriggerType(Enum):
    SCHEDULED = "scheduled"
    EVENT_BASED = "event_based"
    MANUAL = "manual"
    CONDITION_BASED = "condition_based"

@dataclass
class AutomationCondition:
    """Condition for triggering automation"""
    metric: str
    operator: str  # gt, lt, eq, gte, lte
    value: float
    time_window: Optional[str] = None  # 1h, 24h, 7d, etc.

@dataclass
class AutomationAction:
    """Action to execute when condition is met"""
    action_type: str  # generate_report, send_email, create_drive_file
    parameters: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class AutomationRule:
    """Complete automation rule definition"""
    id: str
    name: str
    description: str
    product_id: str
    
    # Trigger configuration
    trigger_type: TriggerType
    schedule: Optional[str] = None  # Cron expression
    conditions: List[AutomationCondition] = None
    
    # Actions
    actions: List[AutomationAction] = None
    
    # Status and metadata
    enabled: bool = True
    created_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.conditions is None:
            self.conditions = []
        if self.actions is None:
            self.actions = []

@dataclass
class AutomationExecution:
    """Track execution of automation rules"""
    id: str
    rule_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: AutomationStatus = AutomationStatus.PENDING
    
    # Results
    results: List[Dict[str, Any]] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.errors is None:
            self.errors = []

class AutomationEngine:
    """Core automation engine for Phase 6"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules: Dict[str, AutomationRule] = {}
        self.executions: Dict[str, AutomationExecution] = {}
        self.running = False
        
        # Service integrations
        self.analytics_service = None
        self.reporting_service = None
        self.mcp_service = None
        
    def register_services(self, analytics_service, reporting_service, mcp_service):
        """Register service dependencies"""
        self.analytics_service = analytics_service
        self.reporting_service = reporting_service
        self.mcp_service = mcp_service
    
    async def start(self):
        """Start the automation engine"""
        self.running = True
        logger.info("Automation engine started")
        
        # Start background scheduler
        asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """Stop the automation engine"""
        self.running = False
        logger.info("Automation engine stopped")
    
    async def create_rule(self, rule: AutomationRule) -> str:
        """Create a new automation rule"""
        try:
            rule.id = str(uuid.uuid4())
            
            # Validate rule
            await self._validate_rule(rule)
            
            # Calculate next run time for scheduled rules
            if rule.trigger_type == TriggerType.SCHEDULED and rule.schedule:
                rule.next_run = self._calculate_next_run(rule.schedule)
            
            # Store rule
            self.rules[rule.id] = rule
            
            logger.info(f"Created automation rule: {rule.name} ({rule.id})")
            return rule.id
            
        except Exception as e:
            logger.error(f"Error creating automation rule: {e}")
            raise
    
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing automation rule"""
        try:
            if rule_id not in self.rules:
                raise ValueError(f"Rule {rule_id} not found")
            
            rule = self.rules[rule_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            # Recalculate next run time if schedule changed
            if rule.trigger_type == TriggerType.SCHEDULED and rule.schedule:
                rule.next_run = self._calculate_next_run(rule.schedule)
            
            logger.info(f"Updated automation rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating automation rule: {e}")
            raise
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete an automation rule"""
        try:
            if rule_id not in self.rules:
                raise ValueError(f"Rule {rule_id} not found")
            
            rule_name = self.rules[rule_id].name
            del self.rules[rule_id]
            
            logger.info(f"Deleted automation rule: {rule_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting automation rule: {e}")
            raise
    
    async def execute_rule(self, rule_id: str, manual_trigger: bool = False) -> str:
        """Execute an automation rule"""
        try:
            if rule_id not in self.rules:
                raise ValueError(f"Rule {rule_id} not found")
            
            rule = self.rules[rule_id]
            
            # Check if rule is enabled
            if not rule.enabled and not manual_trigger:
                raise ValueError(f"Rule {rule_id} is disabled")
            
            # Create execution record
            execution = AutomationExecution(
                id=str(uuid.uuid4()),
                rule_id=rule_id,
                started_at=datetime.now(),
                status=AutomationStatus.RUNNING
            )
            
            self.executions[execution.id] = execution
            
            logger.info(f"Executing automation rule: {rule.name}")
            
            # Execute the rule
            await self._execute_rule_actions(rule, execution)
            
            # Update execution status
            execution.status = AutomationStatus.COMPLETED
            execution.completed_at = datetime.now()
            
            # Update rule last run time
            rule.last_run = datetime.now()
            
            # Calculate next run time for scheduled rules
            if rule.trigger_type == TriggerType.SCHEDULED and rule.schedule:
                rule.next_run = self._calculate_next_run(rule.schedule)
            
            logger.info(f"Completed automation rule: {rule.name}")
            return execution.id
            
        except Exception as e:
            # Update execution status on error
            if execution.id in self.executions:
                execution = self.executions[execution.id]
                execution.status = AutomationStatus.FAILED
                execution.completed_at = datetime.now()
                execution.errors.append(str(e))
            
            logger.error(f"Error executing automation rule: {e}")
            raise
    
    async def get_rule_executions(self, rule_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history for a rule"""
        try:
            executions = []
            
            for execution in self.executions.values():
                if execution.rule_id == rule_id:
                    executions.append({
                        "id": execution.id,
                        "started_at": execution.started_at.isoformat(),
                        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                        "status": execution.status.value,
                        "results": execution.results,
                        "errors": execution.errors
                    })
            
            # Sort by started_at descending
            executions.sort(key=lambda x: x["started_at"], reverse=True)
            
            return executions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting rule executions: {e}")
            raise
    
    async def _scheduler_loop(self):
        """Background loop for scheduled rule execution"""
        while self.running:
            try:
                await self._check_scheduled_rules()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_scheduled_rules(self):
        """Check and execute scheduled rules"""
        now = datetime.now()
        
        for rule in self.rules.values():
            if (rule.enabled and 
                rule.trigger_type == TriggerType.SCHEDULED and
                rule.next_run and
                rule.next_run <= now):
                
                try:
                    await self.execute_rule(rule.id)
                except Exception as e:
                    logger.error(f"Error executing scheduled rule {rule.id}: {e}")
    
    async def _execute_rule_actions(self, rule: AutomationRule, execution: AutomationExecution):
        """Execute all actions for a rule"""
        for action in rule.actions:
            try:
                result = await self._execute_action(action, rule)
                execution.results.append(result)
                
            except Exception as e:
                error_msg = f"Error executing action {action.action_type}: {e}"
                execution.errors.append(error_msg)
                logger.error(error_msg)
                
                # Retry logic
                if action.retry_count < action.max_retries:
                    action.retry_count += 1
                    logger.info(f"Retrying action {action.action_type} (attempt {action.retry_count})")
                    await asyncio.sleep(5)  # Wait before retry
                    await self._execute_action(action, rule)
                    execution.results.append({"retry": True, "attempt": action.retry_count})
    
    async def _execute_action(self, action: AutomationAction, rule: AutomationRule) -> Dict[str, Any]:
        """Execute a single automation action"""
        try:
            if action.action_type == "generate_report":
                return await self._generate_report_action(action, rule)
            
            elif action.action_type == "send_email":
                return await self._send_email_action(action, rule)
            
            elif action.action_type == "create_drive_file":
                return await self._create_drive_file_action(action, rule)
            
            elif action.action_type == "update_dashboard":
                return await self._update_dashboard_action(action, rule)
            
            else:
                raise ValueError(f"Unknown action type: {action.action_type}")
                
        except Exception as e:
            logger.error(f"Error executing action {action.action_type}: {e}")
            raise
    
    async def _generate_report_action(self, action: AutomationAction, rule: AutomationRule) -> Dict[str, Any]:
        """Generate report action"""
        if not self.reporting_service:
            raise ValueError("Reporting service not available")
        
        parameters = action.parameters
        report_type = parameters.get("report_type", "executive_summary")
        time_range = parameters.get("time_range", "30_days")
        
        # Generate report
        report = await self.reporting_service.generate_report(
            product_id=rule.product_id,
            report_type=report_type,
            time_range=time_range,
            template=parameters.get("template")
        )
        
        return {
            "action": "generate_report",
            "report_id": report.get("report_id"),
            "status": "success"
        }
    
    async def _send_email_action(self, action: AutomationAction, rule: AutomationRule) -> Dict[str, Any]:
        """Send email action"""
        if not self.mcp_service:
            raise ValueError("MCP service not available")
        
        parameters = action.parameters
        recipients = parameters.get("recipients", [])
        subject = parameters.get("subject", f"Automated Report - {rule.product_id}")
        
        results = []
        
        for recipient in recipients:
            try:
                # Generate email content
                body = parameters.get("body", f"Automated report for {rule.product_id}")
                
                # Send via MCP service
                result = await self.mcp_service.send_email_notification(
                    to=recipient,
                    subject=subject,
                    body=body
                )
                
                results.append({
                    "recipient": recipient,
                    "status": "success",
                    "draft_id": result.get("draft_id")
                })
                
            except Exception as e:
                results.append({
                    "recipient": recipient,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "action": "send_email",
            "results": results,
            "status": "success"
        }
    
    async def _create_drive_file_action(self, action: AutomationAction, rule: AutomationRule) -> Dict[str, Any]:
        """Create Drive file action"""
        if not self.mcp_service:
            raise ValueError("MCP service not available")
        
        parameters = action.parameters
        filename = parameters.get("filename", f"Report_{rule.product_id}_{datetime.now().strftime('%Y%m%d')}")
        content = parameters.get("content", f"Automated report for {rule.product_id}")
        
        # Create file via MCP service
        result = await self.mcp_service.deliver_report_to_docs(
            doc_id=filename,
            report_content=content
        )
        
        return {
            "action": "create_drive_file",
            "file_id": result.get("doc_id"),
            "status": "success"
        }
    
    async def _update_dashboard_action(self, action: AutomationAction, rule: AutomationRule) -> Dict[str, Any]:
        """Update dashboard action"""
        # Placeholder for dashboard update logic
        return {
            "action": "update_dashboard",
            "dashboard_id": action.parameters.get("dashboard_id"),
            "status": "success"
        }
    
    async def _validate_rule(self, rule: AutomationRule):
        """Validate automation rule configuration"""
        if not rule.name:
            raise ValueError("Rule name is required")
        
        if not rule.product_id:
            raise ValueError("Product ID is required")
        
        if not rule.actions:
            raise ValueError("At least one action is required")
        
        # Validate scheduled rules
        if rule.trigger_type == TriggerType.SCHEDULED and not rule.schedule:
            raise ValueError("Schedule is required for scheduled rules")
        
        # Validate conditions for condition-based rules
        if rule.trigger_type == TriggerType.CONDITION_BASED and not rule.conditions:
            raise ValueError("Conditions are required for condition-based rules")
    
    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time from cron expression"""
        # Simplified implementation - in production, use a proper cron library
        now = datetime.now()
        
        if schedule == "hourly":
            return now + timedelta(hours=1)
        elif schedule == "daily":
            return now + timedelta(days=1)
        elif schedule == "weekly":
            return now + timedelta(weeks=1)
        elif schedule == "monthly":
            return now + timedelta(days=30)
        else:
            # Default to daily
            return now + timedelta(days=1)

# Factory function
def create_automation_engine(config: Dict[str, Any]) -> AutomationEngine:
    """Create automation engine instance"""
    return AutomationEngine(config)
