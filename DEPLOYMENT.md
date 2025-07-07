# Deployment Guide

This guide covers deploying csDNA to various platforms for production use.

## Prerequisites

- Python 3.8+
- Web server (nginx, Apache)
- Database (PostgreSQL recommended for production)
- SSL certificate for HTTPS

## Production Settings

Create a production settings file:

```python
# csDNA/production_settings.py
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'csdna_db',
        'USER': 'csdna_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files
STATIC_ROOT = '/var/www/csdna/static/'
MEDIA_ROOT = '/var/www/csdna/media/'
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "csDNA.wsgi:application"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./media:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=csDNA.production_settings
    depends_on:
      - db

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=csdna_db
      - POSTGRES_USER=csdna_user
      - POSTGRES_PASSWORD=your_password

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/var/www/static
      - ./media:/var/www/media
    depends_on:
      - web

volumes:
  postgres_data:
```

## Cloud Platforms

### Heroku

1. Install Heroku CLI
2. Create requirements.txt with gunicorn
3. Create Procfile:
   ```
   web: gunicorn csDNA.wsgi:application --log-file -
   ```
4. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku run python manage.py migrate
   ```

### AWS EC2

1. Launch EC2 instance
2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-pip nginx postgresql
   ```
3. Clone repository and set up environment
4. Configure nginx and systemd service
5. Set up SSL with Let's Encrypt

### DigitalOcean

Similar to AWS EC2, but with simplified droplet setup.

## Environment Variables

Create a `.env` file for production:

```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/dbname
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## Performance Optimization

### Database
- Use PostgreSQL for production
- Set up database connection pooling
- Configure appropriate indexes

### Caching
- Implement Redis for session caching
- Use CDN for static files
- Enable browser caching

### Monitoring
- Set up logging with structured logs
- Implement health checks
- Monitor resource usage

## Backup Strategy

### Database Backups
```bash
# Daily database backup
pg_dump csdna_db > backup_$(date +%Y%m%d).sql
```

### Media Files
```bash
# Sync media files to cloud storage
aws s3 sync /var/www/csdna/media/ s3://your-bucket/media/
```

## Security Checklist

- [ ] HTTPS enabled
- [ ] Firewall configured
- [ ] Database secured
- [ ] Regular updates applied
- [ ] Backup system tested
- [ ] Monitoring in place
- [ ] Log analysis configured

## Troubleshooting

### Common Issues

1. **Static files not loading**
   - Check STATIC_ROOT setting
   - Run `python manage.py collectstatic`
   - Verify nginx configuration

2. **Database connection errors**
   - Check database credentials
   - Verify database server is running
   - Test connection manually

3. **Memory issues**
   - Monitor resource usage
   - Optimize image processing
   - Consider scaling horizontally

## Maintenance

### Regular Tasks
- Update dependencies monthly
- Monitor logs daily
- Test backups weekly
- Review security monthly

For additional support, check the main README or open an issue on GitHub.