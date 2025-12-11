import sqlite3
from typing import Dict, Any, List

DB_NAME = 'github_statistics.db'

def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repo_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            repo_name TEXT NOT NULL,
            total_commits INTEGER,
            total_contributors INTEGER,
            avg_commits_per_day REAL,
            analysis_period_days INTEGER,
            last_request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    
initialize_db()

def save_statistics_to_db(owner: str, repo_name: str, days: int, statistics: Dict[str, Any]):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO repo_stats 
        (owner, repo_name, total_commits, total_contributors, avg_commits_per_day, analysis_period_days)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        owner,
        repo_name,
        statistics['totalCommits'],
        statistics['totalContributors'],
        statistics['avgCommitsPerDay'],
        days
    ))
    
    conn.commit()
    conn.close()

def get_history() -> List[tuple]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM repo_stats
        ORDER BY last_request_time DESC
        LIMIT 50
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows