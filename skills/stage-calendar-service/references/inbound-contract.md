# Inbound calendar-service contract

The practice_900 calendar router sends its separator-labeled text to the authenticated Hermes `/webhooks/ap-calendar-service` route. Its Activepieces HTTP action must use that URL instead of the payment-email `/webhooks/ap-push` route. Set the `X-Gitlab-Token` header to this calendar route's separate protected secret; do not reuse the payment route's secret. Keep the concatenator output as the HTTP Raw Body. The practice_900 Hermes gateway now wraps authenticated raw UTF-8 text as `{"data":"<concatenator output>"}` before rendering the skill prompt. An existing JSON body with one `data` string is also accepted. Empty raw text is rejected.

The preferred Activepieces concatenator produces:

```text
***Service Date:2026-09-15***Client:<calendar client text>***Map ID:<color mapping UUID>***Event Calendar ID:<stable Google Calendar event ID>
```

`Service Date` is the Google event end timestamp converted by Activepieces to its `America/Chicago` calendar date and formatted as `YYYY-MM-DD`. It is already the value required by Grist `Service_Date`; Hermes must not require a time or offset or reinterpret it in another time zone. In Date Helper 0.1.35, use `YYYY-MM-DDTHH:mm:ss` as the input format, `America/Chicago` as both source and output time zone for the event end timestamp, and `YYYY-MM-DD` as the output format. Keep the separately normalized event-update date only for the Activepieces eligibility comparison; do not send it as `Service Date`.

For backward compatibility, also accept the former body when `Service Date` is absent:

```text
***Start Time:2026-09-15T17:00:00-05:00***Client:<calendar client text>***Map ID:<color mapping UUID>***Event Caledar ID:<stable Google Calendar event ID>
```

Legacy `Start Time` must include an explicit offset so Hermes can derive its local calendar date. When both date fields are present, `Service Date` is authoritative. The label `Event Caledar ID` is the old concatenator spelling; accept it as well as the corrected `Event Calendar ID`. The event ID is source identity and must remain the same on updates to that calendar event. Send it to the live practice_900 Grist column `Service_Staging.Event_Calendar_ID`. The Map ID chooses the service status and is not the source identity.

| Map ID | Meaning | Staging status |
|---|---|---|
| `ff679245-cd83-43e5-9761-6a80b53864d8` | Appointment | Send `Service_Status: null` for a past event |
| `93195fab-638d-4f79-a561-79523b4e205c` | Present / Attended | `Present` |
| `6e1fcca8-c580-4fed-92aa-b5a91b6f9308` | No Show | `No Show` |
| `dede1349-e1b4-4635-874c-398737378239` | Same-Day Cancel | `Same-day cancel` |
| `0285c3b2-5ec3-4667-ac04-eee55f04a922` | Available | Send `Service_Status: null` for a past event |

Two other calendar colors are reserved for future reminder work and are outside this skill.

The current body contains no event update timestamp or version. Replacement therefore follows arrival order; an older event notification delivered later could overwrite a newer unreviewed staging row. When the calendar router can supply the source event's `updated` timestamp, include it as a labeled field before event text and have Activepieces reject an older version for the same event ID. Until then, do not claim out-of-order safety.

For a past Appointment or Available event, submit the same event ID with `Service_Status: null`. The explicit null clears an old status when the matching unreviewed staging row is updated, and Grist's validation should require the owner to choose a status before promotion. Do not delete the row or leave its prior outcome. Once reviewed, a later update creates a new review item instead of changing the reviewed row.

Hermes's `202 Accepted` confirms only that an asynchronous run began. Verify the staging result in Grist after controlled tests.
