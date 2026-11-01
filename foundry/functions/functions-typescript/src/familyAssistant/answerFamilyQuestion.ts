import { Function, UserFacingError } from "@foundry/functions-api";
import { AnthropicClaude_5_5_Sonnet } from "@foundry/models-api/language-models";
import { AipfFamilyMember, AipfMemberFact, AipfMemberRelation, Objects } from "@foundry/ontology-api";

const SYSTEM_PROMPT = "Use all of the data in the given context to answer the given question. "
    + "Be quick and helpful. You are an expert, remember. "
    + "Note that all of the person ids link back to the id declared in the family members area. "
    + "Be concise in your response.";

export class FamilyQuestionFunctions {
    @Function()
    public async answerFamilyQuestion(question: string): Promise<string> {
        if (!question.trim()) {
            throw new UserFacingError("Please enter a question.");
        }

        const [members, relations, facts] = await Promise.all([
            Objects.search().aipfFamilyMember().allAsync(),
            Objects.search().aipfMemberRelation().allAsync(),
            Objects.search().aipfMemberFact().allAsync(),
        ]);

        const userMessage = [
            `Question: ${question}`,
            `Family members:\n${members.map(describeMember).join("\n")}`,
            `Family inter-relations:\n${relations.map(describeRelation).join("\n")}`,
            `Family facts:\n${facts.map(describeFact).join("\n")}`,
        ].join("\n\n");

        const response = await AnthropicClaude_5_5_Sonnet.createGenericChatCompletion({
            params: { temperature: 0, maxTokens: 1000 },
            messages: [
                { role: "SYSTEM", contents: [{ text: SYSTEM_PROMPT }] },
                { role: "USER", contents: [{ text: userMessage }] },
            ],
        });

        return response.completion ?? "";
    }
}

function describeMember(member: AipfFamilyMember): string {
    return `id: ${member.personId}. name: ${member.firstName} ${member.lastName}. age: ${member.age}. `
        + `fav activities: ${member.favouriteActivities}. fav foods: ${member.favouriteFoods?.join(", ")}. `
        + `gender: ${member.gender}. goodness: ${member.goodMemberCredit}`;
}

function describeRelation(relation: AipfMemberRelation): string {
    return `member id 1: ${relation.personId1}. member id 2: ${relation.personId2}. `
        + `relationship type: ${relation.relationshipType}. closeness of relation out of 5: ${relation.affection}`;
}

function describeFact(fact: AipfMemberFact): string {
    return `person id: ${fact.personId}. fact detail: ${fact.factDetail}. fact type: ${fact.factType}.`;
}
