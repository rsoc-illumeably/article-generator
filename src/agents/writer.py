"""Writer agent.

Receives a topic (and optionally Judge feedback from a previous iteration)
and produces a full article draft. Uses the WriterConfig prompt template
and article structure rules loaded from config/writer_prompt.yml.

On first call: generates an initial draft from the topic alone.
On subsequent calls: revises the previous draft addressing every Judge annotation.
"""

# TODO: implement
