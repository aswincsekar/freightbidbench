#!/usr/bin/env python3
"""Inspect public FAF/USDA inputs for the FreightBidBench v1 calibration.

The script intentionally uses only the Python standard library so it can run in
the lightweight research workspace without dependency setup.
"""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FAF_ZIP = ROOT / "data" / "raw" / "faf" / "FAF5.7.1_State.zip"
FAF_CSV_NAME = "FAF5.7.1_State.csv"
FAF_METADATA = ROOT / "data" / "raw" / "faf" / "FAF5_metadata.xlsx"
USDA_TEXT = ROOT / "data" / "raw" / "usda" / "fvwtrk.txt"
PROCESSED = ROOT / "data" / "processed"
REPORT = ROOT / "reports" / "initial_calibration_report.md"


STATE_NAMES = {
    "01": "Alabama",
    "02": "Alaska",
    "04": "Arizona",
    "05": "Arkansas",
    "06": "California",
    "08": "Colorado",
    "09": "Connecticut",
    "10": "Delaware",
    "11": "District of Columbia",
    "12": "Florida",
    "13": "Georgia",
    "15": "Hawaii",
    "16": "Idaho",
    "17": "Illinois",
    "18": "Indiana",
    "19": "Iowa",
    "20": "Kansas",
    "21": "Kentucky",
    "22": "Louisiana",
    "23": "Maine",
    "24": "Maryland",
    "25": "Massachusetts",
    "26": "Michigan",
    "27": "Minnesota",
    "28": "Mississippi",
    "29": "Missouri",
    "30": "Montana",
    "31": "Nebraska",
    "32": "Nevada",
    "33": "New Hampshire",
    "34": "New Jersey",
    "35": "New Mexico",
    "36": "New York",
    "37": "North Carolina",
    "38": "North Dakota",
    "39": "Ohio",
    "40": "Oklahoma",
    "41": "Oregon",
    "42": "Pennsylvania",
    "44": "Rhode Island",
    "45": "South Carolina",
    "46": "South Dakota",
    "47": "Tennessee",
    "48": "Texas",
    "49": "Utah",
    "50": "Vermont",
    "51": "Virginia",
    "53": "Washington",
    "54": "West Virginia",
    "55": "Wisconsin",
    "56": "Wyoming",
}

DESTINATIONS = {
    "Atlanta",
    "Baltimore",
    "Boston",
    "Chicago",
    "Dallas",
    "Los Angeles",
    "Miami",
    "New York",
    "Philadelphia",
    "Seattle",
}

DESTINATION_STATE = {
    "Atlanta": "13",
    "Baltimore": "24",
    "Boston": "25",
    "Chicago": "17",
    "Dallas": "48",
    "Los Angeles": "06",
    "Miami": "12",
    "New York": "36",
    "Philadelphia": "42",
    "Seattle": "53",
}

ORIGIN_STATE_RULES = [
    ("NOGALES ARIZONA", "04", "Arizona", "direct"),
    ("CENTRAL AND WESTERN AZ", "06", "California", "mixed_ca_az_primary_ca"),
    ("CALEXICO AND SAN LUIS", "06", "California", "mixed_ca_az_primary_ca"),
    ("CALIFORNIA", "06", "California", "direct"),
    ("COLORADO", "08", "Colorado", "direct"),
    ("FLORIDA", "12", "Florida", "direct"),
    ("GEORGIA", "13", "Georgia", "direct"),
    ("NEW YORK", "36", "New York", "direct"),
    ("SOUTH TEXAS", "48", "Texas", "direct"),
    ("WASHINGTON", "53", "Washington", "direct"),
]

SCARCITY_MULTIPLIER = {
    "Surplus": "0.80",
    "Slight Surplus": "0.90",
    "Adequate": "1.00",
    "Slight Shortage": "1.15",
    "Shortage": "1.35",
}

SKIP_ORIGIN_LINES = {
    "SPECIALTY CROPS NATIONAL TRUCK RATE REPORT",
    "AGRICULTURAL MARKETING SERVICE",
    "SPECIALTY CROPS MARKET NEWS",
    "FVWTRK",
    "PRICES FOR TUESDAY APRIL 28, 2026",
    "DISTRICT/REGION",
    "TRUCK AVAILABILITY",
    "REPORT TYPE",
    "RANGE",
    "MOSTLY",
    "FIRST REPORT",
    "LAST REPORT",
    "USDA, AMS, SPECIALTY CROPS MARKET NEWS",
}


@dataclass
class FafSummary:
    total_rows: int
    domestic_truck_rows: int
    mode_counts: Counter[str]
    mode_names: dict[str, str]
    lane_summaries: list[dict[str, str]]
    top_lanes: list[dict[str, str]]
    imbalances: list[dict[str, str]]
    top_commodities: list[dict[str, str]]


def as_float(value: str) -> float:
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def state_name(code: str) -> str:
    return STATE_NAMES.get(code, code or "Unknown")


def read_xlsx_sheet(path: Path, sheet_name: str) -> list[list[str]]:
    ns = {
        "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        for shared_item in shared_root.findall("a:si", ns):
            shared_strings.append(
                "".join(text.text or "" for text in shared_item.findall(".//a:t", ns))
            )

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        target = None
        for sheet in workbook.findall("a:sheets/a:sheet", ns):
            if sheet.attrib["name"] == sheet_name:
                rel_id = sheet.attrib[
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                ]
                target = "xl/" + relmap[rel_id]
                break
        if target is None:
            raise ValueError(f"Could not find sheet {sheet_name!r} in {path}")

        rows: list[list[str]] = []
        worksheet = ET.fromstring(archive.read(target))
        for row in worksheet.findall("a:sheetData/a:row", ns):
            values: list[str] = []
            for cell in row.findall("a:c", ns):
                value = cell.find("a:v", ns)
                text = "" if value is None else value.text or ""
                if cell.attrib.get("t") == "s" and text:
                    text = shared_strings[int(text)]
                values.append(text)
            rows.append(values)
        return rows


def read_codebook(sheet_name: str) -> dict[str, str]:
    rows = read_xlsx_sheet(FAF_METADATA, sheet_name)
    codebook: dict[str, str] = {}
    for row in rows[1:]:
        if len(row) >= 2:
            codebook[row[0]] = row[1]
    return codebook


def inspect_faf() -> FafSummary:
    mode_names = read_codebook("Mode")
    commodity_names = read_codebook("Commodity (SCTG2)")
    total_rows = 0
    domestic_truck_rows = 0
    mode_counts: Counter[str] = Counter()
    lane_tons: defaultdict[tuple[str, str], float] = defaultdict(float)
    lane_value: defaultdict[tuple[str, str], float] = defaultdict(float)
    lane_tmiles: defaultdict[tuple[str, str], float] = defaultdict(float)
    outbound: defaultdict[str, float] = defaultdict(float)
    inbound: defaultdict[str, float] = defaultdict(float)
    commodity_tons: defaultdict[str, float] = defaultdict(float)

    with zipfile.ZipFile(FAF_ZIP) as archive:
        with archive.open(FAF_CSV_NAME) as raw:
            rows = csv.DictReader((line.decode("utf-8-sig") for line in raw))
            for row in rows:
                total_rows += 1
                mode = row["dms_mode"]
                mode_counts[mode] += 1

                origin = row["dms_origst"]
                destination = row["dms_destst"]
                is_domestic_truck = (
                    mode == "1"
                    and bool(origin)
                    and bool(destination)
                    and not row["fr_orig"]
                    and not row["fr_dest"]
                )
                if not is_domestic_truck:
                    continue

                domestic_truck_rows += 1
                tons = as_float(row["tons_2024"])
                value = as_float(row["value_2024"])
                tmiles = as_float(row["tmiles_2024"])
                lane = (origin, destination)
                lane_tons[lane] += tons
                lane_value[lane] += value
                lane_tmiles[lane] += tmiles
                outbound[origin] += tons
                inbound[destination] += tons
                commodity_tons[row["sctg2"]] += tons

    lane_summaries = []
    for (origin, destination), tons in sorted(
        lane_tons.items(), key=lambda item: item[1], reverse=True
    ):
        lane_summaries.append(
            {
                "origin_state": origin,
                "origin_name": state_name(origin),
                "destination_state": destination,
                "destination_name": state_name(destination),
                "tons_2024": f"{tons:.6f}",
                "value_2024": f"{lane_value[(origin, destination)]:.6f}",
                "tmiles_2024": f"{lane_tmiles[(origin, destination)]:.6f}",
            }
        )
    top_lanes = lane_summaries[:50]

    imbalances = []
    for state in sorted(set(outbound) | set(inbound)):
        out_tons = outbound[state]
        in_tons = inbound[state]
        imbalances.append(
            {
                "state": state,
                "state_name": state_name(state),
                "outbound_tons_2024": f"{out_tons:.6f}",
                "inbound_tons_2024": f"{in_tons:.6f}",
                "net_outbound_tons_2024": f"{out_tons - in_tons:.6f}",
            }
        )
    imbalances.sort(key=lambda row: abs(float(row["net_outbound_tons_2024"])), reverse=True)

    top_commodities = [
        {
            "sctg2": commodity,
            "commodity_name": commodity_names.get(commodity, ""),
            "tons_2024": f"{tons:.6f}",
        }
        for commodity, tons in sorted(
            commodity_tons.items(), key=lambda item: item[1], reverse=True
        )[:25]
    ]

    return FafSummary(
        total_rows=total_rows,
        domestic_truck_rows=domestic_truck_rows,
        mode_counts=mode_counts,
        mode_names=mode_names,
        lane_summaries=lane_summaries,
        top_lanes=top_lanes,
        imbalances=imbalances,
        top_commodities=top_commodities,
    )


def is_origin_line(line: str) -> bool:
    if line in SKIP_ORIGIN_LINES or line.startswith("--"):
        return False
    if line.title() in DESTINATIONS:
        return False
    if re.fullmatch(r"Page \d+", line):
        return False
    if re.fullmatch(r"\([+-]?\d+\)|\(\)", line):
        return False
    if re.fullmatch(r"\d{3,5}-\d{3,5}", line):
        return False
    return bool(re.search(r"[A-Z]", line)) and line.upper() == line


def parse_usda_rates() -> tuple[str, list[dict[str, str]], Counter[str]]:
    text = USDA_TEXT.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    report_date = "unknown"
    for line in lines[:20]:
        if re.match(r"^[A-Z][a-z]+ \d{1,2},\d{4}$", line):
            report_date = line
            break

    current_origin = ""
    in_commodity_block = False
    rows: list[dict[str, str]] = []
    availability_counts: Counter[str] = Counter()

    for idx, line in enumerate(lines):
        if line.startswith("--"):
            in_commodity_block = True
            continue

        if in_commodity_block:
            if line in {"RANGE", "MOSTLY"}:
                in_commodity_block = False
                continue
            if line not in DESTINATIONS:
                continue
            in_commodity_block = False

        if is_origin_line(line):
            current_origin = line
            continue

        if line not in DESTINATIONS or not current_origin:
            continue

        availability = lines[idx + 1] if idx + 1 < len(lines) else ""
        if availability not in {
            "Surplus",
            "Slight Surplus",
            "Adequate",
            "Slight Shortage",
            "Shortage",
        }:
            continue

        rate_range = ""
        pct_change = ""
        for candidate in lines[idx + 2 : idx + 8]:
            if candidate in DESTINATIONS or is_origin_line(candidate):
                break
            if re.fullmatch(r"\d{3,5}-\d{3,5}", candidate):
                if rate_range:
                    break
                rate_range = candidate
                continue
            if rate_range and re.fullmatch(r"\([+-]?\d+\)|\(\)", candidate):
                pct_change = candidate
                break

        if not rate_range:
            continue

        low, high = rate_range.split("-", maxsplit=1)
        availability_counts[availability] += 1
        rows.append(
            {
                "report_date": report_date,
                "origin": current_origin,
                "destination": line,
                "availability": availability,
                "rate_low": low,
                "rate_high": high,
                "pct_change": pct_change,
            }
        )

    return report_date, rows, availability_counts


def map_origin_to_state(origin: str) -> tuple[str, str, str]:
    origin_upper = origin.upper()
    for pattern, state, name, note in ORIGIN_STATE_RULES:
        if pattern in origin_upper:
            return state, name, note
    return "", "", "unmapped"


def build_mapped_usda_lanes(
    usda_rows: list[dict[str, str]], faf_lanes: list[dict[str, str]]
) -> list[dict[str, str]]:
    faf_lookup = {
        (row["origin_state"], row["destination_state"]): row for row in faf_lanes
    }
    mapped_rows: list[dict[str, str]] = []
    for row in usda_rows:
        origin_state, origin_name, origin_mapping_note = map_origin_to_state(row["origin"])
        destination_state = DESTINATION_STATE.get(row["destination"], "")
        destination_name = state_name(destination_state)
        faf_lane = faf_lookup.get((origin_state, destination_state), {})
        rate_low = as_float(row["rate_low"])
        rate_high = as_float(row["rate_high"])
        mapped_rows.append(
            {
                "report_date": row["report_date"],
                "usda_origin": row["origin"],
                "origin_state": origin_state,
                "origin_name": origin_name,
                "origin_mapping_note": origin_mapping_note,
                "destination_city": row["destination"],
                "destination_state": destination_state,
                "destination_name": destination_name,
                "availability": row["availability"],
                "scarcity_multiplier": SCARCITY_MULTIPLIER.get(row["availability"], "1.00"),
                "rate_low": row["rate_low"],
                "rate_high": row["rate_high"],
                "rate_midpoint": f"{(rate_low + rate_high) / 2:.2f}",
                "pct_change": row["pct_change"],
                "faf_tons_2024": faf_lane.get("tons_2024", "0.000000"),
                "faf_value_2024": faf_lane.get("value_2024", "0.000000"),
                "faf_tmiles_2024": faf_lane.get("tmiles_2024", "0.000000"),
            }
        )
    return mapped_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    summary: FafSummary,
    report_date: str,
    usda_rows: list[dict[str, str]],
    mapped_usda_lanes: list[dict[str, str]],
    availability_counts: Counter[str],
) -> None:
    top_lanes = "\n".join(
        f"- {row['origin_name']} -> {row['destination_name']}: {float(row['tons_2024']):,.1f} tons"
        for row in summary.top_lanes[:10]
    )
    top_imbalances = "\n".join(
        f"- {row['state_name']}: {float(row['net_outbound_tons_2024']):+,.1f} net outbound tons"
        for row in summary.imbalances[:10]
    )
    availability = "\n".join(
        f"- {label}: {count} lane quotes" for label, count in availability_counts.most_common()
    )
    mapped_count = sum(
        1 for row in mapped_usda_lanes if row["origin_state"] and row["destination_state"]
    )
    faf_positive_count = sum(
        1 for row in mapped_usda_lanes if as_float(row["faf_tons_2024"]) > 0
    )
    mapped_sample = "\n".join(
        f"- {row['origin_name']} -> {row['destination_city']} ({row['destination_name']}): "
        f"${float(row['rate_midpoint']):,.0f}, {row['availability']}, "
        f"FAF tons {float(row['faf_tons_2024']):,.1f}"
        for row in mapped_usda_lanes[:10]
    )
    mode_counts = "\n".join(
        f"- mode {mode or '<blank>'}"
        f" ({summary.mode_names.get(mode, 'unknown')}): {count:,} rows"
        for mode, count in summary.mode_counts.most_common()
    )
    commodities = "\n".join(
        f"- SCTG {row['sctg2']} ({row['commodity_name']}): {float(row['tons_2024']):,.1f} tons"
        for row in summary.top_commodities[:10]
    )

    content = f"""# Initial Calibration Report

## Inputs Inspected

- FAF state package: `{FAF_ZIP.relative_to(ROOT)}`
- USDA truck-rate PDF text: `{USDA_TEXT.relative_to(ROOT)}`

## FAF State Schema Summary

- Total CSV rows inspected: {summary.total_rows:,}
- Domestic truck rows used for v1 summaries: {summary.domestic_truck_rows:,}
- Mode counts:

{mode_counts}

The FAF metadata workbook confirms `dms_mode == 1` maps to Truck.

## Top FAF State Truck Lanes By 2024 Tons

{top_lanes}

## Largest State Imbalances By 2024 Truck Tons

{top_imbalances}

## Top FAF Truck Commodities By 2024 Tons

{commodities}

## USDA FVWTRK Summary

- Report date parsed from PDF: {report_date}
- Parsed lane-rate quotes: {len(usda_rows)}
- Availability categories observed:

{availability}

## USDA-To-FAF Lane Mapping

- USDA quotes with mapped origin/destination states: {mapped_count} of {len(mapped_usda_lanes)}
- Mapped USDA quotes with positive FAF 2024 truck flow on the same state OD lane: {faf_positive_count}

Sample mapped lanes:

{mapped_sample}

## Calibration Decision

The first benchmark can proceed with a state-level FAF backbone and a USDA reefer rate subset.

Recommended v1:

1. Use FAF state-level domestic truck rows for OD intensity and imbalance.
2. Use USDA FVWTRK lane quotes for reefer rate ranges and availability shocks.
3. Use `data/processed/v1_usda_faf_mapped_lanes.csv` as the first seed lane table.
4. Generate synthetic event-level tenders from those public marginals.
5. Keep all realism claims constrained to public calibration, not real tender validation.

## Immediate Next Build Steps

1. Refine mixed-origin USDA mappings, especially CA/AZ border districts.
2. Decide whether v1 should use all truck FAF flows or only food/agricultural SCTG groups.
3. Implement the first synthetic tender generator from the processed CSV summaries.
4. Run opportunity-cost sanity checks before training any model.
"""
    REPORT.write_text(content, encoding="utf-8")


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    faf_summary = inspect_faf()
    report_date, usda_rows, availability_counts = parse_usda_rates()
    mapped_usda_lanes = build_mapped_usda_lanes(usda_rows, faf_summary.lane_summaries)

    write_csv(PROCESSED / "faf_state_lane_intensities_2024.csv", faf_summary.lane_summaries)
    write_csv(PROCESSED / "faf_state_top_lanes_2024.csv", faf_summary.top_lanes)
    write_csv(PROCESSED / "faf_state_imbalance_2024.csv", faf_summary.imbalances)
    write_csv(PROCESSED / "faf_state_top_commodities_2024.csv", faf_summary.top_commodities)
    write_csv(
        PROCESSED / "faf_metadata_modes.csv",
        [{"mode": code, "mode_name": name} for code, name in faf_summary.mode_names.items()],
    )
    write_csv(PROCESSED / "usda_fvwtrk_rate_quotes.csv", usda_rows)
    write_csv(PROCESSED / "v1_usda_faf_mapped_lanes.csv", mapped_usda_lanes)
    write_report(faf_summary, report_date, usda_rows, mapped_usda_lanes, availability_counts)

    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"FAF rows inspected: {faf_summary.total_rows:,}")
    print(f"Domestic truck rows: {faf_summary.domestic_truck_rows:,}")
    print(f"USDA rate quotes parsed: {len(usda_rows):,}")
    print(f"USDA quotes mapped to FAF state lanes: {len(mapped_usda_lanes):,}")


if __name__ == "__main__":
    main()
