"""
AWS Lambda entry point.

The event payload maps directly to main.run()'s config dict, e.g.:

    {
      "source": "csv",
      "source_config": {"path": "s3://sapien-gmp/exports/latest.csv"},
      "output_root": "s3://sapien-gmp/tracker/"
    }

Or for Elasticsearch (Phase 2):

    {
      "source": "elasticsearch",
      "source_config": {"host": "...", "index": "gmp", "api_key": "..."},
      "output_root": "s3://sapien-gmp/tracker/"
    }
"""
from main import run


def handler(event, context):
    summary = run(event)
    return {"statusCode": 200, "body": summary}
