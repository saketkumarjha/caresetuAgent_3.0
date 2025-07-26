# CareSetu Voice Agent - AWS EC2 Deployment Guide

This guide will help you deploy your CareSetu Voice Agent on AWS EC2 with Nginx as a reverse proxy.

## Prerequisites

- AWS Account with EC2 access
- Domain name (optional, for SSL)
- LiveKit Cloud account and credentials

## Deployment Steps

### 1. Launch EC2 Instance

1. **Create EC2 Instance:**

   - Instance Type: `t3.medium` or higher (recommended for voice processing)
   - AMI: Ubuntu 22.04 LTS
   - Storage: 20GB+ SSD
   - Security Group: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (app)

2. **Connect to Instance:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

### 2. Server Setup

1. **Update System:**

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Dependencies:**

   ```bash
   # Install Python 3.11
   sudo apt install python3.11 python3.11-venv python3-pip -y

   # Install Nginx
   sudo apt install nginx -y

   # Install Git
   sudo apt install git -y

   # Install system dependencies for audio processing
   sudo apt install ffmpeg portaudio19-dev -y
   ```

### 3. Application Deployment

1. **Clone Repository:**

   ```bash
   cd /opt
   sudo git clone https://github.com/your-username/caresetuAgent_3.0.git
   sudo chown -R ubuntu:ubuntu caresetuAgent_3.0
   cd caresetuAgent_3.0
   ```

2. **Setup Python Environment:**

   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment:**

   ```bash
   cp .env.example .env
   nano .env
   ```

   Update with your credentials:

   ```
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your-api-key
   LIVEKIT_API_SECRET=your-api-secret
   ASSEMBLYAI_API_KEY=your-key
   GOOGLE_API_KEY=your-key
   # Add other required API keys
   ```

### 4. Nginx Configuration

1. **Create Nginx Config:**

   ```bash
   sudo nano /etc/nginx/sites-available/caresetu-agent
   ```

2. **Add Configuration:**

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # Replace with your domain or EC2 IP

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_cache_bypass $http_upgrade;
           proxy_read_timeout 86400;
       }
   }
   ```

3. **Enable Site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/caresetu-agent /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### 5. SSL Setup (Optional but Recommended)

1. **Install Certbot:**

   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```

2. **Get SSL Certificate:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

### 6. Service Setup

1. **Create Systemd Service:**

   ```bash
   sudo nano /etc/systemd/system/caresetu-agent.service
   ```

2. **Add Service Configuration:**

   ```ini
   [Unit]
   Description=CareSetu Voice Agent
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/opt/caresetuAgent_3.0
   Environment=PATH=/opt/caresetuAgent_3.0/venv/bin
   ExecStart=/opt/caresetuAgent_3.0/venv/bin/python main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Start Service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable caresetu-agent
   sudo systemctl start caresetu-agent
   ```

### 7. Verification

1. **Check Service Status:**

   ```bash
   sudo systemctl status caresetu-agent
   ```

2. **Check Nginx Status:**

   ```bash
   sudo systemctl status nginx
   ```

3. **Test Application:**
   ```bash
   curl http://your-domain.com/health
   ```

## Monitoring & Maintenance

### Log Management

1. **View Application Logs:**

   ```bash
   sudo journalctl -u caresetu-agent -f
   ```

2. **View Nginx Logs:**
   ```bash
   sudo tail -f /var/log/nginx/access.log
   sudo tail -f /var/log/nginx/error.log
   ```

### Performance Monitoring

1. **Install Monitoring Tools:**

   ```bash
   sudo apt install htop iotop -y
   ```

2. **Monitor Resources:**
   ```bash
   htop  # CPU and memory usage
   df -h # Disk usage
   ```

### Backup Strategy

1. **Backup Application:**

   ```bash
   sudo tar -czf /backup/caresetu-$(date +%Y%m%d).tar.gz /opt/caresetuAgent_3.0
   ```

2. **Backup Database (if applicable):**
   ```bash
   # Add database backup commands as needed
   ```

## Scaling & Load Balancing

### Horizontal Scaling

1. **Launch Additional EC2 Instances**
2. **Setup Load Balancer (ALB)**
3. **Configure Auto Scaling Group**

### Vertical Scaling

1. **Stop Application:**

   ```bash
   sudo systemctl stop caresetu-agent
   ```

2. **Resize EC2 Instance**
3. **Restart Application:**
   ```bash
   sudo systemctl start caresetu-agent
   ```

## Security Best Practices

1. **Firewall Configuration:**

   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 'Nginx Full'
   ```

2. **Regular Updates:**

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **SSL/TLS Configuration:**
   - Use strong SSL ciphers
   - Enable HSTS headers
   - Regular certificate renewal

## Troubleshooting

### Common Issues

1. **Service Won't Start:**

   ```bash
   sudo journalctl -u caresetu-agent --no-pager
   ```

2. **Nginx Configuration Errors:**

   ```bash
   sudo nginx -t
   ```

3. **SSL Certificate Issues:**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

### Performance Issues

1. **High CPU Usage:**

   - Monitor with `htop`
   - Consider upgrading instance type
   - Optimize application code

2. **Memory Issues:**
   - Check memory usage with `free -h`
   - Add swap space if needed
   - Optimize application memory usage

## Frontend Integration

Update your frontend to connect to your deployed agent:

```javascript
const LIVEKIT_URL = "wss://your-project.livekit.cloud";
const AGENT_URL = "https://your-domain.com"; // Your EC2 deployment
```

## Cost Optimization

1. **Use Reserved Instances** for predictable workloads
2. **Enable CloudWatch** for monitoring
3. **Set up Auto Scaling** to handle traffic spikes
4. **Use Spot Instances** for development environments

## Support Resources

- **AWS Documentation**: https://docs.aws.amazon.com/ec2/
- **Nginx Documentation**: https://nginx.org/en/docs/
- **LiveKit Documentation**: https://docs.livekit.io/
- **Ubuntu Server Guide**: https://ubuntu.com/server/docs
