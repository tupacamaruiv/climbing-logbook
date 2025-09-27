# Climbing Logger - Technical Documentation

## Technology Stack

### Frontend
- **HTML5** - Semantic markup with modern form controls
- **CSS3** - Flexbox, Grid, custom properties, responsive design  
- **Vanilla JavaScript (ES6+)** - Async/await, Fetch API, localStorage, DOM manipulation
- **Progressive Web App** - Mobile-first responsive design

### Backend & Storage
- **GitHub API v3** - RESTful API for data persistence
- **JSON** - Structured data format for climbing logs
- **OAuth2 (Personal Access Tokens)** - Secure authentication with GitHub

### Hosting & Deployment
- **GitHub Pages** - Static site hosting with HTTPS
- **CDN** - Global content delivery via GitHub's infrastructure
- **Git-based Deployment** - Automatic updates on repository changes

### External Services
- **Google Fonts** - Roboto Mono typography
- **Fetch API** - Native browser HTTP client

## System Architecture

```
┌─────────────┐    HTTPS     ┌─────────────┐    API      ┌─────────────┐    JSON     ┌─────────────┐
│             │   Request    │             │   Calls     │             │    CRUD     │             │
│   Mobile    │ ──────────►  │ Web App     │ ──────────► │ GitHub      │──────────►  │ Repository  │
│    User     │              │ GitHub Pages│             │  REST API   │             │ Data Storage│
│             │              │ HTML+CSS+JS │             │             │             │             |
└─────────────┘              └─────────────┘             └─────────────┘             └─────────────┘
     │                                                                                      │
     │                                                                                      │
     └─ Gym Logging                                                                         └─ sessions.json
                                                                                               climbs.json
                                                                                               training.json

 Authentication Flow:
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│ PAT Token   │ ────►  │ GitHub Auth │ ────►  │Repo Access  │
└─────────────┘        └─────────────┘        └─────────────┘
```

## Data Structure

### Sessions Data Model

```json
{
  "sessionId": "S1758849068880",           // Unique identifier
  "date": "2025-09-26",                     // ISO date format
  "location": "Peak Boulders",              // Climbing location
  "rpe": 8,                                 // Rate of Perceived Exertion (1-10)
  "rating": 4,                              // Session quality rating (1-10)
  "notes": "Good session with progress...", // Free text notes
  "videos": "https://example.com/video",    // Video URLs
  "timestamp": "2025-09-26T01:11:08.880Z", // Creation timestamp
  "lastUpdated": "2025-09-27T00:46:39.845Z" // Last modification
}
```

### Individual Climbs Data Model

```json
{
  "climbId": "C1758849205145",             // Unique identifier
  "sessionId": "S1758849068880",           // Links to parent session
  "boulderName": "Tighty Whities",         // Route name
  "grade": "V6",                           // Difficulty grade
  "gradeSystem": "V",                      // V-scale or B-scale
  "sendStatus": "Attempt",                 // Flash/Send/Attempt/Gave Up
  "isProject": true,                       // Long-term project flag
  "attempts": 1,                           // Attempts this session
  "performanceHighlight": false,           // Breakthrough moment
  "notes": "Made barn door right move...", // Beta and progress notes
  "videos": "",                            // Climb-specific videos
  "timestamp": "2025-09-26T01:13:25.145Z" // Creation timestamp
}
```

### Training Data Model

```json
{
  "trainingId": "T1758933957563",          // Unique identifier
  "date": "2025-09-24",                     // Training date
  "exercise": "20mm Lift",                 // Exercise type
  "weight": 31,                            // Working weight in pounds
  "performanceHighlight": false,           // PR or significant achievement
  "notes": "First normal feeling lift...", // Training notes
  "timestamp": "2025-09-27T00:45:57.563Z" // Creation timestamp
}
```

## GitHub API Integration

### Core API Endpoints

#### Get Existing Data
```http
GET https://api.github.com/repos/{owner}/{repo}/contents/data/{filename}
```
Retrieves existing data files. Returns base64-encoded JSON content with SHA for updates.

#### Create/Update Data
```http
PUT https://api.github.com/repos/{owner}/{repo}/contents/data/{filename}
```
Creates or updates data files. Requires base64-encoded content and SHA for updates.

#### Validate Access
```http
GET https://api.github.com/repos/{owner}/{repo}
```
Validates repository access and tests authentication during setup.

### Authentication

All API requests require authentication headers:

```javascript
{
  "Authorization": "token ghp_xxxxxxxxxxxxxxxxxxxx",
  "Content-Type": "application/json"
}
```

### Data Flow Example

```javascript
// 1. Read existing data
const response = await fetch(`/repos/${repo}/contents/data/sessions.json`, {
  headers: { 'Authorization': `token ${token}` }
});

// 2. Decode base64 content
const existingFile = await response.json();
const existingContent = JSON.parse(atob(existingFile.content));

// 3. Add new entry
existingContent.push(newSessionData);

// 4. Update file
await fetch(`/repos/${repo}/contents/data/sessions.json`, {
  method: 'PUT',
  headers: { 'Authorization': `token ${token}` },
  body: JSON.stringify({
    message: 'Add session entry',
    content: btoa(JSON.stringify(existingContent, null, 2)),
    sha: existingFile.sha
  })
});
```

## File Structure

```
climbing-logbook/
├── index.html              # Main application
├── README.md               # User documentation
├── TECHNICAL.md            # This technical documentation
└── data/
    ├── sessions.json       # Climbing sessions
    ├── climbs.json        # Individual boulder attempts
    └── training.json      # Strength training logs
```
## Performance Characteristics

### Data Limits
- **Repository size** - Effectively unlimited for JSON data
- **API rate limits** - 5,000 authenticated requests/hour
- **File size limits** - 100MB per file (far exceeds typical usage)
- **Browser storage** - ~10MB for localStorage (setup data)

### Scalability
- **Years of data** - JSON format scales to thousands of entries
- **Mobile performance** - Lightweight, single-file application
- **Offline capability** - All data operations cached locally
- **Global CDN** - Fast loading worldwide via GitHub Pages

### Browser Compatibility
- **Chrome/Edge** - Full support (recommended)
- **Safari** - Full support
- **Firefox** - Full support
- **Mobile browsers** - Optimized for iOS Safari and Chrome

## Deployment

### GitHub Pages Setup
1. Repository must be public
2. Enable Pages in repository settings
3. Deploy from `main` branch, root folder
4. Access at `https://username.github.io/repository-name`
