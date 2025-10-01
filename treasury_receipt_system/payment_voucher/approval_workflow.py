"""Approval workflow management for Payment Vouchers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum

LOGGER = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class ApprovalLevel(Enum):
    """Approval level enumeration."""
    STANDARD = "standard"
    HIGH = "high"
    EXECUTIVE = "executive"


@dataclass
class ApprovalStep:
    """Individual approval step in the workflow."""
    step_id: str
    approver_role: str
    approver_name: Optional[str]
    status: ApprovalStatus
    comments: Optional[str]
    approved_date: Optional[datetime]
    due_date: Optional[datetime]
    is_required: bool = True


@dataclass
class ApprovalWorkflow:
    """Complete approval workflow for a Payment Voucher."""
    workflow_id: str
    voucher_number: str
    current_step: int
    total_steps: int
    status: ApprovalStatus
    steps: List[ApprovalStep]
    created_date: datetime
    completed_date: Optional[datetime]
    escalation_reason: Optional[str] = None


class ApprovalWorkflowManager:
    """Manages approval workflows for Payment Vouchers."""
    
    def __init__(self):
        self.workflow_templates = self._build_workflow_templates()
        self.escalation_rules = self._build_escalation_rules()
    
    def _build_workflow_templates(self) -> Dict[ApprovalLevel, List[Dict]]:
        """Build approval workflow templates for different levels."""
        return {
            ApprovalLevel.STANDARD: [
                {
                    "step_id": "dept_head",
                    "approver_role": "Department Head",
                    "timeout_hours": 24,
                    "is_required": True
                },
                {
                    "step_id": "finance_processing",
                    "approver_role": "Finance Processor",
                    "timeout_hours": 48,
                    "is_required": True
                }
            ],
            ApprovalLevel.HIGH: [
                {
                    "step_id": "dept_head",
                    "approver_role": "Department Head",
                    "timeout_hours": 24,
                    "is_required": True
                },
                {
                    "step_id": "finance_director",
                    "approver_role": "Finance Director",
                    "timeout_hours": 48,
                    "is_required": True
                },
                {
                    "step_id": "finance_processing",
                    "approver_role": "Finance Processor",
                    "timeout_hours": 48,
                    "is_required": True
                }
            ],
            ApprovalLevel.EXECUTIVE: [
                {
                    "step_id": "dept_head",
                    "approver_role": "Department Head",
                    "timeout_hours": 24,
                    "is_required": True
                },
                {
                    "step_id": "finance_director",
                    "approver_role": "Finance Director",
                    "timeout_hours": 48,
                    "is_required": True
                },
                {
                    "step_id": "executive",
                    "approver_role": "Executive",
                    "timeout_hours": 72,
                    "is_required": True
                },
                {
                    "step_id": "finance_processing",
                    "approver_role": "Finance Processor",
                    "timeout_hours": 48,
                    "is_required": True
                }
            ]
        }
    
    def _build_escalation_rules(self) -> Dict[str, Dict]:
        """Build escalation rules for different scenarios."""
        return {
            "timeout": {
                "escalate_after_hours": 72,
                "escalate_to": "Finance Director",
                "notification_required": True
            },
            "rejection": {
                "escalate_after_rejections": 2,
                "escalate_to": "Executive",
                "notification_required": True
            },
            "high_amount": {
                "threshold": 500000,
                "escalate_to": "Executive",
                "notification_required": True
            }
        }
    
    def create_workflow(self, 
                       voucher_number: str, 
                       approval_level: ApprovalLevel,
                       amount: float,
                       created_by: str) -> ApprovalWorkflow:
        """Create a new approval workflow for a Payment Voucher."""
        
        workflow_id = f"WF-{voucher_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        template = self.workflow_templates[approval_level]
        
        steps = []
        for i, step_template in enumerate(template):
            due_date = datetime.now() + timedelta(hours=step_template["timeout_hours"])
            
            step = ApprovalStep(
                step_id=step_template["step_id"],
                approver_role=step_template["approver_role"],
                approver_name=None,
                status=ApprovalStatus.PENDING,
                comments=None,
                approved_date=None,
                due_date=due_date,
                is_required=step_template["is_required"]
            )
            steps.append(step)
        
        # Check for high-amount escalation
        if amount >= self.escalation_rules["high_amount"]["threshold"]:
            # Add executive step if not already present
            if not any(step.approver_role == "Executive" for step in steps):
                executive_step = ApprovalStep(
                    step_id="executive_escalation",
                    approver_role="Executive",
                    approver_name=None,
                    status=ApprovalStatus.PENDING,
                    comments="Escalated due to high amount",
                    approved_date=None,
                    due_date=datetime.now() + timedelta(hours=72),
                    is_required=True
                )
                steps.append(executive_step)
        
        workflow = ApprovalWorkflow(
            workflow_id=workflow_id,
            voucher_number=voucher_number,
            current_step=0,
            total_steps=len(steps),
            status=ApprovalStatus.PENDING,
            steps=steps,
            created_date=datetime.now(),
            completed_date=None
        )
        
        LOGGER.info(f"Created approval workflow {workflow_id} for voucher {voucher_number}")
        return workflow
    
    def approve_step(self, 
                    workflow: ApprovalWorkflow, 
                    step_id: str, 
                    approver_name: str,
                    comments: Optional[str] = None) -> bool:
        """Approve a specific step in the workflow."""
        
        # Find the step
        step = next((s for s in workflow.steps if s.step_id == step_id), None)
        if not step:
            LOGGER.error(f"Step {step_id} not found in workflow {workflow.workflow_id}")
            return False
        
        if step.status != ApprovalStatus.PENDING:
            LOGGER.warning(f"Step {step_id} is not pending (status: {step.status})")
            return False
        
        # Approve the step
        step.status = ApprovalStatus.APPROVED
        step.approver_name = approver_name
        step.comments = comments
        step.approved_date = datetime.now()
        
        # Move to next step
        workflow.current_step += 1
        
        # Check if workflow is complete
        if workflow.current_step >= workflow.total_steps:
            workflow.status = ApprovalStatus.APPROVED
            workflow.completed_date = datetime.now()
            LOGGER.info(f"Workflow {workflow.workflow_id} completed")
        else:
            LOGGER.info(f"Workflow {workflow.workflow_id} moved to step {workflow.current_step}")
        
        return True
    
    def reject_step(self, 
                   workflow: ApprovalWorkflow, 
                   step_id: str, 
                   approver_name: str,
                   comments: str) -> bool:
        """Reject a specific step in the workflow."""
        
        step = next((s for s in workflow.steps if s.step_id == step_id), None)
        if not step:
            LOGGER.error(f"Step {step_id} not found in workflow {workflow.workflow_id}")
            return False
        
        if step.status != ApprovalStatus.PENDING:
            LOGGER.warning(f"Step {step_id} is not pending (status: {step.status})")
            return False
        
        # Reject the step
        step.status = ApprovalStatus.REJECTED
        step.approver_name = approver_name
        step.comments = comments
        step.approved_date = datetime.now()
        
        # Check for escalation
        rejection_count = sum(1 for s in workflow.steps if s.status == ApprovalStatus.REJECTED)
        if rejection_count >= self.escalation_rules["rejection"]["escalate_after_rejections"]:
            workflow.status = ApprovalStatus.ESCALATED
            workflow.escalation_reason = f"Escalated after {rejection_count} rejections"
            LOGGER.warning(f"Workflow {workflow.workflow_id} escalated due to rejections")
        else:
            workflow.status = ApprovalStatus.REJECTED
            workflow.completed_date = datetime.now()
            LOGGER.info(f"Workflow {workflow.workflow_id} rejected at step {step_id}")
        
        return True
    
    def check_timeouts(self, workflow: ApprovalWorkflow) -> List[str]:
        """Check for timed out steps and return escalation recommendations."""
        timeouts = []
        current_time = datetime.now()
        
        for step in workflow.steps:
            if step.status == ApprovalStatus.PENDING and step.due_date:
                if current_time > step.due_date:
                    timeouts.append(f"Step {step.step_id} ({step.approver_role}) timed out")
        
        # Check for overall workflow timeout
        if workflow.status == ApprovalStatus.PENDING:
            workflow_age = current_time - workflow.created_date
            if workflow_age.total_seconds() / 3600 > self.escalation_rules["timeout"]["escalate_after_hours"]:
                timeouts.append("Workflow overall timeout - escalation required")
                workflow.status = ApprovalStatus.ESCALATED
                workflow.escalation_reason = "Workflow timeout"
        
        return timeouts
    
    def get_workflow_status(self, workflow: ApprovalWorkflow) -> Dict:
        """Get current status of the workflow."""
        pending_steps = [s for s in workflow.steps if s.status == ApprovalStatus.PENDING]
        completed_steps = [s for s in workflow.steps if s.status == ApprovalStatus.APPROVED]
        rejected_steps = [s for s in workflow.steps if s.status == ApprovalStatus.REJECTED]
        
        return {
            "workflow_id": workflow.workflow_id,
            "voucher_number": workflow.voucher_number,
            "status": workflow.status.value,
            "progress": f"{workflow.current_step}/{workflow.total_steps}",
            "pending_steps": len(pending_steps),
            "completed_steps": len(completed_steps),
            "rejected_steps": len(rejected_steps),
            "escalation_reason": workflow.escalation_reason,
            "created_date": workflow.created_date.isoformat(),
            "completed_date": workflow.completed_date.isoformat() if workflow.completed_date else None
        }
    
    def get_next_approver(self, workflow: ApprovalWorkflow) -> Optional[str]:
        """Get the next approver in the workflow."""
        if workflow.current_step < len(workflow.steps):
            return workflow.steps[workflow.current_step].approver_role
        return None
