# Vertical Skill Contract

browser-automation-omni is the base browser operation layer. Vertical skills should keep business semantics outside the base and call the base for browser actions.

## What belongs in the base

```text
open/attach browser
choose backend
read page cheaply
find entrance
click/type/select/upload/download
query/filter/export
extract table/card/form/chart-adjacent data
handle iframe/modal/native dialog
visual verification
approval gating
execution logging
handoff structured data
```

## What belongs in vertical skills

```text
aftersale business policy
ad bidding strategy
ROI optimization rules
product listing copy/categorization rules
refund/return decisions
platform-specific workflow semantics
output formatting for a business process
```

## Required vertical skill declaration

```yaml
base_skill: browser-automation-omni
business_domain: <aftersale | ads | product_publish | report_export | crm | erp | finance | other>
required_context:
  platform: <site/platform>
  profile: <browser profile or current Chrome requirement>
  login_state: <required/optional>
entrypoints:
  - human_name: <入口名称>
    route_hint: <menu/search/url/filter path>
queries:
  - name: <query name>
    fields: [<keyword/date/status/...>]
outputs:
  - type: <json/table/csv/xlsx/screenshot>
    schema: <fields or path convention>
high_risk_actions:
  - <publish/delete/payment/authorize/price/inventory/budget/bid/...>
verification:
  - <readback/table count/toast/download exists/screenshot/...>
```

## Runtime call pattern

```text
1. Load browser-automation-omni.
2. Load the vertical skill.
3. Vertical skill states business goal and required browser context.
4. Base skill runs backend_router.
5. Base skill performs browser navigation/query/extraction/export.
6. Base skill returns structured JSON/table/file path/page evidence.
7. Vertical skill applies business rules.
8. Base skill executes approved browser writes only after approval_gate.
9. Base skill verifies browser state after execution.
```

## Template for a new vertical skill

```text
# <Domain Skill Name>

Depends on: browser-automation-omni
Purpose: <business domain goal>

Context:
- Platform:
- Required browser/profile/login state:
- Preferred backend hints:

Entrances:
- <human label> -> <route/menu/url/search hint>

Query / Form Schema:
- field: <name>
  label: <visible label>
  type: <input/select/date/table/export>
  required: <true/false>
  validation: <readback rule>

Extraction Output:
- format: <JSON/CSV/XLSX/table>
- fields: <field list>
- file naming/path convention:

Domain Rules:
- <business-specific decisions live here, not in browser-automation-omni>

High-Risk Actions:
- <actions requiring explicit approval>

Verification:
- <toast/readback/download exists/table count/screenshot>
```

## Examples

Aftersale skill:

```text
Base: opens/attaches browser, navigates to aftersale area, fills date/status filters, extracts/export table.
Vertical: knows aftersale type semantics, refund/logistics fields, output schema, and summary rules.
```

Ad optimization skill:

```text
Base: reads campaign dashboard/filter/table safely.
Vertical: computes ROI/ROAS rules and proposes bid/budget changes.
Approval: required before any budget/bid write.
```
