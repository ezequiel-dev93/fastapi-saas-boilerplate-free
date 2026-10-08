# Skill: debug-stripe-webhook

## Description
Debug Stripe webhook issues locally using Stripe CLI. Covers forwarding, testing, inspecting, and troubleshooting common webhook problems.

## Usage
```
/debug-stripe-webhook <action> [--event=<event_type>] [--forward-to=<url>]
```

## Actions
| Action | Description |
|--------|-------------|
| `forward` | Start Stripe CLI forwarding to local endpoint |
| `trigger` | Send test event to local endpoint |
| `logs` | View webhook delivery logs |
| `verify` | Verify webhook signature locally |
| `replay` | Replay a failed webhook from Stripe Dashboard |

## Quick Start

### 1. Install Stripe CLI
```bash
# macOS
brew install stripe/stripe-cli/stripe

# Linux
sudo snap install stripe

# Windows (PowerShell)
choco install stripe-cli
```

### 2. Login to Stripe
```bash
stripe login
# Opens browser to authenticate
```

### 3. Forward Webhooks Locally
```bash
# Terminal 1: Start your API
make run
# or: uvicorn api.main:app --reload --port 8000

# Terminal 2: Forward webhooks
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

**Copy the webhook signing secret** (starts with `whsec_`) and add to `.env`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
```

### 4. Trigger Test Events
```bash
# List available events
stripe trigger --help

# Common test events
stripe trigger invoice.payment_failed
stripe trigger customer.subscription.updated
stripe trigger checkout.session.completed
stripe trigger payment_intent.succeeded
stripe trigger invoice.paid
```

## Common Event Types for This Project

| Event | Handler | Purpose |
|-------|---------|---------|
| `invoice.payment_failed` | Dunning email + past_due status | Failed payment recovery |
| `invoice.paid` | Sync subscription status | Successful payment |
| `customer.subscription.updated` | Sync status, cancel_at_period_end | Plan changes, cancellations |
| `customer.subscription.deleted` | Revoke access | Subscription cancelled |
| `checkout.session.completed` | Provision access | New subscription |
| `payment_method.attached` | Update default payment method | Card added |

## Debugging Checklist

### Webhook Not Received
- [ ] `stripe listen` running in separate terminal
- [ ] Correct `--forward-to` URL (check port)
- [ ] API server running and accessible
- [ ] No firewall blocking localhost
- [ ] Check Stripe CLI output for errors

### Signature Verification Failed (400)
- [ ] `STRIPE_WEBHOOK_SECRET` matches `whsec_` from `stripe listen`
- [ ] No extra whitespace in `.env`
- [ ] Using raw request body (not parsed JSON)
- [ ] Check `api/modules/billing/routes.py` webhook handler

### Event Not Processed
- [ ] Check logs: `tail -f logs/app.log` or docker logs
- [ ] Verify idempotency: `StripeWebhookEvent` table for duplicates
- [ ] Check `BillingService.handle_webhook` for event type handling
- [ ] Database transaction committed? (check `db.commit()`)

### Duplicate Processing
- [ ] `StripeWebhookEvent` table has unique constraint on `stripe_event_id`
- [ ] Idempotency check runs BEFORE processing
- [ ] See `api/modules/billing/services.py` lines 150-170

## Inspecting Webhook Payloads

### View Raw Payload in Logs
```python
# In api/modules/billing/routes.py webhook handler
logger.info("Stripe webhook received", extra={
    "event_type": event["type"],
    "event_id": event["id"],
    "payload": event["data"]["object"]  # Full object
})
```

### Replay from Stripe Dashboard
1. Go to Stripe Dashboard → Developers → Webhooks
2. Click your webhook endpoint
3. Find failed delivery → "Resend"
4. Or use CLI:
```bash
stripe webhook_retry <delivery_id>
```

### Manual Testing with curl
```bash
# Get a real event from Stripe Dashboard → Webhooks → [event] → "Copy as cURL"
curl -X POST http://localhost:8000/api/v1/billing/webhook \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: <signature_from_stripe>" \
  -d '{"id":"evt_xxx","type":"invoice.payment_failed",...}'
```

## Local Testing Without Stripe CLI

### Using the Test Endpoint (Dev Only)
```bash
# If you added a test endpoint in development
curl -X POST http://localhost:8000/dev/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"type": "invoice.payment_failed", "data": {"object": {"customer": "cus_test", "amount_due": 2000}}}'
```

### Unit Test Webhook Handler
```python
# tests/modules/billing/test_webhooks.py
def test_invoice_payment_failed_webhook(client, db, org_with_subscription, auth_headers):
    from api.modules.billing.models import StripeWebhookEvent
    
    # Create mock event
    event = {
        "id": "evt_test_123",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "customer": org_with_subscription.stripe_customer_id,
                "amount_due": 2000,
                "currency": "usd",
                "id": "in_test_123"
            }
        }
    }
    
    # Sign payload (simplified - use stripe.Webhook.construct_event in real test)
    response = client.post("/api/v1/billing/webhook", json=event)
    assert response.status_code == 200
    
    # Verify idempotency
    assert db.query(StripeWebhookEvent).filter_by(stripe_event_id="evt_test_123").count() == 1
    
    # Verify dunning email queued
    # Verify subscription status = past_due
```

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `No such customer` | Test customer doesn't exist in Stripe | Use `stripe trigger` which creates test objects |
| `Subscription not found` | Local DB out of sync | Run `sync_access` or check webhook order |
| `Portal URL generation failed` | No return URL configured | Set `STRIPE_PORTAL_RETURN_URL` in `.env` |
| `Email not sent` | Mailpit not running / SES config | Check `make docker-up` for Mailpit, or AWS creds |

## Stripe CLI Cheatsheet
```bash
stripe listen --forward-to localhost:8000/api/v1/billing/webhook --print-json
stripe trigger invoice.payment_failed --override customer:cus_xxx
stripe events list --limit 20
stripe webhook_endpoints list
stripe webhook_endpoints delete we_xxx
stripe samples list  # See example integrations
```

## Production Debugging
- Check CloudWatch/DataDog logs for `X-Request-ID` correlation
- Verify `StripeWebhookEvent` table for processed events
- Monitor Stripe Dashboard → Webhooks → Delivery success rate
- Set up alerting on webhook failures (>1% failure rate)