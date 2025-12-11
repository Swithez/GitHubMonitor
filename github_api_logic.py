import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from db_manager import save_statistics_to_db

GITHUB_API_URL = "https://api.github.com"
headers = {}

class GitHubAPIError(Exception):
    pass

def fetch_github_data(endpoint: str, params: Dict = None) -> Any:
    url = f"{GITHUB_API_URL}/{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise GitHubAPIError("Репозиторий или ресурс не найден (404). Проверьте владельца/имя.")
    elif response.status_code == 403 and 'rate limit exceeded' in response.text:
        raise GitHubAPIError("Превышен лимит запросов GitHub API (403). Попробуйте позже или используйте токен.")
    else:
        error_message = response.json().get('message', f"Неизвестная ошибка: {response.status_code}")
        raise GitHubAPIError(f"Ошибка GitHub API: {error_message}")


def get_repo_info(owner: str, repo_name: str) -> Dict[str, Any]:
    return fetch_github_data(f"repos/{owner}/{repo_name}")


def get_repo_statistics(owner: str, repo_name: str, days: int) -> Dict[str, Any]:
    # 1. Расчет периода
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    since_date = start_date.isoformat() + 'Z' 

    # 2. Получение базовой информации
    repo_info = get_repo_info(owner, repo_name)
    
    repo_full_name = repo_info['full_name']
    total_stars = repo_info.get('stargazers_count', 0)
    subscribers = repo_info.get('subscribers_count', 1)
    
    # 3. Сбор коммитов
    total_commits = 0
    page = 1
    
    while True:
        commits = fetch_github_data(
            f"repos/{owner}/{repo_name}/commits",
            params={'since': since_date, 'per_page': 100, 'page': page}
        )
        if not commits:
            break
            
        total_commits += len(commits)
        
        if len(commits) < 100:
            break
        
        page += 1
            
    # 4. Получение участников
    contributors = fetch_github_data(f"repos/{owner}/{repo_name}/contributors")
    total_contributors = len(contributors)

    # 5. Расчет метрик
    total_days = days
    avg_commits_per_day = total_commits / total_days if total_days > 0 else 0
    
    activity_index = (total_commits / subscribers) * 100 if subscribers > 0 else 0

    statistics = {
        'repo_full_name': repo_full_name,
        'totalCommits': total_commits,
        'totalContributors': total_contributors,
        'totalStars': total_stars,
        'avgCommitsPerDay': round(avg_commits_per_day, 2),
        'activityIndex': round(activity_index, 2),
        'analysis_period_days': days
    }

    # 6. Сохранение в БД
    save_statistics_to_db(owner, repo_name, days, statistics)

    return statistics