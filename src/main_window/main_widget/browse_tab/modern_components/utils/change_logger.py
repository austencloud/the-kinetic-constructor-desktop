"""
Modernization Change Logger - Track all modernization changes and performance impact

MODERNIZATION LOG:
- Date: 2025-01-27
- Changes Made: Created comprehensive logging system for tracking modernization progress
- Performance Impact: Minimal overhead, helps track performance improvements
- Breaking Changes: None (new component)
- Migration Notes: Use this to log all modernization activities
- Visual Changes: Provides detailed logging for all UI changes
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class ModernizationLogger:
    """
    Comprehensive logging system for tracking modernization changes.
    
    Features:
    - Component update tracking
    - Performance impact measurement
    - User interaction analytics
    - Visual change documentation
    - Migration assistance
    - Rollback support information
    """
    
    def __init__(self, log_file_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set up log file path
        if log_file_path is None:
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file_path = log_dir / f"modernization_{datetime.now().strftime('%Y%m%d')}.json"
        
        self.log_file_path = Path(log_file_path)
        self.session_start = datetime.now()
        self.performance_metrics = {}
        self.component_changes = {}
        self.user_interactions = []
        
        self.logger.info(f"📊 ModernizationLogger initialized - Log file: {self.log_file_path}")
    
    def log_component_update(self, 
                           component_name: str, 
                           changes_made: List[str],
                           old_version: str = "legacy",
                           new_version: str = "modern_2025",
                           breaking_changes: List[str] = None,
                           migration_notes: List[str] = None) -> None:
        """
        Log component modernization updates.
        
        Args:
            component_name: Name of the component being updated
            changes_made: List of changes made to the component
            old_version: Previous version identifier
            new_version: New version identifier
            breaking_changes: List of breaking changes (if any)
            migration_notes: Notes for migrating to new version
        """
        timestamp = datetime.now().isoformat()
        
        change_record = {
            "timestamp": timestamp,
            "component": component_name,
            "old_version": old_version,
            "new_version": new_version,
            "changes_made": changes_made,
            "breaking_changes": breaking_changes or [],
            "migration_notes": migration_notes or [],
            "session_id": id(self)
        }
        
        self.component_changes[component_name] = change_record
        
        self.logger.info(f"🔄 Component updated: {component_name}")
        self.logger.debug(f"Changes: {', '.join(changes_made)}")
        
        self._save_to_file()
    
    def log_performance_impact(self, 
                             operation: str, 
                             time_taken: float,
                             before_metrics: Dict[str, Any] = None,
                             after_metrics: Dict[str, Any] = None,
                             improvement_percentage: float = None) -> None:
        """
        Track performance impact of modernization changes.
        
        Args:
            operation: Name of the operation being measured
            time_taken: Time taken for the operation (in seconds)
            before_metrics: Performance metrics before change
            after_metrics: Performance metrics after change
            improvement_percentage: Calculated improvement percentage
        """
        timestamp = datetime.now().isoformat()
        
        perf_record = {
            "timestamp": timestamp,
            "operation": operation,
            "time_taken_seconds": time_taken,
            "time_taken_ms": time_taken * 1000,
            "before_metrics": before_metrics or {},
            "after_metrics": after_metrics or {},
            "improvement_percentage": improvement_percentage,
            "session_id": id(self)
        }
        
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = []
        
        self.performance_metrics[operation].append(perf_record)
        
        self.logger.info(f"⚡ Performance logged: {operation} - {time_taken*1000:.2f}ms")
        if improvement_percentage:
            self.logger.info(f"📈 Performance improvement: {improvement_percentage:.1f}%")
        
        self._save_to_file()
    
    def log_user_interaction(self, 
                           interaction_type: str, 
                           component: str,
                           details: Dict[str, Any] = None,
                           success: bool = True) -> None:
        """
        Track user interactions with modernized components.
        
        Args:
            interaction_type: Type of interaction (hover, click, scroll, etc.)
            component: Component being interacted with
            details: Additional interaction details
            success: Whether the interaction was successful
        """
        timestamp = datetime.now().isoformat()
        
        interaction_record = {
            "timestamp": timestamp,
            "interaction_type": interaction_type,
            "component": component,
            "details": details or {},
            "success": success,
            "session_id": id(self)
        }
        
        self.user_interactions.append(interaction_record)
        
        self.logger.debug(f"👆 User interaction: {interaction_type} on {component}")
        
        # Save periodically (every 10 interactions)
        if len(self.user_interactions) % 10 == 0:
            self._save_to_file()
    
    def log_visual_change(self, 
                         component: str, 
                         change_description: str,
                         before_screenshot: str = None,
                         after_screenshot: str = None,
                         css_changes: List[str] = None) -> None:
        """
        Log visual changes for documentation and rollback purposes.
        
        Args:
            component: Component with visual changes
            change_description: Description of the visual change
            before_screenshot: Path to before screenshot (optional)
            after_screenshot: Path to after screenshot (optional)
            css_changes: List of CSS changes made
        """
        timestamp = datetime.now().isoformat()
        
        visual_record = {
            "timestamp": timestamp,
            "component": component,
            "description": change_description,
            "before_screenshot": before_screenshot,
            "after_screenshot": after_screenshot,
            "css_changes": css_changes or [],
            "session_id": id(self)
        }
        
        # Add to component changes if it exists
        if component in self.component_changes:
            if "visual_changes" not in self.component_changes[component]:
                self.component_changes[component]["visual_changes"] = []
            self.component_changes[component]["visual_changes"].append(visual_record)
        
        self.logger.info(f"🎨 Visual change logged: {component} - {change_description}")
        
        self._save_to_file()
    
    def start_performance_timer(self, operation: str) -> str:
        """
        Start a performance timer for an operation.
        
        Args:
            operation: Name of the operation to time
            
        Returns:
            Timer ID for stopping the timer
        """
        timer_id = f"{operation}_{int(time.time() * 1000)}"
        self.performance_metrics[timer_id] = {
            "operation": operation,
            "start_time": time.time(),
            "timer_id": timer_id
        }
        
        self.logger.debug(f"⏱️ Performance timer started: {operation}")
        return timer_id
    
    def stop_performance_timer(self, timer_id: str, 
                             additional_metrics: Dict[str, Any] = None) -> float:
        """
        Stop a performance timer and log the result.
        
        Args:
            timer_id: Timer ID returned from start_performance_timer
            additional_metrics: Additional metrics to include
            
        Returns:
            Time taken in seconds
        """
        if timer_id not in self.performance_metrics:
            self.logger.warning(f"Timer ID not found: {timer_id}")
            return 0.0
        
        timer_data = self.performance_metrics[timer_id]
        end_time = time.time()
        time_taken = end_time - timer_data["start_time"]
        
        operation = timer_data["operation"]
        
        # Log the performance
        self.log_performance_impact(
            operation=operation,
            time_taken=time_taken,
            after_metrics=additional_metrics
        )
        
        # Clean up timer data
        del self.performance_metrics[timer_id]
        
        return time_taken
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary report of all modernization activities.
        
        Returns:
            Dictionary containing summary statistics and insights
        """
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        summary = {
            "session_info": {
                "start_time": self.session_start.isoformat(),
                "duration_seconds": session_duration,
                "session_id": id(self)
            },
            "components_updated": len(self.component_changes),
            "performance_operations": len(self.performance_metrics),
            "user_interactions": len(self.user_interactions),
            "component_details": list(self.component_changes.keys()),
            "performance_summary": self._calculate_performance_summary(),
            "interaction_summary": self._calculate_interaction_summary()
        }
        
        self.logger.info(f"📋 Generated summary report - {summary['components_updated']} components updated")
        return summary
    
    def _calculate_performance_summary(self) -> Dict[str, Any]:
        """Calculate performance summary statistics."""
        if not self.performance_metrics:
            return {"total_operations": 0}
        
        all_times = []
        operations = {}
        
        for operation, records in self.performance_metrics.items():
            if isinstance(records, list):
                for record in records:
                    time_taken = record.get("time_taken_seconds", 0)
                    all_times.append(time_taken)
                    
                    op_name = record.get("operation", operation)
                    if op_name not in operations:
                        operations[op_name] = []
                    operations[op_name].append(time_taken)
        
        if not all_times:
            return {"total_operations": 0}
        
        return {
            "total_operations": len(all_times),
            "average_time_ms": (sum(all_times) / len(all_times)) * 1000,
            "fastest_operation_ms": min(all_times) * 1000,
            "slowest_operation_ms": max(all_times) * 1000,
            "operations_breakdown": {
                op: {
                    "count": len(times),
                    "average_ms": (sum(times) / len(times)) * 1000
                }
                for op, times in operations.items()
            }
        }
    
    def _calculate_interaction_summary(self) -> Dict[str, Any]:
        """Calculate user interaction summary statistics."""
        if not self.user_interactions:
            return {"total_interactions": 0}
        
        interaction_types = {}
        components = {}
        success_count = 0
        
        for interaction in self.user_interactions:
            # Count by interaction type
            int_type = interaction.get("interaction_type", "unknown")
            interaction_types[int_type] = interaction_types.get(int_type, 0) + 1
            
            # Count by component
            component = interaction.get("component", "unknown")
            components[component] = components.get(component, 0) + 1
            
            # Count successes
            if interaction.get("success", True):
                success_count += 1
        
        total = len(self.user_interactions)
        
        return {
            "total_interactions": total,
            "success_rate": (success_count / total) * 100 if total > 0 else 0,
            "interaction_types": interaction_types,
            "components_interacted": components,
            "most_used_component": max(components.items(), key=lambda x: x[1])[0] if components else None
        }
    
    def _save_to_file(self) -> None:
        """Save current state to JSON file."""
        try:
            data = {
                "session_info": {
                    "start_time": self.session_start.isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "session_id": id(self)
                },
                "component_changes": self.component_changes,
                "performance_metrics": self.performance_metrics,
                "user_interactions": self.user_interactions
            }
            
            with open(self.log_file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save log file: {e}")


# Global instance for easy access
modernization_logger = ModernizationLogger()
