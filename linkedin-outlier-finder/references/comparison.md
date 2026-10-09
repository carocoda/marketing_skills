# Calculating an outlier from supplied history

Use this route only when the supplied dataset reasonably represents each author's recent posting, including ordinary results. A handpicked set of popular posts is not a representative baseline. Ask about coverage if it is unclear.

## Metric and sample

Use reactions as the default when available consistently. If the user requests reactions plus comments, use that consistently instead. Do not count likes and reactions twice when they describe the same total. Missing values are unknown, not zero. Public interaction counts are not impression-based engagement rates; comments may include the author's replies.

For each candidate:

1. Deduplicate by post ID or canonical URL. Resolve conflicting duplicates rather than counting both.
2. Exclude the candidate and all later posts from its comparison.
3. Select up to 20 earlier posts from that same author, within 90 days before the candidate. Exclude records without the chosen metric.
4. Calculate the median of those comparison values.
5. Divide the candidate's value by that median.

Report the candidate's absolute count, metric, comparison median, number of eligible posts, date window and multiple. If the baseline is zero, the ratio is undefined; report the counts without a multiple.

Sample guidance:

- At least 10 eligible prior posts: assessed comparison, subject to dataset coverage.
- 5–9: provisional comparison; show that label beside the result.
- Fewer than 5: insufficient data for a score.

These are practical research rules, not statistical significance thresholds. A tiny positive median can produce a large multiple, so keep absolute counts visible. Lifetime counts are not matched-age measurements: a new post and a month-old post have had different time to gather reactions. Mention material differences in age or format. If sufficient same-format history is available, a separate same-format comparison may help.

## Worked examples (fictional)

- An author has 10 prior posts with reactions `[4, 6, 5, 8, 6, 7, 6, 4, 8, 6]`. The median is 6. A new post with 54 reactions is 9× that baseline.
- Another author has 10 prior posts with reactions `[280, 310, 330, 350, 360, 326, 328, 328, 320, 340]`. The median is 328. A new post with 328 reactions is 1× its baseline.
- Three screenshots showing 4, 6 and 54 reactions are insufficient to score the last post. They do not establish representative prior history or the minimum sample.

Keep these calculations separate from a connector-provided score whose method is not exposed.
