# Code Standards

Two sections: Frontend (TypeScript/React) and Backend (Python/FastAPI). Both apply to all code — human-written and AI-generated.

---

## Frontend (TypeScript / React)

### General Rules

- TypeScript strict mode everywhere — `"strict": true` in tsconfig
- All functions have explicit return types
- No `any` — use `unknown` and narrow, or define a proper type
- No `console.log` in committed code
- No TODO comments — either do it or open a spec
- Biome for formatting and linting (replaces ESLint + Prettier)

### Type Patterns

```typescript
// Discriminated unions for state
type GenerationState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: Project }
  | { status: 'error'; message: string }

// Explicit return types
async function fetchProject(id: string): Promise<Project> { ... }

// Zod for runtime validation at API boundaries
const ProjectSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  status: z.enum(['draft', 'building', 'ready', 'deployed', 'error']),
})
type Project = z.infer<typeof ProjectSchema>
```

### File Naming

```
components/workspace/FileTree.tsx    # PascalCase for components
lib/api.ts                           # kebab-case for lib files
lib/use-project.ts                   # kebab-case for hooks
app/workspace/[id]/page.tsx          # Next.js conventions
```

### Component Structure

```tsx
// 1. Imports
import { useState } from 'react'
import { useProject } from '@/lib/use-project'

// 2. Props type
interface FileTreeProps {
  projectId: string
  onFileSelect: (path: string) => void
}

// 3. Component
export function FileTree({ projectId, onFileSelect }: FileTreeProps) {
  // 4. Hooks
  const { data: project } = useProject(projectId)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  // 5. Handlers
  function handleToggle(path: string) {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(path) ? next.delete(path) : next.add(path)
      return next
    })
  }

  // 6. Effects (only if necessary)

  // 7. Render
  return (...)
}
```

### State Management

| Concern | Tool |
|---------|------|
| Server data (projects, credits, user) | TanStack Query |
| Local UI state (open/closed, selected) | `useState` |
| Cross-component shared UI state | `useState` lifted + context |
| Complex global client state | Zustand (sparingly) |

No Redux. No MobX.

### Error Handling

```tsx
// TanStack Query error state
const { data, error, isLoading } = useQuery(...)
if (error) return <ErrorBoundary message={error.message} />

// React Error Boundary for unexpected throws
<ErrorBoundary fallback={<ErrorFallback />}>
  <WorkspaceLayout />
</ErrorBoundary>
```

### API Client Pattern

```typescript
// lib/api.ts — all requests go through here
export async function apiRequest<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const token = await clerk.session?.getToken()
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options?.headers,
    },
  })
  if (!res.ok) throw new ApiError(res.status, await res.json())
  return res.json() as Promise<T>
}
```

### Commits

Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`

---

## Backend (Python / FastAPI)

### General Rules

- Python 3.12 — use modern syntax (`match`, `|` union types, `X | None`)
- Type hints on every function signature and class attribute
- `mypy --strict` must pass with zero errors
- Pydantic v2 for all request/response schemas and settings
- Ruff for linting and formatting (replaces black, isort, flake8)
- No `print()` debug — use `logging` with structured output
- No bare `except:` — catch specific exceptions
- No synchronous I/O calls inside async route handlers

### File Naming

```
app/routers/projects.py      # snake_case everywhere
app/agents/plan_agent.py
app/models/user.py
app/schemas/project.py
tests/test_projects.py
```

### FastAPI Route Pattern

```python
# app/routers/projects.py
router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    # 1. Validate credits
    await credit_service.check_credits(current_user.id, cost=0, db=db)
    # 2. Business logic
    project = await project_service.create(body, current_user.id, db)
    # 3. Return typed response
    return ProjectResponse.model_validate(project)
```

### SQLAlchemy Async Patterns

```python
# Always use async sessions
async with AsyncSession(engine) as session:
    async with session.begin():
        result = await session.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .options(selectinload(Project.versions))
        )
        projects = result.scalars().all()

# Explicit column selection — never SELECT *
result = await session.execute(
    select(User.id, User.email, User.credits)
    .where(User.clerk_id == clerk_id)
)

# Soft deletes — never hard delete user data
await session.execute(
    update(Project)
    .where(Project.id == project_id)
    .values(deleted_at=datetime.utcnow())
)
```

### LangGraph Node Pattern

```python
# app/agents/plan_agent.py
from langgraph.graph import StateGraph
from app.agents.state import AgentState

async def plan_node(state: AgentState) -> dict:
    llm = get_model("plan")   # from agents/router.py
    prompt = build_plan_prompt(state["user_message"], state["tech_stack"])
    response = await llm.ainvoke(prompt)
    plan = parse_plan_json(response.content)
    return {"plan": plan}
```

### Pydantic Settings

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    clerk_secret_key: str
    openrouter_api_key: str
    e2b_api_key: str
    stripe_secret_key: str

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
```

Never access `os.environ` directly — always use `settings`.

### Error Handling

```python
# Specific exceptions, always
try:
    result = await some_operation()
except OperationalError as e:
    logger.error("DB error", exc_info=e)
    raise HTTPException(status_code=503, detail="Database unavailable")
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))

# Custom exception classes for domain errors
class InsufficientCreditsError(Exception):
    def __init__(self, required: int, available: int) -> None:
        self.required = required
        self.available = available
```

### What AI Must Never Generate

1. `Any` type annotation — use specific types or `object`
2. `print()` for debugging — use `logging.getLogger(__name__)`
3. Hardcoded secrets, API keys, or passwords
4. Synchronous DB calls in async functions (`session.execute` not `session.sync_execute`)
5. Bare `except:` or `except Exception:` without re-raise or structured logging
6. `SELECT *` queries — always specify columns
7. String interpolation in SQL — always use ORM or parameterized queries
8. Hard-deleting user data — always soft delete with `deleted_at`
9. Blocking `time.sleep()` in async code — use `asyncio.sleep()`
10. TODO comments — either implement it or create a spec
