.PHONY: backend frontend test docker seed

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && PYTHONPATH=. pytest -q

seed:
	cd backend && PYTHONPATH=. python seed_demo.py

docker:
	docker compose up --build
