"""Tests for password_policy.validate_password_strength.

This is the easiest possible place to start: a pure function, no database,
no TestClient, no fixtures beyond what pytest gives you for free. It either
returns None or raises ValueError.

Cases to write (see the plan for details):
- A password shorter than 12 characters raises ValueError.
- A password missing an uppercase letter raises ValueError.
- A password missing a lowercase letter raises ValueError.
- A password missing a digit raises ValueError.
- A password missing a special character raises ValueError.
- A password meeting every rule does not raise.

Tip: `pytest.raises(ValueError)` is how you assert a call raises. Example:

    import pytest
    from password_policy import validate_password_strength

    def test_short_password_rejected():
        with pytest.raises(ValueError):
            validate_password_strength("Ab1!")
"""
