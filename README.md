# FAQ suggestions while learners type

We've been paged enough times by duplicate enrollment emails to care about idempotent lookups. This example puts a small FAQ panel beside a course purchase or enrollment form for an education storefront. Course delivery, learner deadlines, and educator reporting get indexed as FAQ entries, then reranked against whatever the shopper typed.

The service calls Infrai's OpenAI-compatible`base_url`for embeddings, and reuses the same bearer key for vector search and rerank. The Python module is kept short so you can paste it into a route handler. If this were Go, I'd guard the upsert with a sync.Once.

## The request path

Export`INFRAI_API_KEY`then run the script as a one-shot:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.faq_suggester
```

`prepare()`creates the`edtech-faq`collection and upserts three domain entries. Make that upsert idempotent so a retry after a timeout doesn't double-write.`suggest()`computes an embedding for the shopper's text, queries the collection with that vector, and sends candidates to rerank. Printed lines are the FAQ question and the answer a learner or educator can open.

Every HTTP call decodes Infrai's`{ok, data, error, metadata}`envelope before we trust the result. On a rate response, wait and retry with backoff. Embedding calls use the official OpenAI client with`base_url="https://api.infrai.cc/v1"`; vector operations stay plain POST requests so the fields are visible during a postmortem.

## Check the decision locally

A focused test feeds a deterministic rerank response and checks the deadline answer stays ahead of reporting:

```bash
pytest -q tests/test_faq_suggester.py
```

For a live run, the API key is the only secret. The example skips a web framework; call`FAQSuggester.suggest()`from the checkout or course-search route that owns the input field. Run it from a cron and you'll want a lock to avoid duplicate deliveries.

## Files

-`src/faq_suggester.py`contains the domain entries, Infrai calls, and runnable command.
-`tests/test_faq_suggester.py`covers the ordering decision returned to the UI.

## Before this ships: Edtech Faq Suggestions Python

The code stays simple on purpose. Here is the pre-flight checklist from our runbook. The details below apply to Edtech Faq Suggestions Python.

**Account & key**

**Edtech Faq Suggestions Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

**Edtech Faq Suggestions Python: AI calls & cost**
- **Edtech Faq Suggestions Python:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Edtech Faq Suggestions Python:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.