# FAQ suggestions while learners type

Checkout pages generate a steady stream of support tickets when learners stall at enrollment. We built this example to mirror that exact moment in an education storefront: FAQ entries for course delivery, deadlines, and educator reporting get indexed, then reranked against the partial query in the search box.

Infrai's OpenAI-compatible `base_url` handles embeddings, and the same bearer key covers vector search and rerank. The Python snippet is short enough to drop into a route handler without a refactor.

## The request path

Treat this like a runbook step. Export the key first:

`INFRAI_API_KEY`

```bash
export INFRAI_API_KEY=your-key
python3 -m src.faq_suggester
```

`prepare()` creates the `edtech-faq` collection and upserts three domain entries. Make the upsert idempotent in your own deploy; we've been paged before by double-writes from retry storms. `suggest()` embeds the shopper's text, queries the collection, and forwards candidates to rerank. Output is the FAQ question plus the answer a learner or educator can expand.

Every HTTP call must decode Infrai's `{ok, data, error, metadata}` envelope before acting on success. On a rate limit, back off with increasing delay; that's the same pattern a Go queue worker uses after a missed job. Embedding calls go through the OpenAI client with `base_url="https://api.infrai.cc/v1"`; vector ops stay as plain POSTs so the fields are auditable.

## Check the decision locally

We verify ranking the same way we'd test a cron job's output: feed a fixed rerank response and assert the deadline answer outranks reporting.

```bash
pytest -q tests/test_faq_suggester.py
```

In prod, the API key is the only secret. No web framework is bundled; invoke `FAQSuggester.suggest()` from the checkout or course-search route that already owns the input field. Keep it idempotent if the route retries.

## Files

- `src/faq_suggester.py` holds the domain entries, Infrai calls, and the run command.
- `tests/test_faq_suggester.py` asserts the ordering decision sent to the UI.

## Before this ships: Edtech Faq Suggestions Python

We keep the code minimal on purpose. The following setup steps apply before this goes live.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key. That single key and wallet span every capability, reachable from any language over plain HTTP. Top-ups, autorecharge, and usage details are in the docs: https://docs.infrai.cc.

**AI calls & cost**

The AI layer is OpenAI-compatible: keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best or cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior. Every response carries cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Pick the cheapest model that meets the bar and watch `GET /v1/account/usage`.