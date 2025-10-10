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
    "symptoms",
    "causes",
    "diagnosis and tests",
    "management and treatment",
    "outlook / prognosis",
    "prevention",
    "living with",
    "additional common questions",
    "suggestions",
]

# All possible top-level section headers found in the files
SECTION_HEADERS = [
    "Overview",
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

def extract_symptoms_and_causes(symptoms_and_causes_text: str):
    """
    Heuristic split of the combined "Symptoms and Causes" section into
    two strings: (symptoms, causes).
    Works with different phrasings like 'What are the symptoms...' and
    'What causes...'.
    """
    s = symptoms_and_causes_text

    def find_first(patterns):
        idxs = []
        for p in patterns:
            m = re.search(p, s, flags=re.IGNORECASE | re.DOTALL)
            if m:
                idxs.append(m.start())
        return min(idxs) if idxs else None

    symptoms_starts = [
        r"\bSymptoms of\b",
        r"\bSigns and symptoms\b",
        r"\bWhat are the signs and symptoms\b",
        r"\bWhat are the symptoms\b",
        r"\bSymptoms include\b",
        r"\bSymptoms\b",
    ]
    causes_starts = [
        r"\bWhat cause\b",
        r"^Causes\b",
        r"\bCauses\b",
        r"\bCause\b",
        r"\bWhy .* (happen|occur)\b",
    ]
    symptoms_end_markers = causes_starts + [
        r"\bRisk factors\b",
        r"\bStages\b",
        r"\bComplications\b",
    ]

    s_sym_start = find_first(symptoms_starts) or 0
    s_cause_start = find_first(causes_starts)

    s_sym_end = None
    for p in symptoms_end_markers:
        m = re.search(p, s, flags=re.IGNORECASE | re.DOTALL)
        if m:
            cand = m.start()
            if cand > s_sym_start and (s_sym_end is None or cand < s_sym_end):
                s_sym_end = cand
    if s_sym_end is None:
        s_sym_end = len(s)

    if s_cause_start is not None:
        symptoms_text = s[s_sym_start:s_sym_end].strip()
        causes_text = s[s_cause_start:].strip()
    else:
        # Fallback: split on the first plain 'Causes' if present; else put all in symptoms.
        m = re.search(r"\bCause?\b", s, flags=re.IGNORECASE)
        if m:
            symptoms_text = s[:m.start()].strip()
            causes_text = s[m.start():].strip()
        else:
            symptoms_text = s.strip()
            causes_text = ""

    return symptoms_text, causes_text

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
    sc_text = section_map["Symptoms and Causes"]
    symptoms, causes = extract_symptoms_and_causes(sc_text) if sc_text else ("", "")
    diagnosis = section_map["Diagnosis and Tests"]
    management = section_map["Management and Treatment"]
    outlook = section_map["Outlook / Prognosis"]
    prevention = section_map["Prevention"]
    living = section_map["Living With"]
    additional = section_map["Additional Common Questions"]
    suggestion = section_map["A note from Cleveland Clinic"]

    overview = clean_field(overview)
    sc_text = clean_field(sc_text)
    symptoms = clean_field(symptoms)
    causes = clean_field(causes)
    diagnosis = clean_field(diagnosis)
    management = clean_field(management)
    prevention = clean_field(prevention)
    living = clean_field(living)
    additional = clean_field(additional)
    suggestion = clean_field(suggestion)
    


    return {
        "disease name": disease_name,
        "overview": overview,
        "symptoms": symptoms,
        "causes": causes,
        "diagnosis and tests": diagnosis,
        "management and treatment": management,
        "outlook / prognosis": outlook,
        "prevention": prevention,
        "living with": living,
        "additional common questions": additional,
        "suggestions": suggestion,
    }

def main(input_dir: str, output_csv: str):
    files = sorted(glob.glob(os.path.join(input_dir, "**", "*.txt"), recursive=True))
    rows = []
    for i, path in enumerate(files, start=1):
        data = parse_file(path)
        row = {"id": i}
        row.update(data)
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
        default="medical_topics.csv",
        help="Output CSV filename (default: medical_topics.csv)"
    )
    args = parser.parse_args()
    main(args.input_dir, args.output_csv)
