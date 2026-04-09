"""Robyn API route definitions.
DEPRECATED: Will be replaced by CLI + Lark Bot.
"""
from robyn import Robyn, jsonify

app = Robyn(__file__)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/getIntelligentReply")
async def get_intelligent_reply(request):
    body = request.json()
    return jsonify({"reply": "placeholder"})


@app.post("/recallContextFromEmbedding")
async def recall_context(request):
    body = request.json()
    return jsonify({"contexts": []})
