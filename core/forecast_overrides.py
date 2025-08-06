"""
Forecast Override System
Allows manual adjustments to pattern-detected forecasts for specific vendors and time periods.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from supabase_client import supabase
from .calendar_forecasting import ForecastEvent

logger = logging.getLogger(__name__)

@dataclass
class ForecastOverride:
    """Represents a manual override to a forecast."""
    id: Optional[str]
    client_id: str
    vendor_display_name: str
    override_date: datetime
    original_amount: float
    override_amount: float
    override_type: str  # 'amount_change', 'date_shift', 'skip_occurrence', 'add_occurrence'
    new_date: Optional[datetime] = None  # For date shifts
    reason: str = ""
    created_by: str = "system"
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'vendor_display_name': self.vendor_display_name,
            'override_date': self.override_date.isoformat() if self.override_date else None,
            'original_amount': self.original_amount,
            'override_amount': self.override_amount,
            'override_type': self.override_type,
            'new_date': self.new_date.isoformat() if self.new_date else None,
            'reason': self.reason,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.now(UTC).isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForecastOverride':
        return cls(
            id=data.get('id'),
            client_id=data['client_id'],
            vendor_display_name=data['vendor_display_name'],
            override_date=datetime.fromisoformat(data['override_date']) if data.get('override_date') else None,
            original_amount=float(data['original_amount']),
            override_amount=float(data['override_amount']),
            override_type=data['override_type'],
            new_date=datetime.fromisoformat(data['new_date']) if data.get('new_date') else None,
            reason=data.get('reason', ''),
            created_by=data.get('created_by', 'system'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )

class ForecastOverrideManager:
    """Manages forecast overrides and applies them to generated events."""
    
    def __init__(self):
        self.table_name = 'forecast_overrides'
    
    def create_override(self, override: ForecastOverride) -> bool:
        """Create a new forecast override."""
        try:
            # Ensure created_at is set
            if not override.created_at:
                override.created_at = datetime.now(UTC)
            
            result = supabase.table(self.table_name).insert(override.to_dict()).execute()
            
            if result.data:
                override.id = result.data[0]['id']
                logger.info(f"Created override for {override.vendor_display_name}: {override.override_type}")
                return True
            else:
                logger.error("Failed to create override - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error creating override: {e}")
            return False
    
    def get_overrides(self, client_id: str, start_date: datetime, end_date: datetime) -> List[ForecastOverride]:
        """Get all overrides for a client within a date range."""
        try:
            result = supabase.table(self.table_name).select('*').eq(
                'client_id', client_id
            ).gte(
                'override_date', start_date.isoformat()
            ).lte(
                'override_date', end_date.isoformat()
            ).execute()
            
            overrides = [ForecastOverride.from_dict(item) for item in result.data]
            logger.info(f"Retrieved {len(overrides)} overrides for {client_id}")
            return overrides
            
        except Exception as e:
            logger.error(f"Error getting overrides: {e}")
            return []
    
    def get_vendor_overrides(self, client_id: str, vendor_display_name: str, 
                           start_date: datetime, end_date: datetime) -> List[ForecastOverride]:
        """Get overrides for a specific vendor within a date range."""
        try:
            result = supabase.table(self.table_name).select('*').eq(
                'client_id', client_id
            ).eq(
                'vendor_display_name', vendor_display_name
            ).gte(
                'override_date', start_date.isoformat()
            ).lte(
                'override_date', end_date.isoformat()
            ).execute()
            
            return [ForecastOverride.from_dict(item) for item in result.data]
            
        except Exception as e:
            logger.error(f"Error getting vendor overrides: {e}")
            return []
    
    def delete_override(self, override_id: str) -> bool:
        """Delete a forecast override."""
        try:
            result = supabase.table(self.table_name).delete().eq('id', override_id).execute()
            logger.info(f"Deleted override {override_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting override {override_id}: {e}")
            return False
    
    def apply_overrides_to_events(self, events: List[ForecastEvent], 
                                client_id: str) -> List[ForecastEvent]:
        """Apply overrides to a list of forecast events."""
        if not events:
            return events
        
        # Get date range from events
        start_date = min(event.date for event in events)
        end_date = max(event.date for event in events)
        
        # Get all overrides for this period
        overrides = self.get_overrides(client_id, start_date, end_date)
        
        if not overrides:
            return events
        
        logger.info(f"Applying {len(overrides)} overrides to {len(events)} events")
        
        # Create override lookup by vendor and date
        override_lookup = {}
        for override in overrides:
            key = (override.vendor_display_name, override.override_date.date())
            override_lookup[key] = override
        
        modified_events = []
        
        for event in events:
            key = (event.vendor_display_name, event.date.date())
            
            if key in override_lookup:
                override = override_lookup[key]
                
                if override.override_type == 'amount_change':
                    # Change the amount
                    modified_event = ForecastEvent(
                        date=event.date,
                        vendor_display_name=event.vendor_display_name,
                        amount=override.override_amount,
                        event_type='override',
                        frequency=event.frequency,
                        confidence=event.confidence,
                        source='manual_override'
                    )
                    modified_events.append(modified_event)
                    logger.debug(f"Override: Changed {event.vendor_display_name} amount from ${event.amount} to ${override.override_amount}")
                    
                elif override.override_type == 'date_shift' and override.new_date:
                    # Move to new date
                    modified_event = ForecastEvent(
                        date=override.new_date,
                        vendor_display_name=event.vendor_display_name,
                        amount=event.amount,
                        event_type='override',
                        frequency=event.frequency,
                        confidence=event.confidence,
                        source='manual_override'
                    )
                    modified_events.append(modified_event)
                    logger.debug(f"Override: Moved {event.vendor_display_name} from {event.date.date()} to {override.new_date.date()}")
                    
                elif override.override_type == 'skip_occurrence':
                    # Skip this event entirely
                    logger.debug(f"Override: Skipped {event.vendor_display_name} on {event.date.date()}")
                    continue
            else:
                # No override, keep original event
                modified_events.append(event)
        
        # Add new occurrences from overrides
        for override in overrides:
            if override.override_type == 'add_occurrence':
                new_event = ForecastEvent(
                    date=override.override_date,
                    vendor_display_name=override.vendor_display_name,
                    amount=override.override_amount,
                    event_type='override',
                    frequency='one_time',
                    confidence=1.0,
                    source='manual_override'
                )
                modified_events.append(new_event)
                logger.debug(f"Override: Added new occurrence for {override.vendor_display_name} on {override.override_date.date()}")
        
        # Sort by date
        modified_events.sort(key=lambda x: x.date)
        
        logger.info(f"Applied overrides: {len(events)} -> {len(modified_events)} events")
        return modified_events
    
    def create_amount_override(self, client_id: str, vendor_display_name: str, 
                             target_date: datetime, new_amount: float, 
                             reason: str = "") -> bool:
        """Convenience method to create an amount change override."""
        override = ForecastOverride(
            id=None,
            client_id=client_id,
            vendor_display_name=vendor_display_name,
            override_date=target_date,
            original_amount=0.0,  # Will be filled when applied
            override_amount=new_amount,
            override_type='amount_change',
            reason=reason
        )
        return self.create_override(override)
    
    def create_date_shift_override(self, client_id: str, vendor_display_name: str,
                                 original_date: datetime, new_date: datetime,
                                 reason: str = "") -> bool:
        """Convenience method to create a date shift override."""
        override = ForecastOverride(
            id=None,
            client_id=client_id,
            vendor_display_name=vendor_display_name,
            override_date=original_date,
            original_amount=0.0,  # Will be filled when applied
            override_amount=0.0,
            override_type='date_shift',
            new_date=new_date,
            reason=reason
        )
        return self.create_override(override)
    
    def create_skip_override(self, client_id: str, vendor_display_name: str,
                           target_date: datetime, reason: str = "") -> bool:
        """Convenience method to skip an occurrence."""
        override = ForecastOverride(
            id=None,
            client_id=client_id,
            vendor_display_name=vendor_display_name,
            override_date=target_date,
            original_amount=0.0,
            override_amount=0.0,
            override_type='skip_occurrence',
            reason=reason
        )
        return self.create_override(override)