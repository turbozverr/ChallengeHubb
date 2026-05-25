# WebSystem Decisions (Locked)

Date: 2026-05-25

## Confirmed Domain Rules
- Database: **MySQL**
- Roles in web system: `Admin`, `Moderator`, `BusinessClient`
- `Guest` is unregistered user; can browse public/mobile content only, no protected actions
- Sponsors/business clients do **not** pay through platform
- Premium subscribers (mobile users) pay through platform via **Stripe**
- `SponsoredChallenge` is created/published by **Admin only**
- `BusinessClient` can only access web dashboard to login and view/analyze own campaign stats
- Web system has an `Admin panel` for full platform management
- Web landing includes button to download mobile `.vpk` artifact

## Web Scope Boundary
- Included: auth/RBAC, admin panel, moderation, reports queue, sponsored challenge administration, analytics/stats
- Excluded: FYP feed and regular mobile user content interactions in web protected area
