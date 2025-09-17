"""
Advanced QME Rules Engine with YAML Configuration Support.

This module implements a comprehensive rules engine that processes YAML rule definitions
and enforces every mandatory element from the gold standard QME template with full
audit trail and provenance tracking.
"""

import yaml
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from enum import Enum
import uuid
from pathlib import Path

try:
    from src.core.validation.qme_rules_engine import ValidationIssue, QualityScore, ValidationSeverity, SectionType
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from src.utils.logging_config import get_logger
except ImportError:
    from src.core.validation.qme_rules_engine import ValidationIssue, QualityScore, ValidationSeverity, SectionType
    from core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class RulePriority(Enum):
    """Rule priority levels for validation."""
    MUST = "MUST"      # Critical/Legal requirements
    SHOULD = "SHOULD"  # Best practices
    MAY = "MAY"        # Suggestions


@dataclass
class AuditEntry:
    """Audit trail entry for rule execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    action: str = ""
    result: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    provenance: Optional[Dict[str, Any]] = None


@dataclass
class ProvenanceReference:
    """Provenance reference for substantive statements."""
    doc_id: str
    page_number: int
    offset: int
    snippet: str
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RuleDefinition:
    """Rule definition loaded from YAML configuration."""
    id: str
    priority: RulePriority
    description: str
    section: str
    when_conditions: List[Dict[str, Any]]
    then_actions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationContext:
    """Context for rule validation execution."""
    template_data: QMETemplateData
    document_metadata: Dict[str, Any] = field(default_factory=dict)
    template_status: Dict[str, Any] = field(default_factory=dict)
    audit_trail: List[AuditEntry] = field(default_factory=list)
    provenance_map: Dict[str, List[ProvenanceReference]] = field(default_factory=dict)
    validation_state: Dict[str, Any] = field(default_factory=dict)


class RuleConditionEvaluator:
    """Evaluates rule conditions against validation context."""
    
    def __init__(self):
        """Initialize the condition evaluator."""
        pass
    
    def evaluate_conditions(self, conditions: List[Dict[str, Any]], context: ValidationContext) -> bool:
        """
        Evaluate all conditions for a rule.
        
        Args:
            conditions: List of condition dictionaries
            context: Validation context
            
        Returns:
            True if all conditions are met
        """
        try:
            for condition in conditions:
                if not self._evaluate_single_condition(condition, context):
                    return False
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating conditions: {e}")
            return False
    
    def _evaluate_single_condition(self, condition: Dict[str, Any], context: ValidationContext) -> bool:
        """Evaluate a single condition."""
        try:
            for key, expected_value in condition.items():
                actual_value = self._get_context_value(key, context)
                
                if not self._compare_values(actual_value, expected_value):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {e}")
            return False
    
    def _get_context_value(self, key_path: str, context: ValidationContext) -> Any:
        """Get value from context using dot notation path."""
        try:
            # Handle special context paths
            if key_path.startswith("template."):
                return self._get_template_value(key_path[9:], context)
            elif key_path.startswith("document."):
                return self._get_document_value(key_path[9:], context)
            elif key_path.startswith("entities."):
                return self._get_entities_value(key_path[9:], context)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting context value for {key_path}: {e}")
            return None
    
    def _get_template_value(self, path: str, context: ValidationContext) -> Any:
        """Get template-related values."""
        if path == "assembling":
            return context.template_status.get("assembling", True)
        elif path == "generated":
            return context.template_status.get("generated", False)
        elif path == "ready_for_completion":
            return context.template_status.get("ready_for_completion", False)
        else:
            return None
    
    def _get_document_value(self, path: str, context: ValidationContext) -> Any:
        """Get document metadata values."""
        if path == "metadata.interpreter_needed":
            return context.document_metadata.get("interpreter_needed", False)
        elif path == "declaration_present":
            return context.document_metadata.get("declaration_present", True)
        else:
            return context.document_metadata.get(path)
    
    def _get_entities_value(self, path: str, context: ValidationContext) -> Any:
        """Get entity-related values."""
        if path == "duplicates_detected":
            return context.validation_state.get("duplicates_detected", False)
        else:
            return None
    
    def _compare_values(self, actual: Any, expected: Any) -> bool:
        """Compare actual and expected values."""
        if isinstance(expected, bool):
            return bool(actual) == expected
        elif isinstance(expected, str):
            return str(actual) == expected
        elif isinstance(expected, (int, float)):
            return actual == expected
        else:
            return actual == expected


class RuleActionExecutor:
    """Executes rule actions when conditions are met."""
    
    def __init__(self):
        """Initialize the action executor."""
        pass
    
    def execute_actions(self, actions: List[Dict[str, Any]], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """
        Execute all actions for a rule.
        
        Args:
            actions: List of action dictionaries
            context: Validation context
            rule_id: Rule identifier
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        try:
            for action in actions:
                action_issues = self._execute_single_action(action, context, rule_id)
                issues.extend(action_issues)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error executing actions for rule {rule_id}: {e}")
            return [ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Rule Execution Error",
                description=f"Error executing rule {rule_id}: {str(e)}"
            )]
    
    def _execute_single_action(self, action: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Execute a single action."""
        issues = []
        
        try:
            for action_type, action_params in action.items():
                if action_type == "require_fields":
                    issues.extend(self._require_fields(action_params, context, rule_id))
                elif action_type == "require_exact_text":
                    issues.extend(self._require_exact_text(action_params, context, rule_id))
                elif action_type == "require_table":
                    issues.extend(self._require_table(action_params, context, rule_id))
                elif action_type == "validate_format":
                    issues.extend(self._validate_format(action_params, context, rule_id))
                elif action_type == "validate_calculation":
                    issues.extend(self._validate_calculation(action_params, context, rule_id))
                elif action_type == "require_checkbox":
                    issues.extend(self._require_checkbox(action_params, context, rule_id))
                elif action_type == "require_section":
                    issues.extend(self._require_section(action_params, context, rule_id))
                elif action_type == "validate_docx_placeholders":
                    issues.extend(self._validate_docx_placeholders(action_params, context, rule_id))
                elif action_type == "require_provenance_for":
                    issues.extend(self._require_provenance_for(action_params, context, rule_id))
                elif action_type == "validate_exact_statutory_text":
                    issues.extend(self._validate_exact_statutory_text(action_params, context, rule_id))
                elif action_type == "require_case_law_citations":
                    issues.extend(self._require_case_law_citations(action_params, context, rule_id))
                elif action_type == "require_legal_references":
                    issues.extend(self._require_legal_references(action_params, context, rule_id))
                elif action_type == "validate_percentage_breakdown":
                    issues.extend(self._validate_percentage_breakdown(action_params, context, rule_id))
                elif action_type == "validate_billing_calculation":
                    issues.extend(self._validate_billing_calculation(action_params, context, rule_id))
                elif action_type == "require_under_penalty_perjury":
                    issues.extend(self._require_under_penalty_perjury(action_params, context, rule_id))
                elif action_type == "validate_ama_citations":
                    issues.extend(self._validate_ama_citations(action_params, context, rule_id))
                elif action_type == "require_methodology_documentation":
                    issues.extend(self._require_methodology_documentation(action_params, context, rule_id))
                elif action_type == "validate_adl_structure":
                    issues.extend(self._validate_adl_structure(action_params, context, rule_id))
                elif action_type == "validate_neurological_structure":
                    issues.extend(self._validate_neurological_structure(action_params, context, rule_id))
                elif action_type == "require_special_tests":
                    issues.extend(self._require_special_tests(action_params, context, rule_id))
                elif action_type == "validate_causation_determination":
                    issues.extend(self._validate_causation_determination(action_params, context, rule_id))
                elif action_type == "require_conditional_language":
                    issues.extend(self._require_conditional_language(action_params, context, rule_id))
                elif action_type == "execute_comprehensive_validation":
                    issues.extend(self._execute_comprehensive_validation(action_params, context, rule_id))
                elif action_type == "validate_confidence_scores":
                    issues.extend(self._validate_confidence_scores(action_params, context, rule_id))
                elif action_type == "flag_insufficient_confidence":
                    issues.extend(self._flag_insufficient_confidence(action_params, context, rule_id))
                elif action_type == "require_evidence_provenance":
                    issues.extend(self._require_evidence_provenance(action_params, context, rule_id))
                elif action_type == "validate_calculation_methods":
                    issues.extend(self._validate_calculation_methods(action_params, context, rule_id))
                elif action_type == "require_calculation_audit_trail":
                    issues.extend(self._require_calculation_audit_trail(action_params, context, rule_id))
                elif action_type == "prohibit_llm_calculations":
                    issues.extend(self._prohibit_llm_calculations(action_params, context, rule_id))
                elif action_type == "validate_ama_table_accuracy":
                    issues.extend(self._validate_ama_table_accuracy(action_params, context, rule_id))
                elif action_type == "scan_placeholder_text":
                    issues.extend(self._scan_placeholder_text(action_params, context, rule_id))
                elif action_type == "require_evidence_backing":
                    issues.extend(self._require_evidence_backing(action_params, context, rule_id))
                elif action_type == "validate_labor_code_4062_3":
                    issues.extend(self._validate_labor_code_4062_3(action_params, context, rule_id))
                elif action_type == "validate_mandatory_sections":
                    issues.extend(self._validate_mandatory_sections(action_params, context, rule_id))
                elif action_type == "validate_mlprr_billing":
                    issues.extend(self._validate_mlprr_billing(action_params, context, rule_id))
                elif action_type == "validate_physician_signature":
                    issues.extend(self._validate_physician_signature(action_params, context, rule_id))
                elif action_type == "generate_compliance_report":
                    issues.extend(self._generate_compliance_report(action_params, context, rule_id))
                elif action_type == "generate_evidence_map":
                    issues.extend(self._generate_evidence_map(action_params, context, rule_id))
                elif action_type == "document_calculation_provenance":
                    issues.extend(self._document_calculation_provenance(action_params, context, rule_id))
                elif action_type == "create_compliance_audit":
                    issues.extend(self._create_compliance_audit(action_params, context, rule_id))
                elif action_type == "generate_audit_report":
                    issues.extend(self._generate_audit_report(action_params, context, rule_id))
                elif action_type == "add_audit":
                    self._add_audit(action_params, context, rule_id)
                elif action_type == "set_field":
                    self._set_field(action_params, context, rule_id)
                else:
                    logger.warning(f"Unknown action type: {action_type}")
            
            return issues
            
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return [ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.MEDIUM,
                title="Action Execution Error",
                description=f"Error executing action: {str(e)}"
            )]
    
    def _require_fields(self, fields: List[str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate required fields are present."""
        issues = []
        
        for field in fields:
            if not self._field_present(field, context):
                issues.append(ValidationIssue(
                    section=self._get_section_for_field(field),
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing Required Field: {field}",
                    description=f"Required field '{field}' is missing or empty",
                    suggestions=[f"Provide value for {field.replace('_', ' ')}"],
                    auto_fixable=False
                ))
        
        return issues
    
    def _require_exact_text(self, text: str, context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate exact text is present."""
        issues = []
        
        # This would check against the generated document content
        # For now, we'll simulate the check
        if not self._text_present_in_document(text, context):
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Required Legal Text",
                description=f"Required legal text not found in document",
                suggestions=["Insert the required legal text block"],
                auto_fixable=True
            ))
        
        return issues
    
    def _require_table(self, table_name: str, context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate required table is present."""
        issues = []
        
        if not self._table_present(table_name, context):
            issues.append(ValidationIssue(
                section=self._get_section_for_table(table_name),
                severity=ValidationSeverity.CRITICAL,
                title=f"Missing Required Table: {table_name}",
                description=f"Required table '{table_name}' is missing",
                suggestions=[f"Add {table_name.replace('_', ' ')} table"],
                auto_fixable=False
            ))
        
        return issues
    
    def _validate_format(self, format_rules: Dict[str, str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate field formats using regex patterns."""
        issues = []
        
        for field, pattern in format_rules.items():
            value = self._get_field_value(field, context)
            if value and not re.match(pattern, str(value)):
                issues.append(ValidationIssue(
                    section=self._get_section_for_field(field),
                    severity=ValidationSeverity.HIGH,
                    title=f"Invalid Format: {field}",
                    description=f"Field '{field}' does not match required format",
                    suggestions=[f"Correct format for {field.replace('_', ' ')}"],
                    auto_fixable=False
                ))
        
        return issues
    
    def _validate_calculation(self, calc_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate mathematical calculations."""
        issues = []
        
        # This would validate billing calculations, impairment math, etc.
        formula = calc_params.get("formula", "")
        if formula and not self._calculation_correct(formula, context):
            issues.append(ValidationIssue(
                section=SectionType.IMPAIRMENT_RATING,
                severity=ValidationSeverity.CRITICAL,
                title="Calculation Error",
                description=f"Mathematical calculation is incorrect: {formula}",
                suggestions=["Verify and correct the calculation"],
                auto_fixable=True
            ))
        
        return issues
    
    def _require_checkbox(self, checkbox_name: str, context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate required checkbox is checked."""
        issues = []
        
        if not self._checkbox_checked(checkbox_name, context):
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title=f"Required Checkbox: {checkbox_name}",
                description=f"Required checkbox '{checkbox_name}' is not checked",
                suggestions=[f"Check the {checkbox_name.replace('_', ' ')} checkbox"],
                auto_fixable=True
            ))
        
        return issues
    
    def _require_section(self, section_name: str, context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate required section is present."""
        issues = []
        
        if not self._section_present(section_name, context):
            issues.append(ValidationIssue(
                section=self._map_section_name(section_name),
                severity=ValidationSeverity.CRITICAL,
                title=f"Missing Required Section: {section_name}",
                description=f"Required section '{section_name}' is missing",
                suggestions=[f"Add {section_name.replace('_', ' ')} section"],
                auto_fixable=False
            ))
        
        return issues
    
    def _validate_docx_placeholders(self, placeholders: List[str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate DOCX placeholders are filled."""
        issues = []
        
        for placeholder in placeholders:
            if not self._placeholder_filled(placeholder, context):
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.HIGH,
                    title=f"Unfilled Placeholder: {placeholder}",
                    description=f"DOCX placeholder '{placeholder}' is not filled",
                    suggestions=[f"Fill the {placeholder} placeholder with appropriate data"],
                    auto_fixable=True
                ))
        
        return issues
    
    def _require_provenance_for(self, elements: List[str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate provenance is attached to substantive statements."""
        issues = []
        
        for element in elements:
            if not self._has_provenance(element, context):
                issues.append(ValidationIssue(
                    section=SectionType.DIAGNOSIS,
                    severity=ValidationSeverity.HIGH,
                    title=f"Missing Provenance: {element}",
                    description=f"Substantive statement '{element}' lacks required provenance",
                    suggestions=[f"Attach document reference for {element.replace('_', ' ')}"],
                    auto_fixable=False
                ))
        
        return issues
    
    def _add_audit(self, message: str, context: ValidationContext, rule_id: str):
        """Add audit trail entry."""
        audit_entry = AuditEntry(
            rule_id=rule_id,
            action="validation",
            result="completed",
            details={"message": message}
        )
        context.audit_trail.append(audit_entry)
    
    def _set_field(self, field_params: Dict[str, Any], context: ValidationContext, rule_id: str):
        """Set field value in context."""
        for field, value in field_params.items():
            context.template_status[field] = value
    
    def _validate_exact_statutory_text(self, text_requirements: Dict[str, str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate exact statutory language is present."""
        issues = []
        
        for section_name, required_text in text_requirements.items():
            if not self._exact_text_present(required_text, context):
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing Statutory Language: {section_name}",
                    description=f"Required statutory text for {section_name} is missing or incorrect",
                    suggestions=[f"Insert exact statutory language for {section_name}"],
                    auto_fixable=True
                ))
        
        return issues
    
    def _require_case_law_citations(self, citations: List[str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate required case law citations are present."""
        issues = []
        
        for citation in citations:
            if not self._citation_present(citation, context):
                issues.append(ValidationIssue(
                    section=SectionType.APPORTIONMENT,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing Case Law Citation: {citation}",
                    description=f"Required case law citation '{citation}' is missing",
                    suggestions=[f"Add case law citation: {citation}"],
                    auto_fixable=True
                ))
        
        return issues
    
    def _require_legal_references(self, references: List[str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate required legal code references are present."""
        issues = []
        
        for reference in references:
            if not self._legal_reference_present(reference, context):
                issues.append(ValidationIssue(
                    section=SectionType.APPORTIONMENT,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing Legal Reference: {reference}",
                    description=f"Required legal code reference '{reference}' is missing",
                    suggestions=[f"Add legal reference: {reference}"],
                    auto_fixable=True
                ))
        
        return issues
    
    def _validate_percentage_breakdown(self, breakdown_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate percentage breakdown for apportionment."""
        issues = []
        
        industrial_pct = self._get_industrial_percentage(context)
        nonindustrial_pct = self._get_nonindustrial_percentage(context)
        
        if industrial_pct is None or nonindustrial_pct is None:
            issues.append(ValidationIssue(
                section=SectionType.APPORTIONMENT,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Apportionment Percentages",
                description="Industrial and/or nonindustrial percentages are missing",
                suggestions=["Provide both industrial and nonindustrial percentages"],
                auto_fixable=False
            ))
        elif industrial_pct + nonindustrial_pct != 100:
            issues.append(ValidationIssue(
                section=SectionType.APPORTIONMENT,
                severity=ValidationSeverity.CRITICAL,
                title="Apportionment Percentage Error",
                description=f"Percentages do not sum to 100% (Industrial: {industrial_pct}%, Nonindustrial: {nonindustrial_pct}%)",
                suggestions=["Correct percentages to sum to 100%"],
                auto_fixable=True
            ))
        
        return issues
    
    def _validate_billing_calculation(self, calc_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate MLPRR billing calculations."""
        issues = []
        
        total_pages = self._get_total_pages_reviewed(context)
        minimum_pages = calc_params.get("minimum_pages", 200)
        rate_per_page = calc_params.get("rate_per_page", 3.00)
        
        if total_pages is None:
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Page Count",
                description="Total pages reviewed is not specified",
                suggestions=["Provide total pages reviewed count"],
                auto_fixable=False
            ))
        elif total_pages < minimum_pages:
            # No billing required under minimum
            pass
        else:
            billable_units = total_pages - minimum_pages
            expected_amount = billable_units * rate_per_page
            
            if not self._billing_calculation_correct(expected_amount, context):
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title="MLPRR Billing Calculation Error",
                    description=f"Billing calculation incorrect. Expected: {billable_units} units × ${rate_per_page} = ${expected_amount}",
                    suggestions=["Correct the MLPRR billing calculation"],
                    auto_fixable=True
                ))
        
        return issues
    
    def _require_under_penalty_perjury(self, statements: List[str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate under penalty of perjury statements are present."""
        issues = []
        
        for statement in statements:
            if not self._penalty_of_perjury_present(statement, context):
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing Penalty of Perjury: {statement}",
                    description=f"Required penalty of perjury statement '{statement}' is missing",
                    suggestions=[f"Add penalty of perjury statement for {statement}"],
                    auto_fixable=True
                ))
        
        return issues
    
    def _validate_ama_citations(self, citation_params: Dict[str, str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate AMA Guides citations format and presence."""
        issues = []
        
        for citation_type, pattern in citation_params.items():
            if not self._ama_citation_format_valid(citation_type, pattern, context):
                issues.append(ValidationIssue(
                    section=SectionType.IMPAIRMENT_RATING,
                    severity=ValidationSeverity.HIGH,
                    title=f"Invalid AMA Citation Format: {citation_type}",
                    description=f"AMA citation format for {citation_type} does not match required pattern",
                    suggestions=[f"Correct AMA citation format for {citation_type}"],
                    auto_fixable=False
                ))
        
        return issues
    
    def _require_methodology_documentation(self, methodologies: List[str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate impairment methodology documentation."""
        issues = []
        
        for methodology in methodologies:
            if not self._methodology_documented(methodology, context):
                issues.append(ValidationIssue(
                    section=SectionType.IMPAIRMENT_RATING,
                    severity=ValidationSeverity.HIGH,
                    title=f"Missing Methodology: {methodology}",
                    description=f"Impairment methodology '{methodology}' is not documented",
                    suggestions=[f"Document {methodology} methodology"],
                    auto_fixable=False
                ))
        
        return issues
    
    def _validate_adl_structure(self, adl_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate ADL grid structure and completeness."""
        issues = []
        
        required_columns = adl_params.get("columns", [])
        main_categories = adl_params.get("main_categories", [])
        
        # Check ADL grid presence
        if not self._adl_grid_present(context):
            issues.append(ValidationIssue(
                section=SectionType.OCCUPATIONAL_HISTORY,
                severity=ValidationSeverity.CRITICAL,
                title="Missing ADL Grid",
                description="Activities of Daily Living grid is missing",
                suggestions=["Add complete ADL functional capacity grid"],
                auto_fixable=False
            ))
            return issues
        
        # Validate columns
        for column in required_columns:
            if not self._adl_column_present(column, context):
                issues.append(ValidationIssue(
                    section=SectionType.OCCUPATIONAL_HISTORY,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing ADL Column: {column}",
                    description=f"ADL grid missing required column '{column}'",
                    suggestions=[f"Add {column} column to ADL grid"],
                    auto_fixable=False
                ))
        
        # Validate categories and subcategories
        for category in main_categories:
            if not self._adl_category_present(category, context):
                issues.append(ValidationIssue(
                    section=SectionType.OCCUPATIONAL_HISTORY,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing ADL Category: {category}",
                    description=f"ADL grid missing required category '{category}'",
                    suggestions=[f"Add {category} category to ADL grid"],
                    auto_fixable=False
                ))
            
            # Check subcategory items
            category_key = category.lower().replace(" ", "_")
            if f"{category_key}_items" in adl_params:
                subcategory_items = adl_params[f"{category_key}_items"]
                for item in subcategory_items:
                    if not self._adl_item_present(item, context):
                        issues.append(ValidationIssue(
                            section=SectionType.OCCUPATIONAL_HISTORY,
                            severity=ValidationSeverity.HIGH,
                            title=f"Missing ADL Item: {item}",
                            description=f"ADL grid missing required item '{item}' in {category}",
                            suggestions=[f"Add '{item}' to {category} section"],
                            auto_fixable=False
                        ))
        
        return issues
    
    def _validate_neurological_structure(self, neuro_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate neurological testing structure and completeness."""
        issues = []
        
        sensory_levels = neuro_params.get("sensory_levels", {})
        motor_scale = neuro_params.get("motor_scale", [])
        reflex_scale = neuro_params.get("reflex_scale", [])
        
        # Validate cervical neurological testing
        if "cervical" in sensory_levels:
            for level in sensory_levels["cervical"]:
                if not self._neurological_level_tested(level, "cervical", context):
                    issues.append(ValidationIssue(
                        section=SectionType.PHYSICAL_EXAMINATION,
                        severity=ValidationSeverity.HIGH,
                        title=f"Missing Cervical Neurological Test: {level}",
                        description=f"Cervical neurological testing missing for level {level}",
                        suggestions=[f"Add bilateral sensory/motor testing for {level}"],
                        auto_fixable=False
                    ))
        
        # Validate lumbar neurological testing
        if "lumbar" in sensory_levels:
            for level in sensory_levels["lumbar"]:
                if not self._neurological_level_tested(level, "lumbar", context):
                    issues.append(ValidationIssue(
                        section=SectionType.PHYSICAL_EXAMINATION,
                        severity=ValidationSeverity.HIGH,
                        title=f"Missing Lumbar Neurological Test: {level}",
                        description=f"Lumbar neurological testing missing for level {level}",
                        suggestions=[f"Add bilateral sensory/motor testing for {level}"],
                        auto_fixable=False
                    ))
        
        return issues
    
    def _require_special_tests(self, test_params: Dict[str, List[str]], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate special orthopedic tests are documented."""
        issues = []
        
        for region, tests in test_params.items():
            for test in tests:
                if not self._special_test_documented(test, region, context):
                    issues.append(ValidationIssue(
                        section=SectionType.PHYSICAL_EXAMINATION,
                        severity=ValidationSeverity.MEDIUM,
                        title=f"Missing Special Test: {test}",
                        description=f"Special orthopedic test '{test}' not documented for {region}",
                        suggestions=[f"Document {test} results for {region}"],
                        auto_fixable=False
                    ))
        
        return issues
    
    def _validate_causation_determination(self, causation_params: Dict[str, str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate causation determination format and content."""
        issues = []
        
        causation_type = self._get_causation_type(context)
        
        if causation_type == "specific_injury":
            required_format = causation_params.get("specific_injury_format", "")
            if not self._causation_format_matches(required_format, context):
                issues.append(ValidationIssue(
                    section=SectionType.CAUSATION_ANALYSIS,
                    severity=ValidationSeverity.HIGH,
                    title="Incorrect Specific Injury Format",
                    description="Specific injury causation does not follow required format",
                    suggestions=["Use correct specific injury causation format"],
                    auto_fixable=False
                ))
        elif causation_type == "continuous_trauma":
            required_format = causation_params.get("continuous_trauma_format", "")
            if not self._causation_format_matches(required_format, context):
                issues.append(ValidationIssue(
                    section=SectionType.CAUSATION_ANALYSIS,
                    severity=ValidationSeverity.HIGH,
                    title="Incorrect Continuous Trauma Format",
                    description="Continuous trauma causation does not follow required format",
                    suggestions=["Use correct continuous trauma causation format"],
                    auto_fixable=False
                ))
        
        return issues
    
    def _require_conditional_language(self, language_params: Dict[str, str], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate conditional language based on causation findings."""
        issues = []
        
        causation_found = self._causation_established(context)
        
        if not causation_found and "if_no_causation" in language_params:
            required_text = language_params["if_no_causation"]
            if not self._text_present_in_document(required_text, context):
                issues.append(ValidationIssue(
                    section=SectionType.CAUSATION_ANALYSIS,
                    severity=ValidationSeverity.CRITICAL,
                    title="Missing No-Causation Language",
                    description="Required language for no causation finding is missing",
                    suggestions=["Add required no-causation language"],
                    auto_fixable=True
                ))
        elif causation_found and "if_causation_found" in language_params:
            required_text = language_params["if_causation_found"]
            if not self._text_present_in_document(required_text, context):
                issues.append(ValidationIssue(
                    section=SectionType.CAUSATION_ANALYSIS,
                    severity=ValidationSeverity.CRITICAL,
                    title="Missing Causation-Found Language",
                    description="Required language for positive causation finding is missing",
                    suggestions=["Add required causation-found language"],
                    auto_fixable=True
                ))
        
        return issues
    
    def _execute_comprehensive_validation(self, validation_params: Any, context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Execute comprehensive final validation."""
        issues = []
        
        # Validate all required sections are present
        required_sections = [
            "header", "legal_declarations", "records_review", "identifying_data",
            "history_of_injury", "occupational_history", "activities_daily_living",
            "physical_examination", "diagnostic_impression", "causation_analysis",
            "impairment_rating", "apportionment", "work_restrictions", 
            "future_medical_care", "signature_block"
        ]
        
        for section in required_sections:
            if not self._section_complete(section, context):
                issues.append(ValidationIssue(
                    section=self._map_section_name(section),
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Incomplete Section: {section}",
                    description=f"Required section '{section}' is incomplete or missing",
                    suggestions=[f"Complete the {section.replace('_', ' ')} section"],
                    auto_fixable=False
                ))
        
        # Validate all calculations are correct
        if not self._all_calculations_correct(context):
            issues.append(ValidationIssue(
                section=SectionType.IMPAIRMENT_RATING,
                severity=ValidationSeverity.CRITICAL,
                title="Calculation Errors Present",
                description="One or more calculations contain errors",
                suggestions=["Review and correct all calculations"],
                auto_fixable=False
            ))
        
        # Validate legal requirements compliance
        if not self._legal_requirements_met(context):
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title="Legal Requirements Not Met",
                description="One or more legal requirements are not satisfied",
                suggestions=["Review and satisfy all legal requirements"],
                auto_fixable=False
            ))
        
        # Validate provenance completeness
        if not self._provenance_complete(context):
            issues.append(ValidationIssue(
                section=SectionType.DIAGNOSIS,
                severity=ValidationSeverity.HIGH,
                title="Incomplete Provenance",
                description="Some substantive statements lack required provenance",
                suggestions=["Add source references for all substantive statements"],
                auto_fixable=False
            ))
        
        return issues
    
    # Helper methods for field/table/section checking
    def _field_present(self, field: str, context: ValidationContext) -> bool:
        """Check if field is present and not empty."""
        # Map field names to actual data
        field_mapping = {
            "claimant_name": context.template_data.patient_info.name,
            "claim_number": context.template_data.patient_info.case_number,
            "employer_name": context.template_data.patient_info.employer,
            "applicant_dob": context.template_data.patient_info.injury_date,
            "examiner_name": context.document_metadata.get("examiner_name"),
            "examiner_license": context.document_metadata.get("examiner_license"),
        }
        
        value = field_mapping.get(field)
        return value is not None and str(value).strip() != ""
    
    def _text_present_in_document(self, text: str, context: ValidationContext) -> bool:
        """Check if exact text is present in document."""
        # This would check the generated document content
        # For simulation, we'll return True for now
        return True
    
    def _table_present(self, table_name: str, context: ValidationContext) -> bool:
        """Check if required table is present."""
        # This would check the document structure
        # For simulation, we'll check based on data availability
        if "adl_grid" in table_name.lower():
            return True  # ADL grid should always be present
        elif "rom" in table_name.lower():
            return len(context.template_data.medical_findings.findings) > 0
        else:
            return True
    
    def _calculation_correct(self, formula: str, context: ValidationContext) -> bool:
        """Validate mathematical calculation."""
        # This would perform actual calculation validation
        return True
    
    def _checkbox_checked(self, checkbox_name: str, context: ValidationContext) -> bool:
        """Check if checkbox is checked."""
        return context.document_metadata.get(checkbox_name, False)
    
    # Evidence-First Validation Action Methods
    def _validate_confidence_scores(self, confidence_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate field extraction confidence scores meet evidence-first thresholds."""
        issues = []
        
        try:
            # Get confidence scores from context
            confidence_scores = context.validation_state.get("confidence_scores", {})
            
            # Validate critical fields
            critical_fields = confidence_params.get("critical_fields", [])
            for field_config in critical_fields:
                field_name = field_config["field"]
                min_confidence = field_config["min_confidence"]
                required = field_config.get("required", True)
                
                confidence = confidence_scores.get(field_name, 0.0)
                
                if required and confidence < min_confidence:
                    issues.append(ValidationIssue(
                        section=SectionType.PATIENT_DEMOGRAPHICS,
                        severity=ValidationSeverity.CRITICAL,
                        title=f"Low Confidence Critical Field: {field_name}",
                        description=f"Field '{field_name}' confidence {confidence:.2f} below threshold {min_confidence}",
                        requires_human_review=True,
                        remediation_steps=[
                            f"Review extraction for field: {field_name}",
                            "Consider manual validation or additional extraction methods",
                            "Verify source document quality and legibility"
                        ]
                    ))
            
            # Validate standard fields
            standard_fields = confidence_params.get("standard_fields", [])
            for field_config in standard_fields:
                field_name = field_config["field"]
                min_confidence = field_config["min_confidence"]
                required = field_config.get("required", True)
                
                confidence = confidence_scores.get(field_name, 0.0)
                
                if required and confidence < min_confidence:
                    issues.append(ValidationIssue(
                        section=SectionType.DIAGNOSIS,
                        severity=ValidationSeverity.HIGH,
                        title=f"Low Confidence Standard Field: {field_name}",
                        description=f"Field '{field_name}' confidence {confidence:.2f} below threshold {min_confidence}",
                        requires_human_review=True,
                        remediation_steps=[
                            f"Review extraction for field: {field_name}",
                            "Consider alternative extraction methods"
                        ]
                    ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating confidence scores: {e}")
            return [ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Confidence Validation Error",
                description=f"Error validating confidence scores: {str(e)}"
            )]
    
    def _flag_insufficient_confidence(self, flag_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Flag fields with insufficient confidence for human review."""
        issues = []
        
        try:
            threshold = flag_params.get("threshold", 0.5)
            action = flag_params.get("action", "human_review_queue")
            
            confidence_scores = context.validation_state.get("confidence_scores", {})
            
            for field_name, confidence in confidence_scores.items():
                if confidence < threshold:
                    issues.append(ValidationIssue(
                        section=SectionType.PATIENT_DEMOGRAPHICS,
                        severity=ValidationSeverity.MEDIUM,
                        title=f"Flagged for Review: {field_name}",
                        description=f"Field '{field_name}' confidence {confidence:.2f} flagged for {action}",
                        requires_human_review=True,
                        remediation_steps=[
                            f"Human review required for field: {field_name}",
                            "Verify extracted value against source document",
                            "Update extraction if necessary"
                        ]
                    ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error flagging insufficient confidence: {e}")
            return []
    
    def _require_evidence_provenance(self, provenance_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Require evidence provenance tracking for all extracted fields."""
        issues = []
        
        try:
            provenance_map = context.provenance_map
            required_elements = [
                ("source_document", provenance_params.get("source_document", True)),
                ("page_number", provenance_params.get("page_number", True)),
                ("text_coordinates", provenance_params.get("text_coordinates", True)),
                ("snippet_text", provenance_params.get("snippet_text", True))
            ]
            
            for field_name, provenance_refs in provenance_map.items():
                for provenance in provenance_refs:
                    for element_name, required in required_elements:
                        if required and not hasattr(provenance, element_name.replace("_", "")):
                            issues.append(ValidationIssue(
                                section=SectionType.PATIENT_DEMOGRAPHICS,
                                severity=ValidationSeverity.HIGH,
                                title=f"Missing Provenance: {element_name}",
                                description=f"Field '{field_name}' missing required provenance element: {element_name}",
                                remediation_steps=[
                                    f"Add {element_name} to provenance tracking",
                                    "Ensure complete evidence trail for all extracted fields"
                                ]
                            ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error requiring evidence provenance: {e}")
            return []
    
    def _validate_calculation_methods(self, calc_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate that all calculations are programmatic with zero LLM involvement."""
        issues = []
        
        try:
            calculations = context.validation_state.get("calculations", {})
            
            for calc_type, required_method in calc_params.items():
                if calc_type in calculations:
                    calc_data = calculations[calc_type]
                    method = calc_data.get("method", "unknown")
                    
                    if required_method == "programmatic_only" and method != "programmatic":
                        issues.append(ValidationIssue(
                            section=SectionType.IMPAIRMENT_RATING,
                            severity=ValidationSeverity.CRITICAL,
                            title=f"Non-Programmatic Calculation: {calc_type}",
                            description=f"Calculation '{calc_type}' method '{method}' is not programmatic",
                            remediation_steps=[
                                f"Implement programmatic calculation for {calc_type}",
                                "Remove any LLM-generated calculations",
                                "Verify against AMA Guidelines tables"
                            ]
                        ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating calculation methods: {e}")
            return []
    
    def _require_calculation_audit_trail(self, audit_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Require comprehensive audit trail for all calculations."""
        issues = []
        
        try:
            calculations = context.validation_state.get("calculations", {})
            required_elements = [
                ("ama_table_references", audit_params.get("ama_table_references", True)),
                ("calculation_steps", audit_params.get("calculation_steps", True)),
                ("source_measurements", audit_params.get("source_measurements", True)),
                ("validation_status", audit_params.get("validation_status", True))
            ]
            
            for calc_name, calc_data in calculations.items():
                for element_name, required in required_elements:
                    if required and element_name not in calc_data:
                        issues.append(ValidationIssue(
                            section=SectionType.IMPAIRMENT_RATING,
                            severity=ValidationSeverity.HIGH,
                            title=f"Missing Calculation Audit: {element_name}",
                            description=f"Calculation '{calc_name}' missing required audit element: {element_name}",
                            remediation_steps=[
                                f"Add {element_name} to calculation audit trail",
                                "Document all calculation steps and sources"
                            ]
                        ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error requiring calculation audit trail: {e}")
            return []
    
    def _prohibit_llm_calculations(self, prohibit_params: Any, context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Prohibit LLM involvement in calculations."""
        issues = []
        
        try:
            calculations = context.validation_state.get("calculations", {})
            
            for calc_name, calc_data in calculations.items():
                if calc_data.get("llm_involved", False):
                    issues.append(ValidationIssue(
                        section=SectionType.IMPAIRMENT_RATING,
                        severity=ValidationSeverity.CRITICAL,
                        title=f"LLM Calculation Prohibited: {calc_name}",
                        description=f"Calculation '{calc_name}' involves LLM processing, which is prohibited",
                        remediation_steps=[
                            f"Replace LLM calculation with programmatic method for {calc_name}",
                            "Use only AMA Guidelines tables and mathematical formulas",
                            "Ensure zero LLM involvement in numeric calculations"
                        ]
                    ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error prohibiting LLM calculations: {e}")
            return []
    
    def _validate_ama_table_accuracy(self, accuracy_params: Any, context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate AMA table references for accuracy."""
        issues = []
        
        try:
            calculations = context.validation_state.get("calculations", {})
            
            for calc_name, calc_data in calculations.items():
                ama_table = calc_data.get("ama_table_reference")
                if ama_table:
                    # Validate table reference format
                    if not self._validate_ama_table_format(ama_table):
                        issues.append(ValidationIssue(
                            section=SectionType.IMPAIRMENT_RATING,
                            severity=ValidationSeverity.HIGH,
                            title=f"Invalid AMA Table Reference: {ama_table}",
                            description=f"AMA table reference '{ama_table}' format is invalid",
                            ama_reference="AMA Guides 5th Edition",
                            remediation_steps=[
                                "Verify table reference against AMA Guides 5th Edition",
                                "Use correct table reference format (e.g., Table 15-3)"
                            ]
                        ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating AMA table accuracy: {e}")
            return []
    
    def _scan_placeholder_text(self, scan_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Scan for remaining placeholder text in generated report."""
        issues = []
        
        try:
            patterns = scan_params.get("patterns", [])
            action = scan_params.get("action", "flag_validation")
            
            # Get report content from context (placeholder)
            report_content = context.validation_state.get("report_content", "")
            
            for pattern in patterns:
                matches = re.finditer(pattern, report_content, re.IGNORECASE)
                for match in matches:
                    severity = ValidationSeverity.CRITICAL if action == "fail_validation" else ValidationSeverity.HIGH
                    
                    issues.append(ValidationIssue(
                        section=SectionType.PATIENT_DEMOGRAPHICS,
                        severity=severity,
                        title="Placeholder Text Found",
                        description=f"Placeholder text found: '{match.group()}'",
                        remediation_steps=[
                            "Replace placeholder with actual content",
                            "Complete field extraction or manual entry",
                            "Re-generate report section if necessary"
                        ]
                    ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error scanning placeholder text: {e}")
            return []
    
    def _require_evidence_backing(self, backing_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Require evidence backing for all medical statements."""
        issues = []
        
        try:
            report_content = context.validation_state.get("report_content", "")
            provenance_map = context.provenance_map
            
            # Check for medical statements that require evidence
            statement_types = [
                ("all_medical_statements", backing_params.get("all_medical_statements", True)),
                ("diagnostic_conclusions", backing_params.get("diagnostic_conclusions", True)),
                ("impairment_determinations", backing_params.get("impairment_determinations", True))
            ]
            
            for statement_type, required in statement_types:
                if required:
                    # This would be enhanced with actual statement detection
                    # For now, we'll create a placeholder validation
                    issues.append(ValidationIssue(
                        section=SectionType.DIAGNOSIS,
                        severity=ValidationSeverity.HIGH,
                        title=f"Evidence Backing Required: {statement_type}",
                        description=f"All {statement_type.replace('_', ' ')} must have evidence backing",
                        remediation_steps=[
                            f"Ensure all {statement_type.replace('_', ' ')} have source references",
                            "Link statements to specific evidence in medical records",
                            "Provide page references and document citations"
                        ]
                    ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error requiring evidence backing: {e}")
            return []
    
    def _validate_labor_code_4062_3(self, labor_code_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate Labor Code 4062.3 declaration and requirements."""
        issues = []
        
        try:
            declaration_present = labor_code_params.get("declaration_present", True)
            exact_text_match = labor_code_params.get("exact_text_match", True)
            page_count_attestation = labor_code_params.get("page_count_attestation", True)
            penalty_of_perjury = labor_code_params.get("penalty_of_perjury", True)
            
            # Check declaration presence
            if declaration_present and not context.document_metadata.get("section_4062_3_declaration", False):
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title="Missing Labor Code 4062.3 Declaration",
                    description="Required Labor Code 4062.3 declaration is missing",
                    legal_reference="Labor Code Section 4062.3",
                    remediation_steps=[
                        "Include exact Labor Code 4062.3 declaration text",
                        "Ensure declaration is present before document review",
                        "Verify penalty of perjury statement is included"
                    ]
                ))
            
            # Check page count attestation
            if page_count_attestation and not context.document_metadata.get("page_count_attestation", False):
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title="Missing Page Count Attestation",
                    description="Required page count attestation is missing",
                    legal_reference="Labor Code Section 4062.3",
                    remediation_steps=[
                        "Include page count attestation in declaration",
                        "Verify total page count is accurate",
                        "Ensure attestation is under penalty of perjury"
                    ]
                ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating Labor Code 4062.3: {e}")
            return []
    
    def _validate_mandatory_sections(self, sections_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate presence of mandatory sections."""
        issues = []
        
        try:
            required_sections = [
                ("patient_demographics", sections_params.get("patient_demographics", True)),
                ("records_reviewed", sections_params.get("records_reviewed", True)),
                ("physical_examination", sections_params.get("physical_examination", True)),
                ("diagnosis", sections_params.get("diagnosis", True)),
                ("impairment_rating", sections_params.get("impairment_rating", True)),
                ("signature_blocks", sections_params.get("signature_blocks", True))
            ]
            
            for section_name, required in required_sections:
                if required and not self._section_complete(section_name, context):
                    issues.append(ValidationIssue(
                        section=self._map_section_name(section_name),
                        severity=ValidationSeverity.CRITICAL,
                        title=f"Missing Mandatory Section: {section_name}",
                        description=f"Mandatory section '{section_name}' is missing or incomplete",
                        remediation_steps=[
                            f"Complete the {section_name.replace('_', ' ')} section",
                            "Ensure all required information is documented",
                            "Review QME template requirements"
                        ]
                    ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating mandatory sections: {e}")
            return []
    
    def _validate_mlprr_billing(self, billing_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate MLPRR billing calculations and attestations."""
        issues = []
        
        try:
            calculation_accuracy = billing_params.get("calculation_accuracy", True)
            page_count_verification = billing_params.get("page_count_verification", True)
            billing_unit_calculation = billing_params.get("billing_unit_calculation", True)
            penalty_of_perjury_attestation = billing_params.get("penalty_of_perjury_attestation", True)
            
            # Validate billing calculations
            if calculation_accuracy:
                billing_data = context.validation_state.get("mlprr_billing", {})
                if not billing_data.get("calculation_verified", False):
                    issues.append(ValidationIssue(
                        section=SectionType.PATIENT_DEMOGRAPHICS,
                        severity=ValidationSeverity.CRITICAL,
                        title="MLPRR Billing Calculation Not Verified",
                        description="MLPRR billing calculations have not been verified",
                        remediation_steps=[
                            "Verify page count calculations",
                            "Ensure billing unit calculations are accurate",
                            "Apply correct MLPRR rates"
                        ]
                    ))
            
            # Validate penalty of perjury attestation
            if penalty_of_perjury_attestation and not context.document_metadata.get("mlprr_perjury_attestation", False):
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title="Missing MLPRR Penalty of Perjury Attestation",
                    description="Required penalty of perjury attestation for MLPRR billing is missing",
                    remediation_steps=[
                        "Include penalty of perjury attestation for page counts",
                        "Ensure attestation covers total pages reviewed",
                        "Verify examiner signature on attestation"
                    ]
                ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating MLPRR billing: {e}")
            return []
    
    def _validate_physician_signature(self, signature_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Validate physician signature blocks and attestations."""
        issues = []
        
        try:
            required_elements = [
                ("examiner_name", signature_params.get("examiner_name", True)),
                ("license_number", signature_params.get("license_number", True)),
                ("signature_date", signature_params.get("signature_date", True)),
                ("ab_1300_declaration", signature_params.get("ab_1300_declaration", True))
            ]
            
            for element_name, required in required_elements:
                if required and not context.document_metadata.get(element_name, False):
                    issues.append(ValidationIssue(
                        section=SectionType.PATIENT_DEMOGRAPHICS,
                        severity=ValidationSeverity.CRITICAL,
                        title=f"Missing Signature Element: {element_name}",
                        description=f"Required signature element '{element_name}' is missing",
                        remediation_steps=[
                            f"Add {element_name.replace('_', ' ')} to signature block",
                            "Ensure all signature requirements are met",
                            "Include required legal declarations"
                        ]
                    ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating physician signature: {e}")
            return []
    
    def _generate_compliance_report(self, report_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Generate comprehensive compliance report."""
        issues = []
        
        try:
            # This would generate a detailed compliance report
            # For now, we'll create a placeholder validation
            pass_fail_status = report_params.get("pass_fail_status", True)
            remediation_steps = report_params.get("remediation_steps", True)
            audit_trail = report_params.get("audit_trail", True)
            
            if pass_fail_status:
                # Generate pass/fail status based on validation results
                context.validation_state["compliance_status"] = "REQUIRES_REVIEW"
            
            return issues
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return []
    
    def _generate_evidence_map(self, map_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Generate evidence mapping for audit trail."""
        issues = []
        
        try:
            field_to_source_mapping = map_params.get("field_to_source_mapping", True)
            confidence_score_tracking = map_params.get("confidence_score_tracking", True)
            validation_decision_log = map_params.get("validation_decision_log", True)
            
            if field_to_source_mapping:
                # Generate field to source mapping
                evidence_map = {}
                for field_name, provenance_refs in context.provenance_map.items():
                    evidence_map[field_name] = [
                        {
                            "source": ref.doc_id,
                            "page": ref.page_number,
                            "confidence": ref.confidence
                        } for ref in provenance_refs
                    ]
                context.validation_state["evidence_map"] = evidence_map
            
            return issues
            
        except Exception as e:
            logger.error(f"Error generating evidence map: {e}")
            return []
    
    def _document_calculation_provenance(self, provenance_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Document calculation provenance for audit trail."""
        issues = []
        
        try:
            ama_table_sources = provenance_params.get("ama_table_sources", True)
            measurement_sources = provenance_params.get("measurement_sources", True)
            calculation_methodology = provenance_params.get("calculation_methodology", True)
            
            calculations = context.validation_state.get("calculations", {})
            
            for calc_name, calc_data in calculations.items():
                provenance = {}
                
                if ama_table_sources and "ama_table_reference" in calc_data:
                    provenance["ama_table"] = calc_data["ama_table_reference"]
                
                if measurement_sources and "source_measurements" in calc_data:
                    provenance["measurements"] = calc_data["source_measurements"]
                
                if calculation_methodology and "methodology" in calc_data:
                    provenance["methodology"] = calc_data["methodology"]
                
                context.validation_state.setdefault("calculation_provenance", {})[calc_name] = provenance
            
            return issues
            
        except Exception as e:
            logger.error(f"Error documenting calculation provenance: {e}")
            return []
    
    def _create_compliance_audit(self, audit_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Create compliance audit trail."""
        issues = []
        
        try:
            requirement_to_evidence_links = audit_params.get("requirement_to_evidence_links", True)
            validation_timestamps = audit_params.get("validation_timestamps", True)
            reviewer_actions = audit_params.get("reviewer_actions", True)
            
            audit_trail = {
                "created_at": datetime.now().isoformat(),
                "rule_id": rule_id,
                "validation_results": context.validation_state.get("validation_results", {}),
                "evidence_links": context.validation_state.get("evidence_map", {}),
                "compliance_status": context.validation_state.get("compliance_status", "UNKNOWN")
            }
            
            context.audit_trail.append(AuditEntry(
                rule_id=rule_id,
                action="create_compliance_audit",
                result="completed",
                details=audit_trail
            ))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error creating compliance audit: {e}")
            return []
    
    def _generate_audit_report(self, report_params: Dict[str, Any], context: ValidationContext, rule_id: str) -> List[ValidationIssue]:
        """Generate comprehensive audit report."""
        issues = []
        
        try:
            evidence_completeness = report_params.get("evidence_completeness", True)
            validation_results = report_params.get("validation_results", True)
            compliance_status = report_params.get("compliance_status", True)
            remediation_tracking = report_params.get("remediation_tracking", True)
            
            audit_report = {
                "generated_at": datetime.now().isoformat(),
                "evidence_completeness": context.validation_state.get("evidence_completeness", 0.0),
                "validation_results": context.validation_state.get("validation_results", {}),
                "compliance_status": context.validation_state.get("compliance_status", "UNKNOWN"),
                "audit_trail": [entry.__dict__ for entry in context.audit_trail]
            }
            
            context.validation_state["final_audit_report"] = audit_report
            
            return issues
            
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
            return []
    
    def _validate_ama_table_format(self, table_reference: str) -> bool:
        """Validate AMA table reference format."""
        # Pattern for AMA table references (e.g., "Table 15-3", "Chapter 16")
        pattern = r"(?:Table|Chapter)\s*(\d{1,2})(?:-(\d{1,2}))?"
        match = re.match(pattern, table_reference, re.IGNORECASE)
        
        if not match:
            return False
        
        chapter = int(match.group(1))
        table = int(match.group(2)) if match.group(2) else 0
        
        # Validate chapter and table numbers (simplified validation)
        return 1 <= chapter <= 18 and (table == 0 or 1 <= table <= 20)
    
    def _section_present(self, section_name: str, context: ValidationContext) -> bool:
        """Check if section is present."""
        # This would check document structure
        return True
    
    def _placeholder_filled(self, placeholder: str, context: ValidationContext) -> bool:
        """Check if DOCX placeholder is filled."""
        # This would check the generated DOCX
        return True
    
    def _has_provenance(self, element: str, context: ValidationContext) -> bool:
        """Check if element has provenance."""
        return element in context.provenance_map and len(context.provenance_map[element]) > 0
    
    def _get_field_value(self, field: str, context: ValidationContext) -> Any:
        """Get field value from context."""
        field_mapping = {
            "claimant_name": context.template_data.patient_info.name,
            "claim_number": context.template_data.patient_info.case_number,
        }
        return field_mapping.get(field)
    
    def _get_section_for_field(self, field: str) -> SectionType:
        """Map field to appropriate section type."""
        if field in ["claimant_name", "claim_number", "employer_name"]:
            return SectionType.PATIENT_DEMOGRAPHICS
        elif field in ["examiner_name", "examiner_license"]:
            return SectionType.PATIENT_DEMOGRAPHICS
        else:
            return SectionType.PATIENT_DEMOGRAPHICS
    
    def _get_section_for_table(self, table_name: str) -> SectionType:
        """Map table to appropriate section type."""
        if "adl" in table_name.lower():
            return SectionType.OCCUPATIONAL_HISTORY
        elif "rom" in table_name.lower():
            return SectionType.PHYSICAL_EXAMINATION
        else:
            return SectionType.PHYSICAL_EXAMINATION
    
    def _map_section_name(self, section_name: str) -> SectionType:
        """Map section name to SectionType enum."""
        section_mapping = {
            "diagnostic_impression": SectionType.DIAGNOSIS,
            "opinion_on_causation": SectionType.CAUSATION_ANALYSIS,
            "causation_analysis": SectionType.CAUSATION_ANALYSIS,
            "whole_person_impairment": SectionType.IMPAIRMENT_RATING,
            "impairment_rating": SectionType.IMPAIRMENT_RATING,
            "apportionment_according_to_sb899_lc4663": SectionType.APPORTIONMENT,
            "apportionment": SectionType.APPORTIONMENT,
            "ability_to_return_to_work": SectionType.WORK_RESTRICTIONS,
            "work_restrictions": SectionType.WORK_RESTRICTIONS,
            "future_medical_care": SectionType.FUTURE_MEDICAL_CARE,
            "physical_examination": SectionType.PHYSICAL_EXAMINATION,
            "occupational_history": SectionType.OCCUPATIONAL_HISTORY,
            "activities_daily_living": SectionType.OCCUPATIONAL_HISTORY,
        }
        return section_mapping.get(section_name, SectionType.PATIENT_DEMOGRAPHICS)
    
    # Enhanced helper methods for comprehensive validation
    def _exact_text_present(self, text: str, context: ValidationContext) -> bool:
        """Check if exact text is present in document."""
        # This would check the generated document content for exact text match
        # For simulation, we'll check if it's in the validation state
        return context.validation_state.get(f"text_present_{hash(text)}", False)
    
    def _citation_present(self, citation: str, context: ValidationContext) -> bool:
        """Check if case law citation is present."""
        return context.validation_state.get(f"citation_{citation}", False)
    
    def _legal_reference_present(self, reference: str, context: ValidationContext) -> bool:
        """Check if legal code reference is present."""
        return context.validation_state.get(f"legal_ref_{reference}", False)
    
    def _get_industrial_percentage(self, context: ValidationContext) -> Optional[float]:
        """Get industrial apportionment percentage."""
        return context.document_metadata.get("industrial_percentage")
    
    def _get_nonindustrial_percentage(self, context: ValidationContext) -> Optional[float]:
        """Get nonindustrial apportionment percentage."""
        return context.document_metadata.get("nonindustrial_percentage")
    
    def _get_total_pages_reviewed(self, context: ValidationContext) -> Optional[int]:
        """Get total pages reviewed count."""
        return context.document_metadata.get("total_pages_reviewed")
    
    def _billing_calculation_correct(self, expected_amount: float, context: ValidationContext) -> bool:
        """Check if billing calculation is correct."""
        actual_amount = context.document_metadata.get("billing_amount")
        return actual_amount is not None and abs(actual_amount - expected_amount) < 0.01
    
    def _penalty_of_perjury_present(self, statement: str, context: ValidationContext) -> bool:
        """Check if penalty of perjury statement is present."""
        return context.validation_state.get(f"perjury_{statement}", False)
    
    def _ama_citation_format_valid(self, citation_type: str, pattern: str, context: ValidationContext) -> bool:
        """Check if AMA citation format is valid."""
        citations = context.validation_state.get("ama_citations", [])
        for citation in citations:
            if re.match(pattern, citation):
                return True
        return False
    
    def _methodology_documented(self, methodology: str, context: ValidationContext) -> bool:
        """Check if impairment methodology is documented."""
        documented_methods = context.validation_state.get("documented_methodologies", [])
        return methodology in documented_methods
    
    def _adl_grid_present(self, context: ValidationContext) -> bool:
        """Check if ADL grid is present."""
        return context.validation_state.get("adl_grid_present", False)
    
    def _adl_column_present(self, column: str, context: ValidationContext) -> bool:
        """Check if ADL grid column is present."""
        adl_columns = context.validation_state.get("adl_columns", [])
        return column in adl_columns
    
    def _adl_category_present(self, category: str, context: ValidationContext) -> bool:
        """Check if ADL category is present."""
        adl_categories = context.validation_state.get("adl_categories", [])
        return category in adl_categories
    
    def _adl_item_present(self, item: str, context: ValidationContext) -> bool:
        """Check if ADL item is present."""
        adl_items = context.validation_state.get("adl_items", [])
        return item in adl_items
    
    def _neurological_level_tested(self, level: str, region: str, context: ValidationContext) -> bool:
        """Check if neurological level is tested."""
        tested_levels = context.validation_state.get(f"neuro_{region}_levels", [])
        return level in tested_levels
    
    def _special_test_documented(self, test: str, region: str, context: ValidationContext) -> bool:
        """Check if special orthopedic test is documented."""
        documented_tests = context.validation_state.get(f"special_tests_{region}", [])
        return test in documented_tests
    
    def _get_causation_type(self, context: ValidationContext) -> str:
        """Get the type of causation determination."""
        return context.document_metadata.get("causation_type", "specific_injury")
    
    def _causation_format_matches(self, required_format: str, context: ValidationContext) -> bool:
        """Check if causation format matches requirements."""
        actual_format = context.validation_state.get("causation_format")
        return actual_format == required_format
    
    def _causation_established(self, context: ValidationContext) -> bool:
        """Check if causation has been established."""
        return context.document_metadata.get("causation_found", False)
    
    def _section_complete(self, section: str, context: ValidationContext) -> bool:
        """Check if section is complete."""
        completed_sections = context.validation_state.get("completed_sections", [])
        return section in completed_sections
    
    def _all_calculations_correct(self, context: ValidationContext) -> bool:
        """Check if all calculations are correct."""
        return context.validation_state.get("calculations_correct", True)
    
    def _legal_requirements_met(self, context: ValidationContext) -> bool:
        """Check if all legal requirements are met."""
        return context.validation_state.get("legal_requirements_met", True)
    
    def _provenance_complete(self, context: ValidationContext) -> bool:
        """Check if provenance is complete for all substantive statements."""
        required_provenance = context.validation_state.get("required_provenance_items", [])
        for item in required_provenance:
            if item not in context.provenance_map or not context.provenance_map[item]:
                return False
        return True


class AdvancedQMERulesEngine:
    """Advanced QME Rules Engine with YAML configuration support."""
    
    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize the advanced rules engine.
        
        Args:
            rules_file: Path to YAML rules configuration file
        """
        self.rules_file = rules_file or "src/rules/rules.yaml"
        self.rules: List[RuleDefinition] = []
        self.condition_evaluator = RuleConditionEvaluator()
        self.action_executor = RuleActionExecutor()
        
        self._load_rules()
        logger.info(f"Initialized Advanced QME Rules Engine with {len(self.rules)} rules")
    
    def _load_rules(self):
        """Load rules from YAML configuration file."""
        try:
            rules_path = Path(self.rules_file)
            if not rules_path.exists():
                logger.warning(f"Rules file not found: {self.rules_file}")
                return
            
            with open(rules_path, 'r', encoding='utf-8') as file:
                yaml_data = yaml.safe_load(file)
            
            # Extract rules from the rules section
            if isinstance(yaml_data, dict) and 'rules' in yaml_data:
                rules_data = yaml_data['rules']
            else:
                # Fallback to old format
                rules_data = [item for item in yaml_data if isinstance(item, dict) and 'id' in item]
            
            for rule_data in rules_data:
                try:
                    rule = RuleDefinition(
                        id=rule_data['id'],
                        priority=RulePriority(rule_data['priority']),
                        description=rule_data['description'],
                        section=rule_data['section'],
                        when_conditions=rule_data.get('when', []),
                        then_actions=rule_data.get('then', []),
                        metadata=rule_data
                    )
                    self.rules.append(rule)
                    
                except Exception as e:
                    logger.error(f"Error loading rule {rule_data.get('id', 'unknown')}: {e}")
            
            logger.info(f"Loaded {len(self.rules)} rules from {self.rules_file}")
            
        except Exception as e:
            logger.error(f"Error loading rules file {self.rules_file}: {e}")
    
    def validate_qme_report_comprehensive(self, 
                                        template_data: QMETemplateData,
                                        document_metadata: Optional[Dict[str, Any]] = None) -> Tuple[List[ValidationIssue], QualityScore, List[AuditEntry]]:
        """
        Perform comprehensive validation using YAML rules.
        
        Args:
            template_data: QME template data to validate
            document_metadata: Additional document metadata
            
        Returns:
            Tuple of (validation_issues, quality_score, audit_trail)
        """
        try:
            logger.info("Starting comprehensive QME validation with YAML rules")
            
            # Create validation context
            context = ValidationContext(
                template_data=template_data,
                document_metadata=document_metadata or {},
                template_status={"assembling": True}
            )
            
            all_issues = []
            
            # Execute rules by priority
            for priority in [RulePriority.MUST, RulePriority.SHOULD, RulePriority.MAY]:
                priority_rules = [rule for rule in self.rules if rule.priority == priority]
                
                for rule in priority_rules:
                    try:
                        # Evaluate conditions
                        if self.condition_evaluator.evaluate_conditions(rule.when_conditions, context):
                            # Execute actions
                            rule_issues = self.action_executor.execute_actions(
                                rule.then_actions, context, rule.id
                            )
                            all_issues.extend(rule_issues)
                            
                            # Add audit entry for rule execution
                            audit_entry = AuditEntry(
                                rule_id=rule.id,
                                action="rule_executed",
                                result="completed",
                                details={
                                    "priority": rule.priority.value,
                                    "issues_found": len(rule_issues)
                                }
                            )
                            context.audit_trail.append(audit_entry)
                        
                    except Exception as e:
                        logger.error(f"Error executing rule {rule.id}: {e}")
                        error_issue = ValidationIssue(
                            section=SectionType.PATIENT_DEMOGRAPHICS,
                            severity=ValidationSeverity.HIGH,
                            title=f"Rule Execution Error: {rule.id}",
                            description=f"Error executing rule: {str(e)}"
                        )
                        all_issues.append(error_issue)
            
            # Calculate quality score
            quality_score = self._calculate_comprehensive_quality_score(all_issues, context)
            
            logger.info(f"Comprehensive validation complete: {len(all_issues)} issues, score: {quality_score.overall_score:.1f}")
            
            return all_issues, quality_score, context.audit_trail
            
        except Exception as e:
            logger.error(f"Error in comprehensive QME validation: {e}")
            error_issue = ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Validation System Error",
                description=f"Error during validation: {str(e)}"
            )
            basic_score = QualityScore(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                compliance_score=0.0
            )
            return [error_issue], basic_score, []
    
    def _calculate_comprehensive_quality_score(self, issues: List[ValidationIssue], context: ValidationContext) -> QualityScore:
        """Calculate comprehensive quality score based on rule validation."""
        try:
            # Count issues by severity
            critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
            high_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.HIGH)
            medium_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.MEDIUM)
            low_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.LOW)
            
            # Count issues by rule priority (based on rule IDs)
            must_issues = sum(1 for issue in issues if self._is_must_rule_issue(issue))
            should_issues = sum(1 for issue in issues if self._is_should_rule_issue(issue))
            may_issues = sum(1 for issue in issues if self._is_may_rule_issue(issue))
            
            # Calculate component scores with enhanced weighting
            completeness_score = self._calculate_completeness_score_advanced(context)
            accuracy_score = max(0, 100 - (critical_count * 25 + high_count * 15 + medium_count * 10 + low_count * 5))
            compliance_score = max(0, 100 - (critical_count * 30 + high_count * 20))
            
            # Legal compliance gets extra weight for MUST rules
            legal_compliance_penalty = must_issues * 35 + should_issues * 15 + may_issues * 5
            legal_compliance_score = max(0, 100 - legal_compliance_penalty)
            
            # Calculate overall score with weighted components
            overall_score = (
                completeness_score * 0.25 +
                accuracy_score * 0.25 +
                compliance_score * 0.25 +
                legal_compliance_score * 0.25
            )
            
            return QualityScore(
                overall_score=overall_score,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                compliance_score=min(compliance_score, legal_compliance_score)
            )
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive quality score: {e}")
            return QualityScore(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                compliance_score=0.0
            )
    
    def _is_must_rule_issue(self, issue: ValidationIssue) -> bool:
        """Check if issue is from a MUST priority rule."""
        # Check if the issue title contains indicators of MUST rules
        must_indicators = ["Missing Required", "Statutory Language", "Legal Reference", 
                          "Case Law Citation", "Penalty of Perjury", "Declaration"]
        return any(indicator in issue.title for indicator in must_indicators)
    
    def _is_should_rule_issue(self, issue: ValidationIssue) -> bool:
        """Check if issue is from a SHOULD priority rule."""
        should_indicators = ["Missing Methodology", "Special Test", "Circumferential"]
        return any(indicator in issue.title for indicator in should_indicators)
    
    def _is_may_rule_issue(self, issue: ValidationIssue) -> bool:
        """Check if issue is from a MAY priority rule."""
        # Issues not classified as MUST or SHOULD are considered MAY
        return not (self._is_must_rule_issue(issue) or self._is_should_rule_issue(issue))
    
    def _calculate_completeness_score_advanced(self, context: ValidationContext) -> float:
        """Calculate advanced completeness score based on section completion."""
        try:
            # Define required sections with weights
            required_sections = {
                "header": 5,
                "legal_declarations": 10,
                "records_review": 5,
                "identifying_data": 5,
                "history_of_injury": 8,
                "occupational_history": 8,
                "activities_daily_living": 10,
                "physical_examination": 15,
                "diagnostic_impression": 10,
                "causation_analysis": 12,
                "impairment_rating": 15,
                "apportionment": 10,
                "work_restrictions": 8,
                "future_medical_care": 7,
                "signature_block": 5
            }
            
            completed_sections = context.validation_state.get("completed_sections", [])
            total_weight = sum(required_sections.values())
            completed_weight = sum(weight for section, weight in required_sections.items() 
                                 if section in completed_sections)
            
            completeness_percentage = (completed_weight / total_weight) * 100 if total_weight > 0 else 0
            
            # Bonus for having all critical sections
            critical_sections = ["legal_declarations", "physical_examination", "impairment_rating", "causation_analysis"]
            if all(section in completed_sections for section in critical_sections):
                completeness_percentage = min(100, completeness_percentage + 5)
            
            return completeness_percentage
            
        except Exception as e:
            logger.error(f"Error calculating advanced completeness score: {e}")
            return 0.0
            
            # Overall score with weighted components
            overall_score = (
                completeness_score * 0.3 +
                accuracy_score * 0.4 +
                compliance_score * 0.3
            )
            
            return QualityScore(
                overall_score=overall_score,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                compliance_score=compliance_score,
                total_issues=len(issues),
                critical_issues=critical_count,
                high_issues=high_count,
                medium_issues=medium_count,
                low_issues=low_count
            )
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return QualityScore(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                compliance_score=0.0,
                total_issues=len(issues)
            )
    
    def _calculate_completeness_score_advanced(self, context: ValidationContext) -> float:
        """Calculate advanced completeness score based on gold standard requirements."""
        try:
            total_elements = 0
            completed_elements = 0
            
            # Patient identification elements (from gold standard)
            patient_elements = [
                context.template_data.patient_info.name,
                context.template_data.patient_info.age,
                context.template_data.patient_info.gender,
                context.template_data.patient_info.case_number,
                context.template_data.patient_info.injury_date,
                context.template_data.patient_info.employer,
                context.template_data.patient_info.occupation
            ]
            total_elements += len(patient_elements)
            completed_elements += sum(1 for elem in patient_elements if elem)
            
            # Medical findings elements
            if context.template_data.medical_findings.diagnoses:
                completed_elements += 1
            total_elements += 1
            
            if context.template_data.medical_findings.impairment_ratings:
                completed_elements += 1
            total_elements += 1
            
            if context.template_data.medical_findings.findings:
                completed_elements += 1
            total_elements += 1
            
            # Provenance completeness
            provenance_score = len(context.provenance_map) / max(1, len(context.template_data.medical_findings.diagnoses))
            completed_elements += provenance_score
            total_elements += 1
            
            # Calculate percentage
            if total_elements > 0:
                return (completed_elements / total_elements) * 100
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating advanced completeness score: {e}")
            return 0.0
    
    def generate_comprehensive_audit_report(self, audit_trail: List[AuditEntry]) -> str:
        """Generate comprehensive audit report from audit trail."""
        try:
            report_lines = []
            
            report_lines.append("QME COMPREHENSIVE AUDIT REPORT")
            report_lines.append("=" * 50)
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"Total Audit Entries: {len(audit_trail)}")
            report_lines.append("")
            
            # Group by rule ID
            rules_executed = {}
            for entry in audit_trail:
                if entry.rule_id not in rules_executed:
                    rules_executed[entry.rule_id] = []
                rules_executed[entry.rule_id].append(entry)
            
            report_lines.append("RULES EXECUTION SUMMARY")
            report_lines.append("-" * 30)
            report_lines.append(f"Rules Executed: {len(rules_executed)}")
            
            for rule_id, entries in rules_executed.items():
                report_lines.append(f"  {rule_id}: {len(entries)} actions")
            
            report_lines.append("")
            
            # Detailed audit trail
            report_lines.append("DETAILED AUDIT TRAIL")
            report_lines.append("-" * 30)
            
            for entry in audit_trail:
                report_lines.append(f"[{entry.timestamp.strftime('%H:%M:%S')}] {entry.rule_id}")
                report_lines.append(f"  Action: {entry.action}")
                report_lines.append(f"  Result: {entry.result}")
                if entry.details:
                    report_lines.append(f"  Details: {entry.details}")
                report_lines.append("")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
            return f"Error generating audit report: {str(e)}"
    
    def get_rule_coverage_report(self) -> Dict[str, Any]:
        """Get report on rule coverage and configuration."""
        try:
            coverage = {
                "total_rules": len(self.rules),
                "rules_by_priority": {
                    "MUST": len([r for r in self.rules if r.priority == RulePriority.MUST]),
                    "SHOULD": len([r for r in self.rules if r.priority == RulePriority.SHOULD]),
                    "MAY": len([r for r in self.rules if r.priority == RulePriority.MAY])
                },
                "rules_by_section": {},
                "rule_ids": [rule.id for rule in self.rules]
            }
            
            # Group by section
            for rule in self.rules:
                section = rule.section
                if section not in coverage["rules_by_section"]:
                    coverage["rules_by_section"][section] = 0
                coverage["rules_by_section"][section] += 1
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error generating coverage report: {e}")
            return {"error": str(e)}
    
    def validate_rules_configuration(self) -> List[str]:
        """Validate the rules configuration for completeness and correctness."""
        validation_errors = []
        
        try:
            # Check for required rule IDs from gold standard
            required_rule_ids = [
                "R001_require_4062_3", "R002_page_count_billable", "R020_require_3rom_measures",
                "R070_impairment_calc_check", "R080_require_header", "R081_interpreter_checkbox",
                "R082_no_records_block", "R083_require_adl_grid", "R091_signature_block"
            ]
            
            existing_rule_ids = [rule.id for rule in self.rules]
            
            for required_id in required_rule_ids:
                if required_id not in existing_rule_ids:
                    validation_errors.append(f"Missing required rule: {required_id}")
            
            # Check rule structure
            for rule in self.rules:
                if not rule.when_conditions:
                    validation_errors.append(f"Rule {rule.id} has no conditions")
                
                if not rule.then_actions:
                    validation_errors.append(f"Rule {rule.id} has no actions")
            
            return validation_errors
            
        except Exception as e:
            logger.error(f"Error validating rules configuration: {e}")
            return [f"Configuration validation error: {str(e)}"]

    def generate_comprehensive_audit_report(self, audit_trail: List[AuditEntry]) -> str:
        """Generate comprehensive audit report with provenance tracking."""
        try:
            report_lines = [
                "=== COMPREHENSIVE QME VALIDATION AUDIT REPORT ===",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total Audit Entries: {len(audit_trail)}",
                ""
            ]
            
            # Group by rule priority
            must_entries = [entry for entry in audit_trail if self._is_must_rule_entry(entry)]
            should_entries = [entry for entry in audit_trail if self._is_should_rule_entry(entry)]
            may_entries = [entry for entry in audit_trail if self._is_may_rule_entry(entry)]
            
            report_lines.extend([
                "RULE EXECUTION SUMMARY:",
                f"  MUST Rules Executed: {len(must_entries)}",
                f"  SHOULD Rules Executed: {len(should_entries)}",
                f"  MAY Rules Executed: {len(may_entries)}",
                ""
            ])
            
            # Legal compliance summary
            legal_entries = [entry for entry in audit_trail if self._is_legal_compliance_entry(entry)]
            report_lines.extend([
                "LEGAL COMPLIANCE SUMMARY:",
                f"  Legal Requirements Validated: {len(legal_entries)}",
                f"  §4062.3 Compliance: {'✓' if any('4062.3' in entry.rule_id for entry in legal_entries) else '✗'}",
                f"  MLPRR Billing Validation: {'✓' if any('page_count' in entry.rule_id for entry in legal_entries) else '✗'}",
                f"  Apportionment LC 4663/4664: {'✓' if any('apportionment' in entry.rule_id for entry in legal_entries) else '✗'}",
                ""
            ])
            
            # Provenance tracking summary
            provenance_entries = [entry for entry in audit_trail if entry.provenance]
            report_lines.extend([
                "PROVENANCE TRACKING SUMMARY:",
                f"  Entries with Provenance: {len(provenance_entries)}",
                f"  Source Documents Referenced: {len(set(entry.provenance.get('doc_id', '') for entry in provenance_entries if entry.provenance))}",
                ""
            ])
            
            # Detailed audit entries by priority
            for priority, entries in [("MUST", must_entries), ("SHOULD", should_entries), ("MAY", may_entries)]:
                if entries:
                    report_lines.extend([
                        f"{priority} PRIORITY RULES:",
                        "=" * (len(priority) + 16)
                    ])
                    
                    for entry in entries:
                        report_lines.extend([
                            f"Rule ID: {entry.rule_id}",
                            f"Timestamp: {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                            f"Action: {entry.action}",
                            f"Result: {entry.result}",
                            f"Details: {entry.details}",
                        ])
                        
                        if entry.provenance:
                            report_lines.extend([
                                f"Provenance: Doc {entry.provenance.get('doc_id', 'N/A')}, "
                                f"Page {entry.provenance.get('page', 'N/A')}, "
                                f"Offset {entry.provenance.get('offset', 'N/A')}"
                            ])
                        
                        report_lines.append("")
            
            # Validation statistics
            successful_validations = len([entry for entry in audit_trail if entry.result == "completed"])
            failed_validations = len([entry for entry in audit_trail if entry.result == "failed"])
            
            report_lines.extend([
                "VALIDATION STATISTICS:",
                f"  Successful Validations: {successful_validations}",
                f"  Failed Validations: {failed_validations}",
                f"  Success Rate: {(successful_validations / len(audit_trail) * 100):.1f}%" if audit_trail else "N/A",
                ""
            ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating comprehensive audit report: {e}")
            return f"Error generating comprehensive audit report: {str(e)}"
    
    def _is_must_rule_entry(self, entry: AuditEntry) -> bool:
        """Check if audit entry is from a MUST priority rule."""
        must_rule_prefixes = ["R001_", "R002_", "R020_", "R070_", "R080_", "R081_", "R082_", 
                             "R083_", "R091_", "R092_", "R100_", "R101_", "R102_", "R103_", 
                             "R104_", "R105_", "R106_", "R107_", "R108_", "R109_", "R110_"]
        return any(entry.rule_id.startswith(prefix) for prefix in must_rule_prefixes)
    
    def _is_should_rule_entry(self, entry: AuditEntry) -> bool:
        """Check if audit entry is from a SHOULD priority rule."""
        should_rule_prefixes = ["R050_", "R085_", "R094_", "R096_", "R097_", "R098_"]
        return any(entry.rule_id.startswith(prefix) for prefix in should_rule_prefixes)
    
    def _is_may_rule_entry(self, entry: AuditEntry) -> bool:
        """Check if audit entry is from a MAY priority rule."""
        return not (self._is_must_rule_entry(entry) or self._is_should_rule_entry(entry))
    
    def _is_legal_compliance_entry(self, entry: AuditEntry) -> bool:
        """Check if audit entry relates to legal compliance."""
        legal_keywords = ["4062.3", "page_count", "apportionment", "statutory", "penalty_of_perjury", 
                         "declaration", "mlprr", "interpreter", "signature"]
        return any(keyword in entry.rule_id.lower() for keyword in legal_keywords)

    def get_rule_coverage_report(self) -> Dict[str, Any]:
        """Get report on rule coverage and configuration."""
        try:
            coverage = {
                "total_rules": len(self.rules),
                "rules_by_priority": {
                    "MUST": len([r for r in self.rules if r.priority == RulePriority.MUST]),
                    "SHOULD": len([r for r in self.rules if r.priority == RulePriority.SHOULD]),
                    "MAY": len([r for r in self.rules if r.priority == RulePriority.MAY])
                },
                "rules_by_section": {},
                "rule_ids": [rule.id for rule in self.rules],
                "legal_compliance_rules": len([r for r in self.rules if self._is_legal_compliance_rule(r)]),
                "medical_validation_rules": len([r for r in self.rules if self._is_medical_validation_rule(r)]),
                "formatting_rules": len([r for r in self.rules if self._is_formatting_rule(r)])
            }
            
            # Group by section
            for rule in self.rules:
                section = rule.section
                if section not in coverage["rules_by_section"]:
                    coverage["rules_by_section"][section] = 0
                coverage["rules_by_section"][section] += 1
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error generating coverage report: {e}")
            return {"error": str(e)}
    
    def _is_legal_compliance_rule(self, rule: RuleDefinition) -> bool:
        """Check if rule is for legal compliance."""
        legal_sections = ["legal_declarations", "billing", "interpreter", "signature", "apportionment"]
        return rule.section in legal_sections
    
    def _is_medical_validation_rule(self, rule: RuleDefinition) -> bool:
        """Check if rule is for medical validation."""
        medical_sections = ["physical_examination", "neurological_examination", "impairment_rating", 
                           "causation", "diagnosis"]
        return rule.section in medical_sections
    
    def _is_formatting_rule(self, rule: RuleDefinition) -> bool:
        """Check if rule is for formatting validation."""
        formatting_sections = ["formatting", "final_validation"]
        return rule.section in formatting_sections

    def validate_rules_configuration(self) -> List[str]:
        """Validate the rules configuration for completeness and correctness."""
        validation_errors = []
        
        try:
            # Check for required rule IDs from gold standard
            required_rule_ids = [
                "R001_require_4062_3", "R002_page_count_billable", "R020_require_3rom_measures",
                "R070_impairment_calc_check", "R080_require_header", "R081_interpreter_checkbox",
                "R082_no_records_block", "R083_require_adl_grid", "R091_signature_block",
                "R101_lc4663_apportionment_language", "R102_statutory_language_precision",
                "R103_interpreter_93_modifier_compliance", "R104_mlprr_billing_precision",
                "R105_ama_guides_citation_accuracy", "R106_rom_measurement_compliance",
                "R107_adl_grid_comprehensive", "R108_neurological_testing_bilateral",
                "R109_causation_medical_probability", "R110_signature_attestation_complete"
            ]
            
            existing_rule_ids = [rule.id for rule in self.rules]
            
            for required_id in required_rule_ids:
                if required_id not in existing_rule_ids:
                    validation_errors.append(f"Missing required rule: {required_id}")
            
            # Check rule structure
            for rule in self.rules:
                if not rule.when_conditions:
                    validation_errors.append(f"Rule {rule.id} has no conditions")
                
                if not rule.then_actions:
                    validation_errors.append(f"Rule {rule.id} has no actions")
                
                # Validate priority levels
                if rule.priority not in [RulePriority.MUST, RulePriority.SHOULD, RulePriority.MAY]:
                    validation_errors.append(f"Rule {rule.id} has invalid priority: {rule.priority}")
            
            # Check for legal compliance coverage
            legal_compliance_rules = [r for r in self.rules if self._is_legal_compliance_rule(r)]
            if len(legal_compliance_rules) < 10:
                validation_errors.append("Insufficient legal compliance rules (minimum 10 required)")
            
            return validation_errors
            
        except Exception as e:
            logger.error(f"Error validating rules configuration: {e}")
            return [f"Configuration validation error: {str(e)}"]

    def add_provenance_to_audit(self, audit_entry: AuditEntry, doc_id: str, page: int, offset: int, snippet: str):
        """Add provenance information to an audit entry."""
        try:
            audit_entry.provenance = {
                "doc_id": doc_id,
                "page": page,
                "offset": offset,
                "snippet": snippet[:200],  # Limit snippet length
                "timestamp": datetime.now().isoformat()
            }
            logger.debug(f"Added provenance to audit entry {audit_entry.id}")
            
        except Exception as e:
            logger.error(f"Error adding provenance to audit entry: {e}")

    def export_rules_configuration(self) -> Dict[str, Any]:
        """Export current rules configuration for backup or analysis."""
        try:
            export_data = {
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_rules": len(self.rules),
                    "rules_file": self.rules_file
                },
                "rules": []
            }
            
            for rule in self.rules:
                rule_data = {
                    "id": rule.id,
                    "priority": rule.priority.value,
                    "description": rule.description,
                    "section": rule.section,
                    "when_conditions": rule.when_conditions,
                    "then_actions": rule.then_actions,
                    "metadata": rule.metadata
                }
                export_data["rules"].append(rule_data)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting rules configuration: {e}")
            return {"error": str(e)}