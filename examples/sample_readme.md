# TaskFlow

Gerenciador de tarefas colaborativo com interface web e API REST.

## Instalação

```bash
pip install taskflow
```

Ou via Docker:

```bash
docker compose up -d
```

## Configuração

Crie um arquivo `.env` baseado no `.env.example`:

```bash
cp .env.example .env
```

Variáveis obrigatórias:

| Variável | Descrição |
|----------|-----------|
| DATABASE_URL | String de conexão PostgreSQL |
| SECRET_KEY | Chave para JWT |
| REDIS_URL | URL do Redis para cache |

## Uso

### Iniciar o servidor

```bash
taskflow serve --port 8000
```

### Criar uma tarefa via CLI

```bash
taskflow create "Implementar login" --priority alta --assignee @dev
```

### API REST

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Nova tarefa", "priority": "media"}'
```

## Arquitetura

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Frontend**: React 18, TailwindCSS
- **Banco**: PostgreSQL 15
- **Cache**: Redis 7

## Testes

```bash
pytest tests/ --cov=src --cov-report=html
```

## Contribuindo

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas alterações: `git commit -m "feat: nova funcionalidade"`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
