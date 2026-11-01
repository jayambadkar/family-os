"""Language models, LLM settings and prompts."""

CLAUDE_MODEL = "ri.language-model-service..language-model.anthropic-claude-5-5-sonnet"
GPT_MODEL = "ri.language-model-service..language-model.gpt-6-luna"

# Lets requests wait out the project's per-minute LLM rate limits.
MAX_RATE_LIMIT_RETRIES = 12
# Leaves room for Claude's thinking as well as its reply.
CLAUDE_MAX_TOKENS = 8192
GPT_TEMPERATURE = 0.0

ACTIVITY_PROMPT = "ID: {}"
ACTIVITY_SYSTEM_PROMPT = (
    "You are a salesperson for random outing activities targeting families in the UK. Generate an activity name "
    "and description and make sure it is family friendly - anything goes really. Choose from one of the following "
    "corresponding to the ID\n\n-London Eye\n\n-Tower of London\n\n-Buckingham Palace\n\n-London Dungeon\n\n"
    "-National Gallery\n\n-The British Museum\n\n-Westminster Abbey\n\n-Borough Market\n\n-SEA LIFE London Aquarium"
    "\n\nMake up a description for the above activity corresponding to the name. Also generate an expected cost in "
    'pounds, the location as a geohash string, the fun as either "low", "medium" or "high" and a cost as one of '
    '"low", "medium" or "high which are all random based on the length of the third word of the action description '
    "using modular arithmetic. Also generate a geohash for its location which must correspond to the location "
    "chosen."
)

PURCHASE_SYSTEM_PROMPT = (
    "Choose from one of the below items corresponding to the id using modular arithmetic:\n1. Colouring pencils\n"
    "2. PS5\n3. Maths textbook\n4. Very big notepad\n5. Birthday card\n\nFrom this, then generate a description of "
    "the product, a notional cost in pounds and pence (2dp), the date of purchase to be anytime in the past year, "
    "the purchaser as a random number which is either 1 or 3 and a reason for the purchase."
)

CORRECT_TYPING_ERRORS_PROMPT = (
    "Correct this text to remove any spelling errors so that it is all coherent English. Return data as a struct "
    "with corrected favourite food in one place and corrected favourite activities in another.\n\n{}\n{}"
)
CORRECT_TYPING_ERRORS_SYSTEM_PROMPT = "You are a very clever spelling corrector"

SUMMARISE_FOODS_PROMPT = "Person's declared food preferences: {}"
SUMMARISE_FOODS_SYSTEM_PROMPT = (
    "You are an expert in food types and cuisine. You are to turn these natural language descriptions of people's "
    "favourite food into an array of words/phrases that succinctly describe the person's food preferences. No more "
    "than 3 words in each phrase, but ideally 2 at most except when unavoidable. Maximum of 5 overall."
)

SUMMARISE_ACTIVITIES_PROMPT = "Person's declared preferred activities: {}"
SUMMARISE_ACTIVITIES_SYSTEM_PROMPT = (
    "You are an expert in activity types and recreation. You are to turn these natural language descriptions of "
    "people's favourite activities into an array of words/phrases that succinctly describe the person's activity "
    "preferences. No more than 3 words in each phrase, but ideally 2 at most except when unavoidable. Maximum of 5 "
    "overall."
)

SCORE_AFFECTION_SYSTEM_PROMPT = (
    "In the context of Classifying emotions, your job is to classify the following user message into an affection "
    "score out of 5, any of 1,2,3,4,5. Warmer affections and more care for each other will yield to a greater "
    "affection score. Be fair."
)
