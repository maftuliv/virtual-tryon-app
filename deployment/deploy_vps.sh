#!/bin/bash
# Quick deployment script for VPS (Ubuntu/Debian)

echo "======================================"
echo "  Virtual Try-On VPS Deployment"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "[1/8] Updating system..."
apt update && apt upgrade -y

# Install dependencies
echo "[2/8] Installing dependencies..."
apt install -y python3 python3-pip python3-venv nginx git curl

# Create directory
echo "[3/8] Creating application directory..."
mkdir -p /var/www
cd /var/www

# Clone or copy project
echo "[4/8] Setting up project..."
if [ -d "virtual-tryon-app" ]; then
    echo "Directory exists, pulling latest changes..."
    cd virtual-tryon-app
    git pull || echo "Not a git repo, skipping..."
else
    echo "Please copy your project to /var/www/virtual-tryon-app"
    echo "Or clone from Git: git clone YOUR_REPO_URL virtual-tryon-app"
    exit 1
fi

cd /var/www/virtual-tryon-app

# Create virtual environment
echo "[5/8] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "[6/8] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create log directories
echo "[7/8] Creating log directories..."
mkdir -p /var/log/tryon
chown www-data:www-data /var/log/tryon

# Set permissions
echo "[8/8] Setting permissions..."
chown -R www-data:www-data /var/www/virtual-tryon-app

# Copy and enable systemd service
echo "Setting up systemd service..."
cp deployment/systemd.service /etc/systemd/system/tryon.service
systemctl daemon-reload
systemctl enable tryon
systemctl start tryon

# Copy and enable nginx config
echo "Setting up Nginx..."
cp deployment/nginx.conf /etc/nginx/sites-available/tryon
ln -sf /etc/nginx/sites-available/tryon /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

echo ""
echo "======================================"
echo "  Deployment Complete!"
echo "======================================"
echo ""
echo "Service status:"
systemctl status tryon --no-pager
echo ""
echo "Next steps:"
echo "1. Update Nginx config with your domain:"
echo "   nano /etc/nginx/sites-available/tryon"
echo ""
echo "2. Install SSL certificate:"
echo "   certbot --nginx -d your-domain.com"
echo ""
echo "3. Check logs:"
echo "   journalctl -u tryon -f"
echo ""
