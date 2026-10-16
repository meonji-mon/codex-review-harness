# Brand and game splash usage

Use for app creation or metadata, publisher, brand asset, icon, and splash changes. Change boundaries: [section 3](../AGENTS.md#3-implementation-and-verification).

## Identity

Unless requested otherwise, use **MEONJI** for organization/publisher/copyright and **com.meonji** as the new bundle/package prefix. Use the MEONJI logo for company branding and game splash.

## Game splash

- Show the company logo for about **1 second** before game entry.
- Use a trimmed **transparent landscape PNG**, roughly 3:2. The iCloud file `${USER_HOME}/Library/Mobile Documents/com~apple~CloudDocs/Downloads/meonji-company-logo-final.png` (960×960) is reference only, not the direct splash asset.
- If unavailable, create one canonical transparent landscape logo in the project's brand folder and use it.
- Portrait: width = `min(screenWidth × 0.36, 174dp)`; center = `(screenWidth × 0.54, screenHeight × 0.5)`.
- Landscape: width = `screenWidth × 0.21`; shift the centered logo by `x += screenWidth × 0.035`.

Value references: Dunk Loop `PublisherSplashScreen` / Dolus `_MeonjiSplash`. These supply the numbers, not an implementation dependency.
