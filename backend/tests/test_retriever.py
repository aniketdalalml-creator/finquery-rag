"""Tests for FinancialRetriever query expansion."""

from app.rag.retriever import FinancialRetriever


def test_expand_query_adds_net_sales_for_revenue():
    expanded = FinancialRetriever._expand_query("What was total revenue?")
    assert "net sales" in expanded.lower()


def test_expand_query_unchanged_when_no_keywords():
    q = "Who is the CEO?"
    assert FinancialRetriever._expand_query(q) == q
