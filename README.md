# MP1 Prompt Lab Script Guide

This guide covers the features and setup for [`MP1_Starter_Template.py`](./MP1_Starter_Template.py).

## What the script does

The script compares four prompting strategies for extracting information from job postings:

- **Zero-shot:** asks for the fields without examples or a persona.
- **Few-shot:** includes worked examples.
- **Structured:** provides a recruiter persona and explicit output requirements.
- **Chain-of-thought:** asks the model to analyze the posting before returning JSON.

For each posting, it requests `company`, `role`, and `years_experience_required`. It then:

1. Runs one extraction request per posting and strategy asynchronously.
2. Parses the JSON response and records the result, token counts, latency, estimated extraction cost, and any extraction error.
3. Compares each result with the golden set, scoring exact field matches from 0 to 3.
4. Uses a `gpt-4o` judge to assign a score from 1 to 4.
5. Prints a pandas summary grouped by strategy, including mean accuracy, parse rate, mean judge score, total estimated cost, and median latency.

The **Total cost ($)** column estimates extraction requests only; judge-request usage is not included. Running the script makes paid API requests.

## Requirements

- Python 3.10 or newer
- An API key for the configured OpenAI-compatible service
- The project data files:
  - `data/job_snippets.jsonl`
  - `data/golden_set.jsonl`

Install the Python dependencies from the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run the interpreter and pip directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure the environment

Create a `.env` file in the project root, next to `requirements.txt`:

```dotenv
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://openai.com/v1
```

`OPENAI_BASE_URL` is optional; the script defaults to the URL shown above. Set it to the endpoint for your API provider if different. Keep `.env` private and do not commit credentials.

## Run

From the project root:

```powershell
python learner\MP1_Starter_Template.py
```

If you did not activate the virtual environment, use its interpreter directly:

```powershell
.\.venv\Scripts\python.exe learner\MP1_Starter_Template.py
```

The script locates the `data` directory relative to its own file, so it does not depend on the current working directory. It prints the number of loaded snippets and scored results, followed by the comparison summary. It does not save the results to a file.

## Understanding the summary

| Column | Meaning |
|---|---|
| Accuracy (mean of 3) | Average number of exact field matches, from 0 to 3 |
| Parse rate | Fraction of responses parsed as JSON objects |
| Judge score | Mean judge score, from 1 to 4 |
| Total cost ($) | Estimated cost of extraction calls only |
| Latency p50 (s) | Median extraction latency in seconds |

With the provided 10 snippets, the script makes 40 extraction requests (10 snippets × 4 strategies), followed by one judge request per result.

## Troubleshooting

- **Missing API key:** confirm `.env` is in the project root and contains `OPENAI_API_KEY`.
- **Missing data file:** confirm both JSONL files are in the root `data` directory.
- **Import error:** activate the virtual environment and install `requirements.txt`.
- **Authentication or connection error:** check the API key and, if necessary, set `OPENAI_BASE_URL` to the correct endpoint.
