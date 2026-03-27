# Button Behavior Issues

## "Send Invite" (Agency)
Expected: Sends invite email.
Actual: Unverified if loading state locks button. Risk of multiple emails sent.

## "Submit Application" (Public Apply)
Expected: Submits candidate data.
Actual: Backend requires `X-Skip-Auth` header. If missing, button will fail silently or throw 401.
