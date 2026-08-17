import os
import time
import pandas as pd
from openai import OpenAI

try:
    from schema import ReviewResult
except ImportError:
    from pydantic import BaseModel, Field


    class ReviewResult(BaseModel):
        justification: str = Field(
            description="Detailed review pointing out specific strengths and weaknesses."
        )
        novelty: int = Field(description="Novelty score from 1 to 10")
        methodological_rigour: int = Field(
            description="Methodological rigour score from 1 to 10"
        )
        result_credibility: int = Field(
            description="Result credibility score from 1 to 10"
        )
        writing_clarity: int = Field(
            description="Writing clarity score from 1 to 10"
        )
        total_score: int = Field(
            description="Overall assessment score from 1 to 10"
        )

# ==================== 1. Configuration Area ====================
# NOTE: set your API key as an environment variable before running:
#   export OPENAI_API_KEY=your_key_here      (Mac/Linux)
#   set OPENAI_API_KEY=your_key_here         (Windows)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=OPENAI_API_KEY)

# NOTE: update these paths to your local paths before running.
DATA_DIR = r"C:\Users\pc\Desktop\paper\processed_variants"
OUTPUT_FILE = r"C:\Users\pc\Desktop\paper\full_126_gpt5_results.csv"

MODEL_NAME = "gpt-5"

SYSTEM_PROMPT = """You are an expert peer reviewer for top-tier AI/NLP conferences (such as ICLR, NeurIPS). 
Evaluate the following academic paper text thoroughly and provide structured scores from 1 to 10 for each criteria."""

VARIANTS = [
    "original",
    "tense_pres",
    "tense_past",
    "hedging_strengthen",
    "hedging_weaken",
    "counterfactual",
]


# ==================== 2. API Call Function ====================
def get_gpt_review(paper_text, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            response = client.beta.chat.completions.parse(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Here is the paper text:\n\n{paper_text[:30000]}",
                    },
                ],
                response_format=ReviewResult,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            print(f"API Call Error (Attempt {attempt}/{max_retries}): {e}")
            time.sleep(2 ** attempt)
    return None


# ==================== 3. Smart File Localization Function ====================
def locate_variant_file(paper_prefix, variant, all_files):
    variant_tags = ["pres", "past", "strengthen", "weaken", "counterfactual"]

    if variant == "original":
        for f in all_files:
            if f.startswith(paper_prefix) and f.endswith(".txt"):
                if not any(tag in f for tag in variant_tags):
                    return f
        for f in all_files:
            if paper_prefix in f and f.endswith(".txt"):
                if "original" in f or not any(
                        tag in f for tag in variant_tags
                ):
                    return f

    variant_keywords = {
        "tense_pres": ["tense_pres", "pres"],
        "tense_past": ["tense_past", "past"],
        "hedging_strengthen": ["hedging_strengthen", "strengthen"],
        "hedging_weaken": ["hedging_weaken", "weaken"],
        "counterfactual": ["counterfactual"],
    }

    keywords = variant_keywords.get(variant, [variant])
    for f in all_files:
        if f.startswith(paper_prefix) and f.endswith(".txt"):
            if any(kw in f for kw in keywords):
                return f

    return None


# ==================== 4. Main Logic ====================
def run_full_experiment():
    if not os.path.exists(DATA_DIR):
        print(f"Data directory not found: {DATA_DIR}")
        return

    all_files_in_dir = os.listdir(DATA_DIR)
    cf_files = [f for f in all_files_in_dir if "_counterfactual.txt" in f]
    paper_prefixes = sorted(
        [f.replace("_counterfactual.txt", "") for f in cf_files]
    )

    print("=" * 80)
    print(
        f"GPT-5 Full 6-Dimension Review Started! (Includes Original + 5 Variants, 21 papers x 6 dims x 3 runs)"
    )
    print(f"Model: {MODEL_NAME}")
    print(f"Output File: {OUTPUT_FILE}")
    print("=" * 80 + "\n")

    all_records = []

    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_csv(OUTPUT_FILE)
            all_records = existing_df.to_dict("records")
            print(f"Detected existing GPT-5 progress, loaded {len(all_records)} records, resuming...")
        except Exception:
            pass

    for p_idx, paper in enumerate(paper_prefixes, 1):
        print(
            f"\n[{p_idx}/{len(paper_prefixes)}] Processing paper: {paper[:30]}..."
        )
        print("-" * 60)

        for variant in VARIANTS:
            actual_file = locate_variant_file(paper, variant, all_files_in_dir)

            if not actual_file:
                print(f"Variant [{variant}] file not found, skipped.")
                continue

            file_path = os.path.join(DATA_DIR, actual_file)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                paper_text = f.read()

            for rep in range(1, 4):
                already_done = any(
                    r.get("paper_name") == paper
                    and r.get("variant_type") == variant
                    and r.get("repeat_index") == rep
                    for r in all_records
                )
                if already_done:
                    print(f"[{variant}] Run {rep}/3 already completed, skipped.")
                    continue

                print(
                    f"[{actual_file[:35]}...] -> [{variant}] Run {rep}/3 calling [{MODEL_NAME}]..."
                )
                result = get_gpt_review(paper_text)

                if result:
                    record = {
                        "paper_name": paper,
                        "variant_type": variant,
                        "repeat_index": rep,
                        "novelty": result.novelty,
                        "methodological_rigour": result.methodological_rigour,
                        "result_credibility": result.result_credibility,
                        "writing_clarity": result.writing_clarity,
                        "total_score": result.total_score,
                        "justification": result.justification,
                    }
                    all_records.append(record)

                    print(
                        f"Total Score: [{result.total_score}] | "
                        f"Sub-scores: [Nov:{result.novelty} | Rig:{result.methodological_rigour} | Cre:{result.result_credibility} | Cla:{result.writing_clarity}]"
                    )
                else:
                    print(f"Run {rep} call failed.")

                time.sleep(0.5)

        if all_records:
            df = pd.DataFrame(all_records)
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 80)
    print(f"GPT-5 Full 6-Dimension Experiment Successfully Completed! Results saved to: {OUTPUT_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    run_full_experiment()