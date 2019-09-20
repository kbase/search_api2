.PHONY: test reset

test:
	docker-compose up -d
	docker-compose exec web python src/test/wait_for_service.py
	docker-compose exec web sh scripts/run_tests.sh
	docker-compose logs web
	docker-compose down

reset:
	docker-compose down -v --remove-orphans --rmi all
	docker-compose build --no-cache
