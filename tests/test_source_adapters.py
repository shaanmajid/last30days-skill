import unittest
from unittest.mock import patch

from lib import pipeline, schema, source_adapters


class SourceRegistryTests(unittest.TestCase):
    def test_registry_exposes_initial_always_available_sources_in_pipeline_order(self):
        self.assertEqual(
            ["hackernews", "polymarket", "github"],
            source_adapters.SOURCE_REGISTRY.always_available_names(),
        )
        sources = pipeline.available_sources({"LAST30DAYS_NATIVE_SEARCH": "1"})
        self.assertIn("hackernews", sources)
        self.assertIn("polymarket", sources)
        self.assertIn("github", sources)

    def test_pipeline_dispatches_registered_sources_through_adapter(self):
        captured: list[source_adapters.SourceRequest] = []

        def fake_fetch(request: source_adapters.SourceRequest):
            captured.append(request)
            return ([{"id": "adapter-item"}], {"artifact": "adapter"})

        registry = source_adapters.SourceRegistry([
            source_adapters.SourceAdapter("adapter-source", fake_fetch, always_available=True),
        ])
        subquery = schema.SubQuery(
            label="primary",
            search_query="test query",
            ranking_query="What happened with test query?",
            sources=["adapter-source"],
        )

        with patch.object(source_adapters, "SOURCE_REGISTRY", registry):
            items, artifact = pipeline._retrieve_stream(
                topic="test topic",
                subquery=subquery,
                source="adapter-source",
                config={"GITHUB_TOKEN": "token"},
                depth="quick",
                date_range=("2026-05-01", "2026-05-31"),
                runtime=None,
                mock=False,
            )

        self.assertEqual([{"id": "adapter-item"}], items)
        self.assertEqual({"artifact": "adapter"}, artifact)
        self.assertEqual(1, len(captured))
        self.assertIs(subquery, captured[0].subquery)
        self.assertEqual(("2026-05-01", "2026-05-31"), captured[0].date_range)
        self.assertEqual({"GITHUB_TOKEN": "token"}, captured[0].config)
        self.assertEqual("quick", captured[0].depth)


if __name__ == "__main__":
    unittest.main()
