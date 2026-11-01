import { Function } from "@foundry/functions-api";
import { GPT_6_LUNA } from "@foundry/models-api/language-models";
import { AipfFamilyRules, ObjectSet } from "@foundry/ontology-api";

const SYSTEM_PROMPT = "Summarize these rules into under 200 words. Be accurate and concise";

export class FamilyRulesFunctions {
    @Function()
    public async summariseRules(rules: ObjectSet<AipfFamilyRules>): Promise<string> {
        const allRules = await rules.allAsync();

        if (allRules.length === 0) {
            return "There are no family rules to summarise.";
        }

        const ruleList = allRules.map(rule => `${rule.name}: ${rule.description}`).join("\n");

        const response = await GPT_6_LUNA.createChatCompletion({
            params: { temperature: 0, maxTokens: 1000 },
            messages: [
                { role: "SYSTEM", contents: [{ text: SYSTEM_PROMPT }] },
                { role: "USER", contents: [{ text: `Rules:\n${ruleList}` }] },
            ],
        });

        return response.choices[0]?.message.content ?? "";
    }
}
