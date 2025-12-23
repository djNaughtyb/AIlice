# 🤖 AIlice Platform - Deployment Package

> **Fully Autonomous AI Agent System with Real-World Capabilities**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/ailice)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)

---

## 🚀 Quick Start

### One-Command Installation

**Unix/Linux/macOS:**
```bash
chmod +x quick-install.sh && ./quick-install.sh
```

**Windows:**
```batch
Right-click quick-install.bat → Run as Administrator
```

**Docker Compose (Fastest):**
```bash
chmod +x docker-compose-start.sh && ./docker-compose-start.sh
```

---

## 📦 What's Included

This deployment package contains everything you need to run AIlice on your infrastructure:

### 🎯 Deployment Scripts
- ✅ `deploy-to-gcloud.sh` - Google Cloud Run deployment (Project: eighth-beacon-479707-c3)
- ✅ `deploy-to-hostinger.sh` - Hostinger VPS automated setup
- ✅ `install-mac.sh` - macOS local installer
- ✅ `install-windows.ps1` - Windows PowerShell installer
- ✅ `quick-install.sh` / `quick-install.bat` - Universal quick installers

### 🐳 Docker Support
- ✅ `docker-compose.yml` - Complete Docker Compose setup
- ✅ `docker-compose-start.sh` - Easy Docker startup script
- ✅ `Dockerfile` - Production-ready container image
- ✅ `.env.example` - Environment configuration template

### 📚 Documentation
- ✅ `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- ✅ `DEPLOYMENT_OPTIONS.md` - Comparison of all deployment methods
- ✅ `README_DEPLOYMENT.md` - This file
- ✅ Configuration examples and guides

### 🛠️ Application Files
- ✅ Complete AIlice application source code
- ✅ FastAPI server (`fastapi_app.py`)
- ✅ Cloud Run adapter (`cloud_run_app.py`)
- ✅ All dependencies (`requirements.txt`)
- ✅ Configuration files (`config.json`, `capabilities_config.json`)
- ✅ Admin dashboard and API documentation

---

## 🎯 Choose Your Deployment Method

### 1. 🐳 Docker Compose (Recommended for Quick Start)
**Best for:** Development, testing, quick production deployments

```bash
# Quick start
./docker-compose-start.sh

# Or manually
docker-compose up -d
```

**Access at:** http://localhost:8080

**Time to deploy:** 5 minutes

---

### 2. ☁️ Google Cloud Run (Recommended for Production)
**Best for:** Scalable production deployments

**Project Details:**
- Project ID: `eighth-beacon-479707-c3`
- Service Name: `viralspark-ailice`
- Auto-scaling, managed infrastructure

```bash
chmod +x deploy-to-gcloud.sh
./deploy-to-gcloud.sh
```

**Features:**
- ✅ Automatic HTTPS
- ✅ Auto-scaling (scales to zero)
- ✅ Cloud SQL PostgreSQL
- ✅ Global deployment
- ✅ $5-20/month (light usage)

**Time to deploy:** 15 minutes

---

### 3. 🌐 Hostinger VPS
**Best for:** Budget-friendly production hosting

```bash
# Upload to your VPS
scp -r ailice-deployment-package root@your-vps-ip:/root/

# SSH and deploy
ssh root@your-vps-ip
cd /root/ailice-deployment-package
chmod +x deploy-to-hostinger.sh
./deploy-to-hostinger.sh
```

**Features:**
- ✅ Full control
- ✅ Fixed costs ($10-30/month)
- ✅ Nginx + SSL setup
- ✅ Docker or native deployment

**Time to deploy:** 30 minutes

---

### 4. 🍎 macOS Local Installation
**Best for:** Development on Mac

```bash
chmod +x install-mac.sh
./install-mac.sh
```

**Features:**
- ✅ Homebrew auto-install
- ✅ PostgreSQL setup
- ✅ Launch scripts
- ✅ Auto-start option

**Time to deploy:** 15 minutes

---

### 5. 🪟 Windows Local Installation
**Best for:** Development on Windows

```powershell
Right-click install-windows.ps1 → Run with PowerShell
```

**Features:**
- ✅ Chocolatey auto-install
- ✅ PostgreSQL setup
- ✅ Desktop shortcut
- ✅ Windows service option

**Time to deploy:** 15 minutes

---

## 📊 Comparison Table

| Method | Difficulty | Cost | Production | Auto-scaling | Setup Time |
|--------|-----------|------|------------|--------------|------------|
| Docker Compose | ⭐ Easy | Free | ✅ Yes | ❌ No | 5 min |
| Google Cloud Run | ⭐⭐ Moderate | $5-20/mo | ✅ Yes | ✅ Yes | 15 min |
| Hostinger VPS | ⭐⭐⭐ Advanced | $10-30/mo | ✅ Yes | ❌ No | 30 min |
| macOS Local | ⭐⭐ Moderate | Free | ❌ No | ❌ No | 15 min |
| Windows Local | ⭐⭐ Moderate | Free | ❌ No | ❌ No | 15 min |

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql://ailice:password@localhost:5432/ailice_db

# Application
ENVIRONMENT=production
PORT=8080
HOST=0.0.0.0

# CORS
CORS_ORIGINS=*

# Optional: API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Model Configuration

Edit `config.json` to configure AI models:

```json
{
  "agentModelConfig": {
    "default": "ollama:gemma3:27b",
    "researcher": "cloud:deepseek-v3.1:671b-cloud",
    "coder": "ollama:qwen3-coder:30b"
  }
}
```

---

## 🎨 Features

### Core Capabilities
- 🤖 **Multiple AI Agents** - 30+ specialized agents for different tasks
- 🔍 **Web Automation** - Scraping, browsing, and data extraction
- 📱 **Social Media Integration** - Twitter, LinkedIn, Instagram posting
- ☁️ **Cloud Management** - AWS, GCP, DigitalOcean integration
- 📊 **Admin Dashboard** - Monitor and manage agents
- 🔒 **Secure API** - Authentication and rate limiting
- 📝 **API Documentation** - Auto-generated Swagger UI

### Agent Capabilities
- Content Creation
- SEO Optimization
- Code Development
- Security Analysis
- DevOps Automation
- Research and Analysis
- And much more!

---

## 📚 Documentation

### Detailed Guides
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Step-by-step deployment instructions
- **[DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)** - Detailed comparison of all methods

### Quick Links
- **Admin Dashboard:** http://localhost:8080/admin/dashboard
- **API Documentation:** http://localhost:8080/docs
- **Health Check:** http://localhost:8080/health

---

## 🔍 Access Points

After deployment, access your platform at:

### Local Deployment
- **Home:** http://localhost:8080
- **Dashboard:** http://localhost:8080/admin/dashboard
- **API Docs:** http://localhost:8080/docs
- **Health:** http://localhost:8080/health

### Cloud Deployment
- URLs provided after deployment
- Automatic HTTPS (Cloud Run)
- Custom domain support

---

## 🐛 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find and kill process
lsof -i :8080              # macOS/Linux
netstat -ano | findstr :8080  # Windows
```

**Database connection failed:**
```bash
# Check PostgreSQL status
ps aux | grep postgres     # macOS/Linux
sc query postgresql        # Windows
```

**Docker issues:**
```bash
# Rebuild everything
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Getting Help

1. **Check logs:**
   - Docker: `docker-compose logs -f`
   - Native: `tail -f logs/ailice.log`

2. **Verify installation:**
   - Python: `python --version` (need 3.10+)
   - PostgreSQL: `psql --version` (need 15+)
   - Docker: `docker --version`

3. **Health check:**
   ```bash
   curl http://localhost:8080/health
   ```

---

## 🔐 Security

### Best Practices

1. **Change default passwords:**
   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

2. **Enable HTTPS:**
   - Cloud Run: Automatic
   - Hostinger: Included in script
   - Local: Use reverse proxy

3. **Firewall setup:**
   ```bash
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

4. **Never commit secrets:**
   - Add `.env` to `.gitignore`
   - Use secret management in production

---

## 📦 Backup and Recovery

### Database Backup

```bash
# Backup
pg_dump -U ailice ailice_db > backup.sql

# Restore
psql -U ailice ailice_db < backup.sql

# Docker backup
docker-compose exec postgres pg_dump -U ailice ailice_db > backup.sql
```

### Full Backup

```bash
tar -czf ailice_backup_$(date +%Y%m%d).tar.gz \
  ~/AIlice/ \
  --exclude='venv' \
  --exclude='__pycache__'
```

---

## 🚀 Performance Optimization

### Production Settings

1. **Increase workers:**
   ```python
   # Edit fastapi_app.py
   uvicorn.run("fastapi_app:app", workers=4)
   ```

2. **Database optimization:**
   ```sql
   CREATE INDEX idx_created_at ON your_table(created_at);
   VACUUM ANALYZE;
   ```

3. **Resource limits:**
   ```yaml
   # docker-compose.yml
   services:
     ailice:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

---

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (Nginx, HAProxy)
- Multiple AIlice instances
- Database replication

### Vertical Scaling
- Increase CPU/RAM
- Faster storage (SSD)
- Connection pooling

---

## 🔄 Updates

### Update Application

**Docker:**
```bash
docker-compose pull
docker-compose up -d
```

**Native:**
```bash
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart ailice
```

**Cloud Run:**
```bash
./deploy-to-gcloud.sh
```

---

## 🎯 Migration

### From Local to Cloud

1. Export database:
   ```bash
   pg_dump ailice_db > backup.sql
   ```

2. Deploy to cloud:
   ```bash
   ./deploy-to-gcloud.sh
   ```

3. Import database:
   ```bash
   psql ailice_db < backup.sql
   ```

---

## 💡 Tips and Tricks

### Development Workflow

1. **Local development:**
   - Use Docker Compose or native installation
   - Fast iteration
   - Full debugging

2. **Staging:**
   - Deploy to Hostinger VPS
   - Test in production-like environment

3. **Production:**
   - Deploy to Google Cloud Run
   - Auto-scaling and high availability

### Monitoring

- Health endpoint: `/health`
- Metrics endpoint: `/metrics`
- Logs: Check platform-specific logs

---

## 📞 Support

### Resources
- **Documentation:** See `DEPLOYMENT_GUIDE.md`
- **API Reference:** http://localhost:8080/docs
- **Configuration:** Edit `config.json`

### Community
- **GitHub:** Report issues and contribute
- **Discussions:** Ask questions

### Commercial Support
- **Email:** support@ailice.platform
- **Website:** https://ailice.platform

---

## 📄 License

Please refer to the LICENSE file in the repository.

---

## 🙏 Acknowledgments

Thank you for choosing AIlice Platform!

### Built With
- **FastAPI** - Modern web framework
- **PostgreSQL** - Reliable database
- **Docker** - Containerization
- **Uvicorn** - ASGI server
- **SQLAlchemy** - Database ORM

---

## 📝 Changelog

### Version 1.0.0 (Current)
- ✅ Multiple deployment options
- ✅ Docker Compose support
- ✅ Google Cloud Run ready
- ✅ Hostinger VPS automation
- ✅ macOS installer
- ✅ Windows installer
- ✅ Comprehensive documentation
- ✅ Admin dashboard
- ✅ API documentation
- ✅ Health checks
- ✅ Rate limiting
- ✅ Authentication

---

## 🚦 Next Steps

1. **Choose your deployment method** from the options above
2. **Read the relevant documentation** in `DEPLOYMENT_GUIDE.md`
3. **Run the installer** for your chosen method
4. **Access the admin dashboard** and start using AIlice!

---

## ⚡ Quick Reference

### Essential Commands

**Docker:**
```bash
docker-compose up -d        # Start
docker-compose down         # Stop
docker-compose logs -f      # View logs
docker-compose restart      # Restart
```

**Native (macOS/Linux):**
```bash
./start_ailice.sh          # Start
./stop_ailice.sh           # Stop
tail -f logs/ailice.log    # View logs
```

**Windows:**
```batch
start_ailice.bat           # Start
stop_ailice.bat            # Stop
```

**Cloud:**
```bash
gcloud run services list                                    # List services
gcloud run services logs read viralspark-ailice            # View logs
gcloud run services update viralspark-ailice               # Update
```

---

**Ready to deploy? Choose your method above and get started! 🚀**

---

*For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)*

*For comparison of methods, see [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)*
