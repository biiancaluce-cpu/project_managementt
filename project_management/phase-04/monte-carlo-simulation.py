from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from calculations import phase4
if __name__ == "__main__":
    print(json.dumps(phase4(),ensure_ascii=False,indent=2))
