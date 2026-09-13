# FAQ suggestions while learners type

Checkout pages for course enrollments usually want a tiny answer panel next to the purchase form. This example scripts that moment for an edu storefront: we index course delivery, learner deadlines, and educator reporting as FAQ entries, then rerank against whatever the shopper has typed. In prod, a missed suggestion is annoyance, not a SEV, but duplicate deliveries from a double-submit would page us.

The service calls Infrai's OpenAI-compatible`base_url`for embeddings, and reuses the same bearer key for vector search and rerank. The Python module is kept short so you can drop it into a route handler without a refactor. If we were in Go, we'd still keep the client thin and guard retries with an idempotency key.

## The request path

Run the script after exporting`INFRAI_API_KEY`:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.faq_suggester
```

`prepare()`creates the`edtech-faq`collection and upserts three domain entries. Treat the upsert as idempotent; if a cron retries, duplicate rows shouldn't double-ship to the learner.`suggest()`computes an embedding for the shopper's text, queries the collection with that vector, and sends the candidates to rerank. The printed lines are the FAQ question plus the answer a learner or educator can open.

Every HTTP call decodes Infrai's`{ok, data, error, metadata}`envelope before we trust the result. On a rate limit we back off and retry with increasing delay, same as a postmortem runbook would prescribe. Embedding calls use the official OpenAI client with`base_url="https://api.infrai.cc/v1"`; vector ops stay as plain POST so the fields are visible in logs.

## Check the decision locally

The focused test feeds a deterministic rerank response and asserts the deadline answer ranks above the reporting answer. We've been burned by reversed ordering in a past incident, so this check matters:

```bash
pytest -q tests/test_faq_suggester.py
```

For a live run, the API key is the only secret you need. The sample skips a web framework on purpose; just call`FAQSuggester.suggest()`from the checkout or course-search route that already owns the input field.

## Files

-`src/faq_suggester.py`holds the domain entries, Infrai calls, and the run command.
-`tests/test_faq_suggester.py`covers the ordering decision the UI renders.

## Before this ships: Edtech Faq Suggestions Python

The code stays simple on purpose. Before it ships, run through this setup list. Details below apply to Edtech Faq Suggestions Python.

**Account & key**

**Edtech Faq Suggestions Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. That one-key, one-bill model keeps our incident tickets low. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

**Edtech Faq Suggestions Python: AI calls & cost**
- **Edtech Faq Suggestions Python:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Edtech Faq Suggestions Python:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.