from dotenv import load_dotenv
load_dotenv()

from app.rag.retrieval.two_step import two_step_retrieve
from backend.app.rag.schemas import TwoStepRetrievalResult, Hit

r = two_step_retrieve("visitation policy")

print(r.mode)
print(r.chosen_files)

for h in r.narrow_hits:
    print(h.meta.get("file_name"), h.distance)