# AIlice Platform API Endpoints Documentation

Complete documentation for all API endpoints in the AIlice platform. All endpoints require authentication unless otherwise noted.

## Table of Contents

1. [Authentication](#authentication)
2. [Billing & Payments](#billing--payments)
3. [Content Management](#content-management)
4. [Media Handling](#media-handling)
5. [File Management](#file-management)
6. [Analytics & Metrics](#analytics--metrics)
7. [Notifications](#notifications)
8. [Search & Discovery](#search--discovery)
9. [AI/ML Inference](#aiml-inference)
10. [Collaboration](#collaboration)
11. [External Integrations](#external-integrations)
12. [System & Admin](#system--admin)

---

## Authentication

### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### POST /api/auth/login
Login to an existing account.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### GET /api/auth/me
Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "role": "user",
  "created_at": "2024-01-01T00:00:00"
}
```

### POST /api/auth/logout
Logout current user.

**Response:** `200 OK`

---

## Billing & Payments

### POST /api/billing/checkout
Create a Stripe checkout session for subscription.

**Request Body:**
```json
{
  "success_url": "https://your-app.com/success",
  "cancel_url": "https://your-app.com/cancel"
}
```

**Response:** `200 OK`
```json
{
  "session_id": "cs_test_...",
  "url": "https://checkout.stripe.com/..."
}
```

### GET /api/billing/subscription
Get current user's subscription details.

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "active",
  "current_period_start": "2024-01-01T00:00:00",
  "current_period_end": "2024-02-01T00:00:00",
  "cancel_at_period_end": false,
  "price": 49.99,
  "currency": "usd"
}
```

### POST /api/billing/subscription/cancel
Cancel current subscription.

**Query Parameters:**
- `cancel_immediately` (boolean): Cancel immediately vs. at period end

**Response:** `200 OK`

### POST /api/billing/subscription/reactivate
Reactivate a canceled subscription.

**Response:** `200 OK`

### GET /api/billing/invoices
Get user's billing invoices.

**Query Parameters:**
- `limit` (integer): Maximum number of invoices (default: 10)

**Response:** `200 OK`
```json
[
  {
    "id": "in_...",
    "amount_due": 4999,
    "amount_paid": 4999,
    "currency": "usd",
    "status": "paid",
    "created": "2024-01-01T00:00:00",
    "invoice_pdf": "https://...",
    "hosted_invoice_url": "https://..."
  }
]
```

### POST /api/billing/webhook
Stripe webhook endpoint (public, no authentication required).

**Note:** This endpoint is called by Stripe to notify about subscription events.

---

## Content Management

### GET /api/items
List all items for the current user.

**Query Parameters:**
- `item_type` (string): Filter by item type
- `status` (string): Filter by status
- `skip` (integer): Number of items to skip (default: 0)
- `limit` (integer): Maximum items to return (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "string",
    "description": "string",
    "content": {},
    "item_type": "post",
    "status": "published",
    "user_id": 1,
    "metadata": {},
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "published_at": "2024-01-01T00:00:00"
  }
]
```

### POST /api/items
Create a new item.

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "content": {},
  "item_type": "post",
  "status": "draft",
  "metadata": {}
}
```

**Response:** `201 Created`

### GET /api/items/{item_id}
Get a specific item by ID.

**Response:** `200 OK`

### PUT /api/items/{item_id}
Update an existing item.

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "content": {},
  "status": "published"
}
```

**Response:** `200 OK`

### DELETE /api/items/{item_id}
Delete an item.

**Response:** `204 No Content`

---

## Media Handling

### POST /api/media/upload
Upload a media file (video, audio, or image).

**Request:** Multipart form data
- `file`: Media file

**Response:** `201 Created`
```json
{
  "id": 1,
  "filename": "uuid.mp4",
  "original_filename": "video.mp4",
  "file_size": 1024000,
  "mime_type": "video/mp4",
  "media_type": "video",
  "duration": 120,
  "width": 1920,
  "height": 1080,
  "transcoded": false,
  "created_at": "2024-01-01T00:00:00"
}
```

### GET /api/media/{media_id}/stream
Stream a media file.

**Response:** `200 OK` (streaming response)

### POST /api/media/{media_id}/transcode
Transcode a media file to a different format.

**Request Body:**
```json
{
  "output_format": "mp4",
  "quality": "medium"
}
```

**Response:** `200 OK`

---

## File Management

### POST /api/files/upload
Upload a file.

**Request:** Multipart form data
- `file`: File to upload
- `description` (optional): File description
- `tags` (optional): Comma-separated tags

**Response:** `201 Created`
```json
{
  "id": 1,
  "filename": "uuid.pdf",
  "original_filename": "document.pdf",
  "file_size": 50000,
  "mime_type": "application/pdf",
  "description": "string",
  "tags": ["tag1", "tag2"],
  "created_at": "2024-01-01T00:00:00"
}
```

### GET /api/files
List all files for the current user.

**Query Parameters:**
- `skip` (integer): Number to skip (default: 0)
- `limit` (integer): Maximum to return (default: 100)

**Response:** `200 OK`

### GET /api/files/{file_id}/download
Download a file.

**Response:** `200 OK` (file download)

### DELETE /api/files/{file_id}
Delete a file.

**Response:** `204 No Content`

---

## Analytics & Metrics

### GET /api/analytics/usage
Get usage statistics for the current user.

**Query Parameters:**
- `days` (integer): Number of days to analyze (1-90, default: 7)

**Response:** `200 OK`
```json
{
  "total_events": 1000,
  "api_calls": 500,
  "page_views": 300,
  "errors": 10,
  "avg_response_time": 150.5,
  "period_start": "2024-01-01T00:00:00",
  "period_end": "2024-01-08T00:00:00"
}
```

### GET /api/analytics/errors
Get error statistics grouped by endpoint.

**Query Parameters:**
- `days` (integer): Number of days (default: 7)
- `limit` (integer): Maximum results (default: 10)

**Response:** `200 OK`
```json
[
  {
    "endpoint": "/api/items",
    "error_count": 5,
    "last_error": "Error message",
    "last_occurred": "2024-01-01T00:00:00"
  }
]
```

### GET /api/analytics/performance
Get performance statistics grouped by endpoint.

**Query Parameters:**
- `days` (integer): Number of days (default: 7)
- `limit` (integer): Maximum results (default: 10)

**Response:** `200 OK`
```json
[
  {
    "endpoint": "/api/items",
    "avg_response_time": 150.5,
    "min_response_time": 50,
    "max_response_time": 500,
    "total_calls": 100
  }
]
```

---

## Notifications

### POST /api/notify/send
Send a notification to a user.

**Request Body:**
```json
{
  "title": "string",
  "message": "string",
  "notification_type": "info",
  "action_url": "https://...",
  "metadata": {}
}
```

**Query Parameters:**
- `user_id` (optional, admin only): Target user ID

**Response:** `201 Created`

### GET /api/notify/history
Get notification history.

**Query Parameters:**
- `unread_only` (boolean): Return only unread (default: false)
- `skip` (integer): Number to skip (default: 0)
- `limit` (integer): Maximum to return (default: 50)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "string",
    "message": "string",
    "notification_type": "info",
    "read": false,
    "action_url": "https://...",
    "metadata": {},
    "created_at": "2024-01-01T00:00:00",
    "read_at": null
  }
]
```

### POST /api/notify/{notification_id}/read
Mark a notification as read.

**Response:** `200 OK`

### POST /api/notify/mark-all-read
Mark all notifications as read.

**Response:** `200 OK`

---

## Search & Discovery

### GET /api/search
Search across all user's content.

**Query Parameters:**
- `q` (required): Search query
- `type` (optional): Filter by type (item, media, file)
- `limit` (integer): Maximum results (default: 20)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "type": "item",
    "title": "string",
    "description": "string",
    "created_at": "2024-01-01T00:00:00",
    "score": 1.0
  }
]
```

### GET /api/recommendations
Get personalized recommendations.

**Query Parameters:**
- `limit` (integer): Maximum recommendations (default: 10)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "type": "item",
    "title": "string",
    "description": "string",
    "reason": "Recently published"
  }
]
```

---

## AI/ML Inference

### POST /api/ai/predict
Run inference on an AI model.

**Request Body:**
```json
{
  "model_id": "openai:gpt-4",
  "input_data": {
    "prompt": "Hello, world!"
  },
  "parameters": {}
}
```

**Supported model providers:**
- `openai:model-name` (e.g., `openai:gpt-4`)
- `google:model-name` (e.g., `google:gemini-pro`)
- `replicate:owner/model-name`

**Response:** `200 OK`
```json
{
  "model_id": "openai:gpt-4",
  "output": "Response from model",
  "metadata": {
    "provider": "openai"
  }
}
```

### POST /api/ai/train
Train a custom AI model (placeholder).

**Request Body:**
```json
{
  "model_name": "string",
  "model_type": "text",
  "base_model": "string",
  "training_data": {},
  "parameters": {}
}
```

**Response:** `200 OK`
```json
{
  "training_id": "1",
  "status": "queued",
  "message": "Training job queued"
}
```

### GET /api/ai/models
List available AI models.

**Query Parameters:**
- `model_type` (optional): Filter by type
- `provider` (optional): Filter by provider

**Response:** `200 OK`

---

## Collaboration

### POST /api/chat/send
Send a chat message to a room.

**Request Body:**
```json
{
  "room_id": "room-123",
  "message": "Hello!",
  "message_type": "text",
  "metadata": {}
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "room_id": "room-123",
  "user_id": 1,
  "username": "user",
  "message": "Hello!",
  "message_type": "text",
  "metadata": {},
  "created_at": "2024-01-01T00:00:00",
  "edited_at": null
}
```

### GET /api/chat/{room_id}
Get chat messages from a room.

**Query Parameters:**
- `skip` (integer): Number to skip (default: 0)
- `limit` (integer): Maximum to return (default: 50)

**Response:** `200 OK`

### POST /api/collab/share
Share a resource with another user or publicly.

**Request Body:**
```json
{
  "resource_type": "item",
  "resource_id": 1,
  "shared_with_user_id": null,
  "permission": "view",
  "expires_in_days": 7
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "resource_type": "item",
  "resource_id": 1,
  "permission": "view",
  "share_token": "uuid",
  "share_url": "https://app.com/shared/uuid",
  "expires_at": "2024-01-08T00:00:00"
}
```

### GET /api/collab/shared
List resources shared by the current user.

**Query Parameters:**
- `resource_type` (optional): Filter by type

**Response:** `200 OK`

---

## External Integrations

### POST /api/integrations/{service}/connect
Connect an external integration.

**Supported services:**
- google_drive
- tradingview
- dropbox
- onedrive
- github
- gitlab
- slack
- discord
- twitter
- linkedin

**Request Body:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "config": {}
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "service_name": "google_drive",
  "connected": true,
  "last_sync": null,
  "sync_status": "idle",
  "error_message": null,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### POST /api/integrations/{service}/sync
Sync data from an integration.

**Request Body:**
```json
{
  "sync_type": "full",
  "options": {}
}
```

**Response:** `200 OK`
```json
{
  "service_name": "google_drive",
  "sync_status": "completed",
  "items_synced": 10,
  "message": "Successfully synced 10 items"
}
```

### GET /api/integrations/{service}/status
Get status of an integration.

**Response:** `200 OK`

### GET /api/integrations
List all integrations.

**Response:** `200 OK`

### DELETE /api/integrations/{service}
Disconnect an integration.

**Response:** `204 No Content`

---

## System & Admin

### GET /api/system/health
System health check (public).

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 86400.0,
  "timestamp": "2024-01-01T00:00:00"
}
```

### GET /api/system/stats
Get system statistics (admin only).

**Response:** `200 OK`
```json
{
  "cpu_percent": 25.5,
  "memory_percent": 60.0,
  "disk_percent": 40.0,
  "python_version": "3.10.0"
}
```

### GET /api/system/config
Get system configuration (admin only).

**Response:** `200 OK`
```json
{
  "environment": "production",
  "debug_mode": false,
  "max_upload_size": 104857600,
  "stripe_enabled": true,
  "redis_enabled": true
}
```

### POST /api/system/restart
Restart the system (admin only).

**Response:** `200 OK`

### GET /api/system/logs
Get recent system logs (admin only).

**Query Parameters:**
- `lines` (integer): Number of log lines (default: 100)

**Response:** `200 OK`

---

## Authentication

All endpoints (except `/api/auth/register`, `/api/auth/login`, `/api/system/health`, and `/api/billing/webhook`) require authentication using a Bearer token:

```
Authorization: Bearer <your_access_token>
```

## Rate Limiting

API requests are rate-limited based on user subscription tier. Free users have lower limits than Pro subscribers.

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message"
}
```

Common status codes:
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File size exceeds limit
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Interactive Documentation

Visit `/docs` for interactive Swagger UI documentation or `/redoc` for ReDoc documentation.

## Stripe Setup

For billing endpoints to work, you need to configure Stripe:

1. Get your API keys from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Set environment variables:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
   - `STRIPE_WEBHOOK_SECRET`
3. Configure webhook endpoint: `https://your-domain.com/api/billing/webhook`

## WebSocket Support

Real-time features like chat use WebSocket connections. (Documentation coming soon)

## Pagination

List endpoints support pagination using `skip` and `limit` parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (varies by endpoint)

---

**Last Updated:** December 2024  
**API Version:** 1.0.0
