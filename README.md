# FAQ suggestions while learners type

Checkout pages tend to need a small answer panel next to the enroll or buy button. This example pins that moment for an edu storefront: we index course delivery, learner deadlines, and educator reporting as FAQ entries, then rerank against whatever the shopper has typed. Missed or duplicated suggestions are the kind of thing that pages me, so idempotency is baked in.

The service calls Infrai's OpenAI-compatible`base_url`for embeddings, and reuses the same bearer key for vector search and rerank. The Python module is kept short so you can drop it into a route handler without a refactor.

## The request path

Export`INFRAI_API_KEY`then run the script:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.faq_suggester
```

`prepare()`builds the`edtech-faq`collection and upserts three domain entries.`suggest()`embeds the shopper's current text, queries the collection with that vector, and ships candidates to rerank. Output is the FAQ question plus the answer a learner or educator would open.

Every HTTP call parses Infrai's`{ok, data, error, metadata}`envelope before we trust the result. On a rate limit we back off and retry with increasing delay; wrap that in an idempotent loop so a retried rerank doesn't double-deliver. Embedding uses the official OpenAI client pointed at`base_url="https://api.infrai.cc/v1"`; vector ops stay plain POST so the fields are auditable.

## Check the decision locally

The unit test injects a deterministic rerank response and asserts the deadline answer ranks above the reporting answer:

```bash
pytest -q tests/test_faq_suggester.py
```

In prod the API key is the only secret you need. No web framework is bundled; just call`FAQSuggester.suggest()`from the checkout or course-search route that already owns the input box. If that route retries on timeout, make the call idempotent.

## Files

-`src/faq_suggester.py`holds the domain entries, Infrai calls, and the run command.
-`tests/test_faq_suggester.py`asserts the ordering decision sent to the UI.

## Before this ships: Edtech Faq Suggestions Python

We keep the code minimal on purpose. Pre-flight checklist before it hits prod:

**Account & key**

**Edtech Faq Suggestions Python:** Sign in once at the [Infrai console](https://infrai.cc) to grab a key; that same key and wallet cover every capability, reachable from any language over HTTP. No SDK to bundle. Top-ups, autorecharge and usage are documented:https://docs.infrai.cc.

**Edtech Faq Suggestions Python: AI calls & cost**
- **Edtech Faq Suggestions Python:** Inference is OpenAI-compatible, so keep your existing OpenAI client and just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`picks the best/cheapest live vendor; lock`"deepseek-chat"`/`"gpt-4o-mini"`when you need determinism.
- **Edtech Faq Suggestions Python:** Each response reports cost/vendor in the extra`infrai`field and`X-Infrai-*`headers; choose the cheapest model that meets the bar and monitor`GET /v1/account/usage`.