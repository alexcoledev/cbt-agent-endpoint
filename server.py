#!/usr/bin/env python3
"""CBT Thought Analyzer + Procrastination Detector — aitopia.ai Agent Endpoints
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

# ── Procrastination Pattern Detector ──
PROCRASTINATION_PATTERNS = [
    {"id":"perfectionism","name":"Perfectionism Block","desc":"You can't start because it won't be perfect.",
     "patterns":["perfect","right way","not good enough","needs to be","has to be perfect","can't get it right","flawless"],
     "intervention":"What's 'good enough' for a first draft? Perfection is the enemy of started. Give yourself permission to make a mess — you can edit bad work, but you can't edit a blank page."},
    {"id":"fear_of_failure","name":"Fear of Failure","desc":"You avoid starting to avoid the possibility of failing.",
     "patterns":["what if it fails","going to fail","fail","wrong","mistake","screw up","mess up","can't fail","embarrassing"],
     "intervention":"What's the actual cost of failing? What's the cost of never trying? Most 'failures' are reversible. The only irreversible failure is the one where you never start."},
    {"id":"overwhelm","name":"Task Overwhelm","desc":"The task feels too big, so you shut down.",
     "patterns":["too much","so many","don't know where to start","overwhelming","too big","complicated","no idea how","too complex"],
     "intervention":"Break it into absurdly small steps. 'Open the document' is step 1. 'Write one sentence' is step 2. What's step 1?"},
    {"id":"waiting_motivation","name":"Waiting for Motivation","desc":"You think you need to feel ready before starting.",
     "patterns":["not in the mood","wait until","when i feel ready","right mindset","need to feel","not feeling it","wait for inspiration","motivated"],
     "intervention":"Action comes BEFORE motivation, not after. You don't need to feel ready. Set a 5-minute timer and start. Motivation follows action — this is the #1 CBT finding on procrastination."},
    {"id":"avoidance","name":"Task Avoidance","desc":"You keep pushing it to 'later' without a concrete plan.",
     "patterns":["later","tomorrow","next week","not now","put it off","another day","someday","eventually","after i"],
     "intervention":"'Later' is not a time. Pick a specific clock time: 'I start at 3:07 PM.' Vague intentions don't trigger action. Specific times do."},
    {"id":"all_or_nothing","name":"All-or-Nothing Approach","desc":"You can only do it if you can do it all at once.",
     "patterns":["all at once","everything done","complete","can't do it all","finish it all","whole thing","from start to finish"],
     "intervention":"You don't need to finish. You need to start. 10% done is infinitely more than 0% done. What's 10% of this task?"},
    {"id":"guilt_cycle","name":"Gilt-Procrastination Cycle","desc":"You feel guilty about procrastinating, which makes you avoid it more.",
     "patterns":["should have","guilty","lazy","beat myself up","procrastinating again","keep putting off","why can't i just","self sabotage"],
     "intervention":"Guilt is fuel for avoidance, not action. Forgive yourself for yesterday. The question isn't 'why did I procrastinate?' — it's 'what's the next 5-minute action?'"},
    {"id":"minimization","name":"Minimization Trap","desc":"You tell yourself it'll be quick, then don't start anyway.",
     "patterns":["only takes","just a few","quick","five minutes","won't take long","easy","no big deal"],
     "intervention":"If it's so quick, do it right now for 2 minutes. 'It's easy' is often a story we tell ourselves to avoid the discomfort of actually starting."}
]

def analyze_procrastination(text):
    lower = text.strip().lower()
    if not lower:
        return {"patterns": [], "summary": "No input provided.", "intervention": ""}

    found = []
    for p in PROCRASTINATION_PATTERNS:
        matches = [m for m in p["patterns"] if m in lower]
        if matches:
            confidence = "high" if len(matches) >= 3 else ("medium" if len(matches) == 2 else "low")
            found.append({"id": p["id"], "name": p["name"], "description": p["desc"],
                          "confidence": confidence, "matched_patterns": matches, "intervention": p["intervention"]})

    order = {"high": 0, "medium": 1, "low": 2}
    found.sort(key=lambda x: order.get(x["confidence"], 3))

    if not found:
        summary = "No strong procrastination patterns detected. Consider whether the delay is logistical (time/scheduling) rather than psychological."
    else:
        names = ", ".join(f["name"] for f in found)
        summary = f"Detected {len(found)} procrastination pattern{'s' if len(found) > 1 else ''}: {names}."

    top_intervention = found[0]["intervention"] if found else "Try the 5-minute rule: commit to just 5 minutes of the task. You can stop after if you want."
    return {"patterns": found, "summary": summary, "intervention": top_intervention}


# ── Attachment Style Detector (based on Bartholomew, 1990; Miller, 2024) ──
ATTACHMENT_TYPES = [
    {"id":"secure","name":"Secure Attachment","desc":"You're comfortable with intimacy and independence. You trust others and have a positive view of yourself and your partner.",
     "dimensions":{"avoidance":"low","anxiety":"low"},
     "patterns":["comfortable","trust","secure","open communication","support each other","healthy","stable","confident","give space","respect boundaries","independent but close","no need to check","honest","vulnerable"],
     "guidance":"You have a solid foundation. Keep nurturing open communication and mutual respect. Even secure relationships need maintenance — continue practicing active listening and emotional availability."},
    {"id":"preoccupied","name":"Preoccupied (Anxious) Attachment","desc":"You crave closeness but fear abandonment. You may seek excessive reassurance and worry your partner will leave.",
     "dimensions":{"avoidance":"low","anxiety":"high"},
     "patterns":["clingy","need reassurance","afraid of losing","can't live without","always worry","jealous","check phone","constant contact","abandonment","overthinking","anxious","panic when","too attached","fear of being alone","double texting","waiting for reply","need to know where","insecure","not enough","smothering"],
     "guidance":"Your anxiety is driving the relationship, not your values. CBT approach: (1) Identify the 'abandonment script' — is there evidence your partner is leaving, or is this fear from past wounds? (2) Practice self-soothing instead of seeking reassurance — the relief from reassurance is temporary, the anxiety returns. (3) Build a life outside the relationship. Anxious attachment thrives when the relationship is your ONLY source of safety."},
    {"id":"fearful","name":"Fearful Attachment","desc":"You want close relationships but fear getting hurt. You may push people away to protect yourself, then feel lonely.",
     "dimensions":{"avoidance":"high","anxiety":"high"},
     "patterns":["want to be close but afraid","fear of rejection","push away","sabotage","afraid of getting hurt","better to be alone","don't deserve","want love but scared","self-sabotage","test them","they'll leave anyway","not good enough for","avoid getting close","walls up","guarded","hot and cold","come here go away","conflicted"],
     "guidance":"You're caught between wanting connection and fearing it. CBT approach: (1) Notice the sabotage pattern — when things get close, you create distance. This feels like protection but is actually self-abandonment. (2) The fear isn't about THIS person — it's about a past wound. Separate the two. (3) Practice 'safe vulnerability' — share something small and let the other person respond before sharing more. Trust is built in increments, not all at once."},
    {"id":"dismissing","name":"Dismissing (Avoidant) Attachment","desc":"You value independence over intimacy. You may feel relationships are more trouble than they're worth.",
     "dimensions":{"avoidance":"high","anxiety":"low"},
     "patterns":["don't need anyone","independent","prefer alone","relationships are trouble","self-sufficient","don't care","not worth the effort","better single","too much drama","happy alone","don't need a relationship","privacy","need space","distant","emotionally unavailable","self-reliant","handle it myself","don't rely on others"],
     "guidance":"Your independence is a strength, but extreme self-reliance is a defense. CBT approach: (1) Ask: does 'I don't need anyone' reflect a genuine preference or a fear of vulnerability? (2) Interdependence is not dependence — needing support is human, not weak. (3) Practice small acts of connection — asking for help, sharing a feeling, letting someone in on a bad day. The goal isn't to become clingy; it's to let the walls down occasionally."}
]

def analyze_attachment(text):
    lower = text.strip().lower()
    if not lower:
        return {"attachment_type": None, "summary": "No input provided.", "guidance": ""}

    scores = {}
    for at in ATTACHMENT_TYPES:
        matches = [p for p in at["patterns"] if p in lower]
        scores[at["id"]] = {"type": at, "matches": matches, "score": len(matches)}

    # Find the type with the most matches
    best_id = max(scores, key=lambda k: scores[k]["score"])
    best = scores[best_id]

    if best["score"] == 0:
        return {"attachment_type": None, "summary": "No strong attachment pattern markers detected. Try describing specific feelings and behaviors in your relationship for better detection.", "guidance": "Consider describing how you feel when your partner needs space, how you handle conflict, or how you feel about emotional vulnerability."}

    at = best["type"]
    confidence = "high" if best["score"] >= 5 else ("medium" if best["score"] >= 3 else "low")
    summary = f"Detected {at['name']} (confidence: {confidence}, {best['score']} markers matched). Avoidance of intimacy: {at['dimensions']['avoidance']}. Anxiety about abandonment: {at['dimensions']['anxiety']}."

    # Also note secondary type
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    secondary = None
    if len(sorted_scores) > 1 and sorted_scores[1][1]["score"] > 0:
        secondary = {"id": sorted_scores[1][0], "name": sorted_scores[1][1]["type"]["name"], "score": sorted_scores[1][1]["score"]}

    return {"attachment_type": {"id": at["id"], "name": at["name"], "description": at["desc"], "dimensions": at["dimensions"], "confidence": confidence, "matched_patterns": best["matches"]}, "secondary_type": secondary, "summary": summary, "guidance": at["guidance"]}

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
            self._json(200, {"status": "ok", "agent": "cbt-thought-analyzer", "version": "1.2.0"})
        elif self.path == "/procrastination" or self.path == "/procrastination/health":
            self._json(200, {"status": "ok", "agent": "procrastination-detector", "version": "1.0.0"})
        elif self.path == "/attachment" or self.path == "/attachment/health":
            self._json(200, {"status": "ok", "agent": "attachment-style-detector", "version": "1.0.0"})
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

        # Route: /procrastination → Procrastination Pattern Detector
        if self.path == "/procrastination":
            thought = body.get("thought") or body.get("input") or body.get("prompt") or body.get("text") or body.get("message") or ""
            if not thought:
                self._json(400, {"error": "Missing 'thought' field. Send {\"thought\": \"describe what you're procrastinating on\"}"})
                return
            result = analyze_procrastination(thought)
            self._json(200, {
                "output": result["summary"],
                "patterns": result["patterns"],
                "intervention": result["intervention"],
                "metadata": {"agent": "procrastination-detector", "version": "1.0.0", "patterns_found": len(result["patterns"])}
            })
            return

        # Route: /attachment → Attachment Style Detector
        if self.path == "/attachment":
            thought = body.get("thought") or body.get("input") or body.get("prompt") or body.get("text") or body.get("message") or ""
            if not thought:
                self._json(400, {"error": "Missing 'thought' field. Send {\"thought\": \"describe how you feel in your relationship\"}"})
                return
            result = analyze_attachment(thought)
            self._json(200, {
                "output": result["summary"],
                "attachment_type": result["attachment_type"],
                "secondary_type": result.get("secondary_type"),
                "guidance": result["guidance"],
                "metadata": {"agent": "attachment-style-detector", "version": "1.0.0", "type_detected": result["attachment_type"] is not None}
            })
            return

        # Default route: / → CBT Thought Analyzer
        thought = body.get("thought") or body.get("input") or body.get("prompt") or body.get("text") or body.get("message") or ""
        if not thought:
            self._json(400, {"error": "Missing 'thought' field. Send {\"thought\": \"your anxious thought here\"}"})
            return

        result = analyze_thought(thought)
        self._json(200, {
            "output": result["summary"],
            "distortions": result["distortions"],
            "reframe": result["reframe"],
            "metadata": {"agent": "cbt-thought-analyzer", "version": "1.2.0", "distortions_found": len(result["distortions"])}
        })

    def log_message(self, format, *args):
        pass  # silent


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"CBT Analyzer + Procrastination Detector + Attachment Detector running on port {port}")
    server.serve_forever()
