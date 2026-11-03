# Latency Benchmark — DeepSeek vs OpenAI

**Date:** 2026-11-03
**Runs per scenario:** 3
**Scenarios:** catalog (1 tool), order (2 tools), and return (2 tools + policy).
**Mode:** Supabase, `STORE_TODAY=2026-02-20`, DeepSeek without thinking, `max_tokens=800`.

## Results by scenario

| Provider | Scenario | Median (s) | Mean (s) | Minimum (s) | Maximum (s) | Success |
|---|---|---:|---:|---:|---:|---:|
| deepseek | catalog | 10.709 | 11.306 | 10.66 | 12.548 | 3/3 |
| deepseek | order | 10.207 | 10.275 | 10.186 | 10.431 | 3/3 |
| deepseek | return | 12.757 | 13.826 | 12.278 | 16.444 | 3/3 |
| openai | catalog | 12.808 | 12.529 | 11.215 | 13.563 | 3/3 |
| openai | order | 11.679 | 11.628 | 10.817 | 12.388 | 3/3 |
| openai | return | 11.65 | 12.723 | 10.76 | 15.759 | 3/3 |

## Summary

| Provider | Median (s) | Mean (s) | Success |
|---|---:|---:|---:|
| deepseek | 10.709 | 11.802 | 9/9 |
| openai | 11.679 | 12.293 | 9/9 |

## Conclusion

The provider with the lowest median latency was **deepseek** (10.709 s), with 9/9 successful runs. The other provider should remain as the fallback.
