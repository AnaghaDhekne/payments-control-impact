"""Build clean and degraded observable benchmark views.

Ground truth stays in data/ground_truth. Outputs here are the only artifacts that
baseline/hybrid systems may consume.
"""
from __future__ import annotations
import json, random, hashlib
from collections import defaultdict, deque
from pathlib import Path

try:
    ROOT=Path(__file__).resolve().parents[1]
except NameError:
    ROOT=Path.cwd().parent
GT_GRAPH=ROOT/"data"/"ground_truth"/"payment_graph_benchmark.json"
GT_CHANGES=ROOT/"data"/"ground_truth"/"benchmark_changes.json"
OUT=ROOT/"data"/"observable"
SEED=20261007
LEVELS=(0,30,60)
MODES=("random","correlated")

def stable_seed(*parts):
    s="|".join(map(str,parts)).encode()
    return int(hashlib.sha256(s).hexdigest()[:16],16)

def load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def undirected_distance(graph,start):
    adj=defaultdict(set)
    for e in graph["edges"]:
        adj[e["source"]].add(e["target"]); adj[e["target"]].add(e["source"])
    dist={start:0}; q=deque([start])
    while q:
        x=q.popleft()
        for y in adj[x]:
            if y not in dist: dist[y]=dist[x]+1; q.append(y)
    return dist

def clean_metadata(graph):
    return {
      "version":graph["version"],
      "nodes":[{k:v for k,v in n.items() if k not in {"family"}} for n in graph["nodes"]],
      "edges":[e.copy() for e in graph["edges"] if e.get("metadata_exposable",True)]
    }

def control_narratives(graph):
    rows=[]
    for n in graph["nodes"]:
        if n["type"]=="CONTROL":
            rows.append({
              "document_id":f"DOC-{n['id']}",
              "control_id":n["id"],
              "title":n["name"],
              "text":n.get("description",""),
              "criticality":n.get("criticality","STANDARD")
            })
    return rows

def change_tickets(changes,nodes):
    byid={n["id"]:n for n in nodes}
    rows=[]
    for c in changes:
        names=", ".join(byid[x]["name"] for x in c["changed_node_ids"])
        rows.append({
          "document_id":f"TICKET-{c['change_id']}",
          "change_id":c["change_id"],
          "title":c["title"],
          "text":f"Release changes {names}. Implementation date: {c['implementation_date']}. Change type: {c['change_type']}.",
          "changed_entity_ids":c["changed_node_ids"],
          "implementation_date":c["implementation_date"]
        })
    return rows

def degrade_edges(graph,change,level,mode):
    edges=[e.copy() for e in graph["edges"] if e.get("metadata_exposable",True)]
    if level==0: return edges,[]
    k=round(len(edges)*level/100)
    rng=random.Random(stable_seed(SEED,change["change_id"],level,mode,"edges"))
    if mode=="random":
        candidates=edges[:]; rng.shuffle(candidates); removed=candidates[:k]
    else:
        dists=[undirected_distance(graph,s) for s in change["changed_node_ids"]]
        def proximity(e):
            vals=[]
            for d in dists:
                vals.extend([d.get(e["source"],999),d.get(e["target"],999)])
            return min(vals)
        # deterministic jitter breaks ties without always deleting same edge type.
        scored=[(proximity(e),rng.random(),e) for e in edges]
        scored.sort(key=lambda x:(x[0],x[1]))
        removed=[x[2] for x in scored[:k]]
    gone={e["id"] for e in removed}
    return [e for e in edges if e["id"] not in gone],sorted(gone)

def degrade_text(text, aliases, level, rng, misleading=False):
    if level==0: return text,[]
    ops=[]; out=text
    if aliases and rng.random() < level/100:
        # Prefix a legacy alias to simulate stale terminology while retaining readable text.
        out=f"Legacy reference: {aliases[0]}. "+out; ops.append("legacy_alias")
    if rng.random() < level/100:
        sentences=[s.strip() for s in out.split(".") if s.strip()]
        if len(sentences)>1:
            out=". ".join(sentences[:-1])+"."; ops.append("omit_sentence")
    if misleading and rng.random() < level/100:
        out+=" Ticket assessment: control impact: N/A."; ops.append("misleading_no_impact")
    return out,ops

def build_condition(graph,changes,level,mode):
    clean=clean_metadata(graph); nodes={n["id"]:n for n in graph["nodes"]}
    controls=control_narratives(graph); tickets=change_tickets(changes,graph["nodes"])
    cases=[]
    for c in changes:
        visible_edges,removed=degrade_edges(graph,c,level,mode)
        rng=random.Random(stable_seed(SEED,c["change_id"],level,mode,"text"))
        changed_aliases=[]
        for nid in c["changed_node_ids"]:
            changed_aliases += nodes[nid].get("aliases",[])
        ticket=next(x.copy() for x in tickets if x["change_id"]==c["change_id"])
        ticket["text"],ticket_ops=degrade_text(ticket["text"],changed_aliases,level,rng,misleading=(int(c["change_id"].split("-")[1])%7==0))
        degraded_controls=[]
        text_ops={}
        for doc in controls:
            d=doc.copy()
            cn=nodes[d["control_id"]]
            crng=random.Random(stable_seed(SEED,c["change_id"],d["control_id"],level,mode,"controltext"))
            d["text"],ops=degrade_text(d["text"],cn.get("aliases",[]),level,crng)
            if ops:text_ops[d["control_id"]]=ops
            degraded_controls.append(d)
        cases.append({
          "change_id":c["change_id"],"split":c["split"],
          "visible_metadata":{"nodes":clean["nodes"],"edges":visible_edges},
          "change_ticket":ticket,"control_documents":degraded_controls,
          "degradation_manifest":{"level":level,"mode":mode,"removed_edge_ids":removed,"ticket_operations":ticket_ops,"control_text_operations":text_ops}
        })
    return {"seed":SEED,"level":level,"mode":mode,"cases":cases}

def main():
    graph=load_json(GT_GRAPH); changes=load_json(GT_CHANGES)
    OUT.mkdir(parents=True,exist_ok=True)
    for level in LEVELS:
        for mode in MODES:
            payload=build_condition(graph,changes,level,mode)
            (OUT/f"benchmark_{level}_{mode}.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print("generated",len(LEVELS)*len(MODES),"observable conditions")

if __name__=="__main__": main()
