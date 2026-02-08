# Redirect gliacloud.online → gliacloud.com (301)

Redirect này **chạy trên VPS** tại reverse proxy (Nginx hoặc Caddy), không phải trong ứng dụng Docker.

## Yêu cầu

- **DNS**: `gliacloud.online` và `www.gliacloud.online` phải trỏ **A record** về **IP của VPS** (cùng VPS đang chạy Nginx/Caddy).

## Nginx

1. Copy file `redirect-gliacloud-online-to-com.nginx.conf` lên VPS (ví dụ `/etc/nginx/sites-available/redirect-gliacloud.conf`).
2. Tạo symlink vào `sites-enabled`:
   ```bash
   sudo ln -s /etc/nginx/sites-available/redirect-gliacloud.conf /etc/nginx/sites-enabled/
   ```
3. Lấy SSL cho domain (để redirect HTTPS → HTTPS):
   ```bash
   sudo certbot --nginx -d gliacloud.online -d www.gliacloud.online
   ```
4. Kiểm tra và reload:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

Sau đó khi khách gõ `http://gliacloud.online` hoặc `https://gliacloud.online` (và www) sẽ nhận **301** tới `https://gliacloud.com` (giữ nguyên path và query).

## Caddy

Thêm vào Caddyfile (trên VPS):

```
gliacloud.online, www.gliacloud.online {
    redir https://gliacloud.com{uri} permanent
}
```

Reload Caddy (ví dụ `sudo systemctl reload caddy` hoặc `caddy reload`).
