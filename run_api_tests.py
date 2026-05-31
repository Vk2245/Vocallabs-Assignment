"""
Vocallabs API — Full Product Test Suite (Live Run)
Reads credentials from api-credentials.csv automatically
"""

import requests
import json
import time
import csv
import sys
from datetime import datetime

# Read credentials from CSV
with open("api-credentials.csv", "r") as f:
    reader = csv.DictReader(f)
    row = next(reader)
    CLIENT_ID = row["Client ID"].strip()
    CLIENT_SECRET = row["Client Secret"].strip()

print(f"Using Client ID: {CLIENT_ID[:12]}...")

BASE = "https://api.superflow.run/b2b"
results = []
auth_token = None
agent_id = None
group_id = None

def timed_request(method, path, payload=None, params=None, label=""):
    """Execute a request and measure latency."""
    global auth_token
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    url = f"{BASE}/{path}"
    start = time.time()
    try:
        if method == "POST":
            r = requests.post(url, json=payload, params=params, headers=headers, timeout=20)
        else:
            r = requests.get(url, params=params, headers=headers, timeout=20)
        latency = round((time.time() - start) * 1000)
        
        try:
            data = r.json()
        except:
            data = {"raw_text": r.text[:500]}
        
        result = {
            "label": label,
            "method": method,
            "path": path,
            "status_code": r.status_code,
            "latency_ms": latency,
            "response": data,
            "url": url,
        }
        
        # Flag findings
        findings = []
        if "superflow" in url:
            findings.append("🔍 Base domain is api.superflow.run, not vocallabs-branded")
        
        resp_str = json.dumps(data).lower()
        for term in ["whatsub", "green", "superflow"]:
            if term in resp_str and term not in path.lower():
                findings.append(f"🔍 Response contains non-Vocallabs term: '{term}'")
        
        if latency > 2000:
            findings.append(f"⚠️ Latency {latency}ms exceeds 2000ms threshold")
        
        if r.status_code == 402:
            findings.append("⚠️ 402 Payment Required — reveals free tier limitation")
        elif r.status_code >= 400:
            findings.append(f"⚠️ {r.status_code} error response")
        
        # Check for empty/unnamed params in response
        if isinstance(data, dict):
            for key in data:
                if key == "" or key == "0":
                    findings.append(f"🔍 Response has unnamed/empty key: '{key}'")
        
        result["findings"] = findings
        results.append(result)
        
        status_icon = "✅" if r.status_code == 200 else "❌"
        print(f"  {status_icon} [{r.status_code}] {latency}ms | {label}")
        if findings:
            for f_item in findings:
                print(f"      {f_item}")
        
        return data, r.status_code
    except Exception as e:
        latency = round((time.time() - start) * 1000)
        result = {
            "label": label,
            "method": method,
            "path": path,
            "status_code": "ERROR",
            "latency_ms": latency,
            "response": {"error": str(e)},
            "url": url,
            "findings": [f"❌ Request failed: {str(e)}"]
        }
        results.append(result)
        print(f"  ❌ [ERR] {latency}ms | {label}: {str(e)[:100]}")
        return {}, 0

print("\n" + "="*60)
print("  VOCALLABS API LIVE TEST — " + datetime.now().strftime("%d %b %Y, %H:%M"))
print("="*60)

# 1. POST /createAuthToken/
print("\n--- 1. Authentication ---")
data, code = timed_request("POST", "createAuthToken/",
    payload={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET},
    label="POST /createAuthToken/")
if code == 200:
    auth_token = data.get("authToken") or data.get("auth_token") or data.get("data", {}).get("authToken") or data.get("data", {}).get("auth_token")
    if auth_token:
        print(f"      Token acquired: {auth_token[:30]}...")
    else:
        print(f"      WARNING: 200 OK but no auth_token found in response keys: {list(data.keys())}")

# 2. GET /getGreenBalance
print("\n--- 2. Wallet Balance ---")
data, code = timed_request("GET", "getGreenBalance",
    label="GET /getGreenBalance")

# 3. GET /vocallabs/getVoices
print("\n--- 3. Voices ---")
data, code = timed_request("GET", "vocallabs/getVoices",
    label="GET /vocallabs/getVoices")
if code == 200:
    voices = data if isinstance(data, list) else data.get("data", []) if isinstance(data, dict) else []
    if isinstance(voices, list):
        print(f"      Total voices: {len(voices)}")
        lang_counts = {}
        for v in voices:
            if isinstance(v, dict):
                lang = v.get("language", v.get("lang", "unknown"))
                lang_counts[str(lang)] = lang_counts.get(str(lang), 0) + 1
        indian_langs = {k: v for k, v in lang_counts.items() 
                        if any(x in str(k).lower() for x in ["hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "india"])}
        print(f"      Language distribution: {json.dumps(lang_counts)[:500]}")
        if indian_langs:
            print(f"      Indian languages found: {indian_langs}")
        else:
            print(f"      WARNING: No Indian language voices found in API response")

# 4. GET /vocallabs/getVoicesByLanguageComment?language=hi-IN
print("\n--- 4. Hindi Voices ---")
data, code = timed_request("GET", "vocallabs/getVoicesByLanguageComment",
    params={"language": "hi-IN"},
    label="GET /vocallabs/getVoicesByLanguageComment?language=hi-IN")

# 5. GET /vocallabs/getAgentTemplates
print("\n--- 5. Agent Templates ---")
data, code = timed_request("GET", "vocallabs/getAgentTemplates",
    label="GET /vocallabs/getAgentTemplates")
if code == 200:
    templates = data if isinstance(data, list) else data.get("data", []) if isinstance(data, dict) else []
    if isinstance(templates, list):
        print(f"      Templates count: {len(templates)}")

# 6. POST /vocallabs/createAIAgent
print("\n--- 6. Create AI Agent ---")
data, code = timed_request("POST", "vocallabs/createAIAgent",
    payload={"name": "teardown-test-agent"},
    label="POST /vocallabs/createAIAgent")
if code == 200:
    agent_data = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(agent_data, dict):
        agent_id = agent_data.get("id") or agent_data.get("agent_id") or agent_data.get("agentId")
        print(f"      Agent ID: {agent_id}")
    elif isinstance(agent_data, str):
        agent_id = agent_data
        print(f"      Agent ID (raw): {agent_id}")

# 7. GET /vocallabs/getAIModels
print("\n--- 7. AI Models ---")
data, code = timed_request("GET", "vocallabs/getAIModels",
    label="GET /vocallabs/getAIModels")
if code == 200:
    models = data if isinstance(data, list) else data.get("data", []) if isinstance(data, dict) else []
    if isinstance(models, list):
        print(f"      Available models ({len(models)}):")
        for m in models[:10]:
            if isinstance(m, dict):
                name = m.get("name", m.get("model", m.get("id", str(m)[:60])))
            else:
                name = str(m)[:60]
            print(f"        - {name}")

# 8. POST /vocallabs/createContactGroup
print("\n--- 8. Create Contact Group ---")
data, code = timed_request("POST", "vocallabs/createContactGroup",
    payload={"name": "teardown-group"},
    label="POST /vocallabs/createContactGroup")
if code == 200:
    group_data = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(group_data, dict):
        group_id = group_data.get("id") or group_data.get("group_id") or group_data.get("groupId")
        print(f"      Group ID: {group_id}")

# 9. GET /vocallabs/getCampaigns
print("\n--- 9. Campaigns ---")
data, code = timed_request("GET", "vocallabs/getCampaigns",
    label="GET /vocallabs/getCampaigns")

# 10. GET /vocallabs/fetchAvailableNumbers
print("\n--- 10. Available Numbers ---")
data, code = timed_request("GET", "vocallabs/fetchAvailableNumbers",
    params={"limit": 10},
    label="GET /vocallabs/fetchAvailableNumbers?limit=10")

# 11. GET /vocallabs/fetchCountries
print("\n--- 11. Supported Countries ---")
data, code = timed_request("GET", "vocallabs/fetchCountries",
    label="GET /vocallabs/fetchCountries")
if code == 200:
    countries = data if isinstance(data, list) else data.get("data", []) if isinstance(data, dict) else []
    if isinstance(countries, list):
        print(f"      Countries count: {len(countries)}")
        country_names = [c.get("name", c.get("country", str(c)[:30])) if isinstance(c, dict) else str(c)[:30] for c in countries[:20]]
        print(f"      Sample: {country_names}")

# 12. GET /vocallabs/getDashboardStats
print("\n--- 12. Dashboard Stats ---")
data, code = timed_request("GET", "vocallabs/getDashboardStats",
    label="GET /vocallabs/getDashboardStats")

# 13. GET /vocallabs/getAllAudits
print("\n--- 13. Audit Log ---")
data, code = timed_request("GET", "vocallabs/getAllAudits",
    label="GET /vocallabs/getAllAudits")

# === SAVE RAW RESULTS ===
print("\n" + "="*60)
print("  SAVING RESULTS")
print("="*60)

with open("api_test_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n  Saved {len(results)} test results to api_test_results.json")
print(f"  ✅ Passed: {sum(1 for r in results if r['status_code'] == 200)}")
print(f"  ❌ Failed: {sum(1 for r in results if r['status_code'] != 200)}")
print(f"  🔍 Findings: {sum(len(r.get('findings',[])) for r in results)}")
