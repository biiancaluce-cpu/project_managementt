from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from calculations import optimize_assignment,P2
if __name__ == "__main__":
    print(json.dumps(optimize_assignment(P2),ensure_ascii=False,indent=2))
