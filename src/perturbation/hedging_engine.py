import os
import re
import pypdf

# ==================== 1. Hedging Pair Configuration ====================

# Weaken hedging mapping: strong/certain assertions -> weak/cautious assertions
HEDGING_WEAKEN_PAIRS = {
    "proves": "suggests a possibility that",
    "prove": "suggest a possibility that",
    "proved": "suggested that",
    "demonstrates": "seems to indicate",
    "demonstrate": "seem to indicate",
    "demonstrated": "seemed to indicate",
    "shows": "tends to show",
    "show": "tend to show",
    "showed": "tended to show",
    "confirms": "appears to support",
    "confirm": "appear to support",
    "confirmed": "appeared to support",
    "ensures": "helps to promote",
    "ensure": "help to promote",
    "definitely": "likely",
    "clearly": "apparently",
    "obviously": "presumably",
    "always": "frequently",
    "never": "rarely",
    "conclusively": "partially",
    "strongly": "moderately",
    "significantly": "potentially",
}

# Strengthen hedging mapping: vague/concession phrases -> strong/certain assertions
HEDGING_STRENGTHEN_PAIRS = {
    # === Adverb combination priority cleanup (prevents double adverbs such as "explicitly clearly proves") ===
    "explicitly suggests": "explicitly proves",
    "explicitly suggest": "explicitly prove",
    "clearly suggests": "clearly proves",
    "clearly suggest": "clearly prove",
    "strongly suggests": "conclusively proves",
    "strongly suggest": "conclusively prove",
    "explicitly indicates": "explicitly demonstrates",
    "explicitly indicate": "explicitly demonstrate",
    # === Conventional phrase and word mapping ===
    "suggests a possibility that": "proves",
    "suggest a possibility that": "prove",
    "tend to show": "clearly prove",
    "tend to": "definitely",
    "appear to support": "confirm",
    "appear to": "clearly",
    "seems to indicate": "demonstrates",
    "seem to indicate": "demonstrate",
    "seemed to indicate": "demonstrated",
    "suggests": "clearly proves",
    "suggest": "clearly prove",
    "suggested": "conclusively proved",
    "indicates": "unmistakably demonstrates",
    "indicate": "unmistakably demonstrate",
    "possibly": "definitely",
    "probably": "certainly",
    "likely": "indubitably",
    "potentially": "significantly",
    "arguably": "conclusively",
    "may": "will certainly",
    "might": "will definitely",
    "seem": "clearly show",
    "appear": "clearly show",
}

# ==================== 2. Core Processing Functions ====================


def weaken_hedging(text: str) -> str:
    """Weaken paper tone (full regex matching, prioritising longer phrases)."""
    result = text
    # Sort by length in descending order so longer phrases are matched first,
    # preventing shorter substrings from being replaced prematurely.
    sorted_pairs = sorted(
        HEDGING_WEAKEN_PAIRS.items(), key=lambda x: len(x[0]), reverse=True
    )
    for strong, weak in sorted_pairs:
        pattern = re.compile(r"\b" + re.escape(strong) + r"\b", re.IGNORECASE)

        def replace_match(m, w=weak):
            if m.group(0)[0].isupper():
                return w.capitalize()
            return w

        result = pattern.sub(replace_match, result)
    return result


def strengthen_hedging(text: str) -> str:
    """Strengthen paper tone (full regex matching, prioritising longer phrases and adverb combinations)."""
    result = text
    # Sort by length in descending order so adverb combinations and longer
    # phrases are matched before shorter, single-word substitutions.
    sorted_pairs = sorted(
        HEDGING_STRENGTHEN_PAIRS.items(), key=lambda x: len(x[0]), reverse=True
    )
    for weak, strong in sorted_pairs:
        pattern = re.compile(r"\b" + re.escape(weak) + r"\b", re.IGNORECASE)

        def replace_match(m, s=strong):
            if m.group(0)[0].isupper():
                return s.capitalize()
            return s

        result = pattern.sub(replace_match, result)
    return result


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a PDF file."""
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


# ==================== 3. Batch Processing Logic for the 21 Papers ====================


def process_all_papers():
    # NOTE: update PDF_DIR and OUTPUT_DIR to your local paths before running.
    PDF_DIR = r"C:\Users\pc\Desktop\paper"
    OUTPUT_DIR = r"C:\Users\pc\Desktop\paper\processed_variants"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Dynamically scan the input folder for the 21 source PDF files.
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    print(
        f"[Hedging Engine] Starting batch processing of {len(pdf_files)} papers "
        f"to generate tone variant files...\n"
    )

    for file_name in pdf_files:
        base_name = os.path.splitext(file_name)[0]
        pdf_path = os.path.join(PDF_DIR, file_name)

        print(f"Parsing PDF: {file_name} ...")
        raw_text = extract_text_from_pdf(pdf_path)

        # 1. Generate the strengthened tone variant.
        strengthened_text = strengthen_hedging(raw_text)
        strong_path = os.path.join(
            OUTPUT_DIR, f"{base_name}_hedging_strengthen.txt"
        )
        with open(strong_path, "w", encoding="utf-8") as f:
            f.write(strengthened_text)
        print(f"   - Saved strengthened tone variant: {base_name}_hedging_strengthen.txt")

        # 2. Generate the weakened tone variant.
        weakened_text = weaken_hedging(raw_text)
        weak_path = os.path.join(
            OUTPUT_DIR, f"{base_name}_hedging_weaken.txt"
        )
        with open(weak_path, "w", encoding="utf-8") as f:
            f.write(weakened_text)
        print(f"   - Saved weakened tone variant: {base_name}_hedging_weaken.txt\n")

    print(
        f"All {len(pdf_files)} papers' strengthened and weakened tone texts "
        f"have been successfully generated."
    )
    print("Output path:", os.path.abspath(OUTPUT_DIR))


if __name__ == "__main__":
    process_all_papers()