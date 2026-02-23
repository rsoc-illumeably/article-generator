"""Agent loop orchestrator.

Drives the Writer → Judge iteration cycle:

    1. Writer produces an initial draft.
    2. Judge fact-checks the draft.
    3. If Judge passes  → return success response.
    4. If Judge flags issues → pass annotations back to Writer → goto 2.
    5. If max_iterations reached without a pass → return error response
       containing the iteration count and the full per-agent reasoning
       chain for every iteration.

The iteration cap is read from AppConfig (config/app.yml).
The verbose and dev_mode flags control how much detail is included
in the returned response.
"""

# TODO: implement
