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
- Destination: `payment-staging`
- Resolve account against `Accounts`
- `Reference_` is the exact Grist column ID; keep the trailing underscore

```json
{"table_columns":{"Account":0,"Payment_Date":"<YYYY-MM-DD>","Payment_Method":"<payment method>","Amount":0,"Reference_":"<reference #>"}}
```

Replace the first `0` with the account's numeric Grist `id` and the second with the supplied numeric amount.

## Service

- Required input: client, service date, service status; event fee is required only for status `Event`
- Destination: `service-staging`
- Resolve client against `Clients`
- When status is not `Event` and no event fee is supplied, send numeric `0`; Grist calculates the normal service charge from the client's account, rate category, and effective rate price

```json
{"table_columns":{"Client":0,"Service_Date":"<YYYY-MM-DD>","Service_Status":"<service status>","Event_Fee":0}}
```

Replace the first `0` with the client's numeric Grist `id`. Replace the second with the supplied event fee for an `Event`; otherwise use the supplied value or numeric `0` when omitted.

## Progress

- Required input: client, date, progress
- Destination: `progress-staging`
- Resolve client against `Clients`

```json
{"table_columns":{"Client":0,"Date":"<YYYY-MM-DD>","Progress":"<progress>"}}
```

Replace `0` with the client's numeric Grist `id`.
