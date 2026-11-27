#!/usr/bin/env python
"""Compare LLM prompt strategies for extracting information from job postings."""

import asyncio
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
load_dotenv(DATA_DIR.parent / ".env")
MODEL = "gpt-4o-mini"
JUDGE_MODEL = "gpt-4o"
TEMPERATURE = 0.0
RATES = {
    "gpt-4o-mini": {"in": 0.15 / 1_000_000, "out": 0.60 / 1_000_000},
    "gpt-4o": {"in": 2.50 / 1_000_000, "out": 10.00 / 1_000_000},
}


def load_data() -> tuple[list[dict], dict[str, dict]]:
    snippets = [
        json.loads(line)
        for line in (DATA_DIR / "job_snippets.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    golden_rows = [
        json.loads(line)
        for line in (DATA_DIR / "golden_set.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    return snippets, {row["id"]: row for row in golden_rows}


def prompt_zero_shot(snippet_text: str) -> list[dict]:
    """Strategy 1 — zero-shot. Just ask, no examples, no persona."""

    return [
        {
            "role": "user",
            "content": f"""
Extract the following information from the job posting:

1. company: Company or organization name.
2. role: Job title.
3. years_experience_required: Minimum years of experience required.

Rules:
- Return years_experience_required as an integer.
- If no experience is required, return 0.
- If experience is not mentioned, return null.
- If a range is provided (e.g., 3 to 5 years), return the minimum.
- Return only valid JSON.
- Do not include explanations.

Job posting:
{snippet_text}

Expected JSON format:
{{
    "company": "string or null",
    "role": "string or null",
    "years_experience_required": "integer or null"
}}
"""
        }
    ]


def prompt_few_shot(snippet_text: str) -> list[dict]:
    """Strategy 2 — few-shot. Include 2-3 worked examples in the prompt."""

    prompt = f"""
You are extracting information from job postings.

Extract these three fields:
- company: Company name
- role: Job title
- years_experience_required: Minimum required years of experience as an integer.

Rules:
1. Return 0 if no prior experience is required or fresh graduates are welcome.
2. Return null if the posting does not specify an experience requirement.
3. If a range is provided (e.g., 3-5 years), return the minimum value.
4. Return only valid JSON. Do not include explanations.

Here are some examples:

Example 1:
Job posting:
"Acme Corp is hiring a Senior Software Engineer.
Candidates should have 5+ years of backend development experience."

Expected output:
{{
    "company": "Acme Corp",
    "role": "Senior Software Engineer",
    "years_experience_required": 5
}}

Example 2:
Job posting:
"Hooli is looking for a Junior Frontend Developer.
Fresh graduates are welcome. No prior experience is required."

Expected output:
{{
    "company": "Hooli",
    "role": "Junior Frontend Developer",
    "years_experience_required": 0
}}

Example 3:
Job posting:
"Cyberdyne Systems is hiring an AI/ML Research Scientist.
No specific years of experience requirement is listed."

Expected output:
{{
    "company": "Cyberdyne Systems",
    "role": "AI/ML Research Scientist",
    "years_experience_required": null
}}

Now extract information from this job posting:

Job posting:
{snippet_text}

Expected JSON output:
"""

    return [
        {
            "role": "user",
            "content": prompt
        }
    ]


def prompt_structured(snippet_text: str) -> list[dict]:
    """Strategy 3 — structured / role-based. Use a system prompt with a persona and explicit JSON schema."""

    system_prompt = """
You are an expert technical recruiter and job description analyst.

Your task is to extract structured information from job postings.

Extract exactly these three fields:

1. company:
   - The organization or company name.
   - Return a string.
   - Return null if not mentioned.

2. role:
   - The job title or position.
   - Return a string.
   - Return null if not mentioned.

3. years_experience_required:
   - Return the minimum required years of experience as an integer.
   - If a range is specified (e.g., 3-5 years), return 3.
   - If fresh graduates are welcome or no prior experience is required, return 0.
   - If no specific experience requirement is mentioned, return null.

Output requirements:
- Return only valid JSON.
- Use exactly the three field names specified above.
- Do not add extra fields or explanations.
- Follow this JSON structure:

{
    "company": "string or null",
    "role": "string or null",
    "years_experience_required": "integer or null"
}
"""

    user_prompt = f"""
Extract the required information from the following job posting:

{snippet_text}
"""

    return [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]


def prompt_cot(snippet_text: str) -> list[dict]:
    """Strategy 4 — chain-of-thought. Ask the model to reason before answering."""

    system_prompt = """
You are an expert job description analyst.

Analyze the job posting carefully before extracting the information.

Follow these steps internally:
1. Identify the company name.
2. Identify the job title.
3. Find the experience requirement.
4. Determine the minimum required years of experience.
5. Check whether experience is optional, not required, or unspecified.

Extraction rules:
- Return the minimum value for experience ranges (e.g., 3-5 years means 3).
- Return 0 if no prior experience is required.
- Return null if the experience requirement is not specified.
- Return null for company or role if they are not mentioned.

Return only valid JSON with exactly these fields:
{
    "company": "string or null",
    "role": "string or null",
    "years_experience_required": "integer or null"
}

Do not include your internal reasoning or explanations in the output.
"""

    user_prompt = f"""
Analyze this job posting and return the extracted information:

{snippet_text}
"""

    return [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]


STRATEGIES = {
    'zero_shot': prompt_zero_shot,
    'few_shot': prompt_few_shot,
    'structured': prompt_structured,
    'cot': prompt_cot,
}


def parse_response(raw_response: str) -> dict | None:
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


async def run_one(
    strategy_name: str,
    snippet: dict,
    client: AsyncOpenAI,
) -> dict:
    start_time = time.perf_counter()
    messages = STRATEGIES[strategy_name](snippet["snippet"])

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
        )
        raw_response = response.choices[0].message.content or ""
        result = parse_response(raw_response)
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        error = None
    except Exception as exc:
        raw_response = ""
        result = None
        prompt_tokens = 0
        completion_tokens = 0
        error = f"{type(exc).__name__}: {exc}"

    elapsed_time = time.perf_counter() - start_time
    cost = (
        prompt_tokens * RATES[MODEL]["in"]
        + completion_tokens * RATES[MODEL]["out"]
    )

    return {
        "strategy": strategy_name,
        "snippet_id": snippet["id"],
        "raw_response": raw_response,
        "parsed": result,
        "company": result.get("company") if result else None,
        "role": result.get("role") if result else None,
        "years_experience_required": (
            result.get("years_experience_required") if result else None
        ),
        "latency_seconds": round(elapsed_time, 3),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": round(cost, 8),
        "success": result is not None,
        "error": error,
    }


async def run_all(
    snippets: list[dict],
    client: AsyncOpenAI,
) -> list[dict]:
    tasks = [
        run_one(strategy, snippet, client)
        for snippet in snippets
        for strategy in STRATEGIES
    ]
    return await asyncio.gather(*tasks)


def normalise_text(value):
    """Normalise a string for case-insensitive, whitespace-trimmed comparison."""
    return value.strip().casefold() if isinstance(value, str) else None


def normalise_years(value):
    """Convert integer-like model output (including 5+) to an integer."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        return int(match.group()) if match else None
    return None


def score_accuracy(extracted: dict | None, gold: dict) -> int:
    """Compare all three fields and return 0-3 exact matches."""
    if not isinstance(extracted, dict):
        return 0

    score = 0
    for field in ("company", "role"):
        if normalise_text(extracted.get(field)) == normalise_text(gold.get(field)):
            score += 1

    extracted_years = normalise_years(extracted.get("years_experience_required"))
    gold_years = normalise_years(gold.get("years_experience_required"))
    if extracted_years == gold_years:
        score += 1
    return score


async def score_llm_judge(
    client: AsyncOpenAI,
    snippet_text: str,
    extracted: dict | None,
    gold: dict,
) -> int:
    """Use gpt-4o with a temperature of zero to judge extraction quality."""
    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an exact scoring judge for structured job-post extraction. "
                "Return only a JSON object like {\"score\": 4}. "
                "Score 4 only if all three fields are correct, 3 if exactly two are "
                "correct, 2 if exactly one is correct, and 1 if none are correct."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Job posting:\n{snippet_text}\n\n"
                f"Gold extraction:\n{json.dumps(gold, ensure_ascii=False)}\n\n"
                f"Model extraction:\n{json.dumps(extracted, ensure_ascii=False)}"
            ),
        },
    ]

    response = await client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=judge_messages,
        response_format={"type": "json_object"},
        temperature=TEMPERATURE,
    )
    judged = parse_response(response.choices[0].message.content or "")
    score = judged.get("score") if judged else None
    if isinstance(score, int) and 1 <= score <= 4:
        return score
    return max(1, score_accuracy(extracted, gold) + 1)


async def apply_scoring(
    results: list[dict],
    snippets: list[dict],
    golden: dict[str, dict],
    client: AsyncOpenAI,
) -> list[dict]:
    scored = []
    snippets_by_id = {snippet["id"]: snippet for snippet in snippets}
    for result in results:
        gold = golden[result["snippet_id"]]
        snippet = snippets_by_id[result["snippet_id"]]
        accuracy = score_accuracy(result["parsed"], gold)
        judge_score = await score_llm_judge(
            client, snippet["snippet"], result["parsed"], gold
        )
        row = dict(result)
        row["accuracy"] = accuracy
        row["parse_success"] = int(result["success"])
        row["llm_judge_score"] = judge_score
        scored.append(row)
    return scored


async def run_experiment(
    snippets: list[dict],
    golden: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY before running the API calls.")

    base_url = os.getenv("OPENAI_BASE_URL", "https://openai.vocareum.com/v1")
    async with AsyncOpenAI(api_key=api_key, base_url=base_url) as client:
        results = await run_all(snippets, client)
        scored = await apply_scoring(results, snippets, golden, client)
        return results, scored


def build_summary(scored: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(scored)
    summary = (
        df.groupby("strategy")
        .agg(
            {
                "accuracy": "mean",
                "parse_success": "mean",
                "llm_judge_score": "mean",
                "cost_usd": "sum",
                "latency_seconds": "median",
            }
        )
        .round(3)
    )
    summary.columns = [
        "Accuracy (mean of 3)",
        "Parse rate",
        "Judge score",
        "Total cost ($)",
        "Latency p50 (s)",
    ]
    return summary


def main() -> None:
    snippets, golden = load_data()
    print(f"Loaded {len(snippets)} snippets, {len(golden)} golden entries.")
    _, scored = asyncio.run(run_experiment(snippets, golden))
    print(f"Scored {len(scored)} results.")
    print("\nComparison summary:")
    print(build_summary(scored).to_string())


if __name__ == "__main__":
    main()
