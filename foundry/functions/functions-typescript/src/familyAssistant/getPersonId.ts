import { Function, Integer, UserFacingError } from "@foundry/functions-api";
import { AipfFamilyMember, ObjectSet } from "@foundry/ontology-api";

export class FamilyMemberFunctions {
    @Function()
    public async getPersonId(familyMembers: ObjectSet<AipfFamilyMember>): Promise<Integer> {
        const members = await familyMembers.allAsync();

        if (members.length !== 1) {
            throw new UserFacingError(`Expected exactly one family member, but received ${members.length}.`);
        }

        return members[0].personId;
    }
}
