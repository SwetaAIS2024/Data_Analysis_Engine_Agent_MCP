"""
Timeline Tracking & Observability Module
Tracks execution timeline for multi-person teams (2-person collaboration)
Provides rough estimates and example frameworks for each block
"""
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskEvent:
    """Single event in task execution"""
    task_id: str
    task_name: str
    status: TaskStatus
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Timeline:
    """Execution timeline for a request"""
    request_id: str
    start_time: float
    events: List[TaskEvent] = field(default_factory=list)
    end_time: Optional[float] = None
    
    def add_event(self, event: TaskEvent):
        """Add event to timeline"""
        self.events.append(event)
    
    def complete(self):
        """Mark timeline as complete"""
        self.end_time = time.time()
    
    def get_duration(self) -> float:
        """Get total duration in seconds"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "request_id": self.request_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration(),
            "events": [
                {
                    "task_id": e.task_id,
                    "task_name": e.task_name,
                    "status": e.status.value,
                    "timestamp": datetime.fromtimestamp(e.timestamp).isoformat(),
                    "metadata": e.metadata
                }
                for e in self.events
            ]
        }


class TimelineTracker:
    """
    Timeline Tracker for Multi-Person Teams
    
    Tracks execution progress for collaborative work:
    - Person 1: User input -> Intent extraction -> Planning
    - Person 2: Tool execution -> Result aggregation -> Response
    
    Example Usage:
        tracker = TimelineTracker()
        timeline = tracker.start_request("req-123")
        tracker.log_task_start(timeline, "intent_extraction", "Extracting user intent")
        # ... work happens ...
        tracker.log_task_complete(timeline, "intent_extraction", metadata={"method": "hybrid"})
    """
    
    def __init__(self):
        self.active_timelines: Dict[str, Timeline] = {}
        self.completed_timelines: List[Timeline] = []
        
        # Rough time estimates for each component (in seconds)
        self.component_estimates = {
            "intent_extraction": {"min": 0.1, "avg": 0.5, "max": 2.0},
            "planning": {"min": 0.2, "avg": 1.0, "max": 3.0},
            "tool_invocation": {"min": 1.0, "avg": 3.0, "max": 10.0},
            "result_aggregation": {"min": 0.1, "avg": 0.5, "max": 2.0},
        }
    
    def start_request(self, request_id: str) -> Timeline:
        """Start tracking a new request"""
        timeline = Timeline(
            request_id=request_id,
            start_time=time.time()
        )
        self.active_timelines[request_id] = timeline
        return timeline
    
    def log_task_start(
        self,
        timeline: Timeline,
        task_id: str,
        task_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log task start event"""
        event = TaskEvent(
            task_id=task_id,
            task_name=task_name,
            status=TaskStatus.IN_PROGRESS,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        timeline.add_event(event)
    
    def log_task_complete(
        self,
        timeline: Timeline,
        task_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log task completion event"""
        # Find the corresponding start event
        task_name = None
        for event in timeline.events:
            if event.task_id == task_id and event.status == TaskStatus.IN_PROGRESS:
                task_name = event.task_name
                break
        
        if not task_name:
            task_name = task_id
        
        event = TaskEvent(
            task_id=task_id,
            task_name=task_name,
            status=TaskStatus.COMPLETED,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        timeline.add_event(event)
    
    def log_task_failed(
        self,
        timeline: Timeline,
        task_id: str,
        error: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log task failure event"""
        task_name = None
        for event in timeline.events:
            if event.task_id == task_id:
                task_name = event.task_name
                break
        
        if not task_name:
            task_name = task_id
        
        meta = metadata or {}
        meta["error"] = error
        
        event = TaskEvent(
            task_id=task_id,
            task_name=task_name,
            status=TaskStatus.FAILED,
            timestamp=time.time(),
            metadata=meta
        )
        timeline.add_event(event)
    
    def complete_request(self, request_id: str) -> Timeline:
        """Mark request as complete and move to history"""
        timeline = self.active_timelines.pop(request_id, None)
        if timeline:
            timeline.complete()
            self.completed_timelines.append(timeline)
        return timeline
    
    def get_timeline(self, request_id: str) -> Optional[Timeline]:
        """Get timeline for a request"""
        return self.active_timelines.get(request_id) or \
               next((t for t in self.completed_timelines if t.request_id == request_id), None)
    
    def get_estimate(self, component: str) -> Dict[str, float]:
        """Get time estimate for a component"""
        return self.component_estimates.get(component, {"min": 0.5, "avg": 2.0, "max": 5.0})
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics from completed timelines"""
        if not self.completed_timelines:
            return {
                "total_requests": 0,
                "avg_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0
            }
        
        durations = [t.get_duration() for t in self.completed_timelines]
        
        return {
            "total_requests": len(self.completed_timelines),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "active_requests": len(self.active_timelines)
        }


# Framework examples for each block
FRAMEWORK_EXAMPLES = {
    "user_input": {
        "description": "User VP (Voice/Text interface, max 500 words)",
        "examples": [
            "Detect anomalies in sensor data with threshold 2.5",
            "Cluster customer segments into 4 groups based on behavior",
            "First engineer features from raw data, then predict churn probability"
        ],
        "rough_timeline": "0-2 seconds (user typing/speaking)",
        "owner": "Person 1 (User interaction)"
    },
    "intent_extraction": {
        "description": "Extract intent and entities using RLB/Regex/ML/Hybrid",
        "methods": ["Rule-based (RLB)", "Regex", "ML (BERT/NER)", "Hybrid"],
        "examples": [
            "Input: 'detect anomalies with zscore 2.5' -> Intent: anomaly_detection, Entities: {threshold: 2.5}",
            "Input: 'cluster into 3 groups' -> Intent: clustering, Entities: {n_clusters: 3}"
        ],
        "rough_timeline": "0.1-2 seconds",
        "owner": "Person 1 (AI/ML Engineer)"
    },
    "planning": {
        "description": "LLM-based planning with 50-word limit",
        "strategies": ["Unified (sequential)", "Parallel", "Conditional"],
        "examples": [
            "Single task: anomaly_detection -> Execute sequentially",
            "Multi-task: feature_engineering -> clustering -> Execute sequentially with dependency",
            "Independent tasks: anomaly_detection + stats_comparison -> Execute in parallel"
        ],
        "rough_timeline": "0.2-3 seconds (50 words max for LLM)",
        "owner": "Person 1 (AI/ML Engineer)"
    },
    "tool_invocation": {
        "description": "Dispatcher executes tools based on plan",
        "execution_modes": ["Sequential", "Parallel", "Conditional"],
        "examples": [
            "Sequential: Task 1 (anomaly_detection) -> Task 2 (incident_detection based on anomalies)",
            "Parallel: Task 1 (anomaly_detection) || Task 2 (clustering) || Task 3 (stats_comparison)"
        ],
        "rough_timeline": "1-10 seconds per tool (depends on data size and complexity)",
        "owner": "Person 2 (Backend Engineer)"
    },
    "if_tools": {
        "description": "Conditional tool execution based on results",
        "examples": [
            "If anomalies found -> trigger incident_detector",
            "If no clusters found -> suggest feature engineering",
            "If accuracy < threshold -> recommend more data"
        ],
        "rough_timeline": "0.1-1 second (decision logic)",
        "owner": "Person 2 (Backend Engineer)"
    },
    "result_aggregation": {
        "description": "Combine results from multiple tools",
        "examples": [
            "Merge anomaly detection + clustering results into unified view",
            "Aggregate statistics from parallel tool executions",
            "Format results for user-friendly display"
        ],
        "rough_timeline": "0.1-2 seconds",
        "owner": "Person 2 (Backend Engineer)"
    }
}


# Example usage
if __name__ == "__main__":
    print("=== Timeline Tracking Example ===\n")
    
    tracker = TimelineTracker()
    
    # Start tracking a request
    timeline = tracker.start_request("req-12345")
    
    # Simulate workflow
    print("1. User Input (Person 1)")
    time.sleep(0.1)
    
    print("2. Intent Extraction (Person 1)")
    tracker.log_task_start(timeline, "intent-1", "Intent Extraction", {"method": "hybrid"})
    time.sleep(0.5)  # Simulate processing
    tracker.log_task_complete(timeline, "intent-1", {"intent": "anomaly_detection", "confidence": 0.9})
    
    print("3. Planning (Person 1)")
    tracker.log_task_start(timeline, "plan-1", "Planning & Decision Making", {"llm_prompt_words": 45})
    time.sleep(1.0)  # Simulate LLM call
    tracker.log_task_complete(timeline, "plan-1", {"tasks": 2, "strategy": "sequential"})
    
    print("4. Tool Invocation (Person 2)")
    tracker.log_task_start(timeline, "tool-1", "Anomaly Detection Tool")
    time.sleep(2.0)  # Simulate tool execution
    tracker.log_task_complete(timeline, "tool-1", {"anomalies_found": 15})
    
    tracker.log_task_start(timeline, "tool-2", "Incident Detection Tool")
    time.sleep(1.5)  # Simulate tool execution
    tracker.log_task_complete(timeline, "tool-2", {"incidents": 3})
    
    print("5. Result Aggregation (Person 2)")
    tracker.log_task_start(timeline, "agg-1", "Result Aggregation")
    time.sleep(0.3)  # Simulate aggregation
    tracker.log_task_complete(timeline, "agg-1", {"combined_results": True})
    
    # Complete request
    timeline = tracker.complete_request("req-12345")
    
    print(f"\n=== Timeline Summary ===")
    print(f"Request ID: {timeline.request_id}")
    print(f"Total Duration: {timeline.get_duration():.2f} seconds")
    print(f"Total Events: {len(timeline.events)}")
    
    print(f"\n=== Event Details ===")
    for event in timeline.events:
        print(f"  [{event.status.value}] {event.task_name} at {datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S.%f')[:-3]}")
        if event.metadata:
            print(f"      Metadata: {event.metadata}")
    
    print(f"\n=== Framework Examples ===")
    for block, info in FRAMEWORK_EXAMPLES.items():
        print(f"\n{block.upper().replace('_', ' ')}:")
        print(f"  Description: {info['description']}")
        print(f"  Timeline: {info['rough_timeline']}")
        print(f"  Owner: {info['owner']}")
