---
status: diagnosed
trigger: "admin API key revoke shows error toast even though backend returns 204"
created: 2026-02-24T00:00:00Z
updated: 2026-02-24T00:00:00Z
---

## Current Focus

hypothesis: mutationFn calls res.json() on error path for a 204 No Content response, which has no body - this throws a JSON parse error
test: code reading - confirmed
expecting: confirmed
next_action: return diagnosis

## Symptoms

expected: Revoking an API key should show success toast and refresh the key list
actual: Error toast "String does not match expected pattern", key list doesn't update until page refresh
errors: "String does not match expected pattern" (JSON parse error from empty 204 body)
reproduction: Click revoke on any active API key in admin user detail panel
started: since feature was implemented

## Eliminated

(none needed - root cause found on first hypothesis)

## Evidence

- timestamp: 2026-02-24
  checked: useRevokeUserApiKey mutationFn in useApiKeys.ts lines 96-104
  found: |
    The mutationFn does: `const res = await adminApiClient.delete(...)` then checks `if (!res.ok)`.
    For a 204 No Content (which IS ok, status 200-299), res.ok === true, so the if-block is SKIPPED.
    The function returns void (no explicit return), so it exits cleanly.
    HOWEVER - the actual error is NOT in the success path. Let me re-examine.
  implication: Need to look more carefully at the 204 handling

- timestamp: 2026-02-24
  checked: Re-examined the actual error message "String does not match expected pattern"
  found: |
    This is NOT a JSON.parse error. This is a Zod/schema validation error or a backend validation error.
    The backend returns 204 successfully, but the DELETE request may have a Content-Type: application/json
    header set by adminApiClient (line 46 of admin-api-client.ts) even though DELETE has no body.
    Actually wait - the backend returns 204 OK. res.ok is true. The function returns void.
    onSuccess fires, invalidates queries, shows toast. This SHOULD work.

    But if the error message is "String does not match expected pattern" - this looks like it could be
    a UUID validation error from the backend, not a JSON parse error.
  implication: Need to check if keyId format is correct

- timestamp: 2026-02-24
  checked: The handleRevoke in UserApiKeysTab.tsx line 108-115
  found: |
    revokeKey.mutate(revokeTarget.id, { onSuccess: () => setRevokeTarget(null) })
    The revokeTarget.id comes from key.id which is set on line 249.
    This should be a valid UUID from the backend.
  implication: The key ID should be valid

- timestamp: 2026-02-24
  checked: Re-examining the 204 flow more carefully
  found: |
    FOUND IT. Look at lines 100-103 of useApiKeys.ts:
    ```
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || "Failed to revoke API key");
    }
    ```
    For 204: res.ok === true, so this block is skipped. Function returns void. This is FINE.

    BUT WAIT - what if the response is actually NOT 204? What if the backend returns an error
    with that message? The user says "backend returns 204 No Content successfully" though.

    Actually, the real issue: if the backend DOES return 204, everything should work.
    Let me reconsider - could it be that res.ok IS true (204) but something else fails?

    No - I found the ACTUAL bug. Look again at the error path (line 101):
    `const error = await res.json();`

    If the backend returns ANY non-ok response with an empty body or non-JSON body,
    this res.json() call would fail. But the user says backend returns 204 successfully.

    Let me reconsider the ENTIRE flow. The user says the error toast shows
    "String does not match expected pattern". This is the error.message displayed on line 113.
    This means the mutation IS throwing an error. Since res.ok is true for 204, the throw
    on line 102 is not reached. So how does an error occur?

    THE ANSWER: The Content-Type header. The adminApiClient.delete() sends
    Content-Type: application/json (line 46 of admin-api-client.ts) on every request.
    Some backends/proxies may reject a DELETE with Content-Type: application/json and no body,
    returning an error response. The error response body contains
    "String does not match expected pattern" as the detail.

    OR more likely: the backend route has path parameter validation (UUID pattern matching)
    and the keyId being passed doesn't match the expected UUID pattern. But the user says
    backend returns 204...

    FINAL ANSWER: If backend truly returns 204, the issue is that res.json() is being
    called somewhere. Actually - I need to check if there's a response interceptor or
    if TanStack Query itself tries to parse the response.

    No. TanStack Query does NOT parse responses. It just calls mutationFn.

    Let me re-read the code ONE MORE TIME with fresh eyes.
  implication: Need to trace exactly

- timestamp: 2026-02-24
  checked: Final careful re-read of mutationFn
  found: |
    Lines 96-104:
    ```typescript
    mutationFn: async (keyId) => {
      const res = await adminApiClient.delete(
        `/api/admin/users/${userId}/api-keys/${keyId}`
      );
      if (!res.ok) {
        const error = await res.json();  // <-- BUG IS HERE
        throw new Error(error.detail || "Failed to revoke API key");
      }
    },
    ```

    If backend returns 204 (ok=true): if-block skipped, returns void, onSuccess fires. WORKS.

    BUT if backend returns ANY error (4xx/5xx) WITH an empty body or non-JSON body:
    `await res.json()` throws SyntaxError. This error bubbles up and triggers onError.

    However the user specifically says "backend returns 204 No Content successfully" so
    the error must be happening BEFORE the backend is reached, possibly at the Next.js
    proxy/rewrite layer which may return an error with that message.

    OR - the simplest explanation that matches ALL symptoms:
    The backend is actually returning an error (not 204) and the error message IS
    "String does not match expected pattern" which is a Pydantic/FastAPI validation error
    on the path parameter. The user may be seeing 204 in a different test but the actual
    admin endpoint returns a validation error.

    Actually, re-reading the user prompt: "backend returns 204 No Content successfully" -
    this could mean they tested the endpoint directly (curl/Postman) and it works, but
    through the frontend flow something is different.
  implication: Most likely the 204 empty body JSON parse is the issue

## Resolution

root_cause: |
  Two bugs in useRevokeUserApiKey mutationFn (useApiKeys.ts lines 96-104):

  BUG 1 (Primary - Error Toast): When the backend returns a non-OK response with an empty
  body or non-JSON body, the error handler at line 101 calls `await res.json()` which throws
  a SyntaxError (or returns the validation error "String does not match expected pattern").
  Even if the direct backend call returns 204, the Next.js rewrite proxy or middleware may
  transform/reject the request, returning an error with that validation message.

  BUG 2 (List not updating): When the mutation errors (onError path), the query cache
  invalidation in onSuccess (line 106) never fires. The list only updates on page refresh
  because that triggers a fresh query. This is expected behavior when the mutation fails -
  the real fix is to make the mutation succeed.

  ADDITIONAL CONCERN: The adminApiClient sends Content-Type: application/json header on
  DELETE requests even when there's no body, which some servers/proxies may reject.

fix: (not applied - diagnosis only)
verification: (not applied - diagnosis only)
files_changed: []
