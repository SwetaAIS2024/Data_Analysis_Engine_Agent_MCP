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
import os

logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    """Extraction approach selection"""
    RULE_BASED = "rule_based"
    REGEX = "regex"
    ML = "ml"
    LLM = "llm"  # LLM-powered extraction
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
        self.adaptive_mode = os.getenv("ADAPTIVE_EXTRACTION", "false").lower() == "true"
        self.enable_fallback_chain = os.getenv("ENABLE_FALLBACK_CHAIN", "true").lower() == "true"  # Default TRUE
        self._init_extractors()
        logger.info(f"ContextExtractor initialized with method: {method.value}, adaptive: {self.adaptive_mode}, fallback_chain: {self.enable_fallback_chain}")
    
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
                "spot anomalies", "anomaly detection", "outlier detection",
                "find anomalies", "detect outliers", "anomalies", "outliers",
                "unusual patterns", "abnormal", "detect anomaly", "find anomaly",
                "anomaly", "outlier",
                # Common misspellings
                "anomoly", "anomolies", "detect anomoly", "find anomoly"
            ],
            "clustering": [
                "cluster", "group data", "segment", "clustering",
                "find patterns", "group similar", "segment data"
            ],
            "feature_engineering": [
                "engineer features", "create features", "feature extraction",
                "transform data", "generate features", "feature engineering"
            ],
            "timeseries_forecasting": [
                "forecast", "predict future", "prediction",
                "trend analysis", "time series forecast", "forecasting",
                "predict trend", "future prediction"
            ],
            "classification": [
                "classify", "classification", "categorize", "predict class",
                "classifier"
            ],
            "regression": [
                "regression", "predict value", "estimate", "predict number",
                "regressor"
            ],
            "stats_comparison": [
                "compare", "comparison", "a/b test", "statistical test"
            ],
            "geospatial_analysis": [
                "geospatial", "map", "location", "spatial analysis"
            ],
            "report_generation": [
                "report", "reporting", "generate report", "comprehensive report", "detailed report"
            ],
            "visualization": [
                "visualize", "visualization", "chart", "graph", "plot"
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
    
    def _select_best_method(self, user_prompt: str, data_info: dict) -> ExtractionMethod:
        """
        Intelligently select the best extraction method based on:
        1. Prompt characteristics (length, complexity, keywords)
        2. API availability (LLM providers)
        3. Data context
        4. Performance requirements
        
        Selection Heuristics:
        - Simple prompts (<20 words, clear keywords) → RULE_BASED (fastest)
        - Medium complexity (20-50 words, some context) → HYBRID (balanced)
        - Complex prompts (>50 words, nuanced) → LLM (most accurate)
        - No API key → Fallback to HYBRID/RULE_BASED
        """
        prompt_lower = user_prompt.lower()
        word_count = len(user_prompt.split())
        
        # Calculate complexity score
        complexity_score = 0
        
        # Factor 1: Length (0-3 points)
        if word_count < 10:
            complexity_score += 0
        elif word_count < 25:
            complexity_score += 1
        elif word_count < 50:
            complexity_score += 2
        else:
            complexity_score += 3
        
        # Factor 2: Contains negations or conditions (0-2 points)
        negation_words = ['not', 'without', 'except', 'exclude', 'ignore']
        conditional_words = ['if', 'when', 'where', 'unless', 'provided']
        if any(word in prompt_lower for word in negation_words):
            complexity_score += 1
        if any(word in prompt_lower for word in conditional_words):
            complexity_score += 1
        
        # Factor 3: Multiple clauses/sentences (0-2 points)
        sentence_count = prompt_lower.count('.') + prompt_lower.count('?') + prompt_lower.count('!')
        if sentence_count > 1:
            complexity_score += 1
        if prompt_lower.count(',') > 2:
            complexity_score += 1
        
        # Factor 4: Contains tool-specific keywords (reduces complexity for rule-based)
        tool_keywords = [
            'detect', 'anomaly', 'forecast', 'cluster', 'classify',
            'regression', 'compare', 'statistics', 'geospatial', 'map'
        ]
        has_clear_tool_match = any(kw in prompt_lower for kw in tool_keywords)
        
        logger.debug(f"Prompt analysis: words={word_count}, complexity={complexity_score}, has_tool_match={has_clear_tool_match}")
        
        # Decision logic based on complexity score (0-8 range)
        if complexity_score <= 2 and has_clear_tool_match:
            # Simple, clear prompts → RULE_BASED (fast, deterministic)
            logger.info("Selected RULE_BASED: Simple prompt with clear tool keywords")
            return ExtractionMethod.RULE_BASED
        
        elif complexity_score >= 6:
            # Complex prompts → Try LLM if available
            if self._check_llm_availability():
                logger.info("Selected LLM: Complex prompt, API available")
                return ExtractionMethod.LLM
            else:
                logger.info("Selected HYBRID: Complex prompt but no LLM API, using hybrid fallback")
                return ExtractionMethod.HYBRID
        
        else:
            # Medium complexity → HYBRID (balanced approach)
            logger.info("Selected HYBRID: Medium complexity prompt")
            return ExtractionMethod.HYBRID
    
    def _check_llm_availability(self) -> bool:
        """Check if LLM API is configured and available"""
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            available = bool(api_key and api_key.strip())
            if available:
                logger.debug("OpenAI API key found")
            return available
        
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            available = bool(api_key and api_key.strip())
            if available:
                logger.debug("Anthropic API key found")
            return available
        
        elif provider == "local":
            # Local LLM via Ollama - check if URL configured
            local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
            available = bool(local_url)
            if available:
                logger.debug(f"Local LLM URL configured: {local_url}")
            return available
        
        return False
    
    def extract(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured metadata from user prompt and data
        
        Supports two modes:
        1. Single method extraction (default)
        2. Fallback chain: RULE_BASED → ML → LLM → User Clarification
        
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
        
        # FALLBACK CHAIN MODE: Try multiple methods in sequence
        if self.enable_fallback_chain:
            logger.info("🔗 Fallback chain enabled - will try multiple extraction methods")
            return self._extract_with_fallback_chain(user_prompt, data_info)
        
        # SINGLE METHOD MODE: Use adaptive or fixed method selection
        if self.adaptive_mode:
            selected_method = self._select_best_method(user_prompt, data_info)
            logger.info(f"Adaptive mode: selected {selected_method.value} for this prompt")
        else:
            selected_method = self.method
        
        if selected_method == ExtractionMethod.RULE_BASED:
            result = self._rule_based_extraction(user_prompt, data_info)
        elif selected_method == ExtractionMethod.REGEX:
            result = self._regex_extraction(user_prompt, data_info)
        elif selected_method == ExtractionMethod.ML:
            result = self._ml_extraction(user_prompt, data_info)
        elif selected_method == ExtractionMethod.LLM:
            result = self._llm_extraction(user_prompt, data_info)
        else:  # HYBRID
            result = self._hybrid_extraction(user_prompt, data_info)
        
        logger.info(f"Extracted goal: {result['goal']}, data_type: {result['data_type']}")
        return result
    
    def _extract_with_fallback_chain(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Consensus-Based Fallback Chain: Try ALL methods and use voting
        
        Strategy:
        1. Try RULE_BASED, ML, and LLM (all available methods)
        2. Collect all results that don't require clarification
        3. Use CONSENSUS (majority vote) to determine final goal
        4. If all agree → High confidence result
        5. If majority agrees → Medium confidence result
        6. If no consensus → Use highest confidence method OR ask for clarification
        
        Returns:
            Consensus result with metadata about all attempts
        """
        logger.info("🔗 Starting consensus-based fallback chain extraction")
        logger.info("📊 Strategy: Try all methods, use voting to determine final answer")
        
        # Track all extraction attempts
        all_results = []
        goal_votes = {}  # goal -> count
        
        # ========== ATTEMPT 1: RULE-BASED ==========
        logger.info("📍 Method 1/3: Trying RULE_BASED extraction...")
        try:
            rule_result = self._rule_based_extraction(user_prompt, data_info)
            
            if not rule_result.get("requires_clarification"):
                goal = rule_result.get("goal", "unknown")
                confidence = rule_result.get("confidence", 0.0)
                
                all_results.append({
                    "method": "rule_based",
                    "goal": goal,
                    "confidence": confidence,
                    "status": "success",
                    "result": rule_result
                })
                
                # Vote for this goal
                goal_votes[goal] = goal_votes.get(goal, 0) + 1
                logger.info(f"✅ RULE_BASED voted for: {goal} (confidence: {confidence:.2f})")
            else:
                all_results.append({
                    "method": "rule_based",
                    "status": "requires_clarification"
                })
                logger.warning("⚠️ RULE_BASED: Requires clarification")
        except Exception as e:
            logger.error(f"❌ RULE_BASED failed: {e}")
            all_results.append({
                "method": "rule_based",
                "status": "failed",
                "error": str(e)
            })
        
        # ========== ATTEMPT 2: ML-BASED ==========
        logger.info("📍 Method 2/3: Trying ML extraction...")
        try:
            ml_result = self._ml_extraction(user_prompt, data_info)
            
            # Check if ML actually ran (not just fallback to rules)
            if ml_result.get("extraction_method") == "ml" and not ml_result.get("requires_clarification"):
                goal = ml_result.get("goal", "unknown")
                confidence = ml_result.get("confidence", 0.0)
                
                all_results.append({
                    "method": "ml",
                    "goal": goal,
                    "confidence": confidence,
                    "status": "success",
                    "result": ml_result
                })
                
                # Vote for this goal
                goal_votes[goal] = goal_votes.get(goal, 0) + 1
                logger.info(f"✅ ML voted for: {goal} (confidence: {confidence:.2f})")
            else:
                all_results.append({
                    "method": "ml",
                    "status": "not_available"
                })
                logger.warning("⚠️ ML: Not available or fell back to rules")
        except Exception as e:
            logger.error(f"❌ ML failed: {e}")
            all_results.append({
                "method": "ml",
                "status": "failed",
                "error": str(e)
            })
        
        # ========== ATTEMPT 3: LLM-BASED ==========
        if self._check_llm_availability():
            logger.info("📍 Method 3/3: Trying LLM extraction...")
            try:
                llm_result = self._llm_extraction(user_prompt, data_info)
                
                if not llm_result.get("requires_clarification"):
                    goal = llm_result.get("goal", "unknown")
                    confidence = llm_result.get("confidence", 0.0)
                    
                    all_results.append({
                        "method": "llm",
                        "goal": goal,
                        "confidence": confidence,
                        "status": "success",
                        "result": llm_result
                    })
                    
                    # Vote for this goal (LLM gets 2 votes due to higher accuracy)
                    goal_votes[goal] = goal_votes.get(goal, 0) + 2
                    logger.info(f"✅ LLM voted for: {goal} (confidence: {confidence:.2f}) [2 votes]")
                else:
                    all_results.append({
                        "method": "llm",
                        "status": "requires_clarification"
                    })
                    logger.warning("⚠️ LLM: Requires clarification")
            except Exception as e:
                logger.error(f"❌ LLM failed: {e}")
                all_results.append({
                    "method": "llm",
                    "status": "failed",
                    "error": str(e)
                })
        else:
            logger.info("⏭️ Method 3/3: Skipping LLM (API not available)")
            all_results.append({
                "method": "llm",
                "status": "skipped",
                "reason": "API not configured"
            })
        
        # ========== CONSENSUS ANALYSIS ==========
        logger.info("�️ Analyzing votes from all methods...")
        logger.info(f"Vote counts: {goal_votes}")
        
        # Get successful results only
        successful_results = [r for r in all_results if r.get("status") == "success"]
        
        if not successful_results:
            # NO METHOD SUCCEEDED → Ask for clarification
            logger.warning("⚠️ All methods failed or require clarification")
            clarification_result = self._create_clarification_request(user_prompt, {})
            clarification_result["fallback_chain_used"] = True
            clarification_result["fallback_strategy"] = "consensus"
            clarification_result["all_attempts"] = all_results
            clarification_result["consensus"] = "none"
            return clarification_result
        
        # Determine consensus
        if goal_votes:
            # Sort by votes (descending)
            sorted_goals = sorted(goal_votes.items(), key=lambda x: x[1], reverse=True)
            winning_goal = sorted_goals[0][0]
            winning_votes = sorted_goals[0][1]
            total_votes = sum(goal_votes.values())
            
            # Check for unanimous consensus
            if len(goal_votes) == 1:
                consensus_level = "unanimous"
                logger.info(f"✅ UNANIMOUS CONSENSUS: All methods agree on '{winning_goal}'")
            # Check for strong consensus (>75%)
            elif winning_votes / total_votes >= 0.75:
                consensus_level = "strong"
                logger.info(f"✅ STRONG CONSENSUS: {winning_votes}/{total_votes} votes for '{winning_goal}'")
            # Check for majority (>50%)
            elif winning_votes / total_votes > 0.50:
                consensus_level = "majority"
                logger.info(f"⚠️ MAJORITY CONSENSUS: {winning_votes}/{total_votes} votes for '{winning_goal}'")
            else:
                consensus_level = "weak"
                logger.warning(f"⚠️ WEAK CONSENSUS: {winning_votes}/{total_votes} votes for '{winning_goal}'")
            
            # Find the result with winning goal and highest confidence
            winning_results = [r for r in successful_results if r["goal"] == winning_goal]
            best_result = max(winning_results, key=lambda x: x["confidence"])
            
            # Build final result
            final_result = best_result["result"].copy()
            
            # Add consensus metadata
            final_result["fallback_chain_used"] = True
            final_result["fallback_strategy"] = "consensus"
            final_result["consensus_level"] = consensus_level
            final_result["winning_goal"] = winning_goal
            final_result["vote_count"] = winning_votes
            final_result["total_votes"] = total_votes
            final_result["all_attempts"] = all_results
            final_result["vote_breakdown"] = dict(sorted_goals)
            
            # Adjust confidence based on consensus
            original_confidence = final_result.get("confidence", 0.0)
            if consensus_level == "unanimous":
                final_result["confidence"] = min(original_confidence * 1.2, 1.0)  # Boost 20%
            elif consensus_level == "strong":
                final_result["confidence"] = min(original_confidence * 1.1, 1.0)  # Boost 10%
            elif consensus_level == "majority":
                final_result["confidence"] = original_confidence  # No change
            else:  # weak
                final_result["confidence"] = original_confidence * 0.9  # Reduce 10%
            
            logger.info(f"🎯 FINAL DECISION: {winning_goal} (confidence: {final_result['confidence']:.2f}, consensus: {consensus_level})")
            
            # If consensus is weak, add a warning
            if consensus_level == "weak":
                final_result["consensus_warning"] = f"Methods disagree. Other options: {[g for g, v in sorted_goals[1:]]}"
            
            return final_result
        
        # Fallback: This shouldn't happen, but handle it
        logger.error("❌ Unexpected: No votes collected despite successful results")
        return self._create_clarification_request(user_prompt, {})
    
    def _rule_based_extraction(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Rule-based extraction using keyword matching"""
        prompt_lower = user_prompt.lower()
        
        # Check for ambiguous/vague prompts first
        ambiguity_result = self._check_ambiguity(user_prompt, prompt_lower)
        if ambiguity_result:
            return ambiguity_result
        
        # Extract goal
        goal = "unknown"
        goal_scores = {}
        for goal_name, patterns in self.goal_patterns.items():
            score = sum(1 for pattern in patterns if pattern in prompt_lower)
            if score > 0:
                goal_scores[goal_name] = score
        
        if goal_scores:
            goal = max(goal_scores.items(), key=lambda x: x[1])[0]
        
        # Check if confidence is too low (ambiguous goal)
        # Confidence calculation: normalize score, but give benefit if ANY match exists
        if goal_scores:
            max_score = goal_scores[goal]
            confidence = min(max_score / 2.0, 1.0)  # Changed from 3.0 to 2.0 for better sensitivity
        else:
            confidence = 0.0
        
        # If goal is unknown or confidence is very low, request clarification
        if goal == "unknown" or confidence < 0.25:  # Lowered threshold from 0.3 to 0.25
            return self._create_clarification_request(user_prompt, goal_scores)
        
        # Extract constraints
        constraints = self._extract_constraints(user_prompt)
        
        # Extract parameters
        parameters = self._extract_parameters(user_prompt)
        
        # Detect data type
        data_type = self._detect_data_type(user_prompt, data_info)
        
        # Analyze data characteristics
        data_characteristics = self._analyze_data(data_info)
        
        result = {
            "goal": goal,
            "constraints": constraints,
            "data_type": data_type,
            "data_characteristics": data_characteristics,
            "parameters": parameters,
            "user_preferences": self._extract_preferences(user_prompt),
            "extraction_method": "rule_based",
            "confidence": confidence
        }
        
        return result
    
    def _check_ambiguity(self, user_prompt: str, prompt_lower: str) -> Optional[Dict[str, Any]]:
        """Check if the prompt is too ambiguous or vague"""
        
        # First, check if there's a clear goal match (HIGHEST PRIORITY)
        has_clear_goal = False
        matched_goal = None
        
        for goal, patterns in self.goal_patterns.items():
            for pattern in patterns:
                # Check for pattern match in prompt
                if pattern in prompt_lower:
                    has_clear_goal = True
                    matched_goal = goal
                    break
            if has_clear_goal:
                break
        
        # If we have a clear goal match, don't ask for clarification
        if has_clear_goal:
            return None
        
        # List of ambiguous/vague single words that need clarification
        single_word_ambiguous = [
            "detect", "detection", "analyze", "analysis", "process", "run", "execute",
            "test", "check", "help"
        ]
        
        # Check if prompt is just a single ambiguous word (without context)
        prompt_words = prompt_lower.strip().split()
        if len(prompt_words) == 1 and prompt_words[0] in single_word_ambiguous:
            return self._create_clarification_request(user_prompt, {})
        
        # Check for vague 2-3 word phrases WITHOUT specific keywords
        if len(prompt_words) <= 3:
            vague_phrases = [
                "do detection", "do analysis", "run analysis", "do something",
                "check data", "process data"
            ]
            if prompt_lower.strip() in vague_phrases:
                return self._create_clarification_request(user_prompt, {})
        
        # If prompt is very short (< 15 chars) and has no clear goal, request clarification
        if len(user_prompt.strip()) < 15:
            return self._create_clarification_request(user_prompt, {})
        
        return None
    
    def _create_clarification_request(
        self, 
        user_prompt: str, 
        goal_scores: Dict[str, int]
    ) -> Dict[str, Any]:
        """Create a result that requests user clarification"""
        
        # Suggest possible goals based on available tools
        suggested_goals = []
        
        if goal_scores:
            # If we have some weak matches, suggest them
            sorted_goals = sorted(goal_scores.items(), key=lambda x: x[1], reverse=True)
            suggested_goals = [goal for goal, score in sorted_goals[:3]]
        else:
            # Otherwise, suggest common goals
            suggested_goals = [
                "anomaly_detection",
                "clustering", 
                "timeseries_forecasting",
                "classification",
                "stats_comparison"
            ]
        
        return {
            "goal": "clarification_required",
            "constraints": {
                "ambiguous_prompt": True,
                "original_prompt": user_prompt
            },
            "data_type": "unknown",
            "data_characteristics": {},
            "parameters": {},
            "user_preferences": {},
            "extraction_method": "ambiguity_detected",
            "confidence": 0.0,
            "requires_clarification": True,
            "clarification_message": f"Your request '{user_prompt}' is too ambiguous. Please specify what analysis you want to perform.",
            "suggested_options": [
                {
                    "id": goal,
                    "label": self._get_goal_label(goal),
                    "description": self._get_goal_description(goal)
                }
                for goal in suggested_goals
            ]
        }
    
    def _get_goal_label(self, goal_id: str) -> str:
        """Get human-readable label for a goal"""
        labels = {
            "anomaly_detection": "Anomaly Detection",
            "clustering": "Clustering / Segmentation",
            "timeseries_forecasting": "Time Series Forecasting",
            "classification": "Classification",
            "regression": "Regression Analysis",
            "stats_comparison": "Statistical Comparison",
            "feature_engineering": "Feature Engineering",
            "geospatial_analysis": "Geospatial Analysis",
            "incident_detection": "Incident Detection"
        }
        return labels.get(goal_id, goal_id.replace("_", " ").title())
    
    def _get_goal_description(self, goal_id: str) -> str:
        """Get description for a goal"""
        descriptions = {
            "anomaly_detection": "Find unusual patterns or outliers in your data",
            "clustering": "Group similar data points together to discover patterns",
            "timeseries_forecasting": "Predict future values based on historical trends",
            "classification": "Categorize data into predefined classes",
            "regression": "Predict continuous numerical values",
            "stats_comparison": "Compare groups statistically (A/B testing, etc.)",
            "feature_engineering": "Create derived features from existing data",
            "geospatial_analysis": "Analyze spatial patterns and locations",
            "incident_detection": "Detect incidents like spikes, drops, or anomalies"
        }
        return descriptions.get(goal_id, "Perform " + goal_id.replace("_", " "))

    
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
        """
        ML-based extraction using traditional ML models
        
        This can use:
        - BERT for intent classification
        - NER (Named Entity Recognition) for parameter extraction
        - Text classification models for goal detection
        
        Currently falls back to rule-based with enhanced confidence scoring
        """
        logger.info("Using ML-based extraction (currently rule-based fallback)")
        
        # In production, this would:
        # 1. Tokenize the prompt
        # 2. Pass through BERT/transformer model
        # 3. Classify intent (goal)
        # 4. Extract entities (parameters, constraints)
        # 5. Return structured output
        
        # For now, use rule-based with adjusted confidence
        result = self._rule_based_extraction(user_prompt, data_info)
        result["extraction_method"] = "ml_fallback"
        
        # Future enhancement: Load and use actual ML model
        # model = load_intent_classifier()
        # goal_probs = model.predict(user_prompt)
        # result["goal"] = max(goal_probs, key=goal_probs.get)
        # result["confidence"] = goal_probs[result["goal"]]
        
        return result
    
    def _llm_extraction(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        LLM-powered extraction using GPT/Claude/Llama
        
        Uses a language model to understand natural language intent
        and extract structured metadata with high accuracy.
        """
        logger.info("Using LLM-based extraction")
        
        # Check if LLM API is configured
        llm_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        llm_provider = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, local
        
        if not llm_api_key and llm_provider != "local":
            logger.warning("No LLM API key found, falling back to rule-based extraction")
            result = self._rule_based_extraction(user_prompt, data_info)
            result["extraction_method"] = "llm_fallback_no_api_key"
            return result
        
        # Build LLM prompt for intent extraction
        system_prompt = self._build_llm_system_prompt()
        user_message = self._build_llm_user_message(user_prompt, data_info)
        
        try:
            # Call LLM API
            if llm_provider == "openai":
                llm_response = self._call_openai_llm(system_prompt, user_message)
            elif llm_provider == "anthropic":
                llm_response = self._call_anthropic_llm(system_prompt, user_message)
            elif llm_provider == "local":
                llm_response = self._call_local_llm(system_prompt, user_message)
            else:
                raise ValueError(f"Unsupported LLM provider: {llm_provider}")
            
            # Parse LLM response to structured format
            result = self._parse_llm_response(llm_response, user_prompt)
            result["extraction_method"] = f"llm_{llm_provider}"
            
            logger.info(f"LLM extraction successful: goal={result.get('goal')}, confidence={result.get('confidence')}")
            return result
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}, falling back to rule-based")
            result = self._rule_based_extraction(user_prompt, data_info)
            result["extraction_method"] = "llm_fallback_error"
            return result
    
    def _build_llm_system_prompt(self) -> str:
        """Build system prompt for LLM intent extraction"""
        available_goals = list(self.goal_patterns.keys())
        
        return f"""You are an expert data analysis intent extraction system. Your task is to understand user requests and extract structured metadata.

Available Analysis Goals:
{json.dumps(available_goals, indent=2)}

Your response must be valid JSON with this exact structure:
{{
  "goal": "one of the available goals or 'unknown'",
  "confidence": 0.0-1.0,
  "data_type": "tabular|timeseries|geospatial|categorical|text|image|graph",
  "constraints": {{
    "threshold": number (optional),
    "max_limit": number (optional),
    "min_limit": number (optional)
  }},
  "parameters": {{
    "metric": "string (optional)",
    "window": "string (optional)",
    "algorithm": "string (optional)"
  }},
  "ambiguous": true|false,
  "reasoning": "brief explanation of your interpretation"
}}

If the request is too vague or ambiguous, set "ambiguous": true and "confidence": 0.0.

Examples:
- "Find anomalies in speed data" → goal: "anomaly_detection", data_type: "timeseries"
- "Cluster customers by behavior" → goal: "clustering", data_type: "tabular"
- "Predict future sales" → goal: "timeseries_forecasting", data_type: "timeseries"
- "Compare A vs B" → goal: "stats_comparison", data_type: "categorical"
- "do detection" → ambiguous: true (too vague)"""
    
    def _build_llm_user_message(self, user_prompt: str, data_info: Optional[Dict[str, Any]]) -> str:
        """Build user message for LLM"""
        message = f"User Request: {user_prompt}\n\n"
        
        if data_info:
            message += f"Data Context:\n"
            message += f"- Rows: {data_info.get('row_count', 'unknown')}\n"
            message += f"- Columns: {', '.join(data_info.get('columns', []))}\n\n"
        
        message += "Extract the intent and return JSON."
        return message
    
    def _call_openai_llm(self, system_prompt: str, user_message: str) -> str:
        """Call OpenAI API (GPT-4, GPT-3.5, etc.)"""
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            response = openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except ImportError:
            logger.error("openai package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _call_anthropic_llm(self, system_prompt: str, user_message: str) -> str:
        """Call Anthropic Claude API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response.content[0].text
        except ImportError:
            logger.error("anthropic package not installed. Install with: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def _call_local_llm(self, system_prompt: str, user_message: str) -> str:
        """Call local LLM (Ollama, llama.cpp, etc.)"""
        try:
            import requests
            
            # Assumes Ollama or similar running locally
            url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/api/generate")
            model = os.getenv("LOCAL_LLM_MODEL", "llama2")
            
            payload = {
                "model": model,
                "prompt": f"{system_prompt}\n\n{user_message}",
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Local LLM call failed: {e}")
            raise
    
    def _parse_llm_response(self, llm_response: str, user_prompt: str) -> Dict[str, Any]:
        """Parse LLM JSON response into structured format"""
        try:
            # Extract JSON from response (may have markdown code blocks)
            json_str = llm_response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            llm_data = json.loads(json_str)
            
            # Check if LLM detected ambiguity
            if llm_data.get("ambiguous") or llm_data.get("confidence", 0) < 0.3:
                return self._create_clarification_request(user_prompt, {})
            
            # Convert to our standard format
            result = {
                "goal": llm_data.get("goal", "unknown"),
                "confidence": llm_data.get("confidence", 0.5),
                "data_type": llm_data.get("data_type", "tabular"),
                "constraints": llm_data.get("constraints", {}),
                "parameters": llm_data.get("parameters", {}),
                "data_characteristics": {},
                "user_preferences": {},
                "extraction_method": "llm",
                "llm_reasoning": llm_data.get("reasoning", "")
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"LLM response was: {llm_response}")
            raise
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            raise
    
    def _hybrid_extraction(
        self,
        user_prompt: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Hybrid: Combine rule-based and regex"""
        rule_result = self._rule_based_extraction(user_prompt, data_info)
        
        # If rule-based detected clarification needed, return it immediately
        if rule_result.get("requires_clarification"):
            return rule_result
        
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
