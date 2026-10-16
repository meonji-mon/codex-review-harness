# TestFlight and account identification

## Approved upload procedure

Applicability, standing approval, and holds: [section 2](../AGENTS.md#2-execution-and-approval).

1. Match included source/settings/check records to the upload artifact.
2. Verify version, build, bundle ID, signing, environment, and unintended dev/mock activation.
3. Increment the build number if needed; never reuse an uploaded number. After interrupted responses, query remote state first.
4. Retain the actual upload response/status; query TestFlight processing separately.
5. Record blocked login, 2FA, certificates, or signing and the required manual action.
6. Report version/build, upload result, and confirmed processing state.

## Account identifiers

Use only to identify the target for connection, authentication, signing, or upload. Identifiers do not approve account switching or settings changes; central security/target-approval rules apply.


- Apple Developer: `${APPLE_DEVELOPER_EMAIL}`
- Google AdMob: `${ADMOB_EMAIL}`
- Apps in Toss: `${APPS_IN_TOSS_EMAIL}`
- App Store Connect API Issuer ID: `${ASC_API_ISSUER_ID}`
