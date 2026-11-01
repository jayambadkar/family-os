import { Edits, OntologyEditFunction } from "@foundry/functions-api";
import { GPT_6_LUNA } from "@foundry/models-api/language-models";
import { AipfFamilyMember, AipfFamilyRules, AipfPurchase, ObjectSet } from "@foundry/ontology-api";

const DECISIONS = ["approved", "rejected", "waiting"] as const;

type Decision = typeof DECISIONS[number];

const SYSTEM_PROMPT = `You are a really rather brilliant PA to the head of a family unit. You are to automate as many of these

Use the provided information to assess whether the given purchase request proposal should be automatically approved, rejected, or left waiting. You may NOT return "waiting" unless this is an absolute EMERGENCY or the user has requested it!!!

Make your decision based on how compatible the request is with:
- family defined rules (takes precedence)
- the requester's characteristics (e.g. their relative goodness, age, favourite activities, etc etc. If this request is a good fit for them then automatically accept, otherwise base on other things or leave as waiting.)
- the heuristics of previously approved purchases. i.e. if something similar has already been bought, be more likely to approve. If something identical has been bought, then think along the lines of that 'we have it, so why do we need another' and so reject it.
- specific details in the user request, e.g. if the user has requested human review then return "waiting".

The output must be exactly one of the following: "approved", "rejected", "waiting". Any other outputs are invalid and cannot be returned. "waiting" means that it goes back for manual human review / approval and is only to be used if you are so clueless that you literally have NO IDEA, or the user has specifically requested that the request be sent through for human review.`;

export class PurchaseFunctions {
    @Edits(AipfPurchase)
    @OntologyEditFunction()
    public async decidePurchase(
        proposal: AipfPurchase,
        rules: ObjectSet<AipfFamilyRules>,
        allPurchases: ObjectSet<AipfPurchase>,
    ): Promise<void> {
        const [requester, familyRules, approvedPurchases] = await Promise.all([
            proposal.aipfFamilyMember.getAsync(),
            rules.allAsync(),
            allPurchases.filter(purchase => purchase.status.exactMatch("approved")).allAsync(),
        ]);

        const previousPurchases = approvedPurchases.filter(purchase => purchase.itemId !== proposal.itemId);
        const ruleList = familyRules.map(rule => `${rule.name}: ${rule.description}`).join("\n");

        const userMessage = [
            `Purchase request proposal:\n${describePurchase(proposal)}`,
            `Purchase requester:\n${requester ? describeRequester(requester) : "Unknown"}`,
            `Previously approved purchases:\n${previousPurchases.map(describePurchase).join("\n\n")}`,
            `Family defined rules:\n${ruleList}`,
        ].join("\n\n");

        const response = await GPT_6_LUNA.createChatCompletion({
            params: { temperature: 0, maxTokens: 1000 },
            messages: [
                { role: "SYSTEM", contents: [{ text: SYSTEM_PROMPT }] },
                { role: "USER", contents: [{ text: userMessage }] },
            ],
        });

        proposal.status = parseDecision(response.choices[0]?.message.content);
    }
}

function describePurchase(purchase: AipfPurchase): string {
    return [
        `Item name: ${purchase.itemName}`,
        `Item description: ${purchase.itemDescription}`,
        `Cost: ${purchase.itemCost}`,
        `Reason: ${purchase.itemReason}`,
    ].join("\n");
}

function describeRequester(member: AipfFamilyMember): string {
    return [
        `Age: ${member.age}`,
        `Relative goodness: ${member.goodMemberCredit}`,
        `Favourite activities: ${member.favouriteActivities}`,
        `Favourite foods: ${member.favouriteFoods?.join(", ")}`,
    ].join("\n");
}

function parseDecision(content: string | undefined): Decision {
    const answer = (content ?? "").toLowerCase().replace(/[^a-z]/g, "");

    return DECISIONS.find(decision => decision === answer) ?? "waiting";
}
