import uvicorn

from fastapi import FastAPI, APIRouter
from schemas import TextQuestion, TextResult

from core.solver import solve_text_question

app = FastAPI(title='PyFreq', version='0.1.0', docs_url='/api/docs')

router = APIRouter(prefix='/api/v1')

@app.get('/')
def index_page():
    return {
        'name': 'PyFreq',
        'version': '0.1.0',
        'repository': 'https://github.com/max-cyou/PyFreq'
    }


@app.get('/health')
def health():
    return {'status': 'ok'}

@router.post('/solve/text', response_model=TextResult)
async def solve_text(data: TextQuestion):
    return solve_text_question(
        question=data.question,
        answers=data.answers,
    )

app.include_router(router)

if __name__ == '__main__':
    uvicorn.run('main:app', host='127.0.0.1', port=8000)
