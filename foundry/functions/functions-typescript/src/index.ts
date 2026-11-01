import { Function, FunctionsMap } from "@foundry/functions-api";

import { AipfFamilyMember, ObjectSet, AipfChore, AipfPurchase } from "@foundry/ontology-api"

export * from "./familyAssistant";

interface AssigneeReturnType {
    name: string
}

export class MyFunctions {
    @Function()
    public getAssignee(chores: ObjectSet<AipfChore>): FunctionsMap<AipfChore, AssigneeReturnType> {
        const map = new FunctionsMap<AipfChore, AssigneeReturnType>();
        chores.all().forEach(chore => {
            const assignee: AipfFamilyMember = chore.aipfFamilyMember.get()!
            map.set(chore, { name: assignee.firstName + " " + assignee.lastName!} )
        })
        return map
    }

    @Function()
    public getRequester(purchases: ObjectSet<AipfPurchase>): FunctionsMap<AipfPurchase, AssigneeReturnType> {
        const map = new FunctionsMap<AipfPurchase, AssigneeReturnType>();
        purchases.all().forEach(purchase => {
            const buyer: AipfFamilyMember = purchase.aipfFamilyMember.get()!
            map.set(purchase, { name: buyer.firstName + " " + buyer.lastName!} )
        })
        return map
    }

    @Function()
    public getEmailAddressOfChoreAssignee(chore: AipfChore): string {
        const foundAddress: string | undefined = chore.aipfFamilyMember.get()?.emailAddress;
        if (!foundAddress) {
            return "NO_EMAIL_FOUND";
        } else {
            return foundAddress
        }
    }

    @Function()
    public getFirstNameOfChoreAssignee(chore: AipfChore): string {
        const name: string | undefined = chore.aipfFamilyMember.get()?.firstName;
        if (!name) {
            return "NO_NAME_FOUND";
        } else {
            return name
        }
    }
}
