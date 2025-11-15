# LLM Configuration for Borg Tools Scanner

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

## Current Configuration (Updated: November 14, 2025)

### Default Model: DeepSeek-R1 (Free Tier)

**Model ID:** `deepseek/deepseek-r1:free`
**Provider:** OpenRouter (free tier)
**Cost:** $0 per request

### Why DeepSeek-R1?

- **Performance:** 96.2% on HumanEval benchmark (beats OpenAI o1 on Codeforces)
- **Cost:** Completely free via OpenRouter free tier
- **Context:** 163K tokens (~120K words) - handles large codebases
- **Quality:** Top-tier reasoning for code analysis, architecture review, technical debt detection
- **Availability:** No rate limits with $10 OpenRouter credit purchase (1000 req/day)

## Usage

### Via run.sh (Recommended)
```bash
./run.sh  # Uses DeepSeek-R1 by default
```

### Direct Command
```bash
python3 borg_tools_scan.py --root ~/Projects --use-llm openrouter --model deepseek/deepseek-r1:free
```

### Custom Model Override
```bash
# Use different model
python3 borg_tools_scan.py --root ~/Projects --use-llm openrouter --model anthropic/claude-sonnet-4.5

# Use OpenAI
python3 borg_tools_scan.py --root ~/Projects --use-llm openai --model gpt-4o
```

## Alternative Models

### Free Options
- **deepseek/deepseek-r1:free** - Current default, best free quality
- **meta-llama/llama-4-maverick:free** - 400B MoE, 256K context
- **meta-llama/llama-4-scout:free** - 109B MoE, 512K context

### Paid Options (If Budget Available)
- **google/gemini-2.5-pro** - $5.63 per 1M tokens (best value, 1M+ context)
- **anthropic/claude-sonnet-4.5** - $9 per 1M tokens (best JSON output)
- **openai/gpt-4o** - $12.50 per 1M tokens (reliable, proven)

## Environment Setup

### Required API Key
```bash
export OPENROUTER_API_KEY="your_key_here"
```

### Optional: Increase Free Tier Limits
1. Purchase $10 credit on OpenRouter.ai
2. Unlocks 1000 free requests/day (vs 50/day default)
3. Credit never expires, only used for paid models

## Cost Comparison

| Scenario | DeepSeek-R1 | Gemini 2.5 Pro | Claude Sonnet 4.5 |
|----------|-------------|----------------|-------------------|
| 100 projects (5M tokens) | $0 | $6-50 | $15-75 |
| 1000 projects/year | $0 | $63-500 | $150-750 |
| Dashboard chat (1M tokens/mo) | $0 | $5.63 | $9 |

## Integration Points

### 1. Scanner (borg_tools_scan.py)
- **Line 1016:** Default model argument
- **Line 591:** OpenRouter fallback model
- **Line 538:** OpenAI fallback model

### 2. Web Dashboard (web_ui.py)
- Uses `OPENROUTER_API_KEY` environment variable
- Same model as scanner for consistency

### 3. Deployment (cube.borg.tools)
- Dashboard service configured with OPENROUTER_API_KEY
- LLM chat feature fully operational

## Testing

### Quick Test (5 Projects)
```bash
# Test with small sample
python3 borg_tools_scan.py --root ~/Projects --use-llm openrouter --limit 5
```

### Verify JSON Parsing
```bash
# Check borg_dashboard.json for LLM-enhanced fields:
jq '.[] | {name, description, monetization_potential}' borg_dashboard.json
```

### Test Dashboard Chat
1. Visit https://cube.borg.tools
2. Click any project
3. Use chat interface
4. Verify DeepSeek responses

## Troubleshooting

### Issue: Rate Limit Exceeded
**Solution:** Purchase $10 OpenRouter credits (unlocks 1000/day free tier)

### Issue: JSON Parsing Errors
**Symptom:** Missing LLM-enhanced fields in dashboard
**Solution:** DeepSeek-R1 may need careful prompting for JSON. Check logs for parsing errors.
**Fallback:** Switch to `anthropic/claude-sonnet-4.5` for critical JSON needs

### Issue: Slow Response Times
**Symptom:** DeepSeek-R1 taking 30+ seconds per request
**Cause:** Reasoning chains (intentional)
**Solution:** Use `:nitro` variant for faster routing: `deepseek/deepseek-r1:nitro`

### Issue: No API Key
**Symptom:** LLM features disabled
**Solution:** Set `export OPENROUTER_API_KEY="..."` in environment

## Monitoring

### Track Usage
```bash
# Check OpenRouter dashboard
https://openrouter.ai/dashboard

# View request counts, costs, model distribution
```

### Performance Metrics
- **Average latency:** 5-15 seconds (DeepSeek-R1 with reasoning)
- **Success rate:** Monitor JSON parsing success in logs
- **Quality:** Compare LLM suggestions vs heuristic baseline

## Future Enhancements

### Planned
- [ ] Add DeepSeek direct API support (completely free, no OpenRouter dependency)
- [ ] Implement retry logic with exponential backoff
- [ ] Add cost tracking per project
- [ ] Smart model selection (size-based routing)
- [ ] Local Ollama support for privacy-critical projects

### Considered
- [ ] Multi-model ensemble (consensus-based suggestions)
- [ ] Streaming responses for real-time dashboard
- [ ] Caching LLM results (only re-analyze on file changes)
- [ ] Batch processing for cost optimization

## References

- **DeepSeek-R1 Benchmarks:** https://github.com/deepseek-ai/DeepSeek-R1
- **OpenRouter Pricing:** https://openrouter.ai/models
- **Model Comparison:** See [LLM_RESEARCH.md](LLM_RESEARCH.md) (if created)

---

Last Updated: November 14, 2025
Configuration Version: 1.0
Default Model: deepseek/deepseek-r1:free
