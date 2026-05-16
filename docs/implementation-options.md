# Implementation Options

Stand: 2026-05-15

## Recommendation

Prefer **Azure serverless** if the school can get minimal Azure access through its Microsoft tenant. It matches the live workflow, keeps the solution close to Microsoft 365, and avoids operating a server.

Use **Supabase EU-hosted** as the pragmatic fallback if Azure access is not available or too hard to administer.

Do not choose **SharePoint-only** for the initial scope; it does not fit the teacher-controlled real-time evaluation flow with anonymous student devices.

## Option 1: SharePoint-only static page plus SharePoint Lists

Shape:
- Static HTML/JS page hosted from SharePoint or linked from Teams.
- SharePoint Lists as storage.
- No separate backend.

Pros:
- Uses existing school environment.
- Very low additional procurement.
- Administration already understands Teams/SharePoint.

Cons:
- Poor fit for anonymous student devices; SharePoint access and Lists are built around Microsoft 365 identities, guest sharing, and tenant permissions.
- No clean real-time teacher-to-student phase control.
- Hard to prevent accidental access to raw list data.
- Client-side code would need direct list access, which is not a good security boundary.
- Re-entry, live status, QR invalidation, and aggregation finalization become brittle.

Verdict:
- Not recommended except as a document distribution surface for QR material or exports.

## Option 2: Power Platform / Power Pages / Dataverse

Shape:
- Power Pages for anonymous student-facing pages.
- Dataverse or Dataverse for Teams for data.
- Power Apps/Dataverse admin surfaces.

Pros:
- Microsoft-native.
- Low-code administration is attractive for schools.
- Dataverse for Teams can be available with Teams/Microsoft 365 licensing and supports relational data.
- Power Pages supports anonymous website users as a product category.

Cons:
- Power Pages anonymous access is separately licensed and may be expensive or unavailable.
- The school probably does not currently know whether Power Platform is available.
- Real-time teacher-controlled phase changes are not the natural strength of Power Pages.
- Low-code can become harder to version, test, and audit than a small purpose-built app.
- Anonymous student live participation plus teacher dashboard may still require custom code.

Verdict:
- Worth checking with IT/licensing, but not the primary implementation assumption.

## Option 3: Azure serverless web app

Shape:
- Frontend: Azure Static Web Apps.
- API: Azure Functions.
- Real-time: Azure Web PubSub or Azure SignalR Service.
- Storage: Azure Table Storage for simple records, or Azure SQL serverless if relational reporting becomes important.
- Admin authentication: Microsoft Entra ID.
- Student access: anonymous QR URLs.
- Teacher access: QR plus yearly PIN.

Pros:
- Best match for the live workflow: real-time push, central state, QR invalidation, re-entry, item finalization.
- No self-operated server; services are managed.
- Stays in Microsoft ecosystem and can use EU regions / Microsoft EU Data Boundary.
- Entra ID can protect the admin area without building admin auth from scratch.
- Technically clean separation between student, teacher, and admin flows.
- Export generation is straightforward in backend functions.

Cons:
- Requires Azure subscription/access and someone to own deployment.
- More software engineering than SharePoint/Power Apps.
- Need monitoring/backups/configuration even if serverless.
- Real-time service adds one more Azure component.

Verdict:
- Recommended target architecture if Azure access is feasible.

## Option 4: Supabase EU-hosted web app

Shape:
- Frontend hosted on a simple static host.
- Backend: Supabase Postgres, Realtime, Edge Functions, Auth.
- Region: Central EU / Frankfurt.
- Admin authentication: Supabase Auth.
- Student access: anonymous QR URLs.

Pros:
- Very fast to build.
- Postgres is a strong fit for imports, evaluation metadata, aggregates, and exports.
- Built-in real-time subscriptions fit the live teacher/student flow.
- EU region available.
- Separate admin login is acceptable under the current scope.
- Less Azure tenant setup than Option 3.

Cons:
- Outside Microsoft 365; requires DPA/vendor review.
- Supabase is hosted on AWS infrastructure, which may matter for school data protection review.
- Admin identity is separate from school Microsoft accounts unless integrated later.
- More vendor lock-in than a plain Azure Functions/Postgres implementation, although Postgres data is portable.

Verdict:
- Strong fallback when Azure access is blocked or the school wants the fastest low-maintenance route.

## Option 5: Firebase

Shape:
- Firebase Hosting plus Realtime Database or Firestore.
- Firebase Auth for admin.
- Student access anonymous.

Pros:
- Excellent real-time primitives.
- Very low operational maintenance.
- European database locations exist.
- Fast implementation.

Cons:
- Google ecosystem, not Microsoft.
- Data protection review may be harder in a school context.
- No advantage over Supabase/Azure for this project.
- Firestore/Realtime Database data modeling is less natural for import/export tabular school data than Postgres.

Verdict:
- Technically viable, but not preferred.

## Option 6: Minimal on-prem server in the school network

Shape:
- One small server in the school network, e.g. mini PC, school VM, or NAS/container host.
- One web application process serving student, teacher, and admin interfaces.
- Reverse proxy in front, preferably Caddy.
- Primary database: SQLite in WAL mode.
- Backups: scheduled encrypted file backups plus regular restore test.
- Optional later: DuckDB only for offline/export analysis, not as the primary transactional application database.

Pros:
- Data can stay inside the school network.
- No dependency on Azure/Supabase/Google availability or vendor review for live data.
- Very low runtime cost after hardware/VM exists.
- SQLite is simple, file-based, transactional, and fits the expected school-scale write volume.
- The whole system can be packaged as one small deployment.
- No student or teacher cloud accounts needed.

Cons:
- The school now operates a server: updates, disk health, backups, restore tests, TLS/certificates, network reachability, and incident handling need an owner.
- QR codes only work where the server is reachable. If it is only internal, student tablets must be on the school network/VPN.
- HTTPS for internal hostnames needs either a trusted internal certificate setup, a public DNS name with a valid certificate, or device trust configuration.
- Availability depends on local power, Wi-Fi, DHCP/DNS, and the server machine.
- Remote continuation from outside school is not available unless the school exposes the service securely.
- SQLite allows many concurrent readers and one writer; this is fine at expected scale but should be implemented with short transactions and WAL mode.
- DuckDB is not a good primary database for this use case because its concurrency model is optimized for analytical use and stable multi-process writes require other coordination patterns.

Verdict:
- Viable if the school can name a responsible operator and accepts that "minimal server" still means real operational responsibility.
- Prefer SQLite over DuckDB as the primary database.
- This option contradicts the current ADR preference against a self-operated server; choosing it would require superseding ADR 0001.

Suggested minimal stack:
- Backend/frontend: one small app, e.g. FastAPI/Starlette or Node/Express, serving static frontend assets and JSON/WebSocket endpoints.
- Realtime: WebSockets or Server-Sent Events from the same app process.
- Database: SQLite WAL.
- Reverse proxy/TLS: Caddy.
- Process supervision: systemd or Docker Compose.
- Backup: daily SQLite online backup or snapshot, copied to a separate school storage location; optionally Litestream-style continuous replication if an S3-compatible target is available.

## Source Notes

- Azure Static Web Apps supports serverless APIs via Azure Functions and authentication/authorization.
- Azure SignalR Service and Azure Web PubSub provide managed real-time communication.
- Azure Table Storage and Azure SQL Database are managed storage options.
- Microsoft EU Data Boundary covers Microsoft enterprise online services including Microsoft 365, Power Platform, and most Azure services, subject to documented continuing transfers.
- Dataverse for Teams is integrated with Teams and has documented capacity limits.
- Power Pages has anonymous-user licensing.
- Supabase has EU regions including Central EU / Frankfurt and provides Realtime on Postgres changes.
- Firebase Realtime Database supports a Europe location.
- SQLite WAL supports concurrent readers while a writer is active, but still has a single-writer model.
- DuckDB supports concurrent writes within a single process but is not the preferred primary database for multi-client transactional web applications.
- Caddy provides automatic HTTPS handling, including internal/local certificate support with trust configuration.
- Litestream can continuously replicate SQLite changes to another storage target.
