import os
import re
import pypdf

# ==================== 1. Core Polarity and Counterfactual Vocabulary Mapping Configuration ====================
POLARITY_PAIRS = {
    # Action and negation mapping (matched from longest to shortest to prioritize complex phrases)
    "outperforms": "fails to outperform",
    "outperform": "fail to outperform",
    "outperformed": "failed to outperform",
    "improves": "fails to improve",
    "improve": "fail to improve",
    "improved": "failed to improve",
    "exceeds": "fails to exceed",
    "exceed": "fail to exceed",
    "exceeded": "failed to exceed",
    "surpasses": "fails to surpass",
    "surpass": "fail to surpass",
    "surpassed": "failed to surpass",
    "achieves": "fails to achieve",
    "achieve": "fail to achieve",
    "achieved": "failed to achieve",
    "demonstrates": "fails to demonstrate",
    "demonstrate": "fail to demonstrate",
    "demonstrated": "failed to demonstrate",
    "shows": "fails to show",
    "show": "fail to show",
    "showed": "failed to show",
    "confirms": "fails to confirm",
    "confirm": "fail to confirm",
    "confirmed": "failed to confirm",
    # Comparison and direction mapping
    "better than": "worse than",
    "superior to": "inferior to",
    "higher than": "lower than",
    "larger than": "smaller than",
    "stronger than": "weaker than",
    "increases": "decreases",
    "increased": "decreased",
    "effective": "ineffective",
    "effectively": "ineffectively",
}


# ==================== 2. Text Parsing and Replacement Core Logic ====================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a PDF file."""
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


def apply_counterfactual(text: str) -> str:
    """Rewrite positive polarity assertions into counterfactual (negative/failed) versions while preserving the initial letter capitalization."""
    result = text
    sorted_pairs = sorted(
        POLARITY_PAIRS.items(), key=lambda x: len(x[0]), reverse=True
    )

    for positive, negative in sorted_pairs:
        pattern = re.compile(r"\b" + re.escape(positive) + r"\b", re.IGNORECASE)

        def replace_match(m, neg=negative):
            if m.group(0)[0].isupper():
                return neg.capitalize()
            return neg

        result = pattern.sub(replace_match, result)
    return result


def clean_counterfactual_grammar(text: str) -> str:
    """Post-processing cleaning: resolve double negations (e.g., failed to fail to) and compound modifier flaws."""
    # 1. Resolve double negations
    cleaned = re.sub(
        r"\bfailed\s+to\s+failed\s+to\b", "failed to", text, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\bfailed\s+to\s+fail\s+to\b", "failed to", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\bfails\s+to\s+fails\s+to\b", "fails to", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\bfails\s+to\s+fail\s+to\b", "fails to", cleaned, flags=re.IGNORECASE
    )

    # 2. Correct compound expressions (e.g., cost-ineffectively -> cost-ineffective)
    cleaned = re.sub(
        r"\bcost-ineffectively\b", "cost-ineffective", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\bcost\s+ineffectively\b", "cost ineffective", cleaned, flags=re.IGNORECASE
    )

    return cleaned


# ==================== 3. Section-Based Precise Slicing Modification ====================

def process_targeted_counterfactual(full_text: str) -> str:
    """
    Identify core sections such as Abstract, Experiments/Results, and Conclusion via regular expressions,
    and apply counterfactual modifications only to these three parts while keeping Intro / Related Work / Method intact.
    """
    section_pattern = re.compile(
        r"^\s*(?:\d+\.?\s*)?(abstract|introduction|related\s+work|method|methodology|approach|experiments?|experimental\s+results?|results?\s+and\s+discussion|discussion|conclusion|conclusions)\b",
        re.IGNORECASE | re.MULTILINE,
    )

    matches = list(section_pattern.finditer(full_text))

    if not matches:
        print("    Warning: Failed to precisely locate section titles; falling back to full-text replacement.")
        raw_cf = apply_counterfactual(full_text)
        return clean_counterfactual_grammar(raw_cf)

    processed_blocks = []

    # 1. Content from the beginning to the first title (usually contains Title and Abstract)
    first_start = matches[0].start()
    preamble = full_text[:first_start]
    processed_blocks.append(apply_counterfactual(preamble))

    # 2. Process each section slice by slice
    for i in range(len(matches)):
        start_idx = matches[i].start()
        end_idx = (
            matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        )

        section_title = matches[i].group(1).lower().strip()
        section_content = full_text[start_idx:end_idx]

        # Determine whether the current section belongs to [Abstract / Experimental Results / Conclusion]
        is_target = any(
            target in section_title
            for target in ["abstract", "experiment", "result", "conclusion"]
        )

        if is_target:
            modified_content = apply_counterfactual(section_content)
            processed_blocks.append(modified_content)
        else:
            processed_blocks.append(section_content)

    full_counterfactual_text = "".join(processed_blocks)
    return clean_counterfactual_grammar(full_counterfactual_text)


# ==================== 4. Main Function and Batch Processing ====================

def process_all_papers():
    PDF_DIR = r"C:\Users\pc\Desktop\paper"
    OUTPUT_DIR = r"C:\Users\pc\Desktop\paper\processed_variants"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    print(
        f"[Full Counterfactual Engine] Starting batch processing of {len(pdf_files)} papers (modifying Abstract / Experiments / Conclusion only)...\n"
    )

    for idx, file_name in enumerate(pdf_files, 1):
        base_name = os.path.splitext(file_name)[0]
        pdf_path = os.path.join(PDF_DIR, file_name)

        print(f"[{idx}/{len(pdf_files)}] Parsing PDF: {file_name} ...")
        raw_text = extract_text_from_pdf(pdf_path)

        cf_text = process_targeted_counterfactual(raw_text)
        cf_path = os.path.join(
            OUTPUT_DIR, f"{base_name}_counterfactual.txt"
        )

        with open(cf_path, "w", encoding="utf-8") as f:
            f.write(cf_text)
        print(f"   └── Generated logical counterfactual variant: {base_name}_counterfactual.txt\n")

    print(
        f"All {len(pdf_files)} papers' logical consistent counterfactual variants have been successfully updated and saved!"
    )
    print("Output path:", os.path.abspath(OUTPUT_DIR))


if __name__ == "__main__":
    process_all_papers()