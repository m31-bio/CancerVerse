"""Rendering the model table.

This lives in the package rather than in `scripts/` because seven callers
import it and two of them do not ship. A loose script
in one repository cannot be imported from another; a module in the installed
package can, whichever repository the caller sits in.

Promoting it also removes the `sys.path.insert` that every renderer needed in
order to import a sibling script, a workaround that only ever worked when run
from a checkout, never from an installed wheel.
"""

from .model_table import (
    AXES,
    AXIS_LABEL,
    COLUMNS,
    DISEASE_LABEL,
    EHR_LABEL,
    GAP_CAPTION,
    GAP_CELL_LABEL,
    OPEN_SOURCE_LABEL,
    SPREADSHEET_EXTRAS,
    build_rows,
    clinical_question,
    ehr_availability,
    equation_location,
    feature_top_predictors,
    flat,
    grouped,
    linked_reference,
    load_models,
    model_cell,
    planned_replacements,
    questions_in,
    rerun_command,
    verified_how,
)

__all__ = [
    "AXES", "AXIS_LABEL", "COLUMNS", "DISEASE_LABEL", "GAP_CAPTION",
    "GAP_CELL_LABEL", "OPEN_SOURCE_LABEL", "SPREADSHEET_EXTRAS",
    "EHR_LABEL", "build_rows", "ehr_availability", "equation_location", "feature_top_predictors", "flat",
    "clinical_question", "grouped", "linked_reference", "load_models", "model_cell", "planned_replacements", "questions_in", "rerun_command", "verified_how",
]
