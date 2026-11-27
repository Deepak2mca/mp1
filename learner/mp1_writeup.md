# MP1 Prompt Lab: Results and Reflection

## Experiment overview

The experiment compared four prompting strategies on 10 job-posting
snippets. Each strategy extracted `company`, `role`, and
`years_experience_required`, then was scored against the golden set.

| Strategy | Accuracy (mean of 3) | Parse rate | Judge score | Total cost ($) | Latency p50 (s) |
|---|---:|---:|---:|---:|---:|
| Chain-of-thought | 2.8 | 0.9 | 4.0 | 0.001 | 1.940 |
| Few-shot | 3.0 | 0.9 | 4.0 | 0.001 | 1.946 |
| Structured | 2.8 | 0.9 | 4.0 | 0.001 | 1.862 |
| Zero-shot | 2.9 | 0.9 | 4.0 | 0.000 | 1.917 |

## 1. Which strategy won, and on what dimension?

Few-shot prompting won on strict extraction accuracy, with a mean score
of 3.0 fields per snippet. It therefore won the accuracy dimension.
Structured prompting was the fastest, at 1.862 seconds median latency,
so it won the speed dimension. Chain-of-thought and structured prompting
tied for accuracy at 2.8, while zero-shot scored 2.9.

All strategies had a 0.9 parse rate and 4.0 judge score, so these metrics
did not distinguish them. Reported costs were $0.001 for three strategies
and $0.000 for zero-shot after rounding; zero-shot was not actually free.

There was no single winner across every dimension. Few-shot is the
accuracy winner, structured prompting is the latency winner, and
zero-shot appears cheapest only in the rounded cost display.

## 2. What surprised you?

The clearest surprise was that few-shot prompting was the only strategy
to reach 3.0 accuracy. I expected structured prompting or chain-of-thought
to be more accurate because they provide explicit instructions or
reasoning guidance.

I was also surprised that every strategy received a 4.0 judge score despite
accuracy ranging from 2.8 to 3.0. This suggests weak judge discrimination
or overly permissive judging. The consistent 0.9 parse rate shows that JSON
reliability remains a pipeline concern.

## 3. Which strategy would I use for my capstone?

For a capstone that prioritises reliable extraction, I would start with
few-shot prompting because it achieved the highest strict accuracy.
Representative examples clarify the expected output and help with
variations in company names, role titles, and experience wording.

I would combine examples with an explicit JSON schema and automated parser,
plus schema validation and bounded retries. Final selection should use
capstone-representative data and consider accuracy, reliability, cost, and
latency.

## 4. What would I try with another day?

First, I would inspect failed and partially correct extractions to identify
missing fields, ambiguous experience expressions, or malformed JSON.

Second, I would test a hybrid few-shot-plus-structured prompt and use
multiple judge runs with a stricter rubric. Keeping the temperature at
zero would improve repeatability, although it would not remove judge
variance entirely.

Finally, I would increase the test set and include edge cases such as
ranges, “not required,” and unspecified experience. This would provide a
fairer comparison and identify which strategy offers the best trade-off
between accuracy, reliability, latency, and cost.
