# nogamy-semantic-model — Microsoft Fabric

Read when `_context/platform.md` §2 names Microsoft Fabric. The BI tool is Power BI.

## Location

| What | Where | Format |
|---|---|---|
| Semantic model | `fabric/bi/<project>/<name>.SemanticModel/` | TMDL |
| Report | `fabric/bi/<project>/<name>.Report/` | PBIR |
| Report specs and mockups | `ui/<report>/` | Markdown |

`fabric/bi/` maps to the BI DEV workspace. Power BI Desktop saves as PBIP, so TMDL and PBIR go through Git and PR like code.

## Ownership

Measures are DAX; the Power BI developer approves them and owns hierarchies, formats and RLS roles.

## Defaults

- Storage mode **Import**. Direct Lake only after a performance test (decision in `_context/architecture.md`).
- Source: `GOLD` only. No views in a Direct Lake model: a view makes it fall back to DirectQuery.
- Measures only in the model. Reports never define measures.

## The Fabric Data Agent

- The Data Agent reads the model, not the data: TMDL `description` and synonyms are its only knowledge.
- It connects to the **semantic model only**; a direct warehouse connection bypasses RLS. Users need Read on the model; RLS is kept.

## Measure drafts

From `_context/legacy-measures.md`: a DAX draft per row with `in_use = yes`, named as `target_measure`, with the legacy expression and the meaning in its description. When the legacy tool is Qlik: `nogamy-legacy-migration` → `references/qlik.md`.

## RLS

Roles from `_context/access-rules.md`. **Admin, Member and Contributor in the workspace bypass RLS; only Viewer is filtered.** Test with a Viewer account.

## Deployment

Direct Lake models do not rebind to the target warehouse by themselves: they need a data source rule (`nogamy-deploy` → `references/fabric.md`).

## Platform specifics — answers

| Topic | Fabric |
|---|---|
| BI tool; text formats; folder | Power BI; TMDL (model), PBIR (report); `fabric/bi/<project>/` |
| How the model reads the data, and the default | Import (default); Direct Lake after a performance test |
| Saved into the repo / published from it | PBIP from Power BI Desktop; promoted by the CI/CD runner after the pipelines (`nogamy-deploy`) |
| Re-pointed per environment | Direct Lake: a data source rule; Import: ? (per project, verify on Learn) |
| Row-level security; who bypasses it | RLS roles in the model; workspace Admin, Member, Contributor bypass it, Viewer is filtered |
| AI assistant over the model | Fabric Data Agent, through the semantic model only; needs descriptions and synonyms |
| Licences | ? (per project) |
| Known traps | a view in a Direct Lake model → DirectQuery fallback; a test with a builder account shows no RLS |
