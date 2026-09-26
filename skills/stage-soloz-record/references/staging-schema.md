# Soloz staging schema

Use the current production tables to resolve references immediately before each staging submission.

## Reference lookups

| Input | Lookup command arguments | JSON value |
|---|---|---|
| Account | `--table Accounts --column Name --stable-column Account_ID` | Matching record's numeric `id` |
| Rate category | `--table Rate_Categories --column Rate_Category --stable-column Rate_Category` | Matching record's numeric `id` |
| Client | `--table Clients --column Name --stable-column Client_ID` | Matching record's numeric `id` |

Accept a stable `Account_ID` or `Client_ID` directly when the user supplies one, but still query Grist and use the returned numeric record `id`. For those inputs, change `--column` to `Account_ID` or `Client_ID` respectively and use `--fallback none`. Names are compared after trimming whitespace and ignoring case. Require exactly one match.

## Account

- Required input: name, email
- Destination: `account-staging`
- No reference lookup

```json
{"table_columns":{"Name":"<name>","Email":"<email>"}}
```

## Client

- Required input: name, account, rate category
- Destination: `client-staging`
- Resolve account against `Accounts`
- Resolve rate category against `Rate_Categories`

```json
{"table_columns":{"Name":"<name>","Account":0,"Rate_Category":0}}
```

Replace each `0` with the matching record's numeric Grist `id`.

## Payment

- Required input: account, payment date, payment method, amount, reference number
- For a validated payment email, account, payment method, positive amount, and `Email_ID` are required. `Payment_Date` and `Reference_` may be omitted when the notification does not establish them; explain missing fields in `Notes` for owner review. `Email_ID` identifies the source email, never the payment transaction.
- Destination: `payment-staging`
- Resolve account against `Accounts`
- `Reference_` is the exact Grist column ID; keep the trailing underscore

```json
{"table_columns":{"Account":0,"Payment_Date":"<YYYY-MM-DD>","Payment_Method":"<payment method>","Amount":0,"Reference_":"<reference #>"}}
```

Replace the first `0` with the account's numeric Grist `id` and the second with the supplied numeric amount.

For payment-email staging, add `Email_ID` as the stable source message ID and concise `Notes` when needed. Keep the exact same `Email_ID` on every delivery of the same email. Do not put it in `Reference_`. The `Email_ID` column exists in the live practice_900 `Payments_Staging` table.

## Service

- For a direct user request, required input is client, service date, and service status; event fee is required only for status `Event`
- For a calendar-derived service, a missing or unresolvable client is allowed in staging. Search current Clients and Accounts for a defensible Client match; if none can be inferred, send `Client: null` and explain it briefly in `Notes`. Grist validation holds the row until the owner fills Client.
- For a calendar-derived service, `Event_Calendar_ID` is required. A past event colored Appointment or Available sends `Service_Status: null` so an existing unreviewed status is cleared and Grist flags the row for owner review. The calendar color `Same-Day Cancel` maps to Grist's exact choice `Same-day cancel`. Singing-event Map ID `506CF18C-FFF5-4539-8C71-7B82BB77FC5A` maps to `Event`; because the calendar input has no fee, send `Event_Fee: null` and explain in `Notes` that the owner must enter it.
- Destination: `service-staging`
- Resolve client against `Clients`
- When status is not `Event` and no event fee is supplied, send numeric `0`; Grist calculates the normal service charge from the client's account, rate category, and effective rate price

```json
{"table_columns":{"Client":0,"Service_Date":"<YYYY-MM-DD>","Service_Status":"<service status>","Event_Fee":0}}
```

Replace the first `0` with the client's numeric Grist `id`. Replace the second with the supplied event fee for an `Event`; otherwise use the supplied value or numeric `0` when omitted.

For calendar staging, add `Event_Calendar_ID` as the stable calendar event ID. Keep the same value across updates, even when the service date, client, or status changes. The live practice_900 table names this column `Event_Calendar_ID`, not `Event_ID`. Send JSON `null` for `Client` when no defensible Client can be inferred, for `Service_Status` when a past Appointment or Available event has no service outcome, and for `Event_Fee` when a calendar color maps to `Event` without supplying a fee. Omission would leave old values in place during an update. Never send a made-up reference, choice, or empty string as a substitute.

## Source-based staging replacement

The payment flow currently creates rows only; `Email_ID` remains available for identifying repeated source emails. For a calendar-derived service, Hermes first reads `Service_Staging` by exact `Event_Calendar_ID`. One unreviewed match goes to the independent `service-staging-update` webhook; no unreviewed match goes to the existing `service-staging` create webhook. A reviewed row must never be updated. If a row has left staging after approval, a later calendar update creates a new staging proposal; Grist's business validation may flag it as a duplicate. A read failure, unclear review state, or multiple unreviewed matches must stop routing for owner review.

The update webhook receives the selected staging row's numeric Grist `id` and the same complete source-derived columns used for creation:

```json
{"record_id":42,"table_columns":{"Client":123,"Service_Date":"2026-09-21","Service_Status":"No Show","Event_Fee":0,"Event_Calendar_ID":"example_event_20260921T170000Z"}}
```

The IDs in this example are placeholders. An additional Activepieces check that `record_id` still has the same `Event_Calendar_ID` and remains unreviewed would guard against a change between Hermes's read and the update action. A stale or missing target is a conflict, not permission to update another row. Hermes must not retry or fall back to create after an uncertain update response.

Do not infer a staging write from a webhook response alone. Verify a controlled delivery by reading the resulting staging row. A repeated source ID should leave one unreviewed row; an event status change should replace that row's status, including clearing it when the owner changes a past event to Appointment or Available.

## Progress

- Required input: client, date, progress
- Destination: `progress-staging`
- Resolve client against `Clients`

```json
{"table_columns":{"Client":0,"Date":"<YYYY-MM-DD>","Progress":"<progress>"}}
```

Replace `0` with the client's numeric Grist `id`.
