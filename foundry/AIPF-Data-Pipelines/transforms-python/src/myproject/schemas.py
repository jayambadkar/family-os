"""Output columns and LLM output schemas."""

import polars as pl
from pyspark.sql import types as T

ACTIVITY_COLUMNS = [
    "activity_id",
    "activity_name",
    "activity_description",
    "activity_fun",
    "activity_cost",
    "activity_location",
]
CHORE_COLUMNS = ["intensity", "chore_id", "asignee_id", "description", "duration", "status"]
PURCHASE_COLUMNS = [
    "item_id",
    "item_name",
    "item_description",
    "item_cost",
    "item_purchase_date",
    "item_purchaser",
    "item_reason",
    "status",
]
FAMILY_MEMBER_SCHEMA = T.StructType(
    [
        T.StructField("favourite_foods", T.ArrayType(T.StringType())),
        T.StructField("person_id", T.IntegerType()),
        T.StructField("email_address", T.StringType()),
        T.StructField("favourite_activities", T.StringType()),
        T.StructField("age", T.LongType()),
        T.StructField("first_name", T.StringType()),
        T.StructField("last_name", T.StringType()),
        T.StructField("date_of_birth", T.DateType()),
        T.StructField("gender", T.StringType()),
        T.StructField("good_member_credit", T.IntegerType()),
    ]
)
MEMBER_FACT_COLUMNS = ["fact_id", "person_id", "fact_type", "fact_detail"]
MEMBER_RELATION_COLUMNS = ["relation_id", "affection", "person_id_1", "person_id_2", "relationship_type", "notes"]

ACTIVITY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "fun": {"type": "string"},
        "cost": {"type": "string"},
        "location": {"type": "string"},
    },
    "required": ["name", "description", "fun", "cost", "location"],
    "additionalProperties": False,
}
ACTIVITY_DTYPE = pl.Struct(
    {"name": pl.String, "description": pl.String, "fun": pl.String, "cost": pl.String, "location": pl.String}
)

PURCHASE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "cost": {"type": "number"},
        "purchase_date": {"type": "string", "format": "date"},
        "purchaser": {"type": "integer"},
        "reason": {"type": "string"},
    },
    "required": ["name", "description", "cost", "purchase_date", "purchaser", "reason"],
    "additionalProperties": False,
}
PURCHASE_DTYPE = pl.Struct(
    {
        "name": pl.String,
        "description": pl.String,
        "cost": pl.Float32,
        "purchase_date": pl.Date,
        "purchaser": pl.Int32,
        "reason": pl.String,
    }
)

CORRECTIONS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "corrected_favourite_food": {"type": "string"},
        "corrected_favourite_activities": {"type": "string"},
    },
    "required": ["corrected_favourite_food", "corrected_favourite_activities"],
    "additionalProperties": False,
}
CORRECTIONS_DTYPE = pl.Struct({"corrected_favourite_food": pl.String, "corrected_favourite_activities": pl.String})

# Structured outputs need an object at the root, so lists and scalars are wrapped in one.
FOODS_JSON_SCHEMA = {
    "type": "object",
    "properties": {"favourite_food": {"type": "array", "items": {"type": "string"}}},
    "required": ["favourite_food"],
    "additionalProperties": False,
}
FOODS_DTYPE = pl.Struct({"favourite_food": pl.List(pl.String)})

AFFECTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {"affection": {"type": "integer"}},
    "required": ["affection"],
    "additionalProperties": False,
}
AFFECTION_DTYPE = pl.Struct({"affection": pl.Int32})
