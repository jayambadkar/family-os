import { Function, ExternalSystems, isOk  } from "@foundry/functions-api";
import { AipfTelegram1 } from "@foundry/external-systems/sources";

export class SentinelFunctions {
    @ExternalSystems({
        sources: [AipfTelegram1]
    })
    @Function()
    public async sendGroupChatMessage(message: string): Promise<boolean> {
        const result = await AipfTelegram1.webhooks.AipfSentinelSend.call({
            text: message
        })
        return isOk(result)
    }

    @Function()
    public async sendGroupChatAnnouncemnt(announcement: string): Promise<boolean> {
        const border: string = "==========="
        const underline: string = "\n------------\n"
        const title: string = "\nANNOUNCEMENT"
        const result = await AipfTelegram1.webhooks.AipfSentinelSend.call({
            text: border + title + underline + announcement + "\n" + border
        })
        return isOk(result)
    }
}
