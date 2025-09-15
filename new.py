@ -1,344 +0,0 @@
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException
import json
from datetime import datetime, timezone
import threading
from collections import defaultdict
import random
import math
import base64

# Custom HTTP Exception for 425
class TooEarly(HTTPException):
    code = 425
    description = "The server is unwilling to risk processing a request that might be replayed."

app = Flask(__name__)

# Preloaded data
voters = {1: {"name": "Alice", "age": 22, "has_voted": False, "updated": False},
          2: {"name": "Bob", "age": 30, "has_voted": False, "updated": False},
          3: {"name": "Charlie", "age": 25, "has_voted": True, "updated": True}}
candidates = {1: {"name": "John Doe", "party": "Green Party", "votes": 15},
              2: {"name": "Jane Roe", "party": "Red Party", "votes": 23},
              3: {"name": "Alex Smith", "party": "Blue Party", "votes": 7}}
votes = [{"vote_id": 1, "voter_id": 3, "candidate_id": 2, "timestamp": "2025-09-10T10:30:00Z", "weight": 1}]
encrypted_ballots = []
ranked_ballots = []

data_lock = threading.Lock()

def get_iso_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

# Error handlers
@app.errorhandler(400)
def bad_request(e): return jsonify(json.loads(e.description) if e.description else {"message": str(e)}), 400
@app.errorhandler(409)
def conflict(e): return jsonify(json.loads(e.description) if e.description else {"message": str(e)}), 409
@app.errorhandler(417)
def expectation_failed(e): return jsonify(json.loads(e.description) if e.description else {"message": str(e)}), 417
@app.errorhandler(422)
def unprocessable(e): return jsonify(json.loads(e.description) if e.description else {"message": str(e)}), 422
@app.errorhandler(423)
def locked(e): return jsonify(json.loads(e.description) if e.description else {"message": str(e)}), 423
@app.errorhandler(424)
def failed_dependency(e): return jsonify(json.loads(e.description) if e.description else {"message": str(e)}), 424
@app.errorhandler(TooEarly)
def too_early(e): return jsonify(json.loads(e.description) if e.description else {"message": str(e)}), 425

# Q1
@app.route('/api/voters', methods=['POST'])
def create_voter():
    data = request.json
    if not data or 'voter_id' not in data or 'name' not in data or 'age' not in data:
        abort(400, description=json.dumps({"message": "Missing required fields: voter_id, name, age"}))
    voter_id = data['voter_id']
    with data_lock:
        if voter_id in voters:
            abort(409, description=json.dumps({"message": f"voter with id: {voter_id} already exists"}))
        if data['age'] < 18:
            abort(422, description=json.dumps({"message": f"invalid age: {data['age']}, must be 18 or older"}))
        voters[voter_id] = {"name": data['name'], "age": data['age'], "has_voted": False, "updated": False}
    return jsonify({"voter_id": voter_id, "name": data['name'], "age": data['age'], "has_voted": False}), 218

# Q2
@app.route('/api/voters/<int:voter_id>', methods=['GET'])
def get_voter(voter_id):
    with data_lock:
        if voter_id not in voters:
            abort(417, description=json.dumps({"message": f"voter with id: {voter_id} was not found"}))
        v = voters[voter_id]
    return jsonify({"voter_id": voter_id, "name": v["name"], "age": v["age"], "has_voted": v["has_voted"]}), 222

# Q3
@app.route('/api/voters', methods=['GET'])
def list_voters():
    with data_lock:
        return jsonify({"voters": [{"voter_id": k, "name": v["name"], "age": v["age"]} for k, v in voters.items()]}), 223

# Q4
@app.route('/api/voters/<int:voter_id>', methods=['PUT'])
def update_voter(voter_id):
    with data_lock:
        if voter_id not in voters:
            abort(417, description=json.dumps({"message": f"voter with id: {voter_id} was not found"}))
        data = request.json or {}
        if 'age' in data and data['age'] < 18:
            abort(422, description=json.dumps({"message": f"invalid age: {data['age']}, must be 18 or older"}))
        if 'name' in data: voters[voter_id]["name"] = data['name']
        if 'age' in data: voters[voter_id]["age"] = data['age']
        if any(k in data for k in ['name', 'age']): voters[voter_id]["updated"] = True
    v = voters[voter_id]
    return jsonify({"voter_id": voter_id, "name": v["name"], "age": v["age"], "has_voted": v["has_voted"]}), 224

# Q5
@app.route('/api/voters/<int:voter_id>', methods=['DELETE'])
def delete_voter(voter_id):
    with data_lock:
        if voter_id not in voters:
            abort(417, description=json.dumps({"message": f"voter with id: {voter_id} was not found"}))
        if voters[voter_id]["has_voted"]:
            abort(423, description=json.dumps({"message": f"cannot delete voter with id: {voter_id} who has already voted"}))
        # Adjust votes
        for vote in votes[:]:
            if vote["voter_id"] == voter_id:
                candidates[vote["candidate_id"]]["votes"] -= vote["weight"]
                votes.remove(vote)
        del voters[voter_id]
    return jsonify({"message": f"voter with id: {voter_id} deleted successfully"}), 225

# Q6
@app.route('/api/candidates', methods=['POST'])
def create_candidate():
    data = request.json
    if not data or 'candidate_id' not in data or 'name' not in data or 'party' not in data:
        abort(400, description=json.dumps({"message": "Missing required fields: candidate_id, name, party"}))
    candidate_id = data['candidate_id']
    with data_lock:
        if candidate_id in candidates:
            abort(409, description=json.dumps({"message": f"candidate with id: {candidate_id} already exists"}))
        candidates[candidate_id] = {"name": data['name'], "party": data['party'], "votes": 0}
    return jsonify({"candidate_id": candidate_id, "name": data['name'], "party": data['party'], "votes": 0}), 226

# Q7/Q10
@app.route('/api/candidates', methods=['GET'])
def list_candidates():
    party = request.args.get('party')
    with data_lock:
        if party:
            return jsonify({"candidates": [c for c in candidates.values() if c["party"] == party]}), 230
        return jsonify({"candidates": [{"candidate_id": k, "name": v["name"], "party": v["party"]} for k, v in candidates.items()]}), 227

# Q8
@app.route('/api/votes', methods=['POST'])
def cast_vote():
    data = request.json
    if not data or 'voter_id' not in data or 'candidate_id' not in data:
        abort(400, description=json.dumps({"message": "Missing required fields: voter_id, candidate_id"}))
    voter_id, candidate_id = data['voter_id'], data['candidate_id']
    with data_lock:
        if voter_id not in voters or candidate_id not in candidates:
            abort(417, description=json.dumps({"message": f"voter or candidate with id: {voter_id}/{candidate_id} was not found"}))
        if voters[voter_id]["has_voted"]:
            abort(423, description=json.dumps({"message": f"voter with id: {voter_id} has already voted"}))
        weight = 1 if not voters[voter_id]["updated"] else 2
        vote_id = len(votes) + 1
        vote = {"vote_id": vote_id, "voter_id": voter_id, "candidate_id": candidate_id, "timestamp": get_iso_timestamp(), "weight": weight}
        votes.append(vote)
        voters[voter_id]["has_voted"] = True
        candidates[candidate_id]["votes"] += weight
    return jsonify({"vote_id": vote_id, "voter_id": voter_id, "candidate_id": candidate_id, "timestamp": vote["timestamp"]}), 228

# Q9
@app.route('/api/candidates/<int:candidate_id>/votes', methods=['GET'])
def get_candidate_votes(candidate_id):
    with data_lock:
        if candidate_id not in candidates:
            abort(417, description=json.dumps({"message": f"candidate with id: {candidate_id} was not found"}))
    return jsonify({"candidate_id": candidate_id, "votes": candidates[candidate_id]["votes"]}), 229

# Q11
@app.route('/api/results', methods=['GET'])
def get_results():
    with data_lock:
        return jsonify({"results": [{"candidate_id": k, "name": v["name"], "votes": v["votes"]} for k, v in candidates.items()]}), 231

# Q12
@app.route('/api/results/winner', methods=['GET'])
def get_winner():
    with data_lock:
        if not candidates:
            return jsonify({"winners": []}), 232
        max_votes = max(c["votes"] for c in candidates.values())
        return jsonify({"winners": [{"candidate_id": k, "name": v["name"], "votes": v["votes"]} for k, v in candidates.items() if v["votes"] == max_votes]}), 232

# Q13
@app.route('/api/votes/timeline', methods=['GET'])
def get_vote_timeline():
    candidate_id = request.args.get('candidate_id')
    if not candidate_id:
        abort(400, description=json.dumps({"message": "Missing required parameter: candidate_id"}))
    try: candidate_id = int(candidate_id)
    except ValueError:
        abort(400, description=json.dumps({"message": "candidate_id must be integer"}))
    with data_lock:
        if candidate_id not in candidates:
            abort(417, description=json.dumps({"message": f"candidate with id: {candidate_id} was not found"}))
        timeline = [{"vote_id": v["vote_id"], "timestamp": v["timestamp"]} for v in votes if v["candidate_id"] == candidate_id]
    return jsonify({"candidate_id": candidate_id, "timeline": sorted(timeline, key=lambda x: x["timestamp"])}), 233

# Q14
@app.route('/api/votes/weighted', methods=['POST'])
def cast_weighted_vote():
    data = request.json
    if not data or 'voter_id' not in data or 'candidate_id' not in data:
        abort(400, description=json.dumps({"message": "Missing required fields: voter_id, candidate_id"}))
    voter_id, candidate_id = data['voter_id'], data['candidate_id']
    with data_lock:
        if voter_id not in voters or candidate_id not in candidates:
            abort(417, description=json.dumps({"message": f"voter or candidate with id: {voter_id}/{candidate_id} was not found"}))
        if voters[voter_id]["has_voted"]:
            abort(423, description=json.dumps({"message": f"voter with id: {voter_id} has already voted"}))
        weight = 2 if voters[voter_id]["updated"] else 1
        vote_id = len(votes) + 1
        vote = {"vote_id": vote_id, "voter_id": voter_id, "candidate_id": candidate_id, "timestamp": get_iso_timestamp(), "weight": weight}
        votes.append(vote)
        voters[voter_id]["has_voted"] = True
        candidates[candidate_id]["votes"] += weight
    return jsonify({"vote_id": vote_id, "voter_id": voter_id, "candidate_id": candidate_id, "weight": weight}), 234

# Q15
@app.route('/api/votes/range', methods=['GET'])
def get_range_votes():
    candidate_id = request.args.get('candidate_id')
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    if not all([candidate_id, from_time, to_time]):
        abort(400, description=json.dumps({"message": "Missing required parameters: candidate_id, from, to"}))
    try:
        candidate_id = int(candidate_id)
        from_dt = datetime.fromisoformat(from_time.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_time.replace('Z', '+00:00'))
    except ValueError:
        abort(400, description=json.dumps({"message": "Invalid datetime format or candidate_id"}))
    if from_dt > to_dt:
        abort(424, description=json.dumps({"message": "invalid interval: from > to"}))
    with data_lock:
        if candidate_id not in candidates:
            abort(417, description=json.dumps({"message": f"candidate with id: {candidate_id} was not found"}))
        count = sum(v["weight"] for v in votes if v["candidate_id"] == candidate_id and
                   from_dt <= datetime.fromisoformat(v["timestamp"].replace('Z', '+00:00')) <= to_dt)
    return jsonify({"candidate_id": candidate_id, "from": from_time, "to": to_time, "votes_gained": count}), 235

# Q16
@app.route('/api/ballots/encrypted', methods=['POST'])
def submit_encrypted_ballot():
    data = request.json
    required = ['election_id', 'ciphertext', 'zk_proof', 'voter_pubkey', 'nullifier', 'signature']
    if not data or not all(k in data for k in required):
        abort(400, description=json.dumps({"message": "Missing required fields for encrypted ballot"}))
    with data_lock:
        if any(b["nullifier"] == data["nullifier"] for b in encrypted_ballots):
            abort(423, description=json.dumps({"message": "nullifier already used"}))
        ballot_id = f"b_{len(encrypted_ballots) + 1:04d}"
        encrypted_ballots.append({"ballot_id": ballot_id, "data": data, "nullifier": data["nullifier"],
                                "timestamp": get_iso_timestamp()})
    return jsonify({"ballot_id": ballot_id, "status": "accepted", "nullifier": data["nullifier"],
                   "anchored_at": get_iso_timestamp()}), 236

# Q17
@app.route('/api/results/homomorphic', methods=['POST'])
def homomorphic_tally():
    data = request.json
    if not data or 'election_id' not in data or 'trustee_decrypt_shares' not in data:
        abort(400, description=json.dumps({"message": "Missing required fields"}))
    if not isinstance(data['trustee_decrypt_shares'], list) or len(data['trustee_decrypt_shares']) < 3:
        abort(400, description=json.dumps({"message": "At least 3 trustee decrypt shares are required"}))
    with data_lock:
        tallies = [{"candidate_id": k, "votes": v["votes"]} for k, v in candidates.items()]
    return jsonify({"election_id": data['election_id'], "encrypted_tally_root": f"0x{hash(str(candidates))%1000000:x}",
                   "candidate_tallies": tallies, "decryption_proof": "mock_proof",
                   "transparency": {"ballot_merkle_root": f"0x{hash(str(votes))%1000000:x}",
                                   "tally_method": "threshold_paillier", "threshold": "3-of-5"}}), 237

# Q18
@app.route('/api/analytics/dp', methods=['POST'])
def get_dp_analytics():
    data = request.json
    if not data or 'election_id' not in data or 'query' not in data or 'epsilon' not in data or 'delta' not in data:
        abort(400, description=json.dumps({"message": "Missing required fields"}))
    epsilon = data['epsilon']
    if epsilon > 2.0:
        abort(423, description=json.dumps({"message": "Insufficient privacy budget"}))
    query = data['query']
    if query.get('type') != 'histogram' or query.get('dimension') != 'voter_age_bucket':
        abort(400, description=json.dumps({"message": "Unsupported query type"}))
    with data_lock:
        buckets = query.get('buckets', ["18-24", "25-34", "35-44", "45-64", "65+"])
        counts = defaultdict(int)
        for v in voters.values():
            if query.get('filter', {}).get('has_voted', False) and not v["has_voted"]: continue
            def get_bucket(age, buckets):
                for b in buckets:
                    if '-' in b:
                        start, end = map(int, b.split('-'))
                        if start <= age <= end:
                            return b
                    elif b == "65+" and age >= 65:
                        return b
                return "65+"
            bucket = get_bucket(v['age'], buckets)
            if bucket in buckets: counts[bucket] += 1
        answer = {b: max(0, int(counts[b] + random.gauss(0, max(1, counts[b]/(10*epsilon))))) for b in buckets}
    return jsonify({"answer": answer, "noise_mechanism": "gaussian", "epsilon_spent": epsilon,
                   "delta": data['delta'], "remaining_privacy_budget": {"epsilon": 2.0 - epsilon, "delta": 1e-6},
                   "composition_method": "advanced_composition"}), 238

# Q19
@app.route('/api/ballots/ranked', methods=['POST'])
def submit_ranked_ballot():
    data = request.json
    if not data or 'election_id' not in data or 'voter_id' not in data or 'ranking' not in data:
        abort(400, description=json.dumps({"message": "Missing required fields for ranked ballot"}))
    voter_id, election_id = data['voter_id'], data['election_id']
    with data_lock:
        if any(b["data"]["voter_id"] == voter_id and b["data"]["election_id"] == election_id for b in ranked_ballots):
            abort(423, description=json.dumps({"message": f"voter {voter_id} has already voted in election {election_id}"}))
        ballot_id = f"rb_{len(ranked_ballots) + 1:04d}"
        ranked_ballots.append({"ballot_id": ballot_id, "data": data})
    return jsonify({"ballot_id": ballot_id, "status": "accepted"}), 239

# Q20
@app.route('/api/audits/plan', methods=['POST'])
def create_audit_plan():
    data = request.json
    if not data or 'election_id' not in data or 'reported_tallies' not in data or 'risk_limit_alpha' not in data:
        abort(400, description=json.dumps({"message": "Missing required fields"}))
    alpha = data['risk_limit_alpha']
    with data_lock:
        total_votes = sum(t["votes"] for t in data['reported_tallies'])
    initial_sample_size = max(1200, int(total_votes * (-math.log(alpha) * 0.1)))
    fake_csv = "county,proportion,seed\nA,0.3,123\nB,0.4,456\nC,0.3,789"
    sampling_plan = base64.b64encode(fake_csv.encode()).decode()
    audit_id = f"rla_{len(encrypted_ballots) + 1:04d}"
    return jsonify({"audit_id": audit_id, "initial_sample_size": initial_sample_size, "sampling_plan": sampling_plan,
                   "test": "kaplan-markov", "status": "planned"}), 240

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)


  