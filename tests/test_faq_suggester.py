from src.faq_suggester import FAQSuggester, FAQS


def test_rerank_results_keep_the_business_order():
    ranked = {"results": [{"id": "deadline-change"}, {"id": "educator-report"}]}
    assert [item.id for item in FAQSuggester._entries_from_rerank(ranked)] == ["deadline-change", "educator-report"]
    assert FAQS[0].answer.startswith("Educators")
