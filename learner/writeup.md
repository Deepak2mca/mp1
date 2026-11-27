1. Which strategy won, and on what dimension?
Few-shot prompting was the winner in terms of accuracy.
- Accuracy: Few-shot achieved 3.0 out of 3, the highest score, meaning it performed best against the golden dataset.
- Parse rate: All four strategies achieved 0.9 (90%), so there was no winner in parsing reliability.
- Judge score: All strategies received 4.0, so the LLM judge did not distinguish between them.
- Cost: Zero-shot had the lowest displayed cost ($0.000), although this is rounded and does not mean the actual cost was zero.
- Latency: Structured prompting was the fastest, with a median latency of 1.862 seconds.
Overall, few-shot was the best choice for extraction accuracy, while structured prompting performed best for speed.
2. What surprised you?
I was surprised that few-shot prompting achieved the highest accuracy (3.0), outperforming both structured prompting and chain-of-thought prompting.

I initially expected structured prompting and chain-of-thought to perform better because they provide more explicit instructions and reasoning guidance. Another interesting observation was that all four strategies received the same LLM judge score of 4.0, even though their accuracy scores differed. This suggests that the judge score may not have been sufficiently discriminative in this experiment.

Additionally, all strategies had a 90% parse rate, indicating that there is still room to improve response reliability.
3. For your capstone domain, which strategy would you reach for first?
I would start with few-shot prompting for my capstone project.

Providing real-world examples helps the LLM understand the expected output format and handle variations in input data more consistently. Since few-shot achieved the highest accuracy in this experiment, I would use it as my baseline strategy and then evaluate structured prompting for scenarios where strict JSON output and predictable extraction are important.
4. If you had another day, what would you try next?
If I had another day, I would focus on the following improvements:
1. Experiment with different models: Compare GPT-4o, GPT-4o-mini, and other models to evaluate accuracy, latency, and cost.
2. Increase the dataset: Test with more job postings covering different industries, job titles, experience ranges, and ambiguous descriptions.
3. Improve prompt engineering: Combine few-shot examples with structured output instructions and test whether this improves accuracy.
4. Investigate failed cases: Identify the 10% of responses that failed parsing and understand why they failed.
5. Improve evaluation: Review the LLM judge because all four strategies received the same score despite differences in accuracy.