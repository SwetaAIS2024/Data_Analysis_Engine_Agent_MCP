"""
User Intent / Context Extraction Layer
Extracts structured metadata from user prompt and data:
- Goal: What the user wants to achieve
- Constraints: Limitations, thresholds, requirements
- Data Type: Tabular, timeseries, geospatial, etc.
- Parameters: Specific values for tool execution
"""
import re
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    """Extraction approach selection"""
    RULE_BASED = "rule_based"
    REGEX = "regex"
    ML = "ml"
    HYBRID = "hybrid"


class ContextExtractor:
    """
    User Intent/Context Extraction Layer
    
    Input: User prompt + Data
    Output: Structured metadata with goal, constraints, data_type, parameters
    
    Example Output:
    {
        "goal": "anomaly_detection",
        "constraints": {
            "threshold": 2.5,
            "max_anomalies": 100
        },
        "data_type": "timeseries",
        "data_characteristics": {
            "row_count": 1000,
            "columns": ["timestamp", "value"],
            "has_nulls": false
        },
        "parameters": {
            "metric": "speed_kmh",
            "timestamp_field": "timestamp"
        }
    }
    """
    
    def __init__(self, method: ExtractionMethod = ExtractionMethod.HYBRID):
        self.method = method
        self._init_extractors()
        logger.info(f"ContextExtractor initialized with method: {method.value}")
    
    def _init_extractors(self):
        """Initialize extraction components"""
        self.goal_patterns = self._load_goal_patterns()
        self.regex_patterns = self._load_regex_patterns()
        self.data_type_indicators = self._load_data_type_indicators()
        self.constraint_patterns = self._load_constraint_patterns()
    
    def _load_goal_patterns(self) -> Dict[str, List[str]]:
        """Goal patterns for identifying user objectives"""
        return {
            "anomaly_detection": [
                "detect anomalies", "find outliers", "identify unusual",
                "spot anomalies", "anomaly detection", "outlier detection"
            ],
            "clustering": [
                "cluster", "group data", "segment", "clustering",
                "find patterns", "group similar"
            ],
            "feature_engineering": [
                "engineer features", "create features", "feature extraction",
                "transform data", "generate features"
            ],
            "timeseries_forecasting": [
                "forecast", "predict future", "prediction",
                "trend analysis", "time series forecast"
            ],
            "classification": [
                "classify", "classification", "categorize", "predict class"
            ],
            "regression": [
                "regression", "predict value", "estimate", "predict number"
            ],
            "stats_comparison": [
                "compare", "comparison", "a/b test", "statistical test"
            ],
            "geospatial_analysis": [
                "geospatial", "map", "location", "spatial analysis"
            ]
        }
    
    def _load_regex_patterns(self) -> Dict[str, str]:
        """Regex patterns for parameter extraction"""
        return {
            "threshold": r"threshold\s+(?:of\s+)?(\d+\.?\d*)",
            "max_limit": r"max(?:imum)?\s+(?:of\s+)?(\d+)",
            "min_limit": r"min(?:imum)?\s+(?:of\s+)?(\d+)",
            "metric": r"metric[s]?\s+['\"]?(\w+)['\"]?",
            "column": r"column[s]?\s+['\"]?(\w+)['\"]?",
            "window": r"window\s+(?:of\s+)?(\d+\s*(?:min|minute|hour|day|week|month)s?)",
            "confidence": r"confidence\s+(?:of\s+)?(\d+\.?\d*)",
            "n_clusters": r"(\d+)\s+clusters?",
            "algorithm": r"(?:using|with|algorithm)\s+(\w+)",
        }
    
    def _load_data_type_indicators(self) -> Dict[str, List[str]]:
        """Indicators for data type detection"""
        return {
            "timeseries": ["timestamp", "time", "date", "datetime", "forecast", "trend"],
            "tabular": ["table", "row", "column", "csv", "dataframe"],
            "geospatial": ["location", "lat", "lon", "latitude", "longitude", "map", "geo"],
            "text": ["text", "document", "corpus", "nlp", "sentiment"],
            "image": ["image", "picture", "photo", "visual", "cv"],
            "graph": ["graph", "network", "node", "edge", "relationship"]
        }
    
    def _load_constraint_patterns(self) -> Dict[str, str]:
        """Patterns for constraint extraction"""
        return {
            "max_time": r"(?:within|in)\s+(\d+)\s*(second|minute|hour|day)s?",
            "min_accuracy": r"(?:at least|minimum)\s+(\d+\.?\d*)%?\s*accuracy",
            "max_memory": r"(?:up to|maximum)\s+(\d+)\s*(MB|GB)",
        }
    
    def extract(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured metadata from user prompt and data
        
        Args:
            user_prompt: User's natural language prompt
            data_info: Information about the data (optional)
                      e.g., {"rows": [...], "columns": [...], "size": 1000}
        
        Returns:
            Structured metadata dictionary with:
            - goal: Primary objective
            - constraints: Limitations and requirements
            - data_type: Type of data
            - data_characteristics: Info about the data
            - parameters: Specific values for tools
            - user_preferences: Output format, visualization, etc.
        """
        logger.info(f"Extracting context from prompt: {user_prompt[:100]}...")
        
        if self.method == ExtractionMethod.RULE_BASED:
            result = self._rule_based_extraction(user_prompt, data_info)
        elif self.method == ExtractionMethod.REGEX:
            result = self._regex_extraction(user_prompt, data_info)
        elif self.method == ExtractionMethod.ML:
            result = self._ml_extraction(user_prompt, data_info)
        else:  # HYBRID
            result = self._hybrid_extraction(user_prompt, data_info)
        
        logger.info(f"Extracted goal: {result['goal']}, data_type: {result['data_type']}")
        return result
    
    def _rule_based_extraction(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Rule-based extraction using keyword matching"""
        prompt_lower = user_prompt.lower()
        
        # Extract goal
        goal = "unknown"
        goal_scores = {}
        for goal_name, patterns in self.goal_patterns.items():
            score = sum(1 for pattern in patterns if pattern in prompt_lower)
            if score > 0:
                goal_scores[goal_name] = score
        
        if goal_scores:
            goal = max(goal_scores.items(), key=lambda x: x[1])[0]
        
        # Extract constraints
        constraints = self._extract_constraints(user_prompt)
        
        # Extract parameters
        parameters = self._extract_parameters(user_prompt)
        
        # Detect data type
        data_type = self._detect_data_type(user_prompt, data_info)
        
        # Analyze data characteristics
        data_characteristics = self._analyze_data(data_info)
        
        return {
            "goal": goal,
            "constraints": constraints,
            "data_type": data_type,
            "data_characteristics": data_characteristics,
            "parameters": parameters,
            "user_preferences": self._extract_preferences(user_prompt),
            "extraction_method": "rule_based",
            "confidence": min(goal_scores.get(goal, 0) / 3.0, 1.0) if goal_scores else 0.0
        }
    
    def _regex_extraction(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Regex-based extraction"""
        parameters = self._extract_parameters(user_prompt)
        constraints = self._extract_constraints(user_prompt)
        goal = self._simple_goal_detection(user_prompt)
        data_type = self._detect_data_type(user_prompt, data_info)
        
        return {
            "goal": goal,
            "constraints": constraints,
            "data_type": data_type,
            "data_characteristics": self._analyze_data(data_info),
            "parameters": parameters,
            "user_preferences": self._extract_preferences(user_prompt),
            "extraction_method": "regex",
            "confidence": 0.7 if goal != "unknown" else 0.0
        }
    
    def _ml_extraction(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """ML-based extraction (placeholder for actual ML model)"""
        # TODO: Implement ML model (BERT, NER, etc.)
        result = self._rule_based_extraction(user_prompt, data_info)
        result["extraction_method"] = "ml_fallback"
        return result
    
    def _hybrid_extraction(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Hybrid: Combine rule-based and regex"""
        rule_result = self._rule_based_extraction(user_prompt, data_info)
        regex_result = self._regex_extraction(user_prompt, data_info)
        
        # Merge results (prefer rule-based for goal, merge parameters)
        return {
            "goal": rule_result["goal"],
            "constraints": {**rule_result["constraints"], **regex_result["constraints"]},
            "data_type": rule_result["data_type"],
            "data_characteristics": rule_result["data_characteristics"],
            "parameters": {**rule_result["parameters"], **regex_result["parameters"]},
            "user_preferences": rule_result["user_preferences"],
            "extraction_method": "hybrid",
            "confidence": (rule_result["confidence"] + regex_result["confidence"]) / 2
        }
    
    def _extract_constraints(self, text: str) -> Dict[str, Any]:
        """Extract constraints from text"""
        constraints = {}
        
        for constraint_type, pattern in self.constraint_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                constraints[constraint_type] = match.group(1)
        
        # Extract threshold constraints
        for param_name in ["threshold", "max_limit", "min_limit", "confidence"]:
            if param_name in self.regex_patterns:
                match = re.search(self.regex_patterns[param_name], text, re.IGNORECASE)
                if match:
                    try:
                        constraints[param_name] = float(match.group(1))
                    except ValueError:
                        constraints[param_name] = match.group(1)
        
        return constraints
    
    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract parameters using regex"""
        parameters = {}
        
        for param_name, pattern in self.regex_patterns.items():
            if param_name in ["threshold", "max_limit", "min_limit", "confidence"]:
                continue  # These are constraints
            
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                # Convert numeric values
                if param_name == "n_clusters":
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                parameters[param_name] = value
        
        return parameters
    
    def _detect_data_type(
        self,
        text: str,
        data_info: Optional[Dict[str, Any]]
    ) -> str:
        """Detect data type from text and data info"""
        text_lower = text.lower()
        
        # Check data_info first
        if data_info:
            columns = data_info.get("columns", [])
            if any("time" in str(col).lower() or "date" in str(col).lower() for col in columns):
                return "timeseries"
            if any("lat" in str(col).lower() or "lon" in str(col).lower() for col in columns):
                return "geospatial"
        
        # Check text for indicators
        scores = {}
        for data_type, indicators in self.data_type_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score > 0:
                scores[data_type] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return "tabular"  # Default
    
    def _analyze_data(self, data_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data characteristics"""
        if not data_info:
            return {}
        
        characteristics = {}
        
        if "rows" in data_info:
            if isinstance(data_info["rows"], list):
                characteristics["row_count"] = len(data_info["rows"])
                if data_info["rows"]:
                    characteristics["columns"] = list(data_info["rows"][0].keys())
            elif isinstance(data_info["rows"], int):
                characteristics["row_count"] = data_info["rows"]
        
        if "columns" in data_info:
            characteristics["columns"] = data_info["columns"]
        
        if "size" in data_info:
            characteristics["size_bytes"] = data_info["size"]
        
        if "has_nulls" in data_info:
            characteristics["has_nulls"] = data_info["has_nulls"]
        
        return characteristics
    
    def _extract_preferences(self, text: str) -> Dict[str, Any]:
        """Extract user preferences"""
        preferences = {}
        
        text_lower = text.lower()
        
        if "json" in text_lower or "api" in text_lower:
            preferences["output_format"] = "json"
        elif "csv" in text_lower:
            preferences["output_format"] = "csv"
        else:
            preferences["output_format"] = "json"  # Default
        
        if "visualize" in text_lower or "chart" in text_lower or "plot" in text_lower:
            preferences["visualization"] = True
        else:
            preferences["visualization"] = False
        
        return preferences
    
    def _simple_goal_detection(self, text: str) -> str:
        """Simple keyword-based goal detection"""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ["anomaly", "outlier", "unusual"]):
            return "anomaly_detection"
        elif any(kw in text_lower for kw in ["cluster", "group", "segment"]):
            return "clustering"
        elif any(kw in text_lower for kw in ["forecast", "predict future"]):
            return "timeseries_forecasting"
        elif any(kw in text_lower for kw in ["classify", "classification"]):
            return "classification"
        elif any(kw in text_lower for kw in ["feature", "engineer"]):
            return "feature_engineering"
        elif any(kw in text_lower for kw in ["geospatial", "map", "location"]):
            return "geospatial_analysis"
        elif any(kw in text_lower for kw in ["compare", "comparison"]):
            return "stats_comparison"
        elif any(kw in text_lower for kw in ["regression", "estimate"]):
            return "regression"
        else:
            return "unknown"


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== Context Extraction Examples ===\n")
    
    extractor = ContextExtractor(method=ExtractionMethod.HYBRID)
    
    # Example 1: Anomaly detection with constraints
    print("1. Anomaly Detection with Constraints:")
    result1 = extractor.extract(
        user_prompt="Detect anomalies in speed_kmh with threshold 2.5, maximum 100 anomalies",
        data_info={"columns": ["timestamp", "speed_kmh", "sensor_id"], "rows": 1000}
    )
    print(json.dumps(result1, indent=2))
    print()
    
    # Example 2: Clustering timeseries data
    print("2. Clustering Timeseries Data:")
    result2 = extractor.extract(
        user_prompt="Cluster sensor data into 4 groups using kmeans algorithm with 5 minute window",
        data_info={"columns": ["timestamp", "value"], "rows": [{"timestamp": "2025-01-01", "value": 10}] * 500}
    )
    print(json.dumps(result2, indent=2))
