# Production Deployment Instructions

This directory contains the necessary configuration files to deploy the Django application in a production environment.

## 1. Environment Variables

Before deploying, you must set the following environment variables on your production server. These are crucial for security and for enabling the production settings.

```bash
export DJANGO_ENV=production
export DJANGO_SECRET_KEY='your-super-secret-key-here'
```

**Note:** Replace `'your-super-secret-key-here'` with a long, random string. You can generate one using an online tool or with Python:
`python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`

To make these variables permanent, add them to your shell's profile script (e.g., `~/.bashrc` or `~/.profile`) and then run `source ~/.bashrc`.

## 2. Collect Static Files

Before deploying, you need to collect all static files into a single directory. Run the following command from the project's root directory:

```bash
source ../venv/bin/activate
python manage.py collectstatic
```

## 3. Gunicorn Setup

Gunicorn is used as the application server.

### a. Copy Service Files

Copy the `gunicorn.socket` and `gunicorn.service` files to the systemd directory:

```bash
sudo cp gunicorn.socket /etc/systemd/system/
sudo cp gunicorn.service /etc/systemd/system/
```

### b. Start and Enable Gunicorn

Start and enable the Gunicorn socket. This will ensure that Gunicorn starts automatically on boot.

```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```

## 4. Nginx Setup

Nginx is used as a reverse proxy to forward requests to Gunicorn.

### a. Create Symbolic Link

Create a symbolic link from the `didar.conf` file to the `sites-enabled` directory:

```bash
sudo ln -s /opt/didar/production/didar.conf /etc/nginx/sites-enabled/
```

### b. Test and Restart Nginx

Test the Nginx configuration for any syntax errors:

```bash
sudo nginx -t
```

If the test is successful, restart Nginx to apply the changes:

```bash
sudo systemctl restart nginx
```

After completing these steps, the Django application should be running and accessible at https://didar.kolang2.ir.