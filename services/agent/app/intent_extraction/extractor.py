"""
User Intent / Context Extraction Layer
Extracts structured metadata from user prompt and data:
- Goal: What the user wants to achieve
- Constraints: Limitations, thresholds, requirements
- Data Type: Tabular, timeseries, geospatial, etc.
- Parameters: Specific values for tool execution
Supports: Rule-based, Regex, ML, and Hybrid extraction
"""
import re
from typing import Dict, Any, List, Optional
from enum import Enum
import json


class ExtractionMethod(Enum):
    """Extraction approach selection"""
    RULE_BASED = "rule_based"  # RLB - Pattern matching
    REGEX = "regex"  # Regular expressions
    ML = "ml"  # Machine Learning (examples: BERT, NER)
    HYBRID = "hybrid"  # Combination of methods


class ContextExtractor:
    """
    Unified intent and entity extractor supporting multiple approaches:
    - Rule-based (RLB): Pattern matching with predefined rules
    - Regex: Regular expression-based extraction for entities
    - ML: Machine learning models (BERT, custom classifiers, NER)
    - Hybrid: Combination of multiple methods for better accuracy
    
    Example Usage:
        # Rule-based extraction
        extractor = IntentExtractor(method=ExtractionMethod.RULE_BASED)
        result = extractor.extract("Detect anomalies in speed_kmh with threshold 2.5")
        
        # Hybrid extraction (recommended)
        extractor = IntentExtractor(method=ExtractionMethod.HYBRID)
        result = extractor.extract("Find outliers and cluster similar patterns")
    """
    
    def __init__(self, method: ExtractionMethod = ExtractionMethod.HYBRID):
        self.method = method
        self._init_extractors()
    
    def _init_extractors(self):
        """Initialize extraction components based on method"""
        self.rule_patterns = self._load_rule_patterns()
        self.regex_patterns = self._load_regex_patterns()
        # ML model placeholder (would be loaded in production)
        self.ml_model = None
    
    def _load_rule_patterns(self) -> Dict[str, List[str]]:
        """
        Rule-based patterns (RLB approach)
        Maps intents to keyword/phrase patterns
        """
        return {
            "anomaly_detection": [
                "detect anomalies", "find outliers", "anomaly detection",
                "identify unusual", "spot anomalies", "find anomalies",
                "unusual patterns", "detect outliers"
            ],
            "clustering": [
                "cluster", "group data", "segment", "clustering",
                "find clusters", "group similar", "segmentation",
                "pattern grouping"
            ],
            "feature_engineering": [
                "engineer features", "create features", "feature engineering",
                "extract features", "generate features", "feature extraction",
                "feature creation", "transform features"
            ],
            "timeseries_forecasting": [
                "forecast", "predict future", "time series forecast",
                "prediction", "trend analysis", "future values",
                "forecasting", "predict next"
            ],
            "classification": [
                "classify", "classification", "categorize",
                "predict class", "label data", "categorization"
            ],
            "regression": [
                "regression", "predict value", "estimate",
                "linear regression", "predict number", "value prediction"
            ],
            "stats_comparison": [
                "compare statistics", "statistical comparison", "compare groups",
                "a/b test", "compare metrics", "statistical test"
            ],
            "geospatial_analysis": [
                "geospatial", "map", "location analysis",
                "spatial analysis", "geographic", "geo analysis",
                "mapping", "spatial"
            ],
            "incident_detection": [
                "detect incident", "incident detection", "alert",
                "threshold breach", "anomaly alert", "incident alert"
            ]
        }
    
    def _load_regex_patterns(self) -> Dict[str, str]:
        """
        Regex patterns for entity extraction
        Extracts: dates, numbers, column names, thresholds, windows, etc.
        """
        return {
            "column_name": r"column[s]?\s+['\"]?(\w+)['\"]?",
            "threshold": r"threshold\s+(?:of\s+)?(\d+\.?\d*)",
            "date_range": r"from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})",
            "metric": r"metric[s]?\s+['\"]?(\w+)['\"]?",
            "window": r"window\s+(?:of\s+)?(\d+\s*(?:min|minute|hour|day|week|month)s?)",
            "zscore": r"z-?score\s+(?:of\s+)?(\d+\.?\d*)",
            "contamination": r"contamination\s+(?:of\s+)?(\d+\.?\d*)",
            "n_clusters": r"(\d+)\s+clusters?",
            "algorithm": r"(?:using|with|algorithm)\s+(\w+)",
        }
    
    def extract(self, user_input: str) -> Dict[str, Any]:
        """
        Extract intent and entities from user input (up to 500 words)
        
        Args:
            user_input: Natural language input from user (VP - Voice/Text)
        
        Returns:
            Dictionary containing:
            - intent: Detected task/intent (e.g., "anomaly_detection")
            - entities: Extracted parameters (e.g., {"threshold": "2.5", "metric": "speed_kmh"})
            - confidence: Confidence score (0.0 to 1.0)
            - method_used: Which extraction method was used
            - raw_input: Original user input for reference
        """
        result = {
            "raw_input": user_input,
            "word_count": len(user_input.split())
        }
        
        if self.method == ExtractionMethod.RULE_BASED:
            extraction = self._rule_based_extraction(user_input)
        elif self.method == ExtractionMethod.REGEX:
            extraction = self._regex_extraction(user_input)
        elif self.method == ExtractionMethod.ML:
            extraction = self._ml_extraction(user_input)
        else:  # HYBRID
            extraction = self._hybrid_extraction(user_input)
        
        result.update(extraction)
        return result
    
    def _rule_based_extraction(self, user_input: str) -> Dict[str, Any]:
        """Rule-based (RLB) extraction using keyword matching"""
        user_input_lower = user_input.lower()
        
        # Find matching intents
        intent_scores = {}
        for intent, patterns in self.rule_patterns.items():
            score = sum(1 for pattern in patterns if pattern.lower() in user_input_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return {
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0,
                "method_used": "rule_based"
            }
        
        # Get highest scoring intent
        detected_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
        confidence = min(intent_scores[detected_intent] / 3.0, 1.0)  # Normalize
        
        # Extract entities using regex
        entities = self._extract_entities_regex(user_input)
        
        return {
            "intent": detected_intent,
            "entities": entities,
            "confidence": confidence,
            "method_used": "rule_based",
            "intent_scores": intent_scores
        }
    
    def _regex_extraction(self, user_input: str) -> Dict[str, Any]:
        """Pure regex-based extraction"""
        entities = self._extract_entities_regex(user_input)
        
        # Simple intent detection based on keywords
        intent = self._simple_intent_from_keywords(user_input)
        
        return {
            "intent": intent,
            "entities": entities,
            "confidence": 0.7 if intent != "unknown" else 0.0,
            "method_used": "regex"
        }
    
    def _ml_extraction(self, user_input: str) -> Dict[str, Any]:
        """
        ML-based extraction (placeholder for actual ML model)
        
        In production, this would use:
        - BERT/RoBERTa for intent classification
        - Named Entity Recognition (NER) for entity extraction
        - Custom trained models on domain-specific data
        
        Example frameworks:
        - Hugging Face Transformers
        - spaCy for NER
        - Custom PyTorch/TensorFlow models
        """
        # TODO: Implement actual ML model
        # Example flow:
        # 1. Tokenize input
        # 2. Pass through BERT for intent classification
        # 3. Use NER model for entity extraction
        # 4. Return structured output
        
        # Fallback to rule-based for now
        result = self._rule_based_extraction(user_input)
        result["method_used"] = "ml_fallback"
        result["note"] = "ML model not loaded, using rule-based fallback"
        return result
    
    def _hybrid_extraction(self, user_input: str) -> Dict[str, Any]:
        """
        Hybrid approach: Combine rule-based, regex, and ML
        Uses voting or confidence-weighted combination
        """
        # Get results from multiple methods
        rule_result = self._rule_based_extraction(user_input)
        regex_result = self._regex_extraction(user_input)
        
        # Combine intents (voting mechanism)
        if rule_result["intent"] == regex_result["intent"]:
            final_intent = rule_result["intent"]
            confidence = (rule_result["confidence"] + regex_result["confidence"]) / 2
        else:
            # Choose higher confidence
            if rule_result["confidence"] >= regex_result["confidence"]:
                final_intent = rule_result["intent"]
                confidence = rule_result["confidence"]
            else:
                final_intent = regex_result["intent"]
                confidence = regex_result["confidence"]
        
        # Merge entities (prefer more specific values)
        entities = {**rule_result["entities"], **regex_result["entities"]}
        
        return {
            "intent": final_intent,
            "entities": entities,
            "confidence": confidence,
            "method_used": "hybrid",
            "components": {
                "rule_based": rule_result["intent"],
                "regex": regex_result["intent"]
            }
        }
    
    def _extract_entities_regex(self, text: str) -> Dict[str, Any]:
        """Extract entities using regex patterns"""
        entities = {}
        
        for entity_type, pattern in self.regex_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if entity_type == "date_range" and len(matches[0]) == 2:
                    entities["start_date"] = matches[0][0]
                    entities["end_date"] = matches[0][1]
                else:
                    # Convert numeric values to appropriate types
                    value = matches[0] if len(matches) == 1 else matches
                    if entity_type in ["threshold", "zscore", "contamination"]:
                        try:
                            value = float(value)
                        except (ValueError, TypeError):
                            pass
                    elif entity_type == "n_clusters":
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            pass
                    entities[entity_type] = value
        
        return entities
    
    def _simple_intent_from_keywords(self, text: str) -> str:
        """Simple keyword-based intent detection"""
        text_lower = text.lower()
        
        # Check for keywords in order of specificity
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
        elif any(kw in text_lower for kw in ["geospatial", "map", "location", "spatial"]):
            return "geospatial_analysis"
        elif any(kw in text_lower for kw in ["incident", "alert"]):
            return "incident_detection"
        elif any(kw in text_lower for kw in ["compare", "comparison"]):
            return "stats_comparison"
        elif any(kw in text_lower for kw in ["regression", "estimate"]):
            return "regression"
        else:
            return "unknown"


# Example usage and framework demonstration
if __name__ == "__main__":
    print("=== Intent/Entity Extraction Examples ===\n")
    
    # Example 1: Rule-based extraction
    print("1. Rule-based (RLB) Extraction:")
    extractor_rlb = IntentExtractor(method=ExtractionMethod.RULE_BASED)
    result1 = extractor_rlb.extract("Detect anomalies in speed_kmh column with zscore 2.5")
    print(f"   Input: {result1['raw_input']}")
    print(f"   Intent: {result1['intent']}")
    print(f"   Entities: {result1['entities']}")
    print(f"   Confidence: {result1['confidence']:.2f}\n")
    
    # Example 2: Hybrid extraction (recommended)
    print("2. Hybrid Extraction:")
    extractor_hybrid = IntentExtractor(method=ExtractionMethod.HYBRID)
    result2 = extractor_hybrid.extract(
        "I need to find outliers in the speed data with a threshold of 2.0 "
        "and group similar patterns using 3 clusters. Use a 5 minute window."
    )
    print(f"   Input: {result2['raw_input']}")
    print(f"   Intent: {result2['intent']}")
    print(f"   Entities: {result2['entities']}")
    print(f"   Confidence: {result2['confidence']:.2f}")
    print(f"   Components: {result2.get('components', {})}\n")
    
    # Example 3: Regex extraction
    print("3. Regex Extraction:")
    extractor_regex = IntentExtractor(method=ExtractionMethod.REGEX)
    result3 = extractor_regex.extract(
        "Forecast sales from 2025-01-01 to 2025-12-31 with metric 'revenue'"
    )
    print(f"   Input: {result3['raw_input']}")
    print(f"   Intent: {result3['intent']}")
    print(f"   Entities: {result3['entities']}")
    print(f"   Confidence: {result3['confidence']:.2f}\n")
    
    # Example 4: Complex multi-intent input
    print("4. Complex Multi-task Input:")
    result4 = extractor_hybrid.extract(
        "Analyze the sensor data: first detect anomalies with contamination 0.05, "
        "then cluster the normal points into 4 groups, and finally create new features "
        "for time-based patterns"
    )
    print(f"   Input: {result4['raw_input'][:80]}...")
    print(f"   Primary Intent: {result4['intent']}")
    print(f"   Entities: {result4['entities']}")
    print(f"   Note: Complex multi-task - planner will decompose this\n")
