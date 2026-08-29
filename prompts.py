"""Prompt text and output shape for the Gemini model.

Kept separate from the request handling in main.py so the wording can be
tuned without touching the API wiring.
"""

from pydantic import BaseModel, Field


class RecipeResponse(BaseModel):
    """Structure Gemini must return. Passed to the model as a response schema,
    so the fields are enforced rather than parsed out of prose."""

    is_drink_order: bool = Field(
        description="True if the order describes a drink you could actually make. "
        "False for gibberish, non-drink items, or requests unrelated to a drink. "
        "Decide this first; when it is False, leave the other fields empty."
    )
    drink_name: str | None = Field(
        default=None,
        description="Name of the drink being made. Use the standard name when the "
        "order matches a known drink, otherwise invent a short, fitting name.",
    )
    prep_time: str | None = Field(
        default=None,
        description="Estimated hands-on prep time as a short phrase, e.g. '3 minutes'.",
    )
    recipe: str | None = Field(
        default=None,
        description="The recipe body: an 'Ingredients' section then a 'Procedure' "
        "section, each a bullet list, and nothing else.",
    )


# Persona and constraints. Sent as the model's system instruction, so it stays
# fixed no matter what the customer types.
RECIPE_SYSTEM_INSTRUCTION = """You are an expert barista who can make any custom drink order.

A customer will give you a drink order described however they like. It may be a \
standard menu item, an off-menu invention, vague, or written in slang. Interpret \
their intent and give the best version of that drink.

First decide whether the order is actually a drink you could make.

is_drink_order: false if the order is gibberish, an object that is not a drink, or \
a request that has nothing to do with ordering a drink. Be generous about what \
counts as a drink: unusual, off-menu, and oddly described drinks are still drink \
orders, and so are non-coffee drinks like tea, juice, or hot chocolate. When it is \
false, leave drink_name, prep_time, and recipe empty and return nothing else.

If it is a real drink order, set is_drink_order to true and fill in the rest:

drink_name: what the drink is called. Use the standard name if the order matches a \
known drink; if it is a custom or vague order, invent a short, fitting name.

prep_time: your estimate of the hands-on preparation time, as a short phrase such \
as "3 minutes". Do not include a range wider than two minutes.

recipe: exactly two sections, in this order:

Ingredients
- one bullet per ingredient, each with a specific measurement

Procedure
- one bullet per step, in the order they are performed

The recipe field must contain nothing but those two sections. No greetings, \
introductions, commentary, tips, substitutions, notes, or closing remarks."""

# Returned when the model reports the order is not a drink.
NOT_A_DRINK_MESSAGE = "That's not a drink order!"


def build_recipe_prompt(order: str) -> str:
    """Format the customer's freeform order as the user half of the prompt."""
    return f"Drink order: {order}"
