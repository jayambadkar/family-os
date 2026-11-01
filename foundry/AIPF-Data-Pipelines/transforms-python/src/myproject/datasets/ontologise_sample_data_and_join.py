# Builds the [AIPF] Family Member, Member Fact and Member Relation object type backing datasets.

from datetime import datetime, timezone

import polars as pl
from language_model_service_api.languagemodelservice_api import ChatMessage, ChatMessageRole
from language_model_service_api.languagemodelservice_api_completion_v3 import (
    GptChatCompletionRequest,
    GptResponseFormat,
    GptResponseFormatType,
)
from palantir_models.models import OpenAiGptChatLanguageModel
from palantir_models.transforms import OpenAiGptChatLanguageModelInput
from transforms.api import (
    Input,
    LightweightInput,
    LightweightOutput,
    Output,
    TransformContext,
    TransformInput,
    TransformOutput,
    transform,
)

from myproject.constants import (
    CORRECT_TYPING_ERRORS_PROMPT,
    CORRECT_TYPING_ERRORS_SYSTEM_PROMPT,
    GPT_MODEL,
    GPT_TEMPERATURE,
    MAX_RATE_LIMIT_RETRIES,
    SCORE_AFFECTION_SYSTEM_PROMPT,
    SUMMARISE_ACTIVITIES_PROMPT,
    SUMMARISE_ACTIVITIES_SYSTEM_PROMPT,
    SUMMARISE_FOODS_PROMPT,
    SUMMARISE_FOODS_SYSTEM_PROMPT,
)
from myproject.schemas import (
    AFFECTION_DTYPE,
    AFFECTION_JSON_SCHEMA,
    CORRECTIONS_DTYPE,
    CORRECTIONS_JSON_SCHEMA,
    FAMILY_MEMBER_SCHEMA,
    FOODS_DTYPE,
    FOODS_JSON_SCHEMA,
    MEMBER_FACT_COLUMNS,
    MEMBER_RELATION_COLUMNS,
)

BASE_SAMPLE_FAMILY_DATA = "ri.foundry.main.dataset.df4068e4-74ea-436b-8dc6-a46f5a63e68a"
SAMPLE_FAMILY_FACTS = "ri.foundry.main.dataset.8fc30db7-fb91-4177-87f6-d56e4dc1a3c6"
SAMPLE_FAMILY_RELATIONS = "ri.foundry.main.dataset.5f418a13-1d80-415b-b98c-80fb112aecc3"

FAMILY_MEMBER_BACKING_DATASET = "ri.foundry.main.dataset.b475ea86-b597-40ab-ada4-8523a7ef80d3"
MEMBER_FACT_BACKING_DATASET = "ri.foundry.main.dataset.b4ce9b06-4004-4729-b0e0-cc04aef305c9"
MEMBER_RELATION_BACKING_DATASET = "ri.foundry.main.dataset.519443c3-422a-40ec-8df7-d5ef5016dd15"


def ask_gpt(model: OpenAiGptChatLanguageModel, system_prompt: str, prompt: str, json_schema: dict | None = None) -> str:
    """Send one prompt to GPT and return its reply, a JSON document matching `json_schema` if one is given."""
    response_format = None
    if json_schema is not None:
        response_format = GptResponseFormat(
            type=GptResponseFormatType.JSON_SCHEMA,
            json_schema={"name": "response", "strict": True, "schema": json_schema},
        )
    request = GptChatCompletionRequest(
        messages=[
            ChatMessage(role=ChatMessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=ChatMessageRole.USER, content=prompt),
        ],
        temperature=GPT_TEMPERATURE,
        response_format=response_format,
    )
    response = model.create_chat_completion(request, max_rate_limit_retries=MAX_RATE_LIMIT_RETRIES)
    return response.choices[0].message.content


@transform.spark.using(
    output=Output(FAMILY_MEMBER_BACKING_DATASET),
    family=Input(BASE_SAMPLE_FAMILY_DATA),
    model=OpenAiGptChatLanguageModelInput(GPT_MODEL),
)
def family_member_backing_dataset(
    ctx: TransformContext, family: TransformInput, model: OpenAiGptChatLanguageModel, output: TransformOutput
) -> None:
    today = datetime.now(timezone.utc).date()
    date_of_birth = pl.col("date_of_birth").dt
    # Dates as YYYYMMDD numbers: the difference divided by 10,000 is the age in whole years.
    today_number = pl.lit(today.year * 10_000 + today.month * 100 + today.day, dtype=pl.Int64)
    date_of_birth_number = (date_of_birth.year() * 100 + date_of_birth.month()) * 100 + date_of_birth.day()

    df = (
        # Spark reads the input's non-UTF-8 text, which Polars rejects.
        pl.from_pandas(family.pandas())
        .lazy()
        .with_columns(
            corrections=pl.format(CORRECT_TYPING_ERRORS_PROMPT, "favourite_food", "favourite_activities")
            .map_elements(
                lambda prompt: ask_gpt(model, CORRECT_TYPING_ERRORS_SYSTEM_PROMPT, prompt, CORRECTIONS_JSON_SCHEMA),
                return_dtype=pl.String,
            )
            .str.json_decode(CORRECTIONS_DTYPE)
        )
        .with_columns(
            favourite_food=pl.col("corrections").struct.field("corrected_favourite_food"),
            favourite_activities=pl.col("corrections").struct.field("corrected_favourite_activities"),
            age=(today_number - date_of_birth_number) // 10_000,
        )
        .with_columns(
            favourite_food=pl.format(SUMMARISE_FOODS_PROMPT, "favourite_food")
            .map_elements(
                lambda prompt: ask_gpt(model, SUMMARISE_FOODS_SYSTEM_PROMPT, prompt, FOODS_JSON_SCHEMA),
                return_dtype=pl.String,
            )
            .str.json_decode(FOODS_DTYPE)
            .struct.field("favourite_food"),
            favourite_activities=pl.format(SUMMARISE_ACTIVITIES_PROMPT, "favourite_activities")
            .map_elements(
                lambda prompt: ask_gpt(model, SUMMARISE_ACTIVITIES_SYSTEM_PROMPT, prompt),
                return_dtype=pl.String,
            ),
        )
        .rename({"id": "person_id", "email": "email_address", "favourite_food": "favourite_foods"})
        .select(FAMILY_MEMBER_SCHEMA.fieldNames())
        .collect()
    )
    output.write_dataframe(ctx.spark_session.createDataFrame(df.rows(), FAMILY_MEMBER_SCHEMA))


@transform.using(
    output=Output(MEMBER_FACT_BACKING_DATASET),
    facts=Input(SAMPLE_FAMILY_FACTS),
)
def member_fact_backing_dataset(facts: LightweightInput, output: LightweightOutput) -> None:
    output.write_table(facts.polars(lazy=True).rename({"id": "fact_id"}).select(MEMBER_FACT_COLUMNS))


@transform.using(
    output=Output(MEMBER_RELATION_BACKING_DATASET),
    relations=Input(SAMPLE_FAMILY_RELATIONS),
    model=OpenAiGptChatLanguageModelInput(GPT_MODEL),
)
def member_relation_backing_dataset(
    relations: LightweightInput, model: OpenAiGptChatLanguageModel, output: LightweightOutput
) -> None:
    output.write_table(
        relations.polars(lazy=True)
        .with_columns(
            affection=pl.col("affection")
            .map_elements(
                lambda prompt: ask_gpt(model, SCORE_AFFECTION_SYSTEM_PROMPT, prompt, AFFECTION_JSON_SCHEMA),
                return_dtype=pl.String,
            )
            .str.json_decode(AFFECTION_DTYPE)
            .struct.field("affection")
        )
        .rename({"id": "relation_id"})
        .select(MEMBER_RELATION_COLUMNS)
    )
