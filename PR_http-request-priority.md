Forward HTTP request priority to the Engine scheduler

## Summary

The Engine already admits waiting work by signed `priority`, but the HTTP frontend always submitted `0`. Chat Completions, Responses, and Messages now accept `priority` and pass it through to `Engine.submit`.

Omitted values default to `0`, matching Engine submission. Negative values remain valid. Out-of-range or non-integer values are rejected. The field is a scheduler control and is not forwarded as a recipe extra.

## Test plan

- [ ] `cargo test -p resin-http --all-targets`
- [ ] `uv run pytest -q tests/test_http_priority.py tests/test_http_session.py tests/test_http_lifecycle.py tests/test_scheduler.py`
- [ ] `cargo clippy --locked --workspace --all-targets -- -D warnings`
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run ty check`
