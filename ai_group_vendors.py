import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
import json
import numpy as np
from sklearn.cluster import DBSCAN
from openai import OpenAI
from supabase_client import supabase
from config.client_context import get_current_client

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_payment_processor(vendor_name: str) -> bool:
    """Check if a vendor is a payment processor."""
    payment_processors = [
        "STRIPE", "PAYPAL", "SHOPIFY", "AFRM", "SHOPPAYINST",
        "SQUARE", "VENMO", "ZELLE", "CASHAPP", "WISE",
        "REVOLUT", "TRANSFERWISE", "MERCADOPAGO", "KLARNA",
        "AFFIRM", "AFTERPAY", "SHOPPAY", "APPLEPAY", "GOOGLEPAY"
    ]
    return any(processor in vendor_name.upper() for processor in payment_processors)

def fetch_unlocked_vendors(client_id=None):
    if client_id is None:
        client_id = get_current_client()
    
    resp = supabase.table("vendors") \
        .select("vendor_name") \
        .eq("client_id", client_id) \
        .eq("group_locked", False) \
        .execute()
    return [row["vendor_name"] for row in resp.data]

def embed_texts(texts, model="text-embedding-ada-002"):
    resp = client.embeddings.create(input=texts, model=model)
    return np.array([e.embedding for e in resp.data])

def cluster_embeddings(embeddings, eps=0.1, min_samples=2):
    # cosine distance = 1 - cosine similarity
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine") \
        .fit(embeddings)
    return clustering.labels_

def name_cluster(vendor_list):
    prompt = f"""You are a CFO assistant.  
Given these vendor strings that all refer to the same underlying payee, propose a concise, human-friendly **display_name** for them:
{json.dumps(vendor_list, indent=2)}

Return ONLY the name."""
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}]
    )
    return resp.choices[0].message.content.strip()

def write_back_cluster(vendors, cluster_id, display_name, client_id=None):
    if client_id is None:
        client_id = get_current_client()
    
    for v in vendors:
        supabase.table("vendors").update({
            "display_name": display_name,
            "vendor_group": display_name,
            "group_locked": True
        }).eq("client_id", client_id) \
          .eq("vendor_name", v).execute()

def run():
    client_id = get_current_client()
    print(f"Running AI vendor grouping for client: {client_id}")
    vendor_names = fetch_unlocked_vendors(client_id)
    if not vendor_names:
        print("No unlocked vendors found.")
        return

    print(f"Found {len(vendor_names)} unlocked vendors")

    # Separate payment processors from other vendors
    payment_processors = []
    other_vendors = []
    for vendor in vendor_names:
        if is_payment_processor(vendor):
            payment_processors.append(vendor)
        else:
            other_vendors.append(vendor)

    print(f"\nFound {len(payment_processors)} payment processors:")
    for pp in payment_processors:
        print(f"  - {pp}")
        # Keep payment processors as individual entries
        supabase.table("vendors").update({
            "display_name": pp,
            "vendor_group": pp,
            "group_locked": True
        }).eq("client_id", client_id) \
          .eq("vendor_name", pp).execute()

    if not other_vendors:
        print("\nNo other vendors to cluster.")
        return

    print(f"\nClustering {len(other_vendors)} other vendors...")

    # 2) Embed all other vendor names
    embs = embed_texts(other_vendors)
    print("Generated embeddings")

    # 3) Cluster
    labels = cluster_embeddings(embs)
    print("Clustered vendors")

    # 4) For each cluster, generate and write back a name
    clusters = {}
    for name, lbl in zip(other_vendors, labels):
        clusters.setdefault(lbl, []).append(name)

    print(f"\nFound {len(clusters)} clusters:")
    for lbl, members in clusters.items():
        if lbl == -1:
            print(f"\nSkipping noise cluster with {len(members)} vendors:")
            for v in members:
                print(f"  - {v}")
            continue
        
        print(f"\nCluster {lbl} ({len(members)} vendors):")
        for v in members:
            print(f"  - {v}")
        display_name = name_cluster(members)
        print(f"  → {display_name}")
        write_back_cluster(members, lbl, display_name, client_id)

    print("\nAI vendor clustering complete.")

if __name__ == "__main__":
    run() 