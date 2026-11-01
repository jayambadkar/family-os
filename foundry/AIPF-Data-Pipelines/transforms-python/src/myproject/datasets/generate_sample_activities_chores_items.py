# Builds the [AIPF] Activity, Chore and Purchase object type backing datasets.

import uuid

import polars as pl
from language_model_service_api.languagemodelservice_api_completion_v3 import (
    ClaudeChatCompletionRequest,
    ClaudeChatMessage,
    ClaudeChatMessageContent,
    ClaudeChatMessageRole,
    ClaudeChatTextContent,
    ClaudeJsonSchemaOutputFormat,
    ClaudeOutputConfig,
    ClaudeOutputFormat,
)
from palantir_models.models import AnthropicClaudeLanguageModel
from palantir_models.transforms import AnthropicClaudeLanguageModelInput
from transforms.api import Input, LightweightInput, LightweightOutput, Output, transform

from myproject.constants import (
    ACTIVITY_PROMPT,
    ACTIVITY_SYSTEM_PROMPT,
    CLAUDE_MAX_TOKENS,
    CLAUDE_MODEL,
    MAX_RATE_LIMIT_RETRIES,
    PURCHASE_SYSTEM_PROMPT,
)
from myproject.schemas import (
    ACTIVITY_COLUMNS,
    ACTIVITY_DTYPE,
    ACTIVITY_JSON_SCHEMA,
    CHORE_COLUMNS,
    PURCHASE_COLUMNS,
    PURCHASE_DTYPE,
    PURCHASE_JSON_SCHEMA,
)

CHORES = "ri.foundry.main.dataset.3caa7723-771a-4209-a405-02187e85c60a"
START_NUMBERS_1_5 = "ri.foundry.main.dataset.1c34345b-d45d-4974-9beb-fd98b4fec894"

ACTIVITY_BACKING_DATASET = "ri.foundry.main.dataset.e0c3bdb4-8b33-4a49-8980-75ea89854b08"
CHORE_BACKING_DATASET = "ri.foundry.main.dataset.52534195-6268-4f9f-bf75-dcb1aaef1b31"
PURCHASE_BACKING_DATASET = "ri.foundry.main.dataset.f279f12c-3cac-46af-9f29-3c1dad345145"


def ask_claude(model: AnthropicClaudeLanguageModel, system_prompt: str, prompt: str, json_schema: dict) -> str:
    """Send one prompt to Claude and return its reply, a JSON document matching `json_schema`."""
    request = ClaudeChatCompletionRequest(
        messages=[
            ClaudeChatMessage(
                role=ClaudeChatMessageRole.USER,
                content=[ClaudeChatMessageContent(text=ClaudeChatTextContent(text=prompt))],
            )
        ],
        system=system_prompt,
        max_tokens=CLAUDE_MAX_TOKENS,
        output_config=ClaudeOutputConfig(
            format=ClaudeOutputFormat(json_schema=ClaudeJsonSchemaOutputFormat(schema=json_schema))
        ),
    )
    response = model.create_chat_completion(request, max_rate_limit_retries=MAX_RATE_LIMIT_RETRIES)
    return next(block.text.text for block in response.content if block.text is not None)


@transform.using(
    output=Output(ACTIVITY_BACKING_DATASET),
    start_numbers=Input(START_NUMBERS_1_5),
    model=AnthropicClaudeLanguageModelInput(CLAUDE_MODEL),
)
def activity_backing_dataset(
    start_numbers: LightweightInput, model: AnthropicClaudeLanguageModel, output: LightweightOutput
) -> None:
    output.write_table(
        start_numbers.polars(lazy=True)
        .with_columns(
            generated_activity=pl.format(ACTIVITY_PROMPT, "id")
            .map_elements(
                lambda prompt: ask_claude(model, ACTIVITY_SYSTEM_PROMPT, prompt, ACTIVITY_JSON_SCHEMA),
                return_dtype=pl.String,
            )
            .str.json_decode(ACTIVITY_DTYPE)
        )
        .with_columns(pl.col("generated_activity").name.prefix_fields("activity_").struct.unnest())
        .drop("generated_activity")
        .rename({"id": "activity_id"})
        .select(ACTIVITY_COLUMNS)
    )


@transform.using(
    output=Output(CHORE_BACKING_DATASET),
    chores=Input(CHORES),
)
def chore_backing_dataset(chores: LightweightInput, output: LightweightOutput) -> None:
    output.write_table(
        chores.polars(lazy=True)
        .with_columns(
            intensity=pl.when(pl.col("intensity").is_in(["low", "medium", "high"]).not_())
            .then(pl.lit("medium"))
            .otherwise(pl.col("intensity")),
            status=pl.lit("incomplete"),
        )
        .select(CHORE_COLUMNS)
    )


@transform.using(
    output=Output(PURCHASE_BACKING_DATASET),
    start_numbers=Input(START_NUMBERS_1_5),
    model=AnthropicClaudeLanguageModelInput(CLAUDE_MODEL),
)
def purchase_backing_dataset(
    start_numbers: LightweightInput, model: AnthropicClaudeLanguageModel, output: LightweightOutput
) -> None:
    output.write_table(
        start_numbers.polars(lazy=True)
        .with_columns(
            purchase=pl.col("id")
            .cast(pl.String)
            .map_elements(
                lambda prompt: ask_claude(model, PURCHASE_SYSTEM_PROMPT, prompt, PURCHASE_JSON_SCHEMA),
                return_dtype=pl.String,
            )
            .str.json_decode(PURCHASE_DTYPE)
        )
        .with_columns(
            pl.col("purchase").name.prefix_fields("item_").struct.unnest(),
            item_id=pl.col("id").map_elements(lambda _: str(uuid.uuid4()), return_dtype=pl.String),
            status=pl.lit("approved"),
        )
        .select(PURCHASE_COLUMNS)
    )
