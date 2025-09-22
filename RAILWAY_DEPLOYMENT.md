# Railway Deployment Guide for ENS Grading System

## What I Fixed

### 1. **Pandas Build Error**
- Updated `requirements.txt` to use pandas 2.1.4 instead of 1.5.3
- Newer versions have better pre-built wheel support on Linux platforms
- Added numpy>=1.24.0 to ensure compatibility

### 2. **Railway Configuration**
- Created `railway.json` with proper deployment settings
- Created `Procfile` for process management
- Created `server.py` as the main web server entry point
- Added `index.html` for health checks and basic info

### 3. **Web Server Setup**
- Extended your existing API handler to serve both static files and API endpoints
- GET `/` serves the index page
- POST requests are handled by your existing API logic

## Files Changed/Added

1. **requirements.txt** - Updated pandas version and added numpy
2. **server.py** - New web server entry point
3. **railway.json** - Railway deployment configuration
4. **Procfile** - Process definition for Railway
5. **index.html** - Basic landing page and health check endpoint

## How to Deploy

### Method 1: Git Push (Recommended)
```bash
# Add all changes to git
git add .
git commit -m "Fix Railway deployment configuration"
git push origin main
```

### Method 2: Railway CLI
```bash
# If you have Railway CLI installed
railway up
```

## Expected Behavior

1. **Build Phase**: Railway will install dependencies using the updated requirements.txt
2. **Deploy Phase**: Railway will start your server using `python server.py`
3. **Health Check**: Railway will check that your app responds to GET `/`
4. **API Endpoint**: Your transcript generation will be available at POST `/api/single`

## Testing Your Deployment

Once deployed, you can:

1. **Visit the main URL** - Should show the ENS Grading System page
2. **Test the API** - Send POST requests to `https://your-app.railway.app/api/single` with:
   - `student_info` (YAML file)
   - `author_info` (YAML file) 
   - `grades` (JSON file)

## Troubleshooting

If you still get build errors:

1. **Check the build logs** in Railway dashboard
2. **Try Python 3.11** by adding a `runtime.txt` file:
   ```
   python-3.11.9
   ```
3. **Remove version pins** if needed - change to:
   ```
   pandas>=2.0.0
   numpy>=1.24.0
   ```

## Next Steps

After successful deployment:
1. Update your frontend to point to the new Railway URL
2. Test transcript generation with real data
3. Monitor performance and logs in Railway dashboard

The main advantage over Vercel: **No 250MB limit!** Your pandas dependencies will install without issues.