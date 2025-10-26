import os
import re
import csv
import glob
import argparse

# Target CSV columns (order matters)
COLUMNS = [
    "id",
    "disease name",
    "overview",
    "symptoms and causes",
    "diagnosis and tests",
    "management and treatment",
    "outlook / prognosis",
    "prevention",
    "living with",
    "additional common questions",
    "suggestions",
    "source url",
]

# All possible top-level section headers found in the files
SECTION_HEADERS = [
    "Overview",
    "What is",
    "What are",
    "Symptoms and Causes",
    "Diagnosis and Tests",
    "Management and Treatment",
    "Outlook / Prognosis",
    "Prevention",
    "Living With",
    "Additional Common Questions",
    "A note from Cleveland Clinic",
]

# Regex to detect a top-level section header followed by hyphens
SECTION_PATTERN = re.compile(r"(?m)^(?P<title>[^\n\r]+)\n[-]{2,}\n")

def _normalize_name(s: str) -> str:
    """Normalize disease names for lookup (lowercase, collapse whitespace)."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.strip().lower())

def build_link_map(input_dir: str):
    """
    Read mapping files named like 'diseases_*.txt' in input_dir (non-recursive)
    and return dict normalized_name -> url.
    Each line expected as: Disease Name:URL
    """
    link_map = {}
    pattern = os.path.join(input_dir, "diseases_*.txt")
    for path in glob.glob(pattern):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln or ":" not in ln:
                        continue
                    name, url = ln.split(":", 1)
                    name = name.strip()
                    url = url.strip()
                    if name and url:
                        link_map[_normalize_name(name)] = url
        except Exception:
            # be tolerant of corrupt files; skip on error
            continue
    return link_map

def clean_field(v):
    """
    Normalize field values:
    - treat None as empty
    - remove any occurrence of "(Not available)" (case-insensitive)
    - collapse whitespace
    """
    if v is None:
        return ""
    v = str(v).strip()
    # Remove occurrences like "(Not available)" or "Not available" anywhere in the text
    v = re.sub(r"\(?\s*Not\s+available\s*\)?", "", v, flags=re.IGNORECASE)
    # Collapse whitespace/newlines to a single space and strip again
    v = re.sub(r"\s+", " ", v).strip()
    return v

def split_sections(text: str):
    """
    Return an ordered list of (title, content) for top-level sections.
    A top-level section is a line of text followed by a line of hyphens.
    """
    sections = []
    matches = list(SECTION_PATTERN.finditer(text))
    for i, m in enumerate(matches):
        title = m.group("title").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append((title, content))
    return sections

def parse_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Disease name = first non-empty line
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    disease_name = lines[0] if lines else os.path.basename(path).rsplit(".", 1)[0]

    # Initialize section map
    section_map = {title: "" for title in SECTION_HEADERS}

    # Fill section map
    for title, content in split_sections(text):
        if title in section_map:
            section_map[title] = content.strip()

    # Extract fields
    overview = section_map["Overview"]
    if not overview or overview == "(Not available)":
        what_is = section_map["What is"]
        if what_is and what_is != "(Not available)":
            overview = what_is
        else:
            what_are = section_map["What are"]
            if what_are and what_are != "(Not available)":
                overview = what_are
    
    symptoms_causes = section_map["Symptoms and Causes"]
    diagnosis = section_map["Diagnosis and Tests"]
    management = section_map["Management and Treatment"]
    outlook = section_map["Outlook / Prognosis"]
    prevention = section_map["Prevention"]
    living = section_map["Living With"]
    additional = section_map["Additional Common Questions"]
    suggestion = section_map["A note from Cleveland Clinic"]

    overview = clean_field(overview)
    symptoms_causes = clean_field(symptoms_causes)
    diagnosis = clean_field(diagnosis)
    management = clean_field(management)
    prevention = clean_field(prevention)
    living = clean_field(living)
    additional = clean_field(additional)
    suggestion = clean_field(suggestion)

    return {
        "disease name": disease_name,
        "overview": overview,
        "symptoms and causes": symptoms_causes,
        "diagnosis and tests": diagnosis,
        "management and treatment": management,
        "outlook / prognosis": outlook,
        "prevention": prevention,
        "living with": living,
        "additional common questions": additional,
        "suggestions": suggestion,
    }

def main(input_dir: str, output_csv: str):
    # build mapping from the summary files first
    link_map = build_link_map(input_dir)
    mapping_files = set(os.path.abspath(p) for p in glob.glob(os.path.join(input_dir, "diseases_*.txt")))

    files = sorted(glob.glob(os.path.join(input_dir, "**", "*.txt"), recursive=True))

    files = [f for f in files if os.path.abspath(f) not in mapping_files]

    rows = []
    for i, path in enumerate(files, start=1):
        data = parse_file(path)
        row = {"id": i}
        row.update(data)
        row["source url"] = link_map.get(_normalize_name(data.get("disease name", "")), "")
        rows.append(row)

    # Write CSV
    with open(output_csv, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            for col in COLUMNS:
                row.setdefault(col, "")
                row[col] = clean_field(row[col])
            writer.writerow(row)

    print(f"Wrote {len(rows)} rows to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert medical .txt files to a CSV.")
    parser.add_argument(
        "-i", "--input-dir",
        default=".",
        help="Directory containing .txt files (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output-csv",
        default="diseases_dataset.csv",
        help="Output CSV filename (default: diseases_dataset.csv)"
    )
    args = parser.parse_args()
    main(args.input_dir, args.output_csv)
