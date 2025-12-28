# Prompts 
A set of prompts for data summary that can be used with any LLM. 

### Training Review 
```
Create a table of all my finger training sessions (20mm Lift and Peak Board Crimp Crawl only). Include columns for: Date, Exercise, Weight (use "N/A" for crimp crawl), and Notes. Sort by date.
```

### Sessions Review 
```
REUSABLE PROMPT FOR CLIMBING LOG GENERATION
============================================

Copy and paste this prompt to generate a climbing log for any date range:

---

Create a table and CSV file with all my climbing sessions and climb data between [START_DATE] and [END_DATE] with the following columns: date, location, notes, video.

Requirements:
- "Notes" should combine all session notes and individual climb notes from that session
- "Video" should include both session video links and climb-specific video links
- Do NOT include any training data (finger training, deadlifts, squats, etc.)
- Format climb entries as: "Boulder Name (Grade) - PROJECT/SENT: notes"
- Separate session notes from climb notes clearly
- In the CSV, use pipe separator (|) between different notes within the same cell

Output:
1. Show me a markdown table with the data
2. Create a CSV file with the same data
3. Present the CSV file for download

---

USAGE EXAMPLES:
- "between October 1, 2025 and December 31, 2025"
- "between November 1, 2025 and present"
- "from September 2025 onwards"
- "in the last 30 days"
- "all data from 2025"

CUSTOMIZATION:
Replace [START_DATE] and [END_DATE] with your desired date range, or use natural language like "the last month" or "since October 20".
```
