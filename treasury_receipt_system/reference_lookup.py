"""Reference data loading and lookup utilities.

Loads Excel reference data and provides fast code->description lookups
for Entity, Cost Center, GL Account, Budget Group, and Futures.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, List, Iterable

import pandas as pd

LOGGER = logging.getLogger(__name__)


def _normalize_sheet_name(name: str) -> str:
    return name.strip().lower().replace("_", " ")


EXPECTED_SHEETS = {
    "entity": ["entity", "entities"],
    "cost_center": ["cost center", "cost centers", "costcentre", "cost centres"],
    "gl_account": ["gl account", "gl accounts", "gl", "account"],
    "budget_group": ["budget group", "budget groups"],
    # Support multiple futures sheets like "Future 1", "Future 2" as well as generic names
    "futures": ["futures", "future", "future codes", "future 1", "future 2"],
}


def _find_sheet_mapping(xls: pd.ExcelFile) -> Dict[str, List[str]]:
    """Map expected logical sheet keys to actual sheet names present in the file.

    Returns a mapping of logical key -> list of sheet names (to support merging).
    """
    present = { _normalize_sheet_name(s): s for s in xls.sheet_names }
    mapping: Dict[str, List[str]] = {}
    for logical, candidates in EXPECTED_SHEETS.items():
        hits: List[str] = []
        for cand in candidates:
            key = _normalize_sheet_name(cand)
            if key in present and present[key] not in hits:
                hits.append(present[key])
        if hits:
            mapping[logical] = hits
        else:
            LOGGER.warning("Sheet for '%s' not found; candidates=%s", logical, candidates)
    return mapping


def _build_lookup(df: pd.DataFrame) -> Dict[str, str]:
    """Build a code->description dictionary from a dataframe.

    Heuristics to find code and description column names.
    """
    # Coerce column headers to strings to avoid attribute errors when headers are not strings
    columns = {str(c).strip().lower(): c for c in df.columns}
    code_col = None
    desc_col = None
    for candidate in ["code", "number", "id", "gl account", "cost center", "entity", "budget group", "future", "future code"]:
        if candidate in columns:
            code_col = columns[candidate]
            break
    for candidate in ["description", "desc", "name", "gl account description", "cost center description", "entity description", "budget group description", "future description"]:
        if candidate in columns:
            desc_col = columns[candidate]
            break
    # Fallback: if we couldn't detect both, attempt to use first two columns
    if code_col is None or desc_col is None:
        if len(df.columns) >= 2:
            code_col = df.columns[0]
            desc_col = df.columns[1]
        else:
            raise ValueError("Unable to determine code/description columns in reference sheet")
    df = df[[code_col, desc_col]].dropna()
    df[code_col] = df[code_col].astype(str).str.strip()
    df[desc_col] = df[desc_col].astype(str).str.strip()
    return dict(zip(df[code_col], df[desc_col]))


def _code_variants(code: str, pad: int = 6) -> List[str]:
    """Generate common normalized variants for a code string.

    Includes the raw code, zero-stripped, and zero-padded to `pad` width.
    """
    raw = str(code).strip()
    stripped = raw.lstrip("0") or "0"
    padded = raw.zfill(pad)
    padded_from_stripped = stripped.zfill(pad)
    variants = {raw, stripped, padded, padded_from_stripped}
    return list(variants)


@dataclass
class ReferenceLookup:
    entity: Dict[str, str]
    cost_center: Dict[str, str]
    gl_account: Dict[str, str]
    budget_group: Dict[str, str]
    futures: Dict[str, str]

    @classmethod
    def from_excel(cls, excel_path: str) -> "ReferenceLookup":
        """Load reference data from the given Excel workbook.

        Parameters
        ----------
        excel_path: str
            Path to the Excel workbook containing reference sheets.
        """
        LOGGER.info("Loading reference data from %s", excel_path)
        xls = pd.ExcelFile(excel_path, engine="openpyxl")
        mapping = _find_sheet_mapping(xls)

        def load_sheet(logical_key: str) -> Dict[str, str]:
            sheet_names = mapping.get(logical_key, [])
            if not sheet_names:
                LOGGER.warning("Sheet for '%s' missing; lookups may fail", logical_key)
                return {}
            merged: Dict[str, str] = {}
            for sheet_name in sheet_names:
                df = xls.parse(sheet_name=sheet_name)
                partial = _build_lookup(df)
                # For futures only, index by multiple normalized variants to handle 0 vs 000000
                if logical_key == "futures":
                    for k, v in partial.items():
                        for variant in _code_variants(k, pad=6):
                            merged[variant] = v
                else:
                    merged.update(partial)
            return merged

        return cls(
            entity=load_sheet("entity"),
            cost_center=load_sheet("cost_center"),
            gl_account=load_sheet("gl_account"),
            budget_group=load_sheet("budget_group"),
            futures=load_sheet("futures"),
        )

    def get_entity_description(self, code: str) -> Optional[str]:
        return self.entity.get(code)

    def get_cost_center_description(self, code: str) -> Optional[str]:
        return self.cost_center.get(code)

    def get_gl_account_description(self, code: str) -> Optional[str]:
        return self.gl_account.get(code)

    def get_budget_group_description(self, code: str) -> Optional[str]:
        return self.budget_group.get(code)

    def get_futures_description(self, code: str) -> Optional[str]:
        # Try direct
        if code in self.futures:
            return self.futures[code]
        # Try normalized variants
        for variant in _code_variants(code, pad=6):
            if variant in self.futures:
                return self.futures[variant]
        # Fallback: treat all-zero codes as N/A
        if str(code).strip().strip("0") == "":
            return "N/A"
        return None



