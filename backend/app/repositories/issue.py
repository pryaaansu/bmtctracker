from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc
from datetime import datetime

from .base import BaseRepository
from ..models.issue import Issue, IssueStatus, IssueCategory, IssuePriority
from ..schemas.driver import IssueReport

class IssueRepository(BaseRepository[Issue]):
    def __init__(self, db: Session):
        super().__init__(Issue, db)

    def create_issue(self, issue_data: IssueReport, driver_id: int) -> Issue:
        """Create a new issue report"""
        issue = Issue(
            category=issue_data.category,
            priority=issue_data.priority,
            title=issue_data.title,
            description=issue_data.description,
            location_lat=issue_data.location_lat,
            location_lng=issue_data.location_lng,
            vehicle_id=issue_data.vehicle_id,
            route_id=issue_data.route_id,
            reported_by=driver_id,
            status=IssueStatus.OPEN
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def get_driver_issues(self, driver_id: int, limit: int = 50) -> List[Issue]:
        """Get all issues reported by a driver"""
        return self.db.query(Issue).options(
            joinedload(Issue.vehicle),
            joinedload(Issue.route)
        ).filter(
            Issue.reported_by == driver_id
        ).order_by(desc(Issue.created_at)).limit(limit).all()

    def get_open_issues(self, driver_id: Optional[int] = None) -> List[Issue]:
        """Get all open issues, optionally filtered by driver"""
        query = self.db.query(Issue).options(
            joinedload(Issue.vehicle),
            joinedload(Issue.route),
            joinedload(Issue.reporter)
        ).filter(Issue.status == IssueStatus.OPEN)
        
        if driver_id:
            query = query.filter(Issue.reported_by == driver_id)
        
        return query.order_by(desc(Issue.created_at)).all()

    def resolve_issue(self, issue_id: int, resolver_id: int) -> Optional[Issue]:
        """Mark an issue as resolved"""
        issue = self.get(issue_id)
        if issue:
            issue.status = IssueStatus.RESOLVED
            issue.resolved_at = datetime.utcnow()
            issue.resolved_by = resolver_id
            self.db.commit()
            self.db.refresh(issue)
        return issue

    def get_issues_by_category(self, category: IssueCategory, limit: int = 100) -> List[Issue]:
        """Get issues by category"""
        return self.db.query(Issue).filter(
            Issue.category == category
        ).order_by(desc(Issue.created_at)).limit(limit).all()

    def get_critical_issues(self) -> List[Issue]:
        """Get all critical priority issues"""
        return self.db.query(Issue).options(
            joinedload(Issue.vehicle),
            joinedload(Issue.route),
            joinedload(Issue.reporter)
        ).filter(
            and_(
                Issue.priority == IssuePriority.CRITICAL,
                Issue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS])
            )
        ).order_by(desc(Issue.created_at)).all()