from pydantic import field_validator


def not_nullable(*fields: str):
    """PATCH helper: the fields may be omitted, but an explicit null is a 422.

    Optional columns (description, brand, ...) stay nullable so clients can
    clear them; required columns must never be set to None.
    Validators do not run for omitted fields, only for values actually sent.
    """
    def check(cls, value):
        if value is None:
            raise ValueError("field may be omitted but cannot be null")
        return value
    return field_validator(*fields, mode="before")(check)
