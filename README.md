# Climbing Logger

A clean, simple web app for tracking your bouldering sessions, individual climbs, and training progress. Log your data directly to GitHub and use your data to create visualizations of your climbing journey. For information on the technical architecture and data structure, see the [technical documentation](https://github.com/tupacamaruiv/climbing-logbook/blob/main/TECHNICAL.md).

## Features

- **Mobile-first design** - Log climbs right from the gym
- **Project tracking** - Monitor your long-term boulder projects  
- **Training logs** - Track deadlifts, squats, and finger strength
- **Smart autocomplete** - Consistent boulder naming across sessions
- **Edit anything** - Update videos, notes, and performance highlights
- **Your data, your control** - Everything stored in your GitHub repository

## Complete Setup Guide

**Never used GitHub before? No problem!** Follow these step-by-step instructions to get your climbing logger up and running in 15 minutes.

### Step 1: Create Your Repository

1. **Make sure you're signed in to GitHub**
   - Go to [github.com](https://github.com) and sign in with your account

2. **Create a new repository**
   - Click the green **"New"** button (or the **"+"** icon in top right → "New repository")
   - **Repository name**: `climbing-logbook` (exactly like this)
   - **Description**: `Personal climbing progress tracker`
   - Make sure **"Public"** is selected (this allows the app to access your data)
   - ✅ Check **"Add a README file"**
   - Click **"Create repository"**

### Step 2: Set Up the App Structure

1. **Create the data folder**
   - In your new repository, click **"Create new file"**
   - In the filename box, type: `data/README.md`
   - This automatically creates a `data` folder with a README inside
   - In the file editor, add this text:
     ```markdown
     # Climbing Data Storage
     This folder contains your climbing session data in JSON format.
     Your app will automatically create files here when you start logging.
     ```
   - Scroll down and click **"Commit new file"**

2. **Add the climbing logger app**
   - Click **"Add file"** → **"Create new file"** 
   - **Filename**: `index.html` (exactly like this)
   - Copy the complete HTML code from the climbing logger app
   - Scroll down and click **"Commit new file"**

### Step 3: Enable GitHub Pages (Make Your App Live)

1. **Go to repository Settings**
   - Click the **"Settings"** tab in the top menu of your repository

2. **Find Pages settings**
   - Scroll down the left sidebar and click **"Pages"**

3. **Configure GitHub Pages**
   - Under **"Source"**, select **"Deploy from a branch"**
   - **Branch**: Select **"main"** from the dropdown
   - **Folder**: Select **"/ (root)"**
   - Click **"Save"**

4. **Wait for deployment**
   - GitHub will show you a URL where your app will be available
   - It typically takes 2-5 minutes to go live
   - Your app will be at: `https://yourusername.github.io/climbing-logbook`
   - (Replace `yourusername` with your actual GitHub username)

### Step 4: Create Your Access Token

Your app needs permission to save data to your repository. Here's how to create that permission:

1. **Go to your GitHub account Settings**
   - Click your profile picture in the top right corner
   - Click **"Settings"** from the dropdown menu

2. **Navigate to Developer Settings**
   - Scroll all the way down the left sidebar
   - Click **"Developer settings"** (at the very bottom)

3. **Create a Personal Access Token**
   - Click **"Personal access tokens"** → **"Tokens (classic)"**
   - Click **"Generate new token"** → **"Generate new token (classic)"**

4. **Configure your token**
   - **Note**: `Climbing Logbook App`
   - **Expiration**: `90 days` (or choose longer if you prefer)
   - **Select scopes**: ✅ Check **"repo"** (this gives full repository access)
   - Click **"Generate token"** at the bottom

5. **⚠️ CRITICAL: Save your token immediately**
   - Copy the token that appears (it starts with `ghp_` followed by random characters)
   - **Paste it somewhere safe immediately** - you won't be able to see it again!
   - Consider saving it in your password manager or a secure note

### Step 5: Set Up and Test Your App

1. **Open your climbing logger**
   - Go to: `https://yourusername.github.io/climbing-logbook`
   - (Replace `yourusername` with your actual GitHub username)
   - If it doesn't load immediately, wait a few more minutes

2. **Complete the initial setup**
   - **Repository**: Type `yourusername/climbing-logbook` (replace with your username)
   - **GitHub Personal Access Token**: Paste the token you just created
   - Click **"Test Connection"** to verify everything works
   - You should see "Connection successful! ✅"
   - Click **"Save & Continue"**

3. **Success!**
   - The setup section will disappear
   - You'll see tabs for Session, Climb, Training, and Edit
   - You're ready to start logging your climbing!

## How to Use Your Climbing Logger

### Logging a Climbing Session

1. **Go to the Session tab** (should be selected by default)
2. **Fill out the session details**:
   - **Date**: Use "Today's Date" button or pick manually
   - **Location**: Choose from Peak Boulders, Triangle Boulders, or Triangle Board
   - **Session RPE**: Slide from 1-10 (how hard did you work?)
   - **Session Rating**: Slide from 1-10 (how good was the session?)
   - **Notes**: Describe how the session went
   - **Videos**: Paste links to any session videos (optional)
3. **Click "Log Session to GitHub"**
4. **You should see "Successfully saved to GitHub! 🎉"**

### Logging Individual Climbs

1. **Make sure you've logged a session first** (climbs need to be linked to sessions)
2. **Go to the Climb tab**
3. **Fill out climb details**:
   - **Session**: Choose from the dropdown (recent sessions will appear)
   - **Boulder Name**: Start typing - the app will suggest names you've used before
   - **Grade**: e.g., V4, V6, B3, etc.
   - **Grade System**: V-Scale or B-Scale
   - **Send Status**: Flash, Send, Attempt, or Gave Up
   - **Project**: ✅ Check if this is a long-term project you're working
   - **Attempts**: How many tries this session
   - **Performance Highlight**: ✅ Check for breakthrough moments
   - **Notes**: Beta, technique thoughts, etc.
   - **Videos**: Links to specific climb videos
4. **Click "Log Climb to GitHub"**

### Logging Training

1. **Go to the Training tab**
2. **Fill out training details**:
   - **Date**: When you trained
   - **Exercise**: Deadlift, Squat, or 20mm Lift
   - **Working Weight**: Your working weight in pounds
   - **Performance Highlight**: ✅ Check for PRs or breakthrough sessions
   - **Notes**: How it felt, form notes, etc.
3. **Click "Log Training to GitHub"**

### Editing Existing Entries

Need to add a video link later? Update notes? Change project status? No problem!

1. **Go to the Edit tab**
2. **Choose what to edit**: Recent Sessions, Recent Climbs, or Recent Training
3. **Click on any entry** to select it
4. **Make your changes** in the form that appears
5. **Click "Update Entry"** to save changes
6. **Or click "Delete Entry"** to remove it entirely (with confirmation)

## Pro Tips for Best Results

### Consistent Boulder Naming
- **Use the suggested names**: The app shows recent boulder names as clickable tags
- **Be consistent**: "Crimpy Corner" and "crimpy corner" are treated as different routes
- **Descriptive names help**: Future you will thank you for clear naming

### Project Tracking Strategy
- ✅ **Mark as "Project"** when you decide to work a boulder seriously over multiple sessions
- **Use the same exact boulder name** across all sessions for proper tracking 
- **Update notes** with progress on each attempt

### Mobile Gym Usage
- **Bookmark your app** (`https://yourusername.github.io/climbing-logbook`) for quick access
- **Log basic info quickly** at the gym, add videos/detailed notes later using Edit tab

### Data Organization
- **Log sessions first**, then add individual climbs to them
- **Use Edit tab** to add video links after uploading footage
- **Mark performance highlights** - they're great for tracking breakthrough moments

## Troubleshooting Common Issues

### "App Won't Load" or Shows Blank Page
- **Wait longer**: GitHub Pages can take up to 10 minutes on first deploy
- **Check repository is public**: Go to your repo Settings → scroll to bottom → should show "Public repository"
- **Verify filename**: Must be exactly `index.html` in the root of your repository
- **Try incognito/private browsing**: Sometimes caching causes issues

### "Setup not complete" or Can't Save Data
- **Double-check repository name**: Should be exactly `yourusername/climbing-logbook`
- **Verify token permissions**: Token must have "repo" scope checked
- **Check token expiration**: Generate a new token if yours expired
- **Test connection**: Use the "Test Connection" button to verify setup

### "Please select a session first" Error
- **Log a session before logging climbs**: Climbs must be linked to sessions
- **Wait for session to appear**: Sometimes takes a moment for sessions to show in dropdown
- **Check session date**: Only recent sessions (past week) appear in dropdown

### Boulder Names Not Appearing as Suggestions
- **Log some climbs first**: The app learns names from your existing data
- **Use consistent spelling**: Small differences create separate names
- **Recent names appear as clickable tags**: Most recent 10 boulder names show below the input

### GitHub Token Issues
- **Token expired**: Generate a new one following Step 4 above
- **Wrong permissions**: Must check "repo" scope when creating token
- **Token not saved**: Make sure you copied the full token starting with `ghp_`

## Understanding Your Data

Your climbing data is automatically saved as JSON files in your GitHub repository:

- **`data/sessions.json`** - All your climbing sessions
- **`data/climbs.json`** - Individual boulder attempts and sends  
- **`data/training.json`** - Strength training logs

### Accessing Your Data
You can view or download your data anytime:
1. Go to your GitHub repository
2. Click on the `data` folder
3. Click on any `.json` file to view it
4. Click "Raw" to get the direct data link for analysis tools

### Why GitHub for Data Storage?
- ✅ **You own your data completely** - no vendor lock-in
- ✅ **Free hosting and unlimited private repositories**
- ✅ **Built-in backup and version history** - never lose data
- ✅ **Easy to export** - standard JSON format works everywhere
- ✅ **Share with coaches or analysts** - just share the repository link

## Updating Your App

When new features are released:

1. **Check for updates** - watch the original repository for new releases
2. **Copy new code**: Get the updated `index.html` code
3. **Update your file**:
   - Go to your repository
   - Click on `index.html`
   - Click the pencil icon (Edit this file)
   - Replace all content with the new code
   - Click **"Commit changes"**
4. **Wait for deployment** - 2-3 minutes for GitHub Pages to update

## Advanced Usage and Data Analysis

### Exporting Your Data
Your data is in standard JSON format, perfect for analysis:

**Direct links to your data:**
- Sessions: `https://raw.githubusercontent.com/yourusername/climbing-logbook/main/data/sessions.json`
- Climbs: `https://raw.githubusercontent.com/yourusername/climbing-logbook/main/data/climbs.json`
- Training: `https://raw.githubusercontent.com/yourusername/climbing-logbook/main/data/training.json`

### Analysis Ideas
- **Share with an LLM of your choice** for unique data visualization and analytics
- **Import into Excel/Google Sheets** for custom charts
- **Track grade progression** over time
- **Analyze project completion rates** 
- **Correlate training with climbing performance**
- **Share with coaches** for technique analysis

### Privacy and Sharing
- **Public repository**: Anyone can see your climbing data (great for sharing achievements)
- **Private repository**: Only you can access (requires GitHub Pro for private Pages)
- **Selective sharing**: Share specific sessions by copying data

## Still Need Help?

### Quick Fixes
1. **Try refreshing the page** - often fixes temporary glitches
2. **Clear browser cache** - helps with outdated files
3. **Use incognito/private mode** - eliminates caching issues
4. **Check GitHub status** - visit [githubstatus.com](https://githubstatus.com)

### Getting Support
- **GitHub Documentation**: [Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- **GitHub Pages Guide**: [pages.github.com](https://pages.github.com/)
- **Repository Issues**: Report bugs or request features

## You're All Set!

Congratulations! You now have your own personal climbing logger that:

- ✅ **Tracks all your climbing progress** in one place
- ✅ **Works perfectly on mobile** for gym logging
- ✅ **Stores your data safely** in your own GitHub repository
- ✅ **Gives you complete ownership** of your climbing history
- ✅ **Provides powerful editing tools** for updating entries
- ✅ **Suggests boulder names** to keep your data consistent

**Happy climbing!** 

Start logging your sessions and watch your progress unfold with data-driven insights. Every send, every project, every training session - all captured and organized to help you climb stronger and smarter.

---

*Climbing Logger - Track your progress, crush your projects, own your data.*
