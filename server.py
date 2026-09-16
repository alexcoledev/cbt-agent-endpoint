#!/usr/bin/env python3
"""CBT Thought Analyzer — aitopia.ai Agent Endpoint
Minimal Python HTTP server (stdlib only, no dependencies).
Deployed on Render as a web service.
"""
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

DISTORTIONS = [
    {"id":"allornothing","name":"All-or-Nothing Thinking","desc":"You see things in black-and-white. If it's not perfect, it's a total failure.",
     "patterns":["always","never","completely","totally","perfect","complete failure","total failure","useless","worthless","100%","all or nothing"],
     "reframe":"Is there a middle ground? What counts as 'good enough' here? One mistake doesn't cancel everything else that went well."},
    {"id":"overgeneralization","name":"Overgeneralization","desc":"You treat one negative event as a never-ending pattern.",
     "patterns":["always","never","every time","every single","nobody","everyone","nothing","no one","typical","as usual"],
     "reframe":"What's the actual evidence this happens 'always'? Can you recall a time it didn't? One event != a permanent pattern."},
    {"id":"mentalfilter","name":"Mental Filter","desc":"You dwell on a single negative detail and ignore the positives.",
     "patterns":["only bad thing","the worst part","can't stop thinking","all i can see","ruined the whole"],
     "reframe":"What else happened today/this week? Force yourself to list 3 neutral or positive things you're filtering out."},
    {"id":"disqualpositive","name":"Disqualifying the Positive","desc":"You reject positive experiences by insisting they 'don't count'.",
     "patterns":["doesn't count","don't count","doesn't matter","just lucky","fluke","but that","yeah but","doesn't really"],
     "reframe":"Why doesn't it count? If a friend had that positive experience, would you dismiss it for them? Give yourself the same credit."},
    {"id":"mindreading","name":"Jumping to Conclusions (Mind Reading)","desc":"You assume others are reacting negatively with no evidence.",
     "patterns":["they think","he thinks","she thinks","they're judging","probably thinks","must think","thinks i'm"],
     "reframe":"What's the actual evidence they think that? Could there be another explanation for their behavior? Have you asked?"},
    {"id":"fortunetelling","name":"Fortune Telling","desc":"You arbitrarily predict things will turn out badly.",
     "patterns":["going to fail","will go wrong","never work","won't work","it's doomed","will be a disaster","bound to fail","never going to"],
     "reframe":"Can you predict the future with certainty? What's a realistic or positive outcome that's also possible? What's one step you control?"},
    {"id":"catastrophizing","name":"Magnification / Catastrophizing","desc":"You exaggerate how bad things are.",
     "patterns":["terrible","awful","horrible","disaster","catastrophe","ruined","end of the world","worst ever","can't cope","unbearable"],
     "reframe":"On a 0-10 scale, how bad is this really? Will it matter in a week? A year? You've coped with hard things before."},
    {"id":"emotionalreasoning","name":"Emotional Reasoning","desc":"You assume your feelings reflect objective reality.",
     "patterns":["i feel","so i must","so it must be","feel guilty so","feel like a","must be true because i feel"],
     "reframe":"Feelings are signals, not facts. 'I feel like a failure' doesn't mean you are one. What would the evidence say?"},
    {"id":"should","name":"Should Statements","desc":"You pressure yourself with 'shoulds' and 'musts', generating guilt.",
     "patterns":["should","must","have to","ought to","need to","supposed to","shouldn't","must not"],
     "reframe":"Replace 'I should...' with 'I choose to...' or 'I'd prefer to...'. What happens if you don't? Is this rule yours or someone else's?"},
    {"id":"labeling","name":"Labeling","desc":"You fix a negative label to yourself instead of describing the action.",
     "patterns":["i'm a failure","i am a failure","i'm a loser","i'm an idiot","i'm stupid","i'm worthless","he's a jerk","she's a","they're a"],
     "reframe":"You are not a label. Describe the behavior, not the person: 'I made a mistake' (action) vs 'I'm a failure' (identity)."},
    {"id":"personalization","name":"Personalization","desc":"You blame yourself for things outside your control.",
     "patterns":["my fault","because of me","i caused","i made them","if only i","i should have prevented"],
     "reframe":"What part was genuinely under your control, and what wasn't? Other people's reactions are their responsibility, not solely yours."}
]

def analyze_thought(text):
    lower = text.strip().lower()
    if not lower:
        return {"distortions": [], "summary": "No input provided.", "reframe": ""}

    found = []
    for d in DISTORTIONS:
        matches = [p for p in d["patterns"] if p in lower]
        if matches:
            confidence = "high" if len(matches) >= 3 else ("medium" if len(matches) == 2 else "low")
            found.append({"id": d["id"], "name": d["name"], "description": d["desc"],
                          "confidence": confidence, "matched_patterns": matches, "reframe": d["reframe"]})

    order = {"high": 0, "medium": 1, "low": 2}
    found.sort(key=lambda x: order.get(x["confidence"], 3))

    if not found:
        summary = "No strong cognitive distortion patterns detected. The thought may be balanced, or distortions may be subtle."
    else:
        names = ", ".join(f["name"] for f in found)
        summary = f"Detected {len(found)} cognitive distortion{'s' if len(found) > 1 else ''}: {names}."

    top_reframe = found[0]["reframe"] if found else "Try examining the evidence for and against this thought."
    return {"distortions": found, "summary": summary, "reframe": top_reframe}


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._json(200, {})

    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            self._json(200, {"status": "ok", "agent": "cbt-thought-analyzer", "version": "1.0.0"})
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            self._json(400, {"error": "Invalid JSON body"})
            return

        thought = body.get("thought") or body.get("input") or body.get("prompt") or body.get("text") or body.get("message") or ""
        if not thought:
            self._json(400, {"error": "Missing 'thought' field. Send {\"thought\": \"your anxious thought here\"}"})
            return

        result = analyze_thought(thought)
        self._json(200, {
            "output": result["summary"],
            "distortions": result["distortions"],
            "reframe": result["reframe"],
            "metadata": {"agent": "cbt-thought-analyzer", "version": "1.0.0", "distortions_found": len(result["distortions"])}
        })

    def log_message(self, format, *args):
        pass  # silent


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"CBT Thought Analyzer running on port {port}")
    server.serve_forever()
