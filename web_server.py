from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta

from github_api_logic import get_repo_info, get_repo_statistics, GitHubAPIError
from db_manager import get_history

app = FastAPI(title="GitHub Stats Web Analyzer")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def root_page(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})

@app.get("/repo/{owner}/{repo_name}", response_class=HTMLResponse)
def repo_details_page(request: Request, owner: str, repo_name: str):
    try:
        repo_info = get_repo_info(owner, repo_name)
        if repo_info:
            return templates.TemplateResponse("repo_details.html", 
                                              {"request": request, "repo_info": repo_info, 
                                               "owner": owner, "repo_name": repo_name,
                                               "stats": None}) 
        else:
            raise HTTPException(status_code=404, detail="Репозиторий не найден")
    except GitHubAPIError as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_msg": str(e)}, status_code=500)

@app.get("/history", response_class=HTMLResponse)
def statistics_history(request: Request):
    rows = get_history()
    return templates.TemplateResponse('history.html', {"request": request, "statistics": rows})

@app.post("/get_stats", response_class=HTMLResponse)
async def get_stats_post(request: Request, 
                         owner: str = Form(...), 
                         repo_name: str = Form(...), 
                         start_date: str = Form(...), 
                         end_date: str = Form(...)):
    
    try:
        # 1. Парсинг дат и расчет дней
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_date_obj > end_date_obj:
             raise ValueError("Начальная дата не может быть позже конечной.")
             
        time_difference = end_date_obj - start_date_obj
        days = time_difference.days + 1

        if days <= 0:
             raise ValueError("Необходимо выбрать период более 0 дней.")
        
        # 2. Получение данных и расчет
        stats = get_repo_statistics(owner, repo_name, days)
        repo_info = get_repo_info(owner, repo_name)
        
        # 3. Возврат страницы с результатами
        return templates.TemplateResponse('repo_details.html', 
                                          {"request": request, 
                                           "repo_info": repo_info, 
                                           "owner": owner, 
                                           "repo_name": repo_name,
                                           "stats": stats,
                                           "start_date": start_date,
                                           "end_date": end_date})

    except GitHubAPIError as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_msg": str(e)}, status_code=500)
    except ValueError as e:
         return templates.TemplateResponse("error.html", {"request": request, "error_msg": f"Ошибка в датах: {e}"}, status_code=400)
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_msg": f"Непредвиденная ошибка: {e}"}, status_code=500)