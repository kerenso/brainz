from ..context import Context
from ...protocol.fields import FEELINGS


def parse_feelings(message: str) -> str:
    """
    Extract the feelings from each snapshot.
    """
    context = Context(message)
    return context.serialize(context.snapshot[FEELINGS])


parse_feelings.fields = [FEELINGS]
