import sys; sys.path.insert(0, '.')
from server.sandbox import SQLSandbox
from server.sql_repair_environment import _TASKS
from server.grader import row_diff_grade

sandbox = SQLSandbox()
print("="*70)
for tid in ['logic_window_partition','logic_missing_having','logic_operator_precedence','logic_date_boundary']:
    task = _TASKS[tid]
    g, gc, ge = sandbox.execute(task['gold_query'])
    b, bc, be = sandbox.execute(task['broken_query'])
    gs = row_diff_grade(g, gc, g, gc)
    bs = row_diff_grade(b, bc, g, gc)
    print(f"{tid}")
    print(f"  gold: {len(g)} rows, score={gs:.3f}, err={ge}")
    print(f"  broken: {len(b)} rows, score={bs:.3f}, err={be}")
sandbox.close()
print("="*70)
