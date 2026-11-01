import { Edits, Integer, MediaItem, OntologyEditFunction } from "@foundry/functions-api";
import { GPT_6_LUNA } from "@foundry/models-api/language-models";
import { AipfChore, AipfFamilyMember, AipfImages, ObjectSet } from "@foundry/ontology-api";

const COMPLETE = "complete";
const CREDIT_PER_CHORE = 25;
const BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

const SYSTEM_PROMPT = `You verify whether household chores have been completed, using a photo submitted as evidence.

Compare the photo with the chore details. Answer "complete" only if the photo clearly shows that the chore has been finished. Otherwise answer "incomplete".

The output must be exactly one of the following: "complete", "incomplete".`;

export class ChoreFunctions {
    @Edits(AipfChore, AipfFamilyMember)
    @OntologyEditFunction()
    public async verifyChoreCompletion(images: ObjectSet<AipfImages>): Promise<void> {
        const completedChoreIds = new Set<Integer>();

        for (const image of await images.allAsync()) {
            if (!image.imageRef) {
                continue;
            }

            const chore = await image.aipfChore.getAsync();

            if (!chore || chore.status === COMPLETE || completedChoreIds.has(chore.choreId)) {
                continue;
            }

            if (await isChoreDone(chore, image.imageRef)) {
                await completeChore(chore);
                completedChoreIds.add(chore.choreId);
            }
        }
    }
}

async function isChoreDone(chore: AipfChore, photo: MediaItem): Promise<boolean> {
    const imageUrl = await toJpegDataUrl(photo);

    const response = await GPT_6_LUNA.createChatCompletion({
        params: { temperature: 0, maxTokens: 1000 },
        messages: [
            { role: "SYSTEM", contents: [{ text: SYSTEM_PROMPT }] },
            { role: "USER", contents: [{ text: describeChore(chore) }, { image: { imageUrl } }] },
        ],
    });

    const answer = (response.choices[0]?.message.content ?? "").toLowerCase().replace(/[^a-z]/g, "");

    return answer === COMPLETE;
}

async function completeChore(chore: AipfChore): Promise<void> {
    const assignee = await chore.aipfFamilyMember.getAsync();

    chore.status = COMPLETE;

    if (assignee) {
        assignee.goodMemberCredit = (assignee.goodMemberCredit ?? 0) + CREDIT_PER_CHORE;
    }
}

function describeChore(chore: AipfChore): string {
    return [
        `Chore: ${chore.description}`,
        `Intensity: ${chore.intensity}`,
        `Duration: ${chore.duration}`,
    ].join("\n");
}

async function toJpegDataUrl(photo: MediaItem): Promise<string> {
    const blob = await photo.readAsync();
    const bytes = new Uint8Array(await blob.arrayBuffer());

    return `data:image/jpeg;base64,${toBase64(bytes)}`;
}

function toBase64(bytes: Uint8Array): string {
    let encoded = "";

    for (let i = 0; i < bytes.length; i += 3) {
        const hasSecond = i + 1 < bytes.length;
        const hasThird = i + 2 < bytes.length;
        const chunk = (bytes[i] << 16) | ((hasSecond ? bytes[i + 1] : 0) << 8) | (hasThird ? bytes[i + 2] : 0);

        encoded += BASE64_ALPHABET[(chunk >> 18) & 63] + BASE64_ALPHABET[(chunk >> 12) & 63];
        encoded += hasSecond ? BASE64_ALPHABET[(chunk >> 6) & 63] : "=";
        encoded += hasThird ? BASE64_ALPHABET[chunk & 63] : "=";
    }

    return encoded;
}
