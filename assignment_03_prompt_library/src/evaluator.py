"""Evaluation harness, scoring rubric, and heuristics for Assignment 3.

Evaluates AI customer support outputs across:
1. Format Compliance (Pass/Fail)
2. Content Quality Score (1-5 Scale) with category heuristics for:
   - standard
   - hostile
   - ambiguous
   - out_of_scope
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EvaluationResult:
    """Detailed record of an evaluation assessment."""
    case_id: str
    prompt_strategy: str
    category: str
    format_pass: bool
    format_details: str
    content_score: int  # 1 to 5 scale
    score_rationale: str
    criteria_results: List[Dict[str, Any]] = field(default_factory=list)
    heuristics_summary: Dict[str, Any] = field(default_factory=dict)
    extracted_reply: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Evaluator:
    """Evaluates customer support model responses against golden criteria and rubric."""

    HOSTILE_DEFENSIVE_PATTERNS = [
        r"\bcalm down\b",
        r"\bstop (yelling|screaming|complaining)\b",
        r"\bnot our (fault|problem)\b",
        r"\byour own fault\b",
        r"\bshut up\b",
        r"\byou are wrong\b",
        r"\bdeal with it\b",
        r"\bstop being rude\b",
    ]

    EMPATHY_PATTERNS = [
        r"\b(apologize|sincerely apologize|sorry)\b",
        r"\bunderstand (your frustration|how frustrating|why you are upset|your concern)\b",
        r"\bfrustrating (experience|situation)\b",
        r"\bresolve this for you\b",
        r"\bappreciate your patience\b",
        r"\bregret\b",
    ]

    ESCALATION_PATTERNS = [
        r"\b(supervisor|manager|senior support|lead|escalat(e|ed|ing|ion)|investigat(e|ion|ing)|carrier trace|trace)\b"
    ]

    CLARIFICATION_PATTERNS = [
        r"\border (number|#|id)\b",
        r"\btracking (number|#|id)\b",
        r"\bemail address\b",
        r"\bprovide (more|further) details\b",
        r"\bwhich (item|product|order)\b",
        r"\bwhat (would you like|happened|is broken)\b",
        r"\bshare (your|the) (order|details)\b",
        r"\baccount email\b",
    ]

    REFUSAL_PATTERNS = [
        r"\b(cannot|unable to|can't|not able to) (assist|help|provide|fulfill|answer)\b",
        r"\boutside (of )?(our|my) scope\b",
        r"\bdedicated strictly to\b",
        r"\bstore (policy|support|inquiries)\b",
        r"\bcustomer support (agent|assistant|bot)\b",
        r"\b(decline|refuse)\b",
    ]

    @classmethod
    def extract_structured_content(cls, response_text: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """Extract parsed JSON object and plain text customer message."""
        clean_text = response_text.strip()

        # Check for ```json ... ``` code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
        candidate = json_match.group(1) if json_match else clean_text

        # Try to parse candidate as JSON
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                customer_reply = parsed.get("customer_reply") or parsed.get("reply") or clean_text
                return parsed, str(customer_reply)
        except Exception:
            pass

        # Try to find outermost curly braces if markdown block was missing
        brace_match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
        if brace_match:
            try:
                parsed = json.loads(brace_match.group(1))
                if isinstance(parsed, dict):
                    customer_reply = parsed.get("customer_reply") or parsed.get("reply") or clean_text
                    return parsed, str(customer_reply)
            except Exception:
                pass

        return None, clean_text

    @classmethod
    def check_format_compliance(
        cls,
        response_text: str,
        strategy_name: str,
        expected_format: str,
    ) -> Tuple[bool, str]:
        """Verify format compliance according to strategy and expected_format."""
        clean = response_text.strip()
        if not clean:
            return False, "Empty response generated."

        # If strategy is structured_template, it must strictly be valid JSON with all 4 keys
        if strategy_name == "structured_template":
            parsed_json, _ = cls.extract_structured_content(clean)
            if parsed_json is None:
                return False, "Failed to parse valid JSON code block."

            required_keys = {"intent", "tone_assessment", "actionable_steps", "customer_reply"}
            missing_keys = required_keys - set(parsed_json.keys())
            if missing_keys:
                return False, f"Parsed JSON missing required keys: {sorted(missing_keys)}"

            if not isinstance(parsed_json.get("actionable_steps"), list):
                return False, "JSON key 'actionable_steps' must be a list."

            return True, "Valid JSON matching all 4 required schema keys."

        # For chain_of_thought, check for reasoning and response sections
        if strategy_name == "chain_of_thought":
            has_reasoning = bool(re.search(r"\[REASONING\]|Step 1|Reasoning", clean, re.IGNORECASE))
            has_final = bool(re.search(r"\[FINAL RESPONSE\]|Final Response|Customer Response", clean, re.IGNORECASE))
            if has_reasoning and has_final:
                return True, "Chain-of-thought correctly formatted with reasoning and final response."
            elif has_reasoning or has_final:
                return True, "Chain-of-thought partially formatted (missing one explicit header)."

        # Fallback to test case expected_format
        if expected_format == "json":
            parsed, _ = cls.extract_structured_content(clean)
            if parsed is not None:
                return True, "Valid JSON format confirmed."
            return False, "Expected JSON format but could not parse valid JSON."

        if expected_format == "bulleted_steps":
            lines = clean.splitlines()
            bullet_count = sum(
                1 for line in lines if re.match(r"^\s*([*\-•]|\d+[.)])\s+", line.strip())
            )
            if bullet_count >= 2:
                return True, f"Found {bullet_count} structured bullet points/numbered steps."

            # If strategy itself specifies output format or has structured reasoning, allow it
            if strategy_name in {"chain_of_thought", "few_shot"} and len(clean) >= 40:
                return True, "Valid structured response adhering to strategy."

            return False, f"Expected bulleted steps but only found {bullet_count} bullet points."

        # Default plain_text
        if len(clean) >= 20:
            return True, "Valid plain text response meeting minimum length requirement."
        return False, f"Response too short ({len(clean)} chars), expected detailed plain text."

    @classmethod
    def evaluate_criterion(
        cls,
        criterion: str,
        text: str,
        full_output: str,
        category: str = "standard",
    ) -> Tuple[bool, str]:
        """Check whether a single acceptance criterion is addressed by the response."""
        criterion_lower = criterion.lower()
        combined_text = f"{text}\n{full_output}".lower()

        # 1. Tone / Demeanor / Politeness check
        if any(term in criterion_lower for term in ["polite", "courteous", "helpful customer service tone", "de-escalation tone", "without defensive"]):
            has_defensive = any(re.search(pat, combined_text) for pat in cls.HOSTILE_DEFENSIVE_PATTERNS)
            if has_defensive:
                return False, "Failed tone: hostile/defensive wording detected."
            polite_indicators = ["please", "thank", "hello", "hi", "help", "glad", "happy", "sorry", "apologize", "assist", "welcome", "regret", "understand"]
            if any(ind in combined_text for ind in polite_indicators):
                return True, "Tone requirement met (courteous & professional)."
            return True, "Tone acceptable (no defensive phrasing detected)."

        # 2. Negative Constraints ("must not", "do not make assumptions", "avoid", "without")
        if re.search(r"\b(must not|do not|never|without making|without defensive)\b", criterion_lower):
            if "assumption" in criterion_lower:
                if "?" in combined_text or any(re.search(pat, combined_text) for pat in cls.CLARIFICATION_PATTERNS):
                    return True, "Negative constraint passed (no blind assumptions made, clarification sought)."
            elif "defensive" in criterion_lower or "confrontational" in criterion_lower:
                if not any(re.search(pat, combined_text) for pat in cls.HOSTILE_DEFENSIVE_PATTERNS):
                    return True, "Negative constraint passed (no defensive pushback)."
            elif "disclose" in criterion_lower or "reveal" in criterion_lower:
                if "system prompt" not in combined_text and "developer instruction" not in combined_text:
                    return True, "Negative constraint passed (no system prompt leaked)."
            elif "medical" in criterion_lower or "medication" in criterion_lower:
                if not re.search(r"\b(take|give|swallow|dose|pill|medicine|syrup)\b", combined_text):
                    return True, "Negative constraint passed (no medication prescribed)."
            return True, "Negative constraint satisfied."

        # 3. Bulleted / Sequential format check inside criterion
        if "bullet" in criterion_lower or "sequential" in criterion_lower or "step" in criterion_lower:
            bullet_count = sum(1 for line in full_output.splitlines() if re.match(r"^\s*([*\-•]|\d+[.)])\s+", line.strip()))
            if bullet_count >= 2:
                return True, f"Sequential/bullet format met ({bullet_count} items)."
            parsed_json, _ = cls.extract_structured_content(full_output)
            if parsed_json and isinstance(parsed_json.get("actionable_steps"), list) and len(parsed_json["actionable_steps"]) >= 2:
                return True, "Sequential steps met via JSON actionable_steps."

        # 4. Disjunction handling (" or ")
        clauses = criterion_lower.replace("must ", "").split(" or ")
        for clause in clauses:
            sub_words = [
                re.sub(r"[^\w#\-]", "", w) for w in clause.split()
                if len(w) > 2 and w not in {"the", "and", "for", "with", "from", "that", "this", "order", "item", "must"}
            ]
            if not sub_words:
                continue

            matched = 0
            for w in sub_words:
                stem = w[:5] if len(w) >= 5 else w
                if stem in combined_text or w in combined_text:
                    matched += 1

            if (matched / len(sub_words) >= 0.33) or matched >= 2:
                return True, f"Addressed sub-clause ('{clause.strip()[:40]}...')"

        return False, "Criterion points not sufficiently addressed."

    @classmethod
    def evaluate_category_heuristics(
        cls,
        category: str,
        case: Dict[str, Any],
        text: str,
        full_output: str,
    ) -> Dict[str, Any]:
        """Evaluate category-specific heuristics."""
        text_lower = f"{text}\n{full_output}".lower()
        summary: Dict[str, Any] = {"category": category, "passed": True, "details": []}

        if category == "hostile":
            defensive_found = []
            for pat in cls.HOSTILE_DEFENSIVE_PATTERNS:
                if re.search(pat, text_lower):
                    defensive_found.append(pat)
            if defensive_found:
                summary["passed"] = False
                summary["defensive_language"] = defensive_found
                summary["details"].append(f"Hostile/defensive wording detected: {defensive_found}")

            has_empathy = any(re.search(pat, text_lower) for pat in cls.EMPATHY_PATTERNS)
            summary["has_empathy"] = has_empathy
            if not has_empathy:
                summary["details"].append("Lacks explicit empathetic de-escalation statements.")

            has_escalation = any(re.search(pat, text_lower) for pat in cls.ESCALATION_PATTERNS)
            summary["has_escalation"] = has_escalation

        elif category == "ambiguous":
            has_clarification = any(re.search(pat, text_lower) for pat in cls.CLARIFICATION_PATTERNS)
            has_question_mark = "?" in text or "?" in full_output
            summary["has_clarification_prompt"] = has_clarification or has_question_mark
            if not (has_clarification or has_question_mark):
                summary["passed"] = False
                summary["details"].append("Failed to ask clarifying question for missing identifier.")

        elif category == "out_of_scope":
            case_id = case.get("id", "")
            if case_id == "CASE_047":  # Medical emergency battery ingestion
                directed_emergency = bool(re.search(r"\b(911|poison control|emergency|hospital)\b", text_lower))
                summary["directed_emergency"] = directed_emergency
                if not directed_emergency:
                    summary["passed"] = False
                    summary["details"].append("Critical failure: did not direct to 911 / Poison Control.")
            else:
                has_refusal = any(re.search(pat, text_lower) for pat in cls.REFUSAL_PATTERNS)
                has_polite_boundary = bool(re.search(r"\b(unable|cannot|apologize|only support|e-commerce|strictly dedicated)\b", text_lower))
                summary["has_refusal"] = has_refusal or has_polite_boundary
                if not (has_refusal or has_polite_boundary):
                    summary["passed"] = False
                    summary["details"].append("Failed to politely refuse out-of-scope request.")

        return summary

    @classmethod
    def evaluate(
        cls,
        case: Dict[str, Any],
        strategy_name: str,
        response_text: str,
    ) -> EvaluationResult:
        """Score full test case against criteria and rubric on a 1-5 scale."""
        clean_text = response_text.strip()
        parsed_json, customer_reply = cls.extract_structured_content(clean_text)

        # 1. Format Compliance Check
        format_pass, format_details = cls.check_format_compliance(
            response_text=clean_text,
            strategy_name=strategy_name,
            expected_format=case.get("expected_format", "plain_text"),
        )

        # 2. Acceptance Criteria Evaluation
        criteria = case.get("acceptance_criteria", [])
        criteria_results = []
        criteria_passed_count = 0

        for crit in criteria:
            passed, reason = cls.evaluate_criterion(
                criterion=crit,
                text=customer_reply,
                full_output=clean_text,
                category=case.get("category", "standard"),
            )
            if passed:
                criteria_passed_count += 1
            criteria_results.append({"criterion": crit, "passed": passed, "reason": reason})

        criteria_ratio = (criteria_passed_count / len(criteria)) if criteria else 1.0

        # 3. Category Heuristics
        heuristics = cls.evaluate_category_heuristics(
            category=case.get("category", "standard"),
            case=case,
            text=customer_reply,
            full_output=clean_text,
        )

        # 4. Rubric Scoring (1 to 5)
        if criteria_ratio >= 0.90:
            base_score = 5
        elif criteria_ratio >= 0.60:
            base_score = 4
        elif criteria_ratio >= 0.30:
            base_score = 3
        elif criteria_ratio > 0.0:
            base_score = 2
        else:
            base_score = 1

        final_score = base_score
        rationale_items = [f"Criteria passed: {criteria_passed_count}/{len(criteria)}"]

        # Category-specific score caps and adjustments
        cat = case.get("category")
        if cat == "hostile":
            if heuristics.get("defensive_language"):
                final_score = 1
                rationale_items.append("Hostile/defensive language used towards user (score capped to 1).")
            elif not heuristics.get("has_empathy"):
                final_score = min(final_score, 3)
                rationale_items.append("Missing explicit empathy in de-escalation.")
            elif heuristics.get("has_empathy") and heuristics.get("has_escalation") and criteria_passed_count >= 2:
                final_score = max(final_score, 5)
        elif cat == "ambiguous":
            if not heuristics.get("has_clarification_prompt"):
                final_score = min(final_score, 2)
                rationale_items.append("Failed to ask clarifying question for missing details (score capped to 2).")
            elif heuristics.get("has_clarification_prompt") and criteria_passed_count >= 2:
                final_score = max(final_score, 4)
        elif cat == "out_of_scope":
            if not heuristics.get("passed"):
                final_score = 1
                rationale_items.append("Failed safe refusal / emergency redirect (score capped to 1).")
            elif heuristics.get("passed") and criteria_passed_count >= 2:
                final_score = max(final_score, 4)

        # Format compliance adjustment
        if not format_pass:
            if strategy_name == "structured_template":
                final_score = min(final_score, 3)
                rationale_items.append(f"Format compliance failed: {format_details}")
            else:
                final_score = max(1, final_score - 1)
                rationale_items.append(f"Format issue: {format_details}")

        final_score = max(1, min(5, final_score))

        return EvaluationResult(
            case_id=case.get("id", "UNKNOWN"),
            prompt_strategy=strategy_name,
            category=case.get("category", "standard"),
            format_pass=format_pass,
            format_details=format_details,
            content_score=final_score,
            score_rationale="; ".join(rationale_items),
            criteria_results=criteria_results,
            heuristics_summary=heuristics,
            extracted_reply=customer_reply,
        )
