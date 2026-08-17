import os
import re
import lemminflect
from pypdf import PdfReader
import spacy

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

PDF_DIR = r"C:\Users\pc\Desktop\paper"  # PDF folder path
OUTPUT_DIR = r"C:\Users\pc\Desktop\paper\processed_variants"  # Output TXT path
os.makedirs(OUTPUT_DIR, exist_ok=True)


def shift_verbs_smart(text: str, target_tense: str = "present") -> str:
    """Smart tense conversion: protects titles, uppercase phrases, participial modifiers (known as), prepositional objects (by doing), and modifies predicates only."""
    doc = nlp(text)
    result = []

    for token in doc:
        # === Protection Rule 1: All uppercase words/titles protection (e.g., YET, PUZZLING, Phenomenal) ===
        if token.text.isupper() and len(token.text) > 1:
            result.append(token.text_with_ws)
            continue

        # Check if the token is a verb or auxiliary verb
        if token.pos_ in ("VERB", "AUX"):

            # ===Protection Rule 2: Non-finite verbs/participial phrases protection ===
            # 1. Prepositional object (e.g., "by examining" -> pcomp)
            is_pcomp = token.dep_ == "pcomp"
            # 2. Noun modifier/participial phrase (e.g., "known as", "puzzling phenomenon" -> acl, amod)
            is_participle = token.dep_ in ("acl", "amod")
            # 3. Infinitive (e.g., "to conduct" -> xcomp or preceded by to)
            is_infinitive = (
                token.dep_ == "xcomp" and token.head.pos_ in ("VERB", "AUX")
            ) or (
                token.i > 0
                and doc[token.i - 1].lower_ == "to"
                and doc[token.i - 1].pos_ == "PART"
            )

            # ===  Only target predicate verbs are allowed to be modified ===
            # ROOT, relcl, advcl, conj, aux, auxpass, ccomp
            is_predicate = token.dep_ in (
                "ROOT",
                "relcl",
                "advcl",
                "conj",
                "aux",
                "auxpass",
                "ccomp",
            )

            # If any protection condition is met, or it is not a predicate, keep it as is!
            if is_pcomp or is_participle or is_infinitive or not is_predicate:
                result.append(token.text_with_ws)
                continue

            # ===  Predicate verb tense conversion ===
            if target_tense == "present":
                target_tag = "VBZ" if token.tag_ in ("VBZ", "VBD") else "VBP"
            elif target_tense == "past":
                target_tag = "VBD"
            else:
                target_tag = token.tag_

            inflected = token._.inflect(target_tag)
            if inflected:
                new_word = inflected
                if token.text[0].isupper():
                    new_word = new_word.capitalize()
                result.append(new_word + token.whitespace_)
            else:
                result.append(token.text_with_ws)
        else:
            result.append(token.text_with_ws)

    return "".join(result)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF"""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text


def process_pdf_papers():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF papers, starting smart extraction and conversion...\n")

    for file_name in pdf_files:
        base_name = os.path.splitext(file_name)[0]
        pdf_path = os.path.join(PDF_DIR, file_name)

        print(f"Parsing PDF: {file_name} ...")
        raw_text = extract_text_from_pdf(pdf_path)

        # 1. Smart present tense variant conversion
        print("   ├── Converting [Smart Present Tense]...")
        pres_text = shift_verbs_smart(raw_text, target_tense="present")
        pres_out_path = os.path.join(
            OUTPUT_DIR, f"{base_name}_tense_pres.txt"
        )
        with open(pres_out_path, "w", encoding="utf-8") as f:
            f.write(pres_text)

        # 2. Smart past tense variant conversion
        print("   └── Converting [Smart Past Tense]...")
        past_text = shift_verbs_smart(raw_text, target_tense="past")
        past_out_path = os.path.join(
            OUTPUT_DIR, f"{base_name}_tense_past.txt"
        )
        with open(past_out_path, "w", encoding="utf-8") as f:
            f.write(past_text)

    print(f"\nAll PDF files processed successfully! Variants saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_pdf_papers()