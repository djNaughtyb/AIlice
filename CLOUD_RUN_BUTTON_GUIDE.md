# 🚀 Cloud Run One-Click Deployment Guide

This guide will walk you through deploying AIlice to Google Cloud Run using the one-click deployment button.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1: Prepare Your Google Cloud Project](#step-1-prepare-your-google-cloud-project)
- [Step 2: Set Up PostgreSQL Database](#step-2-set-up-postgresql-database)
- [Step 3: Configure Stripe](#step-3-configure-stripe)
- [Step 4: Gather API Keys](#step-4-gather-api-keys)
- [Step 5: Click the Deploy Button](#step-5-click-the-deploy-button)
- [Step 6: Configure Environment Variables](#step-6-configure-environment-variables)
- [Step 7: Post-Deployment Setup](#step-7-post-deployment-setup)
- [Troubleshooting](#troubleshooting)
- [Manual Deployment (Alternative)](#manual-deployment-alternative)

---

## Prerequisites

Before you start, ensure you have:

1. **Google Cloud Account**
   - Active billing account
   - Owner or Editor role on a project
   - Cloud Run API enabled

2. **Database**
   - PostgreSQL database (Cloud SQL recommended)
   - Connection string ready

3. **Payment Processing**
   - Stripe account ([sign up here](https://dashboard.stripe.com/register))
   - Stripe API keys (test or live mode)

4. **AI API Keys** (Optional but recommended)
   - [OpenAI API Key](https://platform.openai.com/api-keys)
   - [Google Gemini API Key](https://makersuite.google.com/app/apikey)
   - [Replicate API Token](https://replicate.com/account/api-tokens)

---

## Step 1: Prepare Your Google Cloud Project

### 1.1 Create or Select a Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown at the top
3. Click "NEW PROJECT" or select an existing project
4. Note your Project ID (e.g., `eighth-beacon-479707-c3`)

### 1.2 Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

Or enable via console:
- Cloud Run API
- Cloud Build API
- Cloud SQL Admin API
- Secret Manager API

### 1.3 Set Up Billing

Ensure billing is enabled for your project:
- Navigate to **Billing** in the console
- Link a billing account to your project

---

## Step 2: Set Up PostgreSQL Database

### Option A: Cloud SQL (Recommended)

1. **Create a Cloud SQL Instance**

```bash
gcloud sql instances create ailice-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=YOUR_ROOT_PASSWORD
```

2. **Create Database**

```bash
gcloud sql databases create ailice --instance=ailice-db
```

3. **Create User**

```bash
gcloud sql users create ailice-user \
  --instance=ailice-db \
  --password=YOUR_PASSWORD
```

4. **Get Connection Name**

```bash
gcloud sql instances describe ailice-db --format="value(connectionName)"
# Output: PROJECT_ID:REGION:INSTANCE_NAME
```

5. **Build Connection String**

```
postgresql://ailice-user:YOUR_PASSWORD@/ailice?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

Or for external connection:
```
postgresql://ailice-user:YOUR_PASSWORD@INSTANCE_IP:5432/ailice
```

### Option B: External Database

If you're using an external PostgreSQL database (e.g., AWS RDS, DigitalOcean, Heroku):

```
postgresql://username:password@host:5432/database_name
```

**Important:** Ensure your database allows connections from Google Cloud IPs.

---

## Step 3: Configure Stripe

### 3.1 Create a Stripe Account

1. Sign up at [stripe.com](https://stripe.com)
2. Complete account verification

### 3.2 Get API Keys

1. Go to [Stripe Dashboard → API Keys](https://dashboard.stripe.com/apikeys)
2. Copy your **Secret Key** (starts with `sk_test_` or `sk_live_`)
3. **Important:** Keep this key secure!

### 3.3 Create Subscription Product

1. Go to [Products](https://dashboard.stripe.com/products)
2. Click "Add product"
3. Set:
   - Name: "AIlice Premium Subscription"
   - Price: $49.99 USD / month (or your preferred amount)
   - Billing period: Monthly
4. Note the **Product ID** (starts with `prod_`)
5. Note the **Price ID** (starts with `price_`)

### 3.4 Webhook Setup (After Deployment)

**You'll need to do this AFTER deployment** to get your service URL:

1. Go to [Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Set endpoint URL: `https://YOUR-SERVICE-URL.run.app/webhooks/stripe`
4. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the **Signing Secret** (starts with `whsec_`)

---

## Step 4: Gather API Keys

### OpenAI (Optional)

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

### Google Gemini (Optional)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Copy the key

### Replicate (Optional)

1. Go to [Replicate Account](https://replicate.com/account/api-tokens)
2. Create a new token
3. Copy the token

### Twitter/X API (Optional)

If you want social media integration:
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create an app
3. Get API Key, API Secret, Access Token, Access Secret

---

## Step 5: Click the Deploy Button

### 5.1 Start Deployment

1. Go to the [AIlice GitHub Repository](https://github.com/djNaughtyb/AIlice)
2. Click the **"Run on Google Cloud"** button in the README
3. You'll be redirected to Google Cloud Console

### 5.2 Deployment Configuration

The Cloud Run deployment wizard will appear:

1. **Select Project**
   - Choose your Google Cloud project

2. **Select Region**
   - Recommended: `us-central1` (Iowa)
   - Or choose a region close to your users

3. **Service Name**
   - Default: `viralspark-ailice`
   - Or customize as needed

4. **Configure Build**
   - The wizard will automatically detect the Dockerfile
   - Build will start automatically

### 5.3 Monitor Build

- The build process takes **5-10 minutes**
- You'll see progress in the Cloud Build logs
- Wait for "BUILD SUCCESS" message

---

## Step 6: Configure Environment Variables

### 6.1 During Deployment

The deployment wizard will prompt you for environment variables. Fill in:

#### Required Variables

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Auto-generated | Secret key for JWT tokens (auto-generated) |
| `STRIPE_SECRET_KEY` | `sk_test_...` or `sk_live_...` | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Stripe webhook signing secret (add later) |

#### Stripe Configuration (Optional)

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `STRIPE_PRICE_ID` | `price_1Sblz7LZxEDQErW5uQyWN5F3` | Your Stripe price ID |
| `STRIPE_PRODUCT_ID` | `prod_TYtmG0y2uNXjSU` | Your Stripe product ID |

#### AI API Keys (Optional)

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `OPENAI_API_KEY` | `sk-...` | OpenAI API key |
| `GEMINI_API_KEY` | `AI...` | Google Gemini API key |
| `GOOGLE_API_KEY` | `AI...` | Google API key |
| `REPLICATE_API_TOKEN` | `r8_...` | Replicate API token |

#### Social Media (Optional)

| Variable | Description |
|----------|-------------|
| `TWITTER_API_KEY` | Twitter API key |
| `TWITTER_API_SECRET` | Twitter API secret |
| `TWITTER_ACCESS_TOKEN` | Twitter access token |
| `TWITTER_ACCESS_SECRET` | Twitter access secret |

#### Other Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `ENVIRONMENT` | `production` | Environment mode |
| `AILICE_TEMPERATURE` | `0.0` | AI model temperature |

### 6.2 After Deployment

To update environment variables later:

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service (`viralspark-ailice`)
3. Click "EDIT & DEPLOY NEW REVISION"
4. Scroll to "Container, Variables & Secrets"
5. Update variables
6. Click "DEPLOY"

---

## Step 7: Post-Deployment Setup

### 7.1 Get Your Service URL

After deployment completes:

1. Go to Cloud Run Console
2. Click on your service
3. Copy the service URL (e.g., `https://viralspark-ailice-xxx-uc.a.run.app`)

### 7.2 Set Up Stripe Webhook

Now that you have your service URL:

1. Go to [Stripe Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Set endpoint URL: `https://YOUR-SERVICE-URL/webhooks/stripe`
4. Select the events listed in Step 3.4
5. Copy the **Signing Secret** (`whsec_...`)

6. Update your Cloud Run service:
   - Go to Cloud Run Console
   - Edit & Deploy New Revision
   - Add/Update `STRIPE_WEBHOOK_SECRET` with the signing secret
   - Deploy

### 7.3 Initialize Database

The FastAPI app should automatically create tables on first run, but if needed:

1. Connect to your database
2. Run migrations or create tables manually

### 7.4 Test the Deployment

#### Health Check

```bash
curl https://YOUR-SERVICE-URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-22T..."
}
```

#### Test Authentication

```bash
curl -X POST https://YOUR-SERVICE-URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

#### Test API Documentation

Visit: `https://YOUR-SERVICE-URL/docs`

You should see the FastAPI interactive documentation.

### 7.5 Set Up Custom Domain (Optional)

1. Go to Cloud Run Console
2. Click on your service
3. Click "MANAGE CUSTOM DOMAINS"
4. Follow the wizard to add your domain
5. Update DNS records as instructed

---

## Troubleshooting

### Build Fails

**Issue:** Cloud Build fails with "permission denied" or "quota exceeded"

**Solution:**
- Ensure billing is enabled
- Check Cloud Build API is enabled
- Verify you have sufficient quota

### Database Connection Fails

**Issue:** Service fails to start with database connection errors

**Solution:**
- Verify `DATABASE_URL` format is correct
- For Cloud SQL: Ensure Cloud SQL connections are enabled
- Check database user has proper permissions
- Test connection string manually

### Stripe Webhooks Not Working

**Issue:** Stripe events not being processed

**Solution:**
- Verify `STRIPE_WEBHOOK_SECRET` is set correctly
- Check webhook endpoint URL is correct
- Review Stripe webhook logs in dashboard
- Ensure webhook events are selected

### Service Won't Start

**Issue:** Cloud Run service fails to start

**Solution:**
- Check Cloud Run logs: `gcloud run services logs read viralspark-ailice`
- Verify all required environment variables are set
- Check health check endpoint is responding
- Review application logs for errors

### Out of Memory Errors

**Issue:** Container crashes with OOM errors

**Solution:**
- Increase memory allocation to 4Gi:
  ```bash
  gcloud run services update viralspark-ailice \
    --memory 4Gi \
    --region us-central1
  ```

### High Latency

**Issue:** API responses are slow

**Solution:**
- Increase CPU allocation to 2 or 4 CPUs
- Set minimum instances to avoid cold starts:
  ```bash
  gcloud run services update viralspark-ailice \
    --min-instances 1 \
    --region us-central1
  ```

---

## Manual Deployment (Alternative)

If the button doesn't work, you can deploy manually:

### 1. Clone Repository

```bash
git clone https://github.com/djNaughtyb/AIlice.git
cd AIlice
git checkout enhanced-sync
```

### 2. Set Environment Variables

Create a `.env.yaml` file:

```yaml
DATABASE_URL: postgresql://user:pass@host/db
JWT_SECRET_KEY: your-jwt-secret
STRIPE_SECRET_KEY: sk_test_...
STRIPE_WEBHOOK_SECRET: whsec_...
GEMINI_API_KEY: your-gemini-key
REPLICATE_API_TOKEN: your-replicate-token
OPENAI_API_KEY: your-openai-key
```

### 3. Build and Deploy

```bash
# Set your project ID
export PROJECT_ID=eighth-beacon-479707-c3
export REGION=us-central1

# Build the container
gcloud builds submit --tag gcr.io/$PROJECT_ID/viralspark-ailice

# Deploy to Cloud Run
gcloud run deploy viralspark-ailice \
  --image gcr.io/$PROJECT_ID/viralspark-ailice \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 100 \
  --port 8080 \
  --env-vars-file .env.yaml
```

### 4. Get Service URL

```bash
gcloud run services describe viralspark-ailice \
  --region $REGION \
  --format "value(status.url)"
```

---

## Cost Estimation

### Cloud Run Costs

**With default configuration:**
- Memory: 2 GiB
- CPU: 2 vCPUs
- Max instances: 100
- Min instances: 0 (pay only when used)

**Estimated monthly cost:**
- Low traffic (<10k requests): **$5-15/month**
- Medium traffic (100k requests): **$30-50/month**
- High traffic (1M+ requests): **$100-300/month**

### Cloud SQL Costs

- **db-f1-micro**: ~$7/month
- **db-g1-small**: ~$25/month
- **db-custom-2-7680**: ~$100/month

### Total Estimated Cost

- **Starter**: $15-25/month (Cloud Run + small DB)
- **Production**: $50-150/month (with moderate traffic)
- **Enterprise**: $200-500/month (high traffic + large DB)

---

## Security Best Practices

1. **Use Secret Manager**
   - Store sensitive values in Secret Manager instead of environment variables
   - Reference secrets in Cloud Run

2. **Enable HTTPS Only**
   - Cloud Run enforces HTTPS by default
   - Never expose plain HTTP endpoints

3. **Restrict CORS Origins**
   - Set specific allowed origins instead of `*`
   - Update `CORS_ORIGINS` environment variable

4. **Use IAM Roles**
   - Don't use "allow unauthenticated" for production
   - Set up proper IAM roles and authentication

5. **Rotate Secrets Regularly**
   - Change JWT secret keys periodically
   - Rotate API keys every 90 days

6. **Monitor Logs**
   - Set up logging and monitoring
   - Create alerts for errors and anomalies

---

## Next Steps

After successful deployment:

1. **Configure AI Models**
   - Update `config.json` with your preferred models
   - Set up Ollama instance if using local models

2. **Set Up Monitoring**
   - Enable Cloud Monitoring
   - Create dashboards for key metrics

3. **Configure Backups**
   - Set up automated database backups
   - Export important data regularly

4. **Scale Settings**
   - Adjust min/max instances based on traffic
   - Configure autoscaling parameters

5. **Custom Branding**
   - Update logo and UI assets
   - Customize email templates

---

## Support

Need help? Here are some resources:

- **GitHub Issues**: [Report bugs](https://github.com/djNaughtyb/AIlice/issues)
- **Documentation**: [Full API Docs](https://YOUR-SERVICE-URL/docs)
- **Google Cloud Support**: [Cloud Run Docs](https://cloud.google.com/run/docs)
- **Stripe Support**: [Stripe Docs](https://stripe.com/docs)

---

## Conclusion

Congratulations! 🎉 You've successfully deployed AIlice to Google Cloud Run.

Your AI agent is now:
- ✅ Running on Google Cloud infrastructure
- ✅ Scalable to 100 concurrent instances
- ✅ Processing payments with Stripe
- ✅ Connected to AI models
- ✅ Ready for production use

Happy building! 🚀
