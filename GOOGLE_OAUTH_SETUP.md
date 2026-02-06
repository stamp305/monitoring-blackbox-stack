# Google OAuth Setup Instructions

## Overview
This monitoring stack now supports Google OAuth authentication with role-based access control.

## User Roles
- **Admin**: `wachirachet@mfu.ac.th` + traditional login `admin:13678`
- **Viewer**: All other users from allowed domains (`mfu.ac.th`, `lamduan.mfu.ac.th`, `maf.ac.th`)

## Setup Steps

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client ID**
5. Configure the OAuth consent screen if prompted
6. For Application type, select **Web application**
7. Add authorized redirect URI: `http://10.1.55.29:3000/login/google`
8. Click **Create**
9. Copy the **Client ID** and **Client Secret**

### 2. Update docker-compose.yml

Open `docker-compose.yml` and replace the placeholder values:

```yaml
- GF_AUTH_GOOGLE_CLIENT_ID=YOUR_ACTUAL_CLIENT_ID
- GF_AUTH_GOOGLE_CLIENT_SECRET=YOUR_ACTUAL_CLIENT_SECRET
```

### 3. Restart the Stack

```bash
cd c:\Users\Classroom\Documents\monitoring-stack\monitoring-blackbox-stack
docker-compose down
docker-compose up -d
```

### 4. Test Authentication

1. **Test Admin Login (Traditional)**
   - Go to http://10.1.55.29:3000
   - Login with username: `admin`, password: `13678`
   - Verify admin access

2. **Test Google OAuth (Admin)**
   - Logout
   - Click "Sign in with Google"
   - Login with `wachirachet@mfu.ac.th`
   - Verify admin access (can edit dashboards, manage settings)

3. **Test Google OAuth (Viewer)**
   - Logout
   - Click "Sign in with Google"
   - Login with any `@lamduan.mfu.ac.th` or `@maf.ac.th` account
   - Verify viewer-only access (can view but not edit)

## Troubleshooting

### OAuth Doesn't Work
- Verify Client ID and Secret are correct
- Check that redirect URI matches exactly: `http://10.1.55.29:3000/login/google`
- Ensure allowed domains include your email domain

### Users Can't Login
- Check Grafana logs: `docker-compose logs grafana`
- Verify email domain is in allowed list

### Wrong Role Assigned
- Check role mapping configuration in docker-compose.yml
- The role attribute path uses: `contains(email, 'wachirachet@mfu.ac.th') && 'Admin' || 'Viewer'`

## Changes Made

### TCP-Only Format
- Services now only monitor TCP port connectivity
- Removed HTTP application layer checks
- Removed ICMP ping checks
- Each service has one entry in `targets.json` with `tcp_connect` module

### Dashboard Note
The Grafana dashboard may need manual updates:
- Some panels still reference the old `layer` label
- Update panel queries to remove `layer` filters
- The Availability panel should group by `service` only

## Service Manager
The web UI at http://10.1.55.29:5000 now creates TCP-only entries when you add services.
