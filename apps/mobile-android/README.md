# ChallengeHub Mobile

Native Android application for ChallengeHub regular users.

## Stack

- Kotlin
- Jetpack Compose
- Retrofit + OkHttp
- DataStore for mobile token storage
- Media3 prepared for short-form video playback

## API

Default backend:

```text
https://challengehubb-production.up.railway.app/api/v1/
```

Override for local backend:

```bash
gradle assembleDebug -PCH_API_BASE_URL=http://10.0.2.2:8000/api/v1/
```

`10.0.2.2` is the Android emulator address for host `localhost`.

## Demo User

```text
user@challengehub.local / user123
```

## Current Scope

Implemented first mobile slice:

- login/register;
- token persistence;
- public feed;
- challenges list;
- join challenge;
- like/unlike video;
- profile screen.

Next mobile features:

- video details/comments modal;
- gallery upload and camera recording;
- challenge submission flow;
- leaderboard;
- badges;
- settings;
- premium screen;
- AI assistant placeholder.
