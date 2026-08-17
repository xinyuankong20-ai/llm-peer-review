# Robustness of LLM-based Peer Reviewers under Text Perturbations

This repository contains the code and results for the MSc dissertation
"Robustness of LLM-based Peer Reviewers under Text Perturbations: A
Comparative Analysis Between GPT-4o-mini and GPT-5" (University of
Edinburgh, School of Informatics, 2026).

## What this repository contains

- `src/perturbation/`: rule-based text perturbation engines
  - `tense_engine.py`: converts paper text to present or past tense
  - `hedging_engine.py`: strengthens or weakens hedging language
  - `counterfactual_engine.py`: reverses a paper's core claims
- `src/schema.py`: the Pydantic schema used to constrain model output
- `src/run_gpt4o_mini.py`, `src/run_gpt5.py`: the automated evaluation
  pipelines for each model
- `prompts/system_prompt.txt`: the fixed system prompt used in all runs
- `results/`: the two raw result files (378 evaluation records per model:
  21 papers x 6 variants x 3 repeated runs)
- `data/paper_list.csv`: the list of the 21 papers used in the study

## What this repository does NOT contain

The full text of the 21 papers, or the perturbed versions of them, is
not included, since these papers are copyrighted by their original
authors. `data/paper_list.csv` lists the paper titles, authors, and
venues so the original PDFs can be retrieved from their publishers.

## How to reproduce

1. Install dependencies:

pip install openai pydantic pandas spacy lemminflect


2. Set your API key as an environment variable:

export OPENAI_API_KEY=your_key_here # Mac/Linux
set OPENAI_API_KEY=your_key_here # Windows


3. Update the `PDF_DIR` and `OUTPUT_DIR` paths in each perturbation
   engine and evaluation script to match your local setup.

4. Run each perturbation engine on your own copy of the source papers
   to generate the six text variants per paper.

5. Run the evaluation pipelines:

python src/run_gpt4o_mini.py
python src/run_gpt5.py


## License

Code is released under the MIT License (see LICENSE).
